#!/usr/bin/env python3
"""
TrustMeImWorking — CLI entry point.

Usage:
  tmw wizard                                   # interactive setup
  tmw start  --config PATH [--foreground]      # start persistent daemon
  tmw stop   --config PATH                     # stop daemon
  tmw logs   --config PATH [--lines N]         # tail daemon log
  tmw run    --config PATH [--dry-run]         # single run (manual)
  tmw status --config PATH                     # consumption stats
  tmw init   [--config PATH] [--mode MODE]     # generate config template
  tmw scheduler --install   --config PATH      # install crontab
  tmw scheduler --uninstall --config PATH
  tmw scheduler --status    [--config PATH]
  tmw platforms                                # list supported platforms
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Ensure package is importable when run directly
sys.path.insert(0, str(Path(__file__).parent))

# Python 3.9+ has zoneinfo in stdlib; 3.8 needs backports.zoneinfo
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
from trustmework.platforms import PLATFORM_DISPLAY_NAMES, list_platforms


# ── Command handlers ──────────────────────────────────────────────────────────

def cmd_init(args):
    path = args.config or "config.json"
    cfg_mod.generate_template(path, mode=args.mode)
    print_success(f"Config template written to: {path}")
    print_info("Edit the file, then run:  tmw start --config " + path)


def cmd_start(args):
    print_banner()
    try:
        config = cfg_mod.load(args.config)
    except (FileNotFoundError, ValueError) as exc:
        print_error(str(exc))
        sys.exit(1)

    # os.fork() is not available on Windows
    if sys.platform == "win32" and not args.foreground:
        print_info("Background daemon is not supported on Windows. Running in foreground mode.")
        args.foreground = True

    from trustmework import daemon
    daemon.start(config, args.config, foreground=args.foreground)


def cmd_stop(args):
    from trustmework import daemon
    daemon.stop(args.config)


def cmd_logs(args):
    from trustmework import daemon
    daemon.logs(args.config, lines=args.lines)


def cmd_run(args):
    print_banner()
    try:
        config = cfg_mod.load(args.config)
    except (FileNotFoundError, ValueError) as exc:
        print_error(str(exc))
        sys.exit(1)

    if config.get("simulate_work"):
        engine.run_work_mode(config, args.config, dry_run=args.dry_run)
    else:
        engine.run_random_mode(config, args.config, dry_run=args.dry_run)


def cmd_status(args):
    print_banner()
    try:
        config = cfg_mod.load(args.config)
    except (FileNotFoundError, ValueError) as exc:
        print_error(str(exc))
        sys.exit(1)

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
    mode = "Work-Simulation" if config.get("simulate_work") else "Random"

    # Show daemon status alongside consumption stats
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
        try:
            config = cfg_mod.load(args.config)
        except (FileNotFoundError, ValueError) as exc:
            print_error(str(exc))
            sys.exit(1)
        sched.install(args.config, config)

    elif args.uninstall:
        sched.uninstall(args.config)

    else:
        sched.status(args.config)


def cmd_wizard(args):
    """Interactive setup wizard."""
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
        epilog="""
Quick start:
  1. tmw wizard                              # interactive setup
  2. tmw start --config config.json         # start background daemon
  3. tmw status --config config.json        # check progress
  4. tmw stop  --config config.json         # stop daemon

Manual / advanced:
  tmw run    --config config.json --dry-run
  tmw logs   --config config.json --lines 100
  tmw init   --config config.json --mode work
  tmw scheduler --install --config config.json
  tmw platforms
        """,
    )
    parser.add_argument("-V", "--version", action="version", version=f"tmw {__version__}")

    sub = parser.add_subparsers(dest="command", metavar="COMMAND")

    # wizard
    sub.add_parser("wizard", help="Interactive setup wizard (recommended first step)")

    # start
    p_start = sub.add_parser(
        "start",
        help="Start persistent daemon — runs forever, auto-consumes tokens per schedule",
    )
    p_start.add_argument("--config", "-c", required=True, metavar="PATH",
                         help="Path to config file (created by 'tmw wizard')")
    p_start.add_argument("--foreground", "-f", action="store_true",
                         help="Run in foreground instead of background (useful for debugging)")

    # stop
    p_stop = sub.add_parser("stop", help="Stop the running daemon")
    p_stop.add_argument("--config", "-c", required=True, metavar="PATH")

    # logs
    p_logs = sub.add_parser("logs", help="Tail the daemon log file")
    p_logs.add_argument("--config", "-c", required=True, metavar="PATH")
    p_logs.add_argument("--lines", "-n", type=int, default=50, metavar="N",
                        help="Number of lines to show (default: 50)")

    # status
    p_status = sub.add_parser("status", help="Show consumption statistics + daemon status")
    p_status.add_argument("--config", "-c", required=True, metavar="PATH")

    # run (manual single-shot)
    p_run = sub.add_parser("run", help="Run a single consumption session (manual)")
    p_run.add_argument("--config", "-c", required=True, metavar="PATH")
    p_run.add_argument("--dry-run", action="store_true", help="Simulate without calling the API")

    # init
    p_init = sub.add_parser("init", help="Generate a config file template")
    p_init.add_argument("--config", "-c", default="config.json", metavar="PATH")
    p_init.add_argument("--mode", choices=["random", "work", "gateway", "proxy"], default="random",
                        help="Template mode: random, work, gateway, proxy")

    # scheduler (legacy crontab method)
    p_sched = sub.add_parser("scheduler", help="Manage crontab-based scheduling (legacy)")
    p_sched.add_argument("--install",   action="store_true")
    p_sched.add_argument("--uninstall", action="store_true")
    p_sched.add_argument("--status",    action="store_true")
    p_sched.add_argument("--config", "-c", metavar="PATH")

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
