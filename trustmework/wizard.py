"""
Interactive setup wizard — guides users through config creation.
"""

from __future__ import annotations

import datetime
import json
from pathlib import Path

from .platforms import PLATFORM_URLS, PLATFORM_DISPLAY_NAMES, PLATFORM_DEFAULT_MODELS, list_platforms
from .display import print_info, print_success, print_warning


def _ask(prompt: str, default=None, required: bool = True) -> str:
    suffix = f" [{default}]" if default is not None else ""
    while True:
        val = input(f"  {prompt}{suffix}: ").strip()
        if val:
            return val
        if default is not None:
            return str(default)
        if not required:
            return ""
        print("    ↳ This field is required.")


def _ask_int(prompt: str, default: int, min_val: int = 1) -> int:
    while True:
        raw = _ask(prompt, default=default)
        try:
            v = int(raw)
            if v >= min_val:
                return v
            print(f"    ↳ Must be ≥ {min_val}")
        except ValueError:
            print("    ↳ Please enter a valid integer.")


def _ask_bool(prompt: str, default: bool = False) -> bool:
    hint = "Y/n" if default else "y/N"
    while True:
        raw = input(f"  {prompt} [{hint}]: ").strip().lower()
        if not raw:
            return default
        if raw in ("y", "yes"):
            return True
        if raw in ("n", "no"):
            return False
        print("    ↳ Please enter y or n.")


def _ask_time(prompt: str, default: str = "09:00") -> str:
    while True:
        raw = _ask(prompt, default=default)
        try:
            h, m = map(int, raw.split(":"))
            if 0 <= h <= 23 and 0 <= m <= 59:
                return f"{h:02d}:{m:02d}"
        except Exception:
            pass
        print("    ↳ Please use HH:MM format (e.g. 09:00).")


def run_wizard() -> None:
    print("\n" + "─" * 60)
    print("  TrustMeImWorking — Setup Wizard")
    print("─" * 60 + "\n")

    output = _ask("Config file path", default="config.json")

    print("\n── Step 1: Platform ──────────────────────────────────────")
    platforms = list_platforms()
    for i, p in enumerate(platforms, 1):
        url = PLATFORM_URLS.get(p, "")
        display = PLATFORM_DISPLAY_NAMES.get(p, p)
        print(f"  {i:2d}. {p:<16} {display}")
    print()

    raw_platform = _ask("Platform name or number", default="openai")
    try:
        idx = int(raw_platform) - 1
        platform = platforms[idx] if 0 <= idx < len(platforms) else raw_platform.lower()
    except ValueError:
        platform = raw_platform.lower()

    if platform not in PLATFORM_URLS:
        print_warning(f"Unknown platform '{platform}' — treating as custom.")
        platform = "custom"

    api_key = _ask("API Key")

    base_url = None
    if platform == "custom":
        base_url = _ask("Base URL (e.g. https://your-proxy.com/v1)")
    elif _ask_bool(f"Override the default URL for {platform}?", default=False):
        base_url = _ask("Custom base URL")

    default_model = PLATFORM_DEFAULT_MODELS.get(platform, "")
    model_raw = _ask(f"Model name (default: {default_model or 'platform default'})",
                     default=default_model, required=False)
    model = model_raw if model_raw and model_raw != default_model else None

    print("\n── Step 2: Weekly Token Budget ───────────────────────────")
    print("  Actual weekly target is randomly chosen in [min, max].")
    print("  Daily quota = weekly / 7 (random) or / 5 (work mode), ±5%.\n")
    weekly_min = _ask_int("Weekly minimum (tokens)", default=50000)
    weekly_max = _ask_int("Weekly maximum (tokens)", default=80000, min_val=weekly_min)

    print("\n── Step 3: Run Mode ──────────────────────────────────────")
    print("  Random mode   — spread usage evenly throughout the day")
    print("  Work-sim mode — consume only during working hours, with")
    print("                  job-relevant prompts and organic pacing\n")
    simulate_work = _ask_bool("Enable work-simulation mode?", default=False)

    config: dict = {
        "platform":      platform,
        "api_key":       api_key,
        "base_url":      base_url,
        "model":         model,
        "weekly_min":    weekly_min,
        "weekly_max":    weekly_max,
        "simulate_work": simulate_work,
    }

    if simulate_work:
        print("\n── Step 4: Work Schedule ─────────────────────────────────")
        job_desc   = _ask("Job description (e.g. Python backend engineer)")
        work_start = _ask_time("Work start time", default="09:00")
        work_end   = _ask_time("Work end time",   default="18:00")
        local_tz   = str(datetime.datetime.now().astimezone().tzinfo)
        print(f"  System timezone: {local_tz}")
        tz = _ask("Timezone (e.g. Asia/Shanghai, leave blank for system)", default="", required=False)
        config.update({
            "job_description": job_desc,
            "work_start":      work_start,
            "work_end":        work_end,
            "timezone":        tz,
        })
    else:
        local_tz = str(datetime.datetime.now().astimezone().tzinfo)
        print(f"\n  System timezone: {local_tz}")
        tz = _ask("Timezone (leave blank for system)", default="", required=False)
        config["timezone"] = tz

    Path(output).write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")

    print("\n" + "─" * 60)
    print_success(f"Config saved to: {output}")
    print("─" * 60)
    print("\nNext steps:")
    print(f"  1. Dry-run test:   python tmw.py run --config {output} --dry-run")
    print(f"  2. Run once:       python tmw.py run --config {output}")
    print(f"  3. Auto-schedule:  python tmw.py scheduler --install --config {output}")
    print(f"  4. Check status:   python tmw.py status --config {output}\n")
