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
    "_base_url_hint": "Override the platform URL (e.g. for a proxy/gateway). Leave null to use the preset.",
    "model": None,
    "_model_hint": "Leave null to use the platform's default cheap model.",
    "weekly_min": 50000,
    "weekly_max": 80000,
    "_weekly_hint": "Actual weekly target is randomly chosen in [min, max]. Daily quota fluctuates ±5%.",
    "simulate_work": False,
    "timezone": "",
    "_timezone_hint": "e.g. 'Asia/Shanghai'. Leave empty to use system timezone.",

    "_gateway_section": "── Enterprise Gateway Options (all optional) ──────────────────",

    "extra_headers": None,
    "_extra_headers_hint": (
        "Extra HTTP headers injected into every request. "
        "Useful for gateways that require custom auth headers. "
        "Example: {\"X-Team-ID\": \"eng\", \"X-Project\": \"ai-tools\"}"
    ),

    "http_proxy": None,
    "_http_proxy_hint": (
        "HTTP/HTTPS proxy URL for outbound requests. "
        "Example: \"http://proxy.corp.com:8080\" or \"socks5://127.0.0.1:1080\""
    ),

    "token_field": None,
    "_token_field_hint": (
        "Dot-path to the token count in the API response body. "
        "Default: 'usage.total_tokens'. "
        "Use 'usage.prompt_tokens+usage.completion_tokens' to sum two fields. "
        "Use 'header:X-Tokens-Used' to read from a response header."
    ),

    "jwt_helper": None,
    "_jwt_helper_hint": (
        "Shell command that prints a fresh JWT/Bearer token to stdout. "
        "Executed before each run; output replaces api_key. "
        "Example: \"vault kv get -field=token secret/llm/mykey\""
    ),

    "jwt_ttl_seconds": 3600,
    "_jwt_ttl_hint": "How often (seconds) to refresh the JWT token. Default: 3600.",

    "mtls_cert": None,
    "_mtls_cert_hint": "Path to client certificate file (PEM) for mutual TLS.",

    "mtls_key": None,
    "_mtls_key_hint": "Path to client private key file (PEM) for mutual TLS.",

    "mtls_ca": None,
    "_mtls_ca_hint": "Path to CA bundle file (PEM) to verify the server certificate.",
}

_WORK_TEMPLATE = {
    **_RANDOM_TEMPLATE,
    "_readme": "TrustMeImWorking config (work-simulation mode)",
    "simulate_work": True,
    "job_description": "Python backend engineer working on microservices and REST APIs",
    "work_start": "09:00",
    "work_end": "18:00",
}

_GATEWAY_TEMPLATE = {
    "_readme": "TrustMeImWorking config — Enterprise Gateway Example",
    "platform": "custom",
    "api_key": "YOUR-GATEWAY-KEY",
    "base_url": "https://ai-gateway.corp.com/v1",
    "model": "gpt-4o-mini",
    "weekly_min": 50000,
    "weekly_max": 80000,
    "simulate_work": False,
    "timezone": "Asia/Shanghai",

    "extra_headers": {
        "X-Team-ID": "engineering",
        "X-Project-ID": "ai-productivity",
        "X-User-Email": "you@company.com"
    },

    "http_proxy": None,
    "token_field": "usage.total_tokens",

    "jwt_helper": None,
    "jwt_ttl_seconds": 3600,

    "mtls_cert": None,
    "mtls_key": None,
    "mtls_ca": None,
}

_PROXY_TEMPLATE = {
    "_readme": "TrustMeImWorking config — HTTP Proxy + mTLS Example",
    "platform": "openai",
    "api_key": "sk-YOUR-API-KEY",
    "base_url": None,
    "model": None,
    "weekly_min": 50000,
    "weekly_max": 80000,
    "simulate_work": False,
    "timezone": "",

    "extra_headers": None,
    "http_proxy": "http://proxy.corp.com:8080",
    "token_field": None,

    "jwt_helper": None,
    "jwt_ttl_seconds": 3600,

    "mtls_cert": "/etc/ssl/client.crt",
    "mtls_key": "/etc/ssl/client.key",
    "mtls_ca": "/etc/ssl/corp-ca-bundle.pem",
}


def generate_template(path: str, mode: str = "random") -> None:
    if mode == "work":
        tpl = _WORK_TEMPLATE
    elif mode == "gateway":
        tpl = _GATEWAY_TEMPLATE
    elif mode == "proxy":
        tpl = _PROXY_TEMPLATE
    else:
        tpl = _RANDOM_TEMPLATE
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

    # Validate extra_headers must be a dict if provided
    if cfg.get("extra_headers") is not None:
        if not isinstance(cfg["extra_headers"], dict):
            raise ValueError("'extra_headers' must be a JSON object (dict), e.g. {\"X-Team\": \"eng\"}")

    # Validate mTLS: cert and key must both be present or both absent
    has_cert = bool(cfg.get("mtls_cert"))
    has_key  = bool(cfg.get("mtls_key"))
    if has_cert != has_key:
        raise ValueError("'mtls_cert' and 'mtls_key' must both be set (or both omitted).")

    # Validate token_field syntax if provided
    tf = cfg.get("token_field")
    if tf and not isinstance(tf, str):
        raise ValueError("'token_field' must be a string.")

    return cfg
