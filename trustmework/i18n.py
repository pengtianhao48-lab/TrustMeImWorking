"""
i18n — Lightweight internationalisation for TrustMeImWorking.

Usage
-----
    from trustmework.i18n import set_lang, t

    # Called once at startup after loading config:
    set_lang(config.get("lang", "en"))

    # Anywhere in the codebase:
    print(t("daemon_started"))
    print(t("today_progress", today=1234, target=5000, pct=25))
"""
from __future__ import annotations

_LANG: str = "en"

# ── String catalogue ──────────────────────────────────────────────────────────
_STRINGS: dict[str, dict[str, str]] = {
    "en": {
        # daemon / dashboard header
        "platform_label":       "Platform",
        "mode_label":           "Mode",
        "uptime_label":         "Uptime",
        "config_label":         "Config",

        # mode display names
        "mode_immediate":       "Immediate (ASAP)",
        "mode_spread":          "Spread (even)",
        "mode_work":            "Work-Simulation",

        # consumption panel
        "consumption_title":    "Consumption",
        "today_label":          "Today",
        "week_label":           "This week",

        # session panel
        "session_title":        "Session",
        "active_label":         "ACTIVE",
        "this_session":         "This session",
        "todays_progress":      "Today's progress",
        "prompt_label":         "Prompt",
        "idle_label":           "Idle",
        "next_request_secs":    "next request in {secs}s",
        "next_request_mins":    "next request in {mins}m {secs:02d}s",
        "starting_up":          "starting up\u2026",
        "last_session_label":   "last session",

        # session done state
        "done_label":           "Today's quota complete!",
        "next_fire_label":      "Next session starts in",
        "next_fire_secs":       "{secs}s",
        "next_fire_mins":       "{mins}m {secs:02d}s",
        "next_fire_hrs":        "{hrs}h {mins:02d}m",

        # history panel
        "last7_title":          "Last 7 Days",

        # log panel
        "log_title":            "Recent Log",
        "no_log_yet":           "No log entries yet.",

        # footer
        "press_ctrl_c":         "Press [bold]Ctrl+C[/bold] to stop",

        # daemon log messages
        "daemon_started":       "Daemon started.",
        "mode_log":             "Mode: {mode}",
        "daily_target_log":     "[{mode}] daily_target={target:,}  consumed={today:,}  remaining={rem:,}",
        "target_reached_log":   "Daily target reached \u2014 skipping.",
        "session_done_log":     "Session done. +{tokens:,} tokens.",
        "heartbeat_log":        "Heartbeat {time} \u2014 waiting.",
        "firing_log":           "Firing session at {time}",
        "sigterm_log":          "Received SIGTERM \u2014 shutting down.",
        "spread_slot_log":      "[Spread] slot {slot}/{total}  interval={interval:.0f}s  target={target:,}",
        "work_segment_log":     "[Work] segment {seg}  target={target:,}",

        # tmw.py messages
        "already_running":      "Daemon already running (PID {pid}). Use 'tmw stop' to stop it.",
        "bg_started":           "Daemon started in background (PID {pid}).",
        "logs_hint":            "Logs: {path}",
        "stop_hint":            "Stop: tmw stop",
        "stopped_summary":      "Stopped. Session: today {today:,} / {target:,} tokens  |  week {week:,} tokens",
        "no_daemon":            "No running daemon found for this config.",
        "daemon_running":       "Daemon: RUNNING (PID {pid})",
        "daemon_not_running":   "Daemon: not running  (use 'tmw start' to start)",
        "tip_run_wizard":       "Tip: run 'tmw wizard' first to create config.json",

        # session sub-status
        "generating_prompts":   "Generating work prompts\u2026",
        "sleeping_label":       "Sleeping {secs}s",

        # wizard next steps
        "next_steps_title":     "Next steps:",
        "next_step_start":      "  1. Start:       {py} tmw.py start",
        "next_step_logs":       "  2. View logs:   {py} tmw.py logs",
        "next_step_stop":       "  (Ctrl+C to stop the dashboard)",
    },
    "zh": {
        # daemon / dashboard header
        "platform_label":       "\u5e73\u53f0",
        "mode_label":           "\u6a21\u5f0f",
        "uptime_label":         "\u8fd0\u884c\u65f6\u957f",
        "config_label":         "\u914d\u7f6e\u6587\u4ef6",

        # mode display names
        "mode_immediate":       "\u7acb\u523b\uff08\u5c3d\u5feb\u6d88\u8017\uff09",
        "mode_spread":          "\u5e73\u5747\uff08\u5747\u5300\u5206\u6563\uff09",
        "mode_work":            "\u5de5\u4f5c\u6a21\u62df",

        # consumption panel
        "consumption_title":    "\u6d88\u8017\u8fdb\u5ea6",
        "today_label":          "\u4eca\u65e5",
        "week_label":           "\u672c\u5468",

        # session panel
        "session_title":        "\u8bf7\u6c42\u8fdb\u5ea6",
        "active_label":         "\u8fdb\u884c\u4e2d",
        "this_session":         "\u672c\u6b21\u8bf7\u6c42",
        "todays_progress":      "\u4eca\u65e5\u8fdb\u5ea6",
        "prompt_label":         "\u8bf7\u6c42\u5185\u5bb9",
        "idle_label":           "\u7b49\u5f85\u4e2d",
        "next_request_secs":    "{secs} \u79d2\u540e\u53d1\u8d77\u4e0b\u6b21\u8bf7\u6c42",
        "next_request_mins":    "{mins} \u5206 {secs:02d} \u79d2\u540e\u53d1\u8d77\u4e0b\u6b21\u8bf7\u6c42",
        "starting_up":          "\u542f\u52a8\u4e2d\u2026",
        "last_session_label":   "\u4e0a\u6b21\u8bf7\u6c42",

        # session done state
        "done_label":           "\u4eca\u65e5\u914d\u989d\u5df2\u5b8c\u6210\uff01",
        "next_fire_label":      "\u4e0b\u6b21\u542f\u52a8\u65f6\u95f4",
        "next_fire_secs":       "{secs} \u79d2\u540e",
        "next_fire_mins":       "{mins} \u5206 {secs:02d} \u79d2\u540e",
        "next_fire_hrs":        "{hrs} \u5c0f\u65f6 {mins:02d} \u5206\u540e",

        # history panel
        "last7_title":          "\u8fd1 7 \u5929",

        # log panel
        "log_title":            "\u6700\u8fd1\u65e5\u5fd7",
        "no_log_yet":           "\u6682\u65e0\u65e5\u5fd7\u8bb0\u5f55\u3002",

        # footer
        "press_ctrl_c":         "\u6309 [bold]Ctrl+C[/bold] \u505c\u6b62",

        # daemon log messages
        "daemon_started":       "\u5b88\u62a4\u8fdb\u7a0b\u5df2\u542f\u52a8\u3002",
        "mode_log":             "\u6a21\u5f0f\uff1a{mode}",
        "daily_target_log":     "[{mode}] \u4eca\u65e5\u76ee\u6807={target:,}  \u5df2\u6d88\u8017={today:,}  \u5269\u4f59={rem:,}",
        "target_reached_log":   "\u4eca\u65e5\u76ee\u6807\u5df2\u8fbe\u6210\uff0c\u8df3\u8fc7\u672c\u6b21\u3002",
        "session_done_log":     "\u672c\u6b21\u5b8c\u6210\u3002+{tokens:,} tokens\u3002",
        "heartbeat_log":        "\u5fc3\u8df3 {time} \u2014 \u7b49\u5f85\u4e2d\u3002",
        "firing_log":           "\u4e8e {time} \u53d1\u8d77\u8bf7\u6c42",
        "sigterm_log":          "\u6536\u5230 SIGTERM \u2014 \u6b63\u5728\u5173\u95ed\u3002",
        "spread_slot_log":      "[\u5e73\u5747] \u7b2c {slot}/{total} \u6b21  \u95f4\u9694={interval:.0f}s  \u76ee\u6807={target:,}",
        "work_segment_log":     "[\u5de5\u4f5c] \u65f6\u6bb5 {seg}  \u76ee\u6807={target:,}",

        # tmw.py messages
        "already_running":      "\u5b88\u62a4\u8fdb\u7a0b\u5df2\u5728\u8fd0\u884c\uff08PID {pid}\uff09\u3002\u8bf7\u5148\u6267\u884c 'tmw stop' \u505c\u6b62\u3002",
        "bg_started":           "\u5b88\u62a4\u8fdb\u7a0b\u5df2\u5728\u540e\u53f0\u542f\u52a8\uff08PID {pid}\uff09\u3002",
        "logs_hint":            "\u65e5\u5fd7\uff1a{path}",
        "stop_hint":            "\u505c\u6b62\uff1atmw stop",
        "stopped_summary":      "\u5df2\u505c\u6b62\u3002\u4eca\u65e5\u5df2\u6d88\u8017 {today:,} / {target:,} tokens  |\u672c\u5468 {week:,} tokens",
        "no_daemon":            "\u672a\u627e\u5230\u6b64\u914d\u7f6e\u5bf9\u5e94\u7684\u8fd0\u884c\u4e2d\u5b88\u62a4\u8fdb\u7a0b\u3002",
        "daemon_running":       "\u5b88\u62a4\u8fdb\u7a0b\uff1a\u8fd0\u884c\u4e2d\uff08PID {pid}\uff09",
        "daemon_not_running":   "\u5b88\u62a4\u8fdb\u7a0b\uff1a\u672a\u8fd0\u884c\uff08\u8fd0\u884c 'tmw start' \u542f\u52a8\uff09",
        "tip_run_wizard":       "\u63d0\u793a\uff1a\u8bf7\u5148\u8fd0\u884c 'tmw wizard' \u521b\u5efa config.json",

        # session sub-status
        "generating_prompts":   "\u6b63\u5728\u751f\u6210\u5de5\u4f5c prompt\u2026",
        "sleeping_label":       "\u7b49\u5f85 {secs} \u79d2",

        # wizard next steps
        "next_steps_title":     "\u4e0b\u4e00\u6b65\uff1a",
        "next_step_start":      "  1. \u542f\u52a8\uff1a         {py} tmw.py start",
        "next_step_logs":       "  2. \u67e5\u770b\u65e5\u5fd7\uff1a   {py} tmw.py logs",
        "next_step_stop":       "  \uff08\u770b\u677f\u8fd0\u884c\u65f6\u6309 Ctrl+C \u505c\u6b62\uff09",
    },
}


def set_lang(lang: str) -> None:
    """Set the active language globally. Call once after loading config."""
    global _LANG
    _LANG = lang if lang in _STRINGS else "en"


def get_lang() -> str:
    return _LANG


def t(key: str, **kwargs) -> str:
    """
    Return the translated string for *key* in the active language.
    Falls back to English if the key is missing in the selected language.
    Supports keyword-argument formatting.
    """
    s = _STRINGS[_LANG].get(key) or _STRINGS["en"].get(key, key)
    return s.format(**kwargs) if kwargs else s
