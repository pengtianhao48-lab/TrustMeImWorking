"""
Local state management — tracks daily and weekly token consumption.
All records are stored in a JSON file alongside the config.
"""

import datetime
import json
from pathlib import Path


def get_state_path(config_path: str) -> Path:
    return Path(config_path).parent / ".tmw_state.json"


def load(config_path: str) -> dict:
    p = get_state_path(config_path)
    if p.exists():
        try:
            return json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {"daily": {}, "weekly": {}}


def save(config_path: str, state: dict) -> None:
    p = get_state_path(config_path)
    p.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")


def _day_key(tz) -> str:
    return datetime.datetime.now(tz).strftime("%Y-%m-%d")


def _week_key(tz) -> str:
    dt = datetime.datetime.now(tz)
    y, w, _ = dt.isocalendar()
    return f"{y}-W{w:02d}"


def today_consumed(state: dict, tz) -> int:
    return state["daily"].get(_day_key(tz), 0)


def week_consumed(state: dict, tz) -> int:
    return state["weekly"].get(_week_key(tz), 0)


def record(config_path: str, state: dict, tokens: int, tz) -> None:
    dk = _day_key(tz)
    wk = _week_key(tz)
    state["daily"][dk] = state["daily"].get(dk, 0) + tokens
    state["weekly"][wk] = state["weekly"].get(wk, 0) + tokens
    save(config_path, state)


def last_n_days(state: dict, tz, n: int = 7) -> list[tuple[str, int]]:
    """Return (date_str, tokens) for the last n days, oldest first."""
    now = datetime.datetime.now(tz)
    result = []
    for i in range(n - 1, -1, -1):
        day = now - datetime.timedelta(days=i)
        key = day.strftime("%Y-%m-%d")
        result.append((key, state["daily"].get(key, 0)))
    return result
