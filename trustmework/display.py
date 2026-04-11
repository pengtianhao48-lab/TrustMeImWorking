"""
Terminal display helpers — rich colors, progress bars, status panels.
Falls back gracefully when 'rich' is not installed.
"""

from __future__ import annotations

import sys

# ── Try to use rich for beautiful output ─────────────────────────────────────
try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    from rich.progress import Progress, BarColumn, TextColumn, TimeElapsedColumn
    from rich.text import Text
    from rich import print as rprint
    _RICH = True
except ImportError:
    _RICH = False

console = Console() if _RICH else None


BANNER = r"""
 ______               _   __  __     ___         __        __         _    _
|_   _|_ _  _ ___ _ _| |_|  \/  |___| __|_ __   \ \      / /__ _ __| | _(_)_ __   __ _
  | || '_| || (_-<| '_| __| |\/| / -_) _|| '  \   \ \ /\ / / _ \ '__| |/ / | '_ \ / _` |
  |_||_|  \_,_/__/|_|  \__|_|  |_\___|___|_|_|_|   \_V__V/\___/_|  |_|\_\_| .__/ \__, |
                                                                             |_|    |___/
"""

TAGLINE = "📊  Simulate API token usage to hit your KPI — the smart way."


def print_banner() -> None:
    if _RICH:
        console.print(f"[bold cyan]{BANNER}[/bold cyan]")
        console.print(f"[dim]{TAGLINE}[/dim]\n")
    else:
        print(BANNER)
        print(TAGLINE + "\n")


def print_info(msg: str) -> None:
    if _RICH:
        console.print(f"[bold blue]ℹ[/bold blue]  {msg}")
    else:
        print(f"[INFO] {msg}")


def print_success(msg: str) -> None:
    if _RICH:
        console.print(f"[bold green]✔[/bold green]  {msg}")
    else:
        print(f"[OK] {msg}")


def print_warning(msg: str) -> None:
    if _RICH:
        console.print(f"[bold yellow]⚠[/bold yellow]  {msg}")
    else:
        print(f"[WARN] {msg}")


def print_error(msg: str) -> None:
    if _RICH:
        err_console = Console(stderr=True)
        err_console.print(f"[bold red]✘[/bold red]  {msg}")
    else:
        print(f"[ERROR] {msg}", file=sys.stderr)


def print_api_call(prompt: str, tokens: int, total: int, target: int) -> None:
    short = prompt[:72].replace("\n", " ")
    pct = min(total / target, 1.0) if target > 0 else 0
    bar_len = 30
    filled = int(bar_len * pct)
    bar = "█" * filled + "░" * (bar_len - filled)

    if _RICH:
        console.print(
            f"  [dim]›[/dim] [italic]{short}[/italic]\n"
            f"    [green]+{tokens:,}[/green] tokens  "
            f"[cyan]{bar}[/cyan]  "
            f"[bold]{total:,}[/bold]/[dim]{target:,}[/dim]"
        )
    else:
        print(f"  > {short}")
        print(f"    +{tokens} tokens  [{bar}]  {total}/{target}")


def print_status_panel(
    platform: str,
    mode: str,
    today_consumed: int,
    week_consumed: int,
    weekly_min: int,
    weekly_max: int,
    daily_target: int,
    tz_name: str,
    last_7_days: list[tuple[str, int]],
) -> None:
    weekly_mid = (weekly_min + weekly_max) / 2
    week_pct = week_consumed / weekly_mid * 100 if weekly_mid > 0 else 0
    day_pct = today_consumed / daily_target * 100 if daily_target > 0 else 0

    if _RICH:
        table = Table(show_header=False, box=None, padding=(0, 1))
        table.add_column(style="dim", width=22)
        table.add_column()

        table.add_row("Platform", f"[cyan]{platform}[/cyan]")
        table.add_row("Mode", f"[magenta]{mode}[/magenta]")
        table.add_row("Timezone", tz_name)
        table.add_row("", "")
        table.add_row("Today consumed", f"[green]{today_consumed:,}[/green] / {daily_target:,} tokens  ({day_pct:.1f}%)")
        table.add_row("This week", f"[green]{week_consumed:,}[/green] tokens  ({week_pct:.1f}% of mid-target)")
        table.add_row("Weekly range", f"{weekly_min:,} – {weekly_max:,} tokens")
        table.add_row("", "")

        # Sparkline
        max_val = max(v for _, v in last_7_days) or 1
        bars = ""
        BLOCKS = " ▁▂▃▄▅▆▇█"
        for date, val in last_7_days:
            idx = int(val / max_val * 8)
            bars += BLOCKS[idx]
        table.add_row("Last 7 days", f"[yellow]{bars}[/yellow]")

        for date, val in last_7_days:
            bar_w = int(val / max_val * 20) if max_val > 0 else 0
            bar = "█" * bar_w
            table.add_row(f"  {date}", f"[dim]{bar}[/dim] {val:,}")

        console.print(Panel(table, title="[bold]TrustMeImWorking — Status[/bold]", border_style="blue"))
    else:
        print("=" * 56)
        print("  TrustMeImWorking — Status")
        print("=" * 56)
        print(f"  Platform : {platform}")
        print(f"  Mode     : {mode}")
        print(f"  Timezone : {tz_name}")
        print(f"  Today    : {today_consumed:,} / {daily_target:,}  ({day_pct:.1f}%)")
        print(f"  Week     : {week_consumed:,}  ({week_pct:.1f}%)")
        print(f"  Range    : {weekly_min:,} – {weekly_max:,}")
        print()
        for date, val in last_7_days:
            bar = "█" * min(int(val / 1000), 30)
            print(f"  {date}  {val:>8,}  {bar}")
        print("=" * 56)


def print_skipped(reason: str) -> None:
    if _RICH:
        console.print(f"[dim]⏭  Skipped — {reason}[/dim]")
    else:
        print(f"[SKIP] {reason}")


def print_mode_header(mode: str, daily_target: int, today_consumed: int, weekly_target: int) -> None:
    remaining = daily_target - today_consumed
    if _RICH:
        console.rule(f"[bold]{mode}[/bold]")
        console.print(
            f"  Weekly target  [bold cyan]{weekly_target:,}[/bold cyan] tokens\n"
            f"  Daily target   [bold cyan]{daily_target:,}[/bold cyan] tokens  "
            f"([green]{today_consumed:,}[/green] consumed, "
            f"[yellow]{remaining:,}[/yellow] remaining)"
        )
    else:
        print(f"\n[{mode}]")
        print(f"  Weekly: {weekly_target:,}  Daily: {daily_target:,}  Remaining: {remaining:,}")
