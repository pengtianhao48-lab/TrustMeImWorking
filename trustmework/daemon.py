"""
Daemon — persistent background runner for TrustMeImWorking.

`tmw start`
  Default (foreground dashboard mode):
    - Daemon loop runs in a background thread
    - Main thread renders a Rich Live dashboard that refreshes every 2 s
    - Shows: daemon status, today/week consumption progress bars,
      next-session countdown, and the last 8 log lines
    - Press Ctrl+C to stop

`tmw start --background`
  Silent background process (fork), logs to <config>.log

`tmw stop`   sends SIGTERM to the background daemon
`tmw logs`   tails the log file
"""

from __future__ import annotations

import datetime
import os
import random
import signal
import sys
import threading
import time
from collections import deque
from pathlib import Path
from typing import Deque, List, Optional, Tuple

try:
    import zoneinfo
except ImportError:
    try:
        from backports import zoneinfo  # type: ignore[no-redef]
    except ImportError:
        zoneinfo = None  # type: ignore[assignment]

from .engine import (
    _resolve_tz, _daily_target, _parse_hhmm, _work_segments, _current_segment,
    _build_client, _call_api, _generate_work_prompts, RANDOM_PROMPTS,
)
from . import state as st
from .platforms import get_default_model, PLATFORM_DISPLAY_NAMES
from .display import print_info, print_success, print_warning, print_error
from . import i18n


# ── Path helpers ──────────────────────────────────────────────────────────────

def _pid_path(config_path: str) -> Path:
    return Path(config_path).with_suffix(".pid")


def _log_path(config_path: str) -> Path:
    return Path(config_path).with_suffix(".log")


# ── PID management ────────────────────────────────────────────────────────────

def _write_pid(config_path: str) -> None:
    _pid_path(config_path).write_text(str(os.getpid()))


def _read_pid(config_path: str) -> Optional[int]:
    p = _pid_path(config_path)
    if not p.exists():
        return None
    try:
        return int(p.read_text().strip())
    except (ValueError, OSError):
        return None


def _remove_pid(config_path: str) -> None:
    try:
        _pid_path(config_path).unlink()
    except OSError:
        pass


def _is_running(config_path: str) -> bool:
    pid = _read_pid(config_path)
    if pid is None:
        return False
    try:
        os.kill(pid, 0)
        return True
    except (ProcessLookupError, PermissionError):
        _remove_pid(config_path)
        return False


# ── Logging ───────────────────────────────────────────────────────────────────

def _redirect_output(config_path: str) -> None:
    log = _log_path(config_path)
    fd = open(log, "a", buffering=1, encoding="utf-8")
    sys.stdout = fd
    sys.stderr = fd


def _ts() -> str:
    return datetime.datetime.now().strftime("%H:%M:%S")


# ── Shared dashboard state ────────────────────────────────────────────────────

class DashState:
    """Thread-safe state shared between daemon thread and dashboard renderer."""

    def __init__(self, config: dict, config_path: str):
        self._lock = threading.Lock()
        self.config = config
        self.config_path = config_path
        self.tz = _resolve_tz(config)
        # Apply language from config
        i18n.set_lang(config.get("lang", "en"))

        # Consumption
        self.today_tokens: int = 0
        self.week_tokens: int = 0
        self.daily_target: int = 0
        self.weekly_min: int = config.get("weekly_min", 0)
        self.weekly_max: int = config.get("weekly_max", 0)
        self.last_7: List[Tuple[str, int]] = []

        # Session
        self.session_active: bool = False
        self.session_tokens: int = 0
        self.session_target: int = 0
        self.last_prompt: str = ""

        # Timing
        self.started_at: datetime.datetime = datetime.datetime.now()
        self.next_check_at: Optional[datetime.datetime] = None
        self.last_fired: Optional[datetime.datetime] = None

        # Log ring buffer (last 8 lines)
        self.log_lines: Deque[str] = deque(maxlen=8)

        # Control
        self.running: bool = True
        self.stop_event = threading.Event()

    def log(self, msg: str) -> None:
        line = f"[{_ts()}] {msg}"
        with self._lock:
            self.log_lines.append(line)
        # Also write to log file
        log_path = _log_path(self.config_path)
        try:
            with open(log_path, "a", encoding="utf-8") as f:
                f.write(line + "\n")
        except OSError:
            pass

    def refresh_consumption(self) -> None:
        state = st.load(self.config_path)
        with self._lock:
            self.today_tokens = st.today_consumed(state, self.tz)
            self.week_tokens  = st.week_consumed(state, self.tz)
            self.last_7       = st.last_n_days(state, self.tz, 7)
            wt = random.randint(self.weekly_min, self.weekly_max)
            divisor = 5 if self.config.get("simulate_work") else 7
            self.daily_target = _daily_target(wt, divisor)

    def snapshot(self) -> dict:
        with self._lock:
            return {
                "today": self.today_tokens,
                "week": self.week_tokens,
                "daily_target": self.daily_target,
                "weekly_min": self.weekly_min,
                "weekly_max": self.weekly_max,
                "last_7": list(self.last_7),
                "session_active": self.session_active,
                "session_tokens": self.session_tokens,
                "session_target": self.session_target,
                "last_prompt": self.last_prompt,
                "started_at": self.started_at,
                "next_check_at": self.next_check_at,
                "last_fired": self.last_fired,
                "log_lines": list(self.log_lines),
                "running": self.running,
            }


# ── Consumption helpers ───────────────────────────────────────────────────────

def _mode(config: dict) -> str:
    """Return 'immediate', 'spread', or 'work'."""
    if config.get("simulate_work"):
        return "work"
    return config.get("mode", "immediate")


def _should_fire_now(config: dict, tz, last_fired_date: Optional[datetime.date]) -> bool:
    """
    Decide whether to start a consumption session right now.

    work      — fire whenever inside a work segment on weekdays.
    immediate — fire immediately at startup (today) or at 00:00 each subsequent day.
    spread    — fire periodically throughout the day; the session itself handles pacing.
    """
    now = datetime.datetime.now(tz)
    today = now.date()
    mode = _mode(config)

    if mode == "work":
        if last_fired_date == today:
            return False
        work_start = _parse_hhmm(config["work_start"])
        work_end   = _parse_hhmm(config["work_end"])
        segments   = _work_segments(work_start, work_end)
        return _current_segment(now.time(), segments) is not None and now.weekday() < 5

    elif mode == "immediate":
        # Today: fire right away (last_fired_date is None or a past date).
        # Subsequent days: fire as soon as midnight passes (00:00–00:01 window).
        if last_fired_date != today:
            if last_fired_date is None:
                return True  # first ever start — fire immediately
            # New day: fire within the first minute after midnight
            return now.hour == 0 and now.minute == 0
        return False

    else:  # spread
        # Spread fires one mini-session per "slot" throughout the day.
        # We divide the day into slots of ~30 min; fire once per slot.
        if last_fired_date != today:
            return True  # first session of the day — start now
        # After first session, the session loop itself handles pacing via sleep.
        return False


def _run_session_with_state(config: dict, config_path: str, ds: DashState) -> None:
    """Run one consumption session, updating DashState throughout."""
    tz = ds.tz
    state = st.load(config_path)
    token_field = config.get("token_field") or None
    model = config.get("model") or get_default_model(config.get("platform", "openai"))
    wt = random.randint(config["weekly_min"], config["weekly_max"])
    mode = _mode(config)

    if mode == "work":
        _work_session(config, config_path, tz, state, token_field, model, wt, ds)
    elif mode == "immediate":
        _immediate_session(config, config_path, tz, state, token_field, model, wt, ds)
    else:  # spread
        _spread_session(config, config_path, tz, state, token_field, model, wt, ds)


def _immediate_session(config, config_path, tz, state, token_field, model, weekly_target, ds: DashState):
    """Consume the full daily budget as fast as possible (short sleeps)."""
    import random as _r
    daily_tgt = _daily_target(weekly_target, 7)
    today = st.today_consumed(state, tz)
    remaining = daily_tgt - today

    ds.log(f"[Immediate] daily_target={daily_tgt:,}  consumed={today:,}  remaining={remaining:,}")
    if remaining <= 0:
        ds.log("Daily target reached — skipping.")
        return

    with ds._lock:
        ds.session_active = True
        ds.session_tokens = 0
        ds.session_target = remaining

    client = _build_client(config)
    prompts = RANDOM_PROMPTS.copy()
    _r.shuffle(prompts)
    pool = prompts * ((remaining // 200) + 5)

    total = 0
    for prompt in pool:
        if ds.stop_event.is_set():
            break
        if total >= remaining:
            break
        with ds._lock:
            ds.last_prompt = prompt[:80]
        tokens = _call_api(client, model, prompt, token_field)
        if tokens:
            total += tokens
            st.record(config_path, state, tokens, tz)
            ds.refresh_consumption()
            with ds._lock:
                ds.session_tokens = total
            ds.log(f"  +{tokens:,} tk  [{prompt[:50]}…]  total={total:,}/{remaining:,}")
        if total < remaining and not ds.stop_event.is_set():
            sleep = _r.randint(2, 8)  # short sleep — immediate mode
            ds.stop_event.wait(sleep)

    with ds._lock:
        ds.session_active = False
    ds.log(f"Session done. +{total:,} tokens.")


def _spread_session(config, config_path, tz, state, token_field, model, weekly_target, ds: DashState):
    """
    Consume the daily budget evenly across the remaining hours of the day.
    Calculates inter-call sleep dynamically so all tokens are consumed by midnight.
    """
    import random as _r
    daily_tgt = _daily_target(weekly_target, 7)
    today_consumed = st.today_consumed(state, tz)
    remaining = daily_tgt - today_consumed

    now = datetime.datetime.now(tz)
    midnight = (now + datetime.timedelta(days=1)).replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    secs_left = max((midnight - now).total_seconds(), 60)

    ds.log(
        f"[Spread] daily_target={daily_tgt:,}  consumed={today_consumed:,}  "
        f"remaining={remaining:,}  time_left={secs_left/3600:.1f}h"
    )
    if remaining <= 0:
        ds.log("Daily target reached — skipping.")
        return

    # Estimate inter-call sleep: spread remaining calls evenly over remaining time
    est_tokens_per_call = 400
    n_calls = max(remaining // est_tokens_per_call, 1)
    sleep_between = max(int(secs_left / n_calls), 5)
    ds.log(f"  ~{n_calls} calls planned, ~{sleep_between}s apart")

    with ds._lock:
        ds.session_active = True
        ds.session_tokens = 0
        ds.session_target = remaining

    client = _build_client(config)
    prompts = RANDOM_PROMPTS.copy()
    _r.shuffle(prompts)
    pool = prompts * ((remaining // 200) + 5)

    total = 0
    for prompt in pool:
        if ds.stop_event.is_set():
            break
        if total >= remaining:
            break
        with ds._lock:
            ds.last_prompt = prompt[:80]
        tokens = _call_api(client, model, prompt, token_field)
        if tokens:
            total += tokens
            st.record(config_path, state, tokens, tz)
            ds.refresh_consumption()
            with ds._lock:
                ds.session_tokens = total
            ds.log(f"  +{tokens:,} tk  [{prompt[:50]}…]  total={total:,}/{remaining:,}")
            # Recalculate sleep dynamically
            remaining_tokens = remaining - total
            if remaining_tokens > 0:
                now2 = datetime.datetime.now(tz)
                secs_left2 = max((midnight - now2).total_seconds(), 5)
                calls_left = max(remaining_tokens // max(tokens, 1), 1)
                sleep_between = max(int(secs_left2 / calls_left), 5)
        if total < remaining and not ds.stop_event.is_set():
            ds.log(f"  Sleeping {sleep_between}s…")
            ds.stop_event.wait(sleep_between)

    with ds._lock:
        ds.session_active = False
    ds.log(f"Session done. +{total:,} tokens.")


def _work_session(config, config_path, tz, state, token_field, model, weekly_target, ds: DashState):
    import random as _r
    now = datetime.datetime.now(tz)
    if now.weekday() >= 5:
        ds.log("Weekend — skipping.")
        return

    work_start = _parse_hhmm(config["work_start"])
    work_end   = _parse_hhmm(config["work_end"])
    job_desc   = config.get("job_description", "software engineer")
    segments   = _work_segments(work_start, work_end)
    weight     = _current_segment(now.time(), segments)

    if weight is None:
        ds.log(f"Outside work hours ({now.strftime('%H:%M')}) — skipping.")
        return

    daily_tgt = _daily_target(weekly_target, 5)
    today = st.today_consumed(state, tz)
    remaining = daily_tgt - today

    ds.log(f"[Work] {now.strftime('%H:%M')}  daily={daily_tgt:,}  consumed={today:,}  remaining={remaining:,}")
    if remaining <= 0:
        ds.log("Daily target reached — skipping.")
        return

    seg_tgt = int(remaining * weight * _r.uniform(0.75, 1.25))
    seg_tgt = max(1, min(seg_tgt, remaining))
    ds.log(f"Segment weight {weight:.0%} → targeting ~{seg_tgt:,} tokens.")

    with ds._lock:
        ds.session_active = True
        ds.session_tokens = 0
        ds.session_target = seg_tgt

    client = _build_client(config)
    ds.log("Generating work prompts…")
    work_prompts = _generate_work_prompts(client, model, job_desc, token_field)
    ds.log(f"Generated {len(work_prompts)} prompts.")

    pool = (work_prompts * 20)
    _r.shuffle(pool)

    total = 0
    for prompt in pool:
        if ds.stop_event.is_set():
            break
        if total >= seg_tgt:
            break
        with ds._lock:
            ds.last_prompt = prompt[:80]
        tokens = _call_api(client, model, prompt, token_field)
        if tokens:
            total += tokens
            st.record(config_path, state, tokens, tz)
            ds.refresh_consumption()
            with ds._lock:
                ds.session_tokens = total
            ds.log(f"  +{tokens:,} tk  [{prompt[:50]}…]  total={total:,}/{seg_tgt:,}")
        if total < seg_tgt and not ds.stop_event.is_set():
            sleep = _r.randint(30, 180)
            ds.log(f"  Sleeping {sleep}s…")
            ds.stop_event.wait(sleep)

    with ds._lock:
        ds.session_active = False
    ds.log(f"Session done. +{total:,} tokens.")


# ── Daemon thread loop ────────────────────────────────────────────────────────

def _daemon_thread(ds: DashState) -> None:
    config = ds.config
    config_path = ds.config_path
    tz = ds.tz
    last_fired_date: Optional[datetime.date] = None

    ds.log("Daemon started.")
    mode_map = {"work": "Work-Simulation", "immediate": "Immediate", "spread": "Spread"}
    mode = mode_map.get(_mode(config), _mode(config))
    ds.log(f"Mode: {mode}")

    while not ds.stop_event.is_set():
        try:
            ds.refresh_consumption()
            now_date = datetime.datetime.now(tz).date()

            if _should_fire_now(config, tz, last_fired_date):
                with ds._lock:
                    ds.last_fired = datetime.datetime.now(tz)
                ds.log(f"Firing session at {datetime.datetime.now(tz).strftime('%H:%M:%S')}")
                _run_session_with_state(config, config_path, ds)
                last_fired_date = now_date
            else:
                now = datetime.datetime.now(tz)
                if now.minute == 0 and now.second < 60:
                    ds.log(f"Heartbeat {now.strftime('%H:%M')} — waiting.")

            # Set next check time
            with ds._lock:
                ds.next_check_at = datetime.datetime.now() + datetime.timedelta(seconds=60)

        except Exception as exc:
            ds.log(f"ERROR: {exc}")

        ds.stop_event.wait(60)

    ds.log("Daemon stopped.")
    with ds._lock:
        ds.running = False


# ── Rich Live dashboard ───────────────────────────────────────────────────────

def _build_dashboard(snap: dict, config: dict, elapsed: str) -> "Table":
    from rich.table import Table
    from rich.panel import Panel
    from rich.progress import BarColumn, Progress, TextColumn
    from rich.columns import Columns
    from rich.text import Text
    from rich import box

    platform = PLATFORM_DISPLAY_NAMES.get(
        config.get("platform", "custom").lower(), config.get("platform", "custom")
    )
    _mode_key = {"work": "mode_work", "immediate": "mode_immediate", "spread": "mode_spread"}
    mode = i18n.t(_mode_key.get(_mode(config), "mode_immediate"))

    today     = snap["today"]
    daily_tgt = max(snap["daily_target"], 1)
    week      = snap["week"]
    wmin      = snap["weekly_min"]
    wmax      = snap["weekly_max"]
    last_7    = snap["last_7"]

    today_pct = min(today / daily_tgt, 1.0)
    week_pct  = min(week / max(wmax, 1), 1.0)

    BAR = 28

    def bar(pct: float, width: int = BAR) -> str:
        filled = int(pct * width)
        return "█" * filled + "░" * (width - filled)

    today_color = "green" if today_pct >= 1.0 else "cyan"
    week_color  = "green" if week_pct  >= 1.0 else "blue"

    # ── Top info row ──
    root = Table.grid(padding=(0, 2))
    root.add_column()

    # Header
    header = Table.grid(padding=(0, 3))
    header.add_column(style="bold cyan")
    header.add_column(style="dim")
    header.add_column(style="dim")
    header.add_row(
        "TrustMeImWorking",
        f"{i18n.t('platform_label')}: {platform}",
        f"{i18n.t('mode_label')}: {mode}",
    )
    header.add_row(
        "",
        f"{i18n.t('uptime_label')}: {elapsed}",
        (f"{i18n.t('config_label')}: {Path(snap.get('config_path', 'config.json')).name}"
         if "config_path" in snap else ""),
    )
    root.add_row(Panel(header, border_style="cyan", padding=(0, 1)))

    # ── Progress bars ──
    prog_table = Table.grid(padding=(0, 1))
    prog_table.add_column(width=14, style="bold")
    prog_table.add_column(width=BAR + 2)
    prog_table.add_column(width=22, style="dim")

    prog_table.add_row(
        i18n.t("today_label"),
        f"[{today_color}]{bar(today_pct)}[/{today_color}]",
        f"[{today_color}]{today:,}[/{today_color}] / {daily_tgt:,}  ({today_pct:.0%})",
    )
    prog_table.add_row(
        i18n.t("week_label"),
        f"[{week_color}]{bar(week_pct)}[/{week_color}]",
        f"[{week_color}]{week:,}[/{week_color}] / {wmin:,}–{wmax:,}",
    )
    root.add_row(Panel(prog_table,
                       title=f"[bold]{i18n.t('consumption_title')}",
                       border_style="blue", padding=(0, 1)))

    # ── Session status ──
    if snap["session_active"]:
        s_pct     = min(snap["session_tokens"] / max(snap["session_target"], 1), 1.0)
        day_pct   = min(today / max(daily_tgt, 1), 1.0)
        day_color = "green" if day_pct >= 1.0 else "cyan"
        sess_text = (
            f"[yellow]● {i18n.t('active_label')}[/yellow]  "
            f"{i18n.t('this_session')}: [yellow]{snap['session_tokens']:,}[/yellow]"
            f" / {snap['session_target']:,}  ({s_pct:.0%})\n"
            f"[dim]{bar(s_pct, BAR)}[/dim]\n"
            f"{i18n.t('todays_progress')}:  [{day_color}]{today:,}[/{day_color}]"
            f" / {daily_tgt:,}  ({day_pct:.0%})\n"
            f"[{day_color}]{bar(day_pct, BAR)}[/{day_color}]\n"
            f"[dim]{i18n.t('prompt_label')}: {snap['last_prompt'][:70]}[/dim]"
        )
    else:
        # Build next-request countdown string
        nxt = snap.get("next_check_at")
        if nxt:
            total_secs = max(0, int((nxt - datetime.datetime.now()).total_seconds()))
            mins, secs = divmod(total_secs, 60)
            if mins > 0:
                nxt_str = i18n.t("next_request_mins", mins=mins, secs=secs)
            else:
                nxt_str = i18n.t("next_request_secs", secs=secs)
        else:
            nxt_str = i18n.t("starting_up")
        last_f = snap.get("last_fired")
        last_str = last_f.strftime("%H:%M:%S") if last_f else "—"
        day_pct   = min(today / max(daily_tgt, 1), 1.0)
        day_color = "green" if day_pct >= 1.0 else "cyan"
        sess_text = (
            f"[dim]● {i18n.t('idle_label')}  {nxt_str}"
            f"  |  {i18n.t('last_session_label')}: {last_str}[/dim]\n"
            f"{i18n.t('todays_progress')}:  [{day_color}]{today:,}[/{day_color}]"
            f" / {daily_tgt:,}  ({day_pct:.0%})\n"
            f"[{day_color}]{bar(day_pct, BAR)}[/{day_color}]"
        )
    root.add_row(Panel(sess_text,
                       title=f"[bold]{i18n.t('session_title')}",
                       border_style="yellow", padding=(0, 1)))

    # ── Last 7 days sparkline ──
    if last_7:
        max_val = max(v for _, v in last_7) or 1
        spark_blocks = " ▁▂▃▄▅▆▇█"
        spark = ""
        for date_str, val in last_7:
            idx = int((val / max_val) * (len(spark_blocks) - 1))
            spark += spark_blocks[idx]
        days_text = "  ".join(
            f"[dim]{d[5:]}[/dim] [cyan]{v:,}[/cyan]" for d, v in last_7[-3:]
        )
        hist_text = f"[bold]{spark}[/bold]   {days_text}"
        root.add_row(Panel(hist_text,
                           title=f"[bold]{i18n.t('last7_title')}",
                           border_style="dim", padding=(0, 1)))

    # ── Log tail ──
    log_lines = snap["log_lines"]
    if log_lines:
        log_text = "\n".join(f"[dim]{line}[/dim]" for line in log_lines)
    else:
        log_text = f"[dim]{i18n.t('no_log_yet')}[/dim]"
    root.add_row(Panel(log_text,
                       title=f"[bold]{i18n.t('log_title')}",
                       border_style="dim", padding=(0, 1)))

    # Footer
    root.add_row(f"[dim]  {i18n.t('press_ctrl_c')}[/dim]")

    return root


def _run_dashboard(ds: DashState) -> None:
    """Main thread: render Rich Live dashboard until stop_event."""
    from rich.live import Live
    from rich.console import Console

    console = Console()
    started = datetime.datetime.now()

    def _elapsed() -> str:
        delta = datetime.datetime.now() - started
        h, rem = divmod(int(delta.total_seconds()), 3600)
        m, s = divmod(rem, 60)
        if h:
            return f"{h}h {m:02d}m {s:02d}s"
        return f"{m:02d}m {s:02d}s"

    with Live(console=console, refresh_per_second=0.5, screen=True) as live:
        while not ds.stop_event.is_set():
            snap = ds.snapshot()
            snap["config_path"] = ds.config_path
            try:
                panel = _build_dashboard(snap, ds.config, _elapsed())
                live.update(panel)
            except Exception:
                pass
            ds.stop_event.wait(2)


# ── Background (fork) mode ────────────────────────────────────────────────────

def _bg_daemon_loop(config: dict, config_path: str) -> None:
    """Simple loop for background (forked) mode — no Rich, logs to file."""
    tz = _resolve_tz(config)
    last_fired_date: Optional[datetime.date] = None

    def _log(msg: str) -> None:
        ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{ts}] {msg}", flush=True)

    def _handle_sigterm(signum, frame):
        _log("Received SIGTERM — shutting down.")
        _remove_pid(config_path)
        sys.exit(0)

    signal.signal(signal.SIGTERM, _handle_sigterm)
    signal.signal(signal.SIGINT,  _handle_sigterm)

    _log("=" * 60)
    _log("TrustMeImWorking background daemon started.")
    _mode_map = {"work": "Work-Simulation", "immediate": "Immediate (ASAP)", "spread": "Spread (even)"}
    mode = _mode_map.get(_mode(config), _mode(config))
    _log(f"Mode: {mode}  |  Config: {config_path}")
    _log("=" * 60)

    # Reuse DashState for its session logic but without dashboard
    ds = DashState(config, config_path)
    # Override log to use simple print
    def _simple_log(msg: str) -> None:
        _log(msg)
        with ds._lock:
            ds.log_lines.append(f"[{_ts()}] {msg}")
        log_path = _log_path(config_path)
        try:
            with open(log_path, "a", encoding="utf-8") as f:
                f.write(f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {msg}\n")
        except OSError:
            pass
    ds.log = _simple_log  # type: ignore[method-assign]

    while True:
        try:
            ds.refresh_consumption()
            now_date = datetime.datetime.now(tz).date()
            if _should_fire_now(config, tz, last_fired_date):
                _log(f"Firing session at {datetime.datetime.now(tz).strftime('%H:%M:%S')}")
                _run_session_with_state(config, config_path, ds)
                last_fired_date = now_date
            else:
                now = datetime.datetime.now(tz)
                if now.minute == 0:
                    _log(f"Heartbeat {now.strftime('%H:%M')} — waiting.")
        except Exception as exc:
            _log(f"ERROR: {exc}")
        time.sleep(60)


# ── Public API ────────────────────────────────────────────────────────────────

def start(config: dict, config_path: str, background: bool = False) -> None:
    """
    Start the daemon.

    background=False (default) → foreground dashboard mode:
      daemon loop runs in a thread, Rich Live dashboard in main thread.

    background=True → fork to background, silent, logs to file.
    """
    config_path = str(Path(config_path).resolve())

    if _is_running(config_path):
        pid = _read_pid(config_path)
        print_warning(f"Daemon already running (PID {pid}). Use 'tmw stop' to stop it.")
        return

    if background:
        if sys.platform == "win32":
            print_info("Background mode not supported on Windows — running dashboard mode.")
            background = False
        else:
            pid = os.fork()
            if pid > 0:
                log = _log_path(config_path)
                print_success(f"Daemon started in background (PID {pid}).")
                print_info(f"Logs: {log}")
                print_info("Stop: tmw stop")
                return
            os.setsid()
            _write_pid(config_path)
            _redirect_output(config_path)
            _bg_daemon_loop(config, config_path)
            return

    # ── Foreground dashboard mode ──────────────────────────────────────────────
    _write_pid(config_path)
    ds = DashState(config, config_path)
    ds.refresh_consumption()

    # Start daemon loop in background thread
    t = threading.Thread(target=_daemon_thread, args=(ds,), daemon=True)
    t.start()

    try:
        _run_dashboard(ds)
    except KeyboardInterrupt:
        pass
    finally:
        ds.stop_event.set()
        t.join(timeout=3)
        _remove_pid(config_path)
        # Print final summary after Live exits
        snap = ds.snapshot()
        print_success(
            f"Stopped. Session: today {snap['today']:,} / {snap['daily_target']:,} tokens  |  "
            f"week {snap['week']:,} tokens"
        )


def stop(config_path: str) -> None:
    config_path = str(Path(config_path).resolve())
    pid = _read_pid(config_path)

    if pid is None or not _is_running(config_path):
        print_warning("No running daemon found for this config.")
        return

    try:
        os.kill(pid, signal.SIGTERM)
        for _ in range(50):
            time.sleep(0.1)
            if not _is_running(config_path):
                break
        _remove_pid(config_path)
        print_success(f"Daemon (PID {pid}) stopped.")
    except ProcessLookupError:
        _remove_pid(config_path)
        print_warning("Process was already gone.")
    except PermissionError:
        print_error(f"Permission denied to kill PID {pid}.")


def status(config_path: str) -> None:
    config_path = str(Path(config_path).resolve())
    log = _log_path(config_path)
    if _is_running(config_path):
        pid = _read_pid(config_path)
        print_success(f"Daemon is RUNNING (PID {pid}).")
        print_info(f"Log file: {log}")
    else:
        print_warning("Daemon is NOT running.")
        if log.exists():
            print_info(f"Last log: {log}")


def logs(config_path: str, lines: int = 50) -> None:
    config_path = str(Path(config_path).resolve())
    log = _log_path(config_path)
    if not log.exists():
        print_warning("No log file found. Has the daemon been started?")
        return
    all_lines = log.read_text(encoding="utf-8", errors="replace").splitlines()
    for line in all_lines[-lines:]:
        print(line)
