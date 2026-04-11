#!/usr/bin/env python3
"""
TrustMeImWorking — CLI entry point.

Usage:
  tmw wizard                          # interactive setup → writes config.json
  tmw start    [--config PATH]        # start persistent daemon
  tmw stop     [--config PATH]        # stop daemon
  tmw logs     [--config PATH] [-n N] # tail daemon log
  tmw status   [--config PATH]        # consumption stats
  tmw run      [--config PATH] [--dry-run]  # single manual run
  tmw init     [--config PATH] [--mode MODE]
  tmw scheduler --install|--uninstall|--status [--config PATH]
  tmw platforms
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

try:
    import zoneinfo
except ImportError:
    try:
        from backports import zoneinfo  # type: ignore[no-redef]
    except ImportError:
        zoneinfo = None  # type: ignore[assignment]

from trustmework import __version__
from trustmework.display import print_banner, print_error, print_info, print_success, print_status_panel
from trustmework import config as cfg_mod
from trustmework import state as st
from trustmework import engine
from trustmework import scheduler as sched
from trustmework import i18n
from trustmework.platforms import PLATFORM_DISPLAY_NAMES, list_platforms

DEFAULT_CONFIG = "config.json"


# ── Helpers ───────────────────────────────────────────────────────────────────

def _load_config(path: str):
    try:
        cfg = cfg_mod.load(path)
        # Apply language from config so all subsequent messages are localised
        i18n.set_lang(cfg.get("lang", "en"))
        return cfg
    except (FileNotFoundError, ValueError) as exc:
        print_error(str(exc))
        if path == DEFAULT_CONFIG:
            print_info(i18n.t("tip_run_wizard"))
        sys.exit(1)


# ── Command handlers ──────────────────────────────────────────────────────────

def cmd_init(args):
    path = args.config
    cfg_mod.generate_template(path, mode=args.mode)
    print_success(f"Config template written to: {path}")
    print_info("Edit the file, then run:  tmw start")


def cmd_start(args):
    if getattr(args, 'background', False):
        print_banner()
    config = _load_config(args.config)
    from trustmework import daemon
    daemon.start(config, args.config, background=getattr(args, 'background', False))


def cmd_stop(args):
    from trustmework import daemon
    daemon.stop(args.config)


def cmd_logs(args):
    from trustmework import daemon
    daemon.logs(args.config, lines=args.lines)


def cmd_run(args):
    print_banner()
    config = _load_config(args.config)
    if config.get("simulate_work"):
        engine.run_work_mode(config, args.config, dry_run=args.dry_run)
    else:
        engine.run_random_mode(config, args.config, dry_run=args.dry_run)


def cmd_status(args):
    print_banner()
    config = _load_config(args.config)

    import datetime
    tz_name = config.get("timezone", "")
    if tz_name and zoneinfo is not None:
        try:
            tz = zoneinfo.ZoneInfo(tz_name)
        except Exception:
            tz = datetime.datetime.now().astimezone().tzinfo
            tz_name = str(tz)
    else:
        tz = datetime.datetime.now().astimezone().tzinfo
        tz_name = str(tz)

    state = st.load(args.config)
    today = st.today_consumed(state, tz)
    week  = st.week_consumed(state, tz)
    last7 = st.last_n_days(state, tz, 7)

    import random
    weekly_target = random.randint(config["weekly_min"], config["weekly_max"])
    divisor = 5 if config.get("simulate_work") else 7
    daily_tgt = int(weekly_target / divisor)

    platform = PLATFORM_DISPLAY_NAMES.get(
        config.get("platform", "custom").lower(), config.get("platform", "custom")
    )
    from trustmework.daemon import _mode as _get_mode
    _mode_key = {"work": "mode_work", "immediate": "mode_immediate", "spread": "mode_spread"}
    mode = i18n.t(_mode_key.get(_get_mode(config), "mode_immediate"))

    from trustmework import daemon as _daemon
    config_abs = str(Path(args.config).resolve())
    if _daemon._is_running(config_abs):
        pid = _daemon._read_pid(config_abs)
        print_info(f"Daemon: RUNNING (PID {pid})")
    else:
        print_info("Daemon: not running  (use 'tmw start' to start)")

    print_status_panel(
        platform=platform,
        mode=mode,
        today_consumed=today,
        week_consumed=week,
        weekly_min=config["weekly_min"],
        weekly_max=config["weekly_max"],
        daily_target=daily_tgt,
        tz_name=tz_name,
        last_7_days=last7,
    )


def cmd_scheduler(args):
    if not args.config and (args.install or args.uninstall):
        print_error("--config is required for --install / --uninstall")
        sys.exit(1)

    if args.install:
        config = _load_config(args.config)
        sched.install(args.config, config)
    elif args.uninstall:
        sched.uninstall(args.config)
    else:
        sched.status(args.config)


def cmd_wizard(args):
    print_banner()
    try:
        from trustmework.wizard import run_wizard
        run_wizard()
    except ImportError:
        print_error("Wizard module not found.")
        sys.exit(1)


def cmd_platforms(args):
    print_banner()
    print_info("Supported platforms:\n")
    for p in list_platforms():
        display = PLATFORM_DISPLAY_NAMES.get(p, p)
        print(f"  {p:<16}  {display}")
    print()
    print_info("Use 'custom' + set base_url for self-hosted or proxy endpoints.")


# ── Argument parser ───────────────────────────────────────────────────────────

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="tmw",
        description="TrustMeImWorking — Simulate API token usage to hit your KPI.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"""
Quick start (3 commands):
  tmw wizard      # one-time setup, writes {DEFAULT_CONFIG}
  tmw start       # start daemon + live dashboard (Ctrl+C to stop)
  tmw start -b    # start silently in background

Other commands (all use {DEFAULT_CONFIG} by default):
  tmw stop
  tmw logs        [-n 100]
  tmw run         [--dry-run]
  tmw init        [--mode random|work|gateway|proxy]
  tmw platforms
        """,
    )
    parser.add_argument("-V", "--version", action="version", version=f"tmw {__version__}")

    sub = parser.add_subparsers(dest="command", metavar="COMMAND")

    def _cfg(p, required=False):
        """Add --config / -c argument (optional, default=config.json)."""
        p.add_argument(
            "--config", "-c",
            default=DEFAULT_CONFIG,
            metavar="PATH",
            help=f"Config file path (default: {DEFAULT_CONFIG})",
        )

    # wizard
    sub.add_parser("wizard", help=f"Interactive setup wizard — writes {DEFAULT_CONFIG}")

    # start
    p_start = sub.add_parser(
        "start",
        help="Start daemon with live dashboard (default) or silent background",
    )
    _cfg(p_start)
    p_start.add_argument("--background", "-b", action="store_true",
                         help="Run silently in background instead of showing dashboard")

    # stop
    p_stop = sub.add_parser("stop", help="Stop the running daemon")
    _cfg(p_stop)

    # logs
    p_logs = sub.add_parser("logs", help="Tail the daemon log file")
    _cfg(p_logs)
    p_logs.add_argument("--lines", "-n", type=int, default=50, metavar="N",
                        help="Number of lines to show (default: 50)")

    # status
    p_status = sub.add_parser("status", help="Show consumption stats + daemon status")
    _cfg(p_status)

    # run
    p_run = sub.add_parser("run", help="Run a single consumption session (manual)")
    _cfg(p_run)
    p_run.add_argument("--dry-run", action="store_true",
                       help="Simulate without calling the API")

    # init
    p_init = sub.add_parser("init", help="Generate a config file template")
    _cfg(p_init)
    p_init.add_argument("--mode", choices=["random", "work", "gateway", "proxy"],
                        default="random",
                        help="Template mode (default: random)")

    # scheduler (legacy)
    p_sched = sub.add_parser("scheduler", help="Manage crontab scheduling (legacy)")
    p_sched.add_argument("--install",   action="store_true")
    p_sched.add_argument("--uninstall", action="store_true")
    p_sched.add_argument("--status",    action="store_true")
    p_sched.add_argument("--config", "-c", default=DEFAULT_CONFIG, metavar="PATH")

    # platforms
    sub.add_parser("platforms", help="List all supported platforms")

    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()

    dispatch = {
        "wizard":    cmd_wizard,
        "start":     cmd_start,
        "stop":      cmd_stop,
        "logs":      cmd_logs,
        "run":       cmd_run,
        "status":    cmd_status,
        "init":      cmd_init,
        "scheduler": cmd_scheduler,
        "platforms": cmd_platforms,
    }

    if args.command in dispatch:
        dispatch[args.command](args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
