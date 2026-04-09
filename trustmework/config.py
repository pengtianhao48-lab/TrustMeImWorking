"""
Configuration loading, validation, and template generation.
"""

from __future__ import annotations

import json
from pathlib import Path

from .platforms import PLATFORM_URLS, PLATFORM_DEFAULT_MODELS, list_platforms

REQUIRED_FIELDS = ["api_key", "weekly_min", "weekly_max"]
WORK_MODE_FIELDS = ["job_description", "work_start", "work_end"]

# ── Templates ─────────────────────────────────────────────────────────────────

_RANDOM_TEMPLATE = {
    "_readme": "TrustMeImWorking config — https://github.com/pengtianhao48-lab/TrustMeImWorking",
    "platform": "openai",
    "_platform_hint": f"Supported: {', '.join(list_platforms())}",
    "api_key": "sk-YOUR-API-KEY",
    "base_url": None,
    "_base_url_hint": "Override the platform URL (e.g. for a proxy). Leave null to use the preset.",
    "model": None,
    "_model_hint": "Leave null to use the platform's default cheap model.",
    "weekly_min": 50000,
    "weekly_max": 80000,
    "_weekly_hint": "Actual weekly target is randomly chosen in [min, max]. Daily quota fluctuates ±5%.",
    "simulate_work": False,
    "timezone": "",
    "_timezone_hint": "e.g. 'Asia/Shanghai'. Leave empty to use system timezone.",
}

_WORK_TEMPLATE = {
    **_RANDOM_TEMPLATE,
    "_readme": "TrustMeImWorking config (work-simulation mode)",
    "simulate_work": True,
    "job_description": "Python backend engineer working on microservices and REST APIs",
    "work_start": "09:00",
    "work_end": "18:00",
}


def generate_template(path: str, mode: str = "random") -> None:
    tpl = _WORK_TEMPLATE if mode == "work" else _RANDOM_TEMPLATE
    Path(path).write_text(json.dumps(tpl, ensure_ascii=False, indent=2), encoding="utf-8")


def load(path: str) -> dict:
    """Load and validate a config file. Raises ValueError on bad config."""
    cfg = json.loads(Path(path).read_text(encoding="utf-8"))

    for f in REQUIRED_FIELDS:
        if not cfg.get(f):
            raise ValueError(f"Missing required field: '{f}'")

    if cfg.get("simulate_work"):
        for f in WORK_MODE_FIELDS:
            if not cfg.get(f):
                raise ValueError(f"Work-simulation mode requires field: '{f}'")

    if cfg["weekly_min"] > cfg["weekly_max"]:
        raise ValueError("weekly_min must be ≤ weekly_max")

    return cfg
