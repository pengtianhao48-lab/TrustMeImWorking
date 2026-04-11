"""
Interactive setup wizard — guides users through config creation.

Field legend used throughout this wizard:
  [required]  — must be filled; wizard will keep asking until a value is given
  [optional]  — can be left blank; press Enter to skip
  [default=X] — press Enter to accept the shown default value
"""

from __future__ import annotations

import datetime
import json
from pathlib import Path

from .platforms import PLATFORM_URLS, PLATFORM_DISPLAY_NAMES, PLATFORM_DEFAULT_MODELS, list_platforms
from .display import print_info, print_success, print_warning

# ── Low-level prompt helpers ──────────────────────────────────────────────────

def _label(tag: str) -> str:
    """Return a coloured-ish inline label for required/optional/default."""
    return tag


def _ask(prompt: str, default=None, required: bool = True, hint: str = "") -> str:
    """
    Prompt the user for a string value.

    - If *default* is given, pressing Enter accepts it.
    - If *required* is True and no default, keeps asking until a value is entered.
    - If *required* is False, pressing Enter returns "".
    """
    if default is not None:
        tag = f"[default={default}]"
    elif required:
        tag = "[required]"
    else:
        tag = "[optional]"

    suffix = f" {default}" if default is not None else ""
    hint_str = f"\n    ↳ {hint}" if hint else ""
    label_str = f" {tag}"

    while True:
        val = input(f"  {prompt}{label_str}{hint_str}\n  > ").strip()
        if val:
            return val
        if default is not None:
            return str(default)
        if not required:
            return ""
        print("    ↳ This field is required. Please enter a value.")


def _ask_int(prompt: str, default: int, min_val: int = 1, hint: str = "") -> int:
    """Prompt for an integer ≥ min_val."""
    while True:
        raw = _ask(prompt, default=default, hint=hint)
        try:
            v = int(raw)
            if v >= min_val:
                return v
            print(f"    ↳ Must be ≥ {min_val}.")
        except ValueError:
            print("    ↳ Please enter a valid integer.")


def _ask_bool(prompt: str, default: bool = False, hint: str = "") -> bool:
    """Prompt for a yes/no answer."""
    hint_label = "Y/n" if default else "y/N"
    hint_str = f"\n    ↳ {hint}" if hint else ""
    while True:
        raw = input(f"  {prompt} [default={'yes' if default else 'no'}]{hint_str}\n  > ").strip().lower()
        if not raw:
            return default
        if raw in ("y", "yes"):
            return True
        if raw in ("n", "no"):
            return False
        print("    ↳ Please enter y or n.")


def _ask_time(prompt: str, default: str = "09:00") -> str:
    """Prompt for a HH:MM time string."""
    while True:
        raw = _ask(prompt, default=default)
        try:
            h, m = map(int, raw.split(":"))
            if 0 <= h <= 23 and 0 <= m <= 59:
                return f"{h:02d}:{m:02d}"
        except Exception:
            pass
        print("    ↳ Please use HH:MM format (e.g. 09:00).")


def _section(title: str) -> None:
    print(f"\n── {title} {'─' * max(0, 54 - len(title))}")


# ── Main wizard ───────────────────────────────────────────────────────────────

CONFIG_FILENAME = "config.json"


def run_wizard() -> None:
    print("\n" + "─" * 60)
    print("  TrustMeImWorking — Interactive Setup Wizard")
    print("─" * 60)
    print("  Legend:  [required]  [optional]  [default=X]")
    print("─" * 60 + "\n")

    output = CONFIG_FILENAME

    # ── Step 1: Platform ──────────────────────────────────────────────────────
    _section("Step 1: Platform")
    platforms = list_platforms()
    print()
    for i, p in enumerate(platforms, 1):
        display = PLATFORM_DISPLAY_NAMES.get(p, p)
        print(f"  {i:2d}. {p:<16} {display}")
    print(f"  {'--':<3} {'custom':<16} Custom / Self-hosted / Third-party relay")
    print()

    raw_platform = _ask(
        "Platform name or number",
        default="openai",
        hint="Enter the platform key (e.g. openai, deepseek) or its list number.",
    )
    try:
        idx = int(raw_platform) - 1
        platform = platforms[idx] if 0 <= idx < len(platforms) else raw_platform.lower()
    except ValueError:
        platform = raw_platform.lower()

    if platform not in PLATFORM_URLS and platform != "custom":
        print_warning(f"Unknown platform '{platform}' — treating as custom.")
        platform = "custom"

    # ── Step 2: API Key ───────────────────────────────────────────────────────
    _section("Step 2: API Key")
    api_key = _ask(
        "API Key",
        required=True,
        hint="Your platform API key (e.g. sk-...). Never committed to git.",
    )

    # ── Step 3: Base URL / Third-party relay ─────────────────────────────────
    _section("Step 3: API Base URL / Third-party Relay")
    base_url = None

    _RELAY_HELP = """
  What is a "third-party relay"?
  ─────────────────────────────────────────────────────────────────
  A relay is an OpenAI-compatible proxy that forwards your requests
  to the real LLM API. You keep your own API key; the relay just
  changes the hostname. Common use-cases:

    • Bypass regional restrictions (e.g. access OpenAI from China)
    • Company internal gateway / cost-control proxy
    • Multi-model aggregators (one key, many models)
    • Self-hosted LLM servers (Ollama, LM Studio, vLLM, etc.)

  How to fill in the URL:
  ─────────────────────────────────────────────────────────────────
  The URL must be the "base" path that ends right before "/chat/completions".
  Almost all OpenAI-compatible relays follow the pattern:

      https://<relay-host>/v1

  Examples by scenario:

    Scenario                       Base URL to enter
    ─────────────────────────────  ──────────────────────────────────────────
    OpenAI official (default)      https://api.openai.com/v1
    api2d.com relay                https://oa.api2d.net/v1
    openai-proxy.example.com       https://openai-proxy.example.com/v1
    Company internal gateway       https://ai-gateway.corp.com/openai/v1
    Ollama (local)                 http://localhost:11434/v1
    LM Studio (local)              http://localhost:1234/v1
    vLLM (local / cloud)           http://your-server:8000/v1
    SiliconFlow (CN mirror)        https://api.siliconflow.cn/v1
    Groq (fast inference)          https://api.groq.com/openai/v1

  Note: The tool appends "/chat/completions" automatically.
        Do NOT include that suffix in the URL you enter here.
  ─────────────────────────────────────────────────────────────────"""

    if platform == "custom":
        print("  You selected 'custom' — a Base URL is required.")
        print(_RELAY_HELP)
        base_url = _ask(
            "Base URL",
            required=True,
            hint="Must end with /v1 (or equivalent path). See examples above.",
        )
    else:
        default_url = PLATFORM_URLS.get(platform, "")
        print(f"  Default URL for {platform}: {default_url}")
        override = _ask_bool(
            "Use a third-party relay or company gateway instead of the official URL?",
            default=False,
            hint="Choose 'y' to enter a custom base URL (relay, proxy, internal gateway).",
        )
        if override:
            print(_RELAY_HELP)
            base_url = _ask(
                "Relay / Gateway Base URL",
                required=True,
                hint="Must end with /v1 (or equivalent path). See examples above.",
            )

    # ── Step 4: Model ─────────────────────────────────────────────────────────
    _section("Step 4: Model")
    default_model = PLATFORM_DEFAULT_MODELS.get(platform, "")
    if default_model:
        print(f"  Recommended flagship model: {default_model}")
    model_raw = _ask(
        "Model name",
        default=default_model or None,
        required=False,
        hint="Leave blank to use the platform default. Flagship models consume the most tokens.",
    )
    model = model_raw if model_raw and model_raw != default_model else None

    # ── Step 5: Weekly Token Budget ───────────────────────────────────────────
    _section("Step 5: Weekly Token Budget")
    print("  The actual weekly target is randomly chosen in [min, max].")
    print("  Daily quota = weekly / 7 (random mode) or / 5 (work-sim mode), ±5%.\n")
    weekly_min = _ask_int(
        "Weekly minimum (tokens)",
        default=50000,
        min_val=1000,
        hint="Lower bound of your weekly token target range.",
    )
    weekly_max = _ask_int(
        "Weekly maximum (tokens)",
        default=80000,
        min_val=weekly_min,
        hint="Upper bound. Must be ≥ weekly minimum.",
    )

    # ── Step 6: Run Mode ──────────────────────────────────────────────────────
    _section("Step 6: Run Mode")
    print("  Random mode   — spread usage evenly throughout the day (24 h)")
    print("  Work-sim mode — consume only during working hours, with")
    print("                  job-relevant prompts and organic pacing\n")
    simulate_work = _ask_bool(
        "Enable work-simulation mode?",
        default=False,
        hint="Recommended if your platform usage is monitored for work-hour patterns.",
    )

    config = {
        "platform":      platform,
        "api_key":       api_key,
        "base_url":      base_url,
        "model":         model,
        "weekly_min":    weekly_min,
        "weekly_max":    weekly_max,
        "simulate_work": simulate_work,
    }

    # ── Step 7: Work Schedule (work-sim only) ─────────────────────────────────
    if simulate_work:
        _section("Step 7: Work Schedule")
        job_desc   = _ask(
            "Job description",
            required=True,
            hint="e.g. 'Python backend engineer', 'data analyst'. Used to generate realistic prompts.",
        )
        work_start = _ask_time("Work start time [default=09:00]", default="09:00")
        work_end   = _ask_time("Work end time   [default=18:00]", default="18:00")
        local_tz   = str(datetime.datetime.now().astimezone().tzinfo)
        print(f"\n  Detected system timezone: {local_tz}")
        tz = _ask(
            "Timezone",
            default="",
            required=False,
            hint="IANA name, e.g. Asia/Shanghai. Leave blank to use system timezone.",
        )
        config.update({
            "job_description": job_desc,
            "work_start":      work_start,
            "work_end":        work_end,
            "timezone":        tz,
        })
    else:
        _section("Step 7: Timezone")
        local_tz = str(datetime.datetime.now().astimezone().tzinfo)
        print(f"  Detected system timezone: {local_tz}")
        tz = _ask(
            "Timezone",
            default="",
            required=False,
            hint="IANA name, e.g. Asia/Shanghai. Leave blank to use system timezone.",
        )
        config["timezone"] = tz

    # ── Step 8: Enterprise / Gateway options ──────────────────────────────────
    _section("Step 8: Enterprise Gateway / Proxy (optional)")
    print("  Skip this section if you connect directly to the platform API.\n")

    want_gateway = _ask_bool(
        "Configure enterprise gateway or proxy settings?",
        default=False,
        hint="Choose 'y' for extra headers, HTTP proxy, mTLS, JWT auth, or custom token field.",
    )

    if want_gateway:
        # Extra headers
        print()
        want_headers = _ask_bool(
            "Add custom HTTP headers? (e.g. X-API-Gateway-Key)",
            default=False,
            hint="Useful for internal gateways that require additional auth headers.",
        )
        extra_headers = {}
        if want_headers:
            print("  Enter headers one by one. Leave header name blank to finish.")
            while True:
                hname = input("    Header name  [optional, blank to stop]\n    > ").strip()
                if not hname:
                    break
                hval = input(f"    Value for '{hname}' [required]\n    > ").strip()
                if hval:
                    extra_headers[hname] = hval
        config["extra_headers"] = extra_headers if extra_headers else None

        # HTTP proxy
        http_proxy = _ask(
            "HTTP/HTTPS proxy URL",
            required=False,
            hint="e.g. http://proxy.corp.com:8080 or socks5://127.0.0.1:1080. Leave blank to skip.",
        )
        config["http_proxy"] = http_proxy or None

        # mTLS
        want_mtls = _ask_bool(
            "Use mutual TLS (mTLS)?",
            default=False,
            hint="Required by some enterprise gateways. You need a client cert + key pair.",
        )
        if want_mtls:
            mtls_cert = _ask(
                "Path to client certificate (.pem)",
                required=True,
                hint="e.g. /etc/certs/client.crt.pem",
            )
            mtls_key = _ask(
                "Path to client private key (.pem)",
                required=True,
                hint="e.g. /etc/certs/client.key.pem",
            )
            mtls_ca = _ask(
                "Path to CA bundle (.pem)",
                required=False,
                hint="Optional. Leave blank to use system CA store.",
            )
            config["mtls_cert"] = mtls_cert
            config["mtls_key"]  = mtls_key
            config["mtls_ca"]   = mtls_ca or None
        else:
            config["mtls_cert"] = None
            config["mtls_key"]  = None
            config["mtls_ca"]   = None

        # Token field
        token_field = _ask(
            "Token count field path in API response",
            default="usage.total_tokens",
            required=False,
            hint="JSON path, e.g. 'usage.total_tokens' or 'data.usage.tokens'. Leave blank for default.",
        )
        config["token_field"] = token_field or "usage.total_tokens"

        # JWT helper
        jwt_helper = _ask(
            "JWT helper command",
            required=False,
            hint="Shell command that prints a fresh bearer token, e.g. 'python gen_token.py'. Leave blank to skip.",
        )
        if jwt_helper:
            jwt_ttl = _ask_int(
                "JWT TTL (seconds)",
                default=3600,
                min_val=60,
                hint="How long the token is valid. The tool refreshes automatically before expiry.",
            )
            config["jwt_helper"]      = jwt_helper
            config["jwt_ttl_seconds"] = jwt_ttl
        else:
            config["jwt_helper"]      = None
            config["jwt_ttl_seconds"] = None
    else:
        # Ensure keys exist with null values so config is always consistent
        config["extra_headers"]   = None
        config["http_proxy"]      = None
        config["mtls_cert"]       = None
        config["mtls_key"]        = None
        config["mtls_ca"]         = None
        config["token_field"]     = "usage.total_tokens"
        config["jwt_helper"]      = None
        config["jwt_ttl_seconds"] = None

    # ── Write config ──────────────────────────────────────────────────────────
    Path(output).write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")

    print("\n" + "─" * 60)
    print_success(f"Config saved to: {output}")
    print("─" * 60)
    print("\nNext steps:")
    print("  1. Start daemon:   python tmw.py start")
    print("  2. Check status:   python tmw.py status")
    print("  3. View logs:      python tmw.py logs")
    print("  4. Stop daemon:    python tmw.py stop\n")
