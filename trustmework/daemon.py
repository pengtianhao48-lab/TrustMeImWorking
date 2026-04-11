"""
Daemon — persistent background runner for TrustMeImWorking.

`tmw start` forks a background process that loops forever:
  - Every minute it checks whether it should run a consumption session.
  - In work-sim mode: only fires during work hours on weekdays.
  - In random mode: fires once per day at a random time.
  - After each session it sleeps until the next check interval.
  - All output is appended to a log file alongside the config.

`tmw stop`  sends SIGTERM to the daemon and removes the PID file.
`tmw logs`  tails the log file.
`tmw start --foreground`  runs in the current terminal (no fork).
"""

from __future__ import annotations

import datetime
import os
import random
import signal
import sys
import time
from pathlib import Path
from typing import Optional

# Python 3.9+ has zoneinfo in stdlib; 3.8 needs backports.zoneinfo
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
from .platforms import get_default_model
from .display import print_info, print_success, print_warning, print_error, print_mode_header, print_skipped

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
        os.kill(pid, 0)  # signal 0 = check existence only
        return True
    except (ProcessLookupError, PermissionError):
        _remove_pid(config_path)
        return False


# ── Logging redirect ──────────────────────────────────────────────────────────

def _redirect_output(config_path: str) -> None:
    """Redirect stdout/stderr to the log file (background mode)."""
    log = _log_path(config_path)
    fd = open(log, "a", buffering=1, encoding="utf-8")
    sys.stdout = fd
    sys.stderr = fd


def _log(msg: str) -> None:
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{ts}] {msg}", flush=True)


# ── Next-run scheduling ───────────────────────────────────────────────────────

def _seconds_until_next_check() -> int:
    """Sleep 60 seconds between loop ticks."""
    return 60


def _random_fire_time(tz) -> datetime.time:
    """
    Pick a random time during the day for random-mode firing.
    Stored in a module-level dict keyed by date so it's stable within a day.
    """
    today = datetime.datetime.now(tz).date()
    key = str(today)
    if not hasattr(_random_fire_time, "_cache"):
        _random_fire_time._cache = {}  # type: ignore[attr-defined]
    if key not in _random_fire_time._cache:  # type: ignore[attr-defined]
        # Random time between 08:00 and 22:00
        h = random.randint(8, 21)
        m = random.randint(0, 59)
        _random_fire_time._cache[key] = datetime.time(h, m)  # type: ignore[attr-defined]
        # Evict old dates
        _random_fire_time._cache = {k: v for k, v in _random_fire_time._cache.items()  # type: ignore[attr-defined]
                                     if k >= str(today)}
    return _random_fire_time._cache[key]  # type: ignore[attr-defined]


# ── Single-session runner (called from the loop) ──────────────────────────────

def _run_session(config: dict, config_path: str) -> None:
    """Execute one consumption session (random or work-sim)."""
    tz = _resolve_tz(config)
    state = st.load(config_path)
    token_field = config.get("token_field") or None
    model = config.get("model") or get_default_model(config.get("platform", "openai"))

    import random as _random
    weekly_target = _random.randint(config["weekly_min"], config["weekly_max"])

    if config.get("simulate_work"):
        _run_work_session(config, config_path, tz, state, token_field, model, weekly_target)
    else:
        _run_random_session(config, config_path, tz, state, token_field, model, weekly_target)


def _run_random_session(config, config_path, tz, state, token_field, model, weekly_target):
    import random as _r
    daily_tgt = _daily_target(weekly_target, 7)
    today = st.today_consumed(state, tz)
    remaining = daily_tgt - today

    _log(f"[Random Mode] daily_target={daily_tgt:,}  consumed={today:,}  remaining={remaining:,}")

    if remaining <= 0:
        _log("Daily target already reached — skipping session.")
        return

    client = _build_client(config)
    _log(f"Using model: {model}")

    prompts = RANDOM_PROMPTS.copy()
    _r.shuffle(prompts)
    pool = prompts * ((remaining // 200) + 5)

    total = 0
    for prompt in pool:
        if total >= remaining:
            break
        tokens = _call_api(client, model, prompt, token_field)
        if tokens:
            total += tokens
            st.record(config_path, state, tokens, tz)
            _log(f"  +{tokens:,} tokens  (prompt: {prompt[:60]}…)  total={total:,}/{remaining:,}")
        if total < remaining:
            sleep = _r.randint(10, 60)
            _log(f"  Sleeping {sleep}s…")
            time.sleep(sleep)

    _log(f"Session done. Consumed {total:,} tokens.")


def _run_work_session(config, config_path, tz, state, token_field, model, weekly_target):
    import random as _r
    now = datetime.datetime.now(tz)

    # Weekend check
    if now.weekday() >= 5:
        _log("Weekend — skipping session.")
        return

    work_start = _parse_hhmm(config["work_start"])
    work_end   = _parse_hhmm(config["work_end"])
    job_desc   = config.get("job_description", "software engineer")
    segments   = _work_segments(work_start, work_end)
    weight     = _current_segment(now.time(), segments)

    if weight is None:
        _log(f"Outside work hours ({now.strftime('%H:%M')}) — skipping session.")
        return

    daily_tgt = _daily_target(weekly_target, 5)
    today = st.today_consumed(state, tz)
    remaining = daily_tgt - today

    _log(f"[Work-Sim Mode] {now.strftime('%H:%M')}  job={job_desc}  "
         f"daily_target={daily_tgt:,}  consumed={today:,}  remaining={remaining:,}")

    if remaining <= 0:
        _log("Daily target already reached — skipping session.")
        return

    seg_tgt = int(remaining * weight * _r.uniform(0.75, 1.25))
    seg_tgt = max(1, min(seg_tgt, remaining))
    _log(f"Segment weight {weight:.0%} → targeting ~{seg_tgt:,} tokens this session.")

    client = _build_client(config)
    _log(f"Using model: {model}")
    _log("Generating work-relevant prompts…")
    work_prompts = _generate_work_prompts(client, model, job_desc, token_field)
    _log(f"Generated {len(work_prompts)} prompts.")

    pool = (work_prompts * 20)
    _r.shuffle(pool)

    total = 0
    for prompt in pool:
        if total >= seg_tgt:
            break
        tokens = _call_api(client, model, prompt, token_field)
        if tokens:
            total += tokens
            st.record(config_path, state, tokens, tz)
            _log(f"  +{tokens:,} tokens  (prompt: {prompt[:60]}…)  total={total:,}/{seg_tgt:,}")
        if total < seg_tgt:
            sleep = _r.randint(30, 180)
            _log(f"  Sleeping {sleep}s…")
            time.sleep(sleep)

    _log(f"Session done. Consumed {total:,} tokens.")


# ── Should-fire logic ─────────────────────────────────────────────────────────

def _should_fire_now(config: dict, tz, last_fired_date: Optional[datetime.date]) -> bool:
    """
    Decide whether to start a session right now.

    Work-sim mode: fire whenever we're inside a work segment (engine will
    skip if already at target). The loop checks every minute, so sessions
    are naturally spaced by the inter-call sleep inside the session itself.

    Random mode: fire once per day at the randomly chosen time.
    """
    now = datetime.datetime.now(tz)
    today = now.date()

    if config.get("simulate_work"):
        # Don't re-fire on the same minute (sessions are long)
        if last_fired_date == today:
            return False
        work_start = _parse_hhmm(config["work_start"])
        work_end   = _parse_hhmm(config["work_end"])
        segments   = _work_segments(work_start, work_end)
        return _current_segment(now.time(), segments) is not None and now.weekday() < 5
    else:
        fire_time = _random_fire_time(tz)
        now_t = now.time()
        # Fire within a 1-minute window of the chosen time
        fire_dt = datetime.datetime.combine(today, fire_time, tzinfo=tz)
        diff = abs((now - fire_dt).total_seconds())
        return diff < 60 and last_fired_date != today


# ── Main daemon loop ──────────────────────────────────────────────────────────

def _daemon_loop(config: dict, config_path: str) -> None:
    """Run forever, firing sessions at the right times."""
    tz = _resolve_tz(config)
    last_fired_date: Optional[datetime.date] = None

    _log("=" * 60)
    _log("TrustMeImWorking daemon started.")
    mode = "Work-Simulation" if config.get("simulate_work") else "Random"
    _log(f"Mode: {mode}  |  Config: {config_path}")
    _log("=" * 60)

    def _handle_sigterm(signum, frame):
        _log("Received SIGTERM — shutting down gracefully.")
        _remove_pid(config_path)
        sys.exit(0)

    signal.signal(signal.SIGTERM, _handle_sigterm)
    signal.signal(signal.SIGINT,  _handle_sigterm)

    while True:
        try:
            now_date = datetime.datetime.now(tz).date()

            if _should_fire_now(config, tz, last_fired_date):
                _log(f"Firing session at {datetime.datetime.now(tz).strftime('%Y-%m-%d %H:%M:%S')}")
                _run_session(config, config_path)
                last_fired_date = now_date
            else:
                # Quiet tick — only log once per hour to avoid log spam
                now = datetime.datetime.now(tz)
                if now.minute == 0:
                    _log(f"Heartbeat {now.strftime('%H:%M')} — waiting for next session window.")

        except Exception as exc:
            _log(f"ERROR in daemon loop: {exc}")

        time.sleep(_seconds_until_next_check())


# ── Public API ────────────────────────────────────────────────────────────────

def start(config: dict, config_path: str, foreground: bool = False) -> None:
    """
    Start the daemon.

    foreground=True  → run in the current process (blocks).
    foreground=False → fork to background, write PID file, return immediately.
    """
    config_path = str(Path(config_path).resolve())

    if _is_running(config_path):
        pid = _read_pid(config_path)
        print_warning(f"Daemon already running (PID {pid}). Use 'tmw stop' to stop it.")
        return

    if foreground:
        print_info("Running in foreground mode. Press Ctrl+C to stop.")
        _write_pid(config_path)
        try:
            _daemon_loop(config, config_path)
        finally:
            _remove_pid(config_path)
        return

    # Fork to background
    pid = os.fork()
    if pid > 0:
        # Parent process — report and exit
        log = _log_path(config_path)
        print_success(f"Daemon started in background (PID {pid}).")
        print_info(f"Logs: {log}")
        print_info(f"Stop: tmw stop --config {config_path}")
        return

    # Child process — become daemon
    os.setsid()
    _write_pid(config_path)
    _redirect_output(config_path)
    _daemon_loop(config, config_path)


def stop(config_path: str) -> None:
    """Send SIGTERM to the running daemon."""
    config_path = str(Path(config_path).resolve())
    pid = _read_pid(config_path)

    if pid is None or not _is_running(config_path):
        print_warning("No running daemon found for this config.")
        return

    try:
        os.kill(pid, signal.SIGTERM)
        # Wait up to 5 seconds for the process to exit
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
    """Print daemon status."""
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
    """Print the last N lines of the log file."""
    config_path = str(Path(config_path).resolve())
    log = _log_path(config_path)

    if not log.exists():
        print_warning("No log file found. Has the daemon been started?")
        return

    all_lines = log.read_text(encoding="utf-8", errors="replace").splitlines()
    tail = all_lines[-lines:]
    for line in tail:
        print(line)
