"""
Core consumption engine — handles both Random and Work-Simulation modes.

Enterprise gateway support:
  - extra_headers   : inject arbitrary HTTP headers into every request
  - http_proxy      : route traffic through an HTTP/HTTPS/SOCKS5 proxy
  - token_field     : configurable dot-path or header for token count extraction
  - jwt_helper      : shell command to fetch a fresh JWT/Bearer token
  - mtls_cert/key   : client certificate for mutual TLS
  - mtls_ca         : custom CA bundle for server certificate verification
"""

from __future__ import annotations

import datetime
import random
import subprocess
import sys
import time
from typing import Any

# Python 3.9+ has zoneinfo in stdlib; 3.8 needs backports.zoneinfo
try:
    import zoneinfo
except ImportError:
    try:
        from backports import zoneinfo  # type: ignore[no-redef]
    except ImportError:
        zoneinfo = None  # type: ignore[assignment]

from . import state as st
from .display import (
    print_api_call, print_error, print_info, print_mode_header,
    print_skipped, print_success, print_warning,
)
from .platforms import get_base_url, get_default_model

# ── Random prompt pool (used in random mode) ─────────────────────────────────

RANDOM_PROMPTS = [
    "Explain the concept of quantum entanglement in simple terms.",
    "What are the key differences between REST and GraphQL APIs?",
    "Write a short poem about autumn leaves.",
    "How does garbage collection work in Python?",
    "Give me 5 tips for improving code readability.",
    "What is the CAP theorem in distributed systems?",
    "Explain the difference between supervised and unsupervised learning.",
    "How do I implement a binary search tree in Python?",
    "What are the SOLID principles in software engineering?",
    "Explain how HTTPS works step by step.",
    "What is the difference between a process and a thread?",
    "How does the transformer architecture work in LLMs?",
    "Write a regex to validate an email address.",
    "What are some common SQL query optimization techniques?",
    "Explain the concept of eventual consistency.",
    "What is the difference between Docker and a virtual machine?",
    "How does React's virtual DOM improve performance?",
    "What are the main principles of clean code?",
    "Explain the concept of idempotency in APIs.",
    "What is the difference between TCP and UDP?",
    "How does a hash table handle collisions?",
    "What is the time complexity of quicksort?",
    "Explain the observer design pattern with an example.",
    "What are microservices and when should you use them?",
    "How does OAuth 2.0 work?",
    "What is the difference between authentication and authorization?",
    "Explain the concept of database indexing.",
    "What are the benefits of using TypeScript over JavaScript?",
    "How does Kubernetes handle container orchestration?",
    "What is a deadlock and how can it be prevented?",
]

# ── Work-mode prompt templates ───────────────────────────────────────────────

# Keywords that identify engineering / technical roles
_ENGINEER_KEYWORDS = {
    "engineer", "developer", "programmer", "coder", "architect",
    "backend", "frontend", "fullstack", "full-stack", "full stack",
    "devops", "sre", "platform", "infrastructure", "infra",
    "data scientist", "ml engineer", "machine learning", "ai engineer",
    "software", "系统", "工程师", "开发", "程序员", "后端", "前端",
    "运维", "架构", "算法",
}


def _is_engineer_role(job_desc: str) -> bool:
    """Return True if the job description matches an engineering / technical role."""
    lower = job_desc.lower()
    return any(kw in lower for kw in _ENGINEER_KEYWORDS)


# Template for non-engineer roles (PM, designer, analyst, etc.)
_WORK_PROMPT_TEMPLATE = """\
You are a {job_description}.
Generate 6 specific, realistic questions you would ask an AI assistant during your typical workday.
Requirements:
- Questions must be directly relevant to your role
- Mix of strategic, analytical, and communication tasks
- Each question on its own line, no numbering or bullet points
- Output only the questions, nothing else

Questions:"""

# Template for engineer roles — generates prompts WITH code context
_ENGINEER_PROMPT_TEMPLATE = """\
You are a {job_description}.
Generate 5 realistic AI assistant prompts that a developer would send during a real workday.

Each prompt MUST:
- Include a realistic file path (e.g. src/api/auth.py, services/UserService.ts)
- Include an actual code snippet (10-25 lines) that looks like real production code
- Describe a specific problem: a bug, a performance issue, a refactor request, a code review, or a new feature
- Be written in first person, as if pasting code into Claude/ChatGPT
- Feel like a real developer asking for help, NOT a textbook question

Format each prompt as a complete message the developer would send, starting directly with the context.
Separate prompts with a line containing only "---".
Output only the prompts, nothing else.

Example style (do NOT copy this, generate role-appropriate ones):
```
I'm getting a 500 error in production on this endpoint. The error is `NullPointerException` at line 47.
Here's the relevant code from `src/handlers/payment.py`:

```python
def process_payment(order_id: str, amount: float):
    order = db.query(Order).filter(Order.id == order_id).first()
    # BUG: order can be None if the ID is invalid
    total = order.amount + amount
    ...
```

How do I add proper null checking and return a 404 instead?
```"""


# ── JWT token cache ───────────────────────────────────────────────────────────

_jwt_cache: dict[str, Any] = {"token": None, "fetched_at": 0.0}


def _fetch_jwt(helper_cmd: str) -> str:
    """Run the JWT helper command and return the token string."""
    try:
        result = subprocess.run(
            helper_cmd, shell=True, capture_output=True, text=True, timeout=15
        )
        token = result.stdout.strip()
        if not token:
            raise RuntimeError(f"JWT helper returned empty output. stderr: {result.stderr.strip()}")
        return token
    except subprocess.TimeoutExpired:
        raise RuntimeError(f"JWT helper timed out after 15 seconds: {helper_cmd}")


def _resolve_api_key(config: dict) -> str:
    """
    Resolve the effective API key.
    If jwt_helper is set, run it (with TTL caching) and use its output.
    Otherwise, return config['api_key'].
    """
    helper = config.get("jwt_helper")
    if not helper:
        return config["api_key"]

    ttl = int(config.get("jwt_ttl_seconds", 3600))
    now = time.time()
    if _jwt_cache["token"] is None or (now - _jwt_cache["fetched_at"]) >= ttl:
        print_info(f"Refreshing JWT token via helper: {helper}")
        _jwt_cache["token"] = _fetch_jwt(helper)
        _jwt_cache["fetched_at"] = now
        print_info("JWT token refreshed.")
    return _jwt_cache["token"]


# ── Token field extraction ────────────────────────────────────────────────────

def _extract_tokens(resp, token_field: Optional[str], response_headers: Optional[dict] = None) -> int:
    """
    Extract token count from an API response.

    token_field formats:
      None / ""                    → resp.usage.total_tokens  (default)
      "usage.total_tokens"         → resp.usage.total_tokens
      "usage.prompt_tokens+usage.completion_tokens"  → sum of two fields
      "header:X-Tokens-Used"       → read from response header
    """
    if not token_field:
        # Default: standard OpenAI usage object
        try:
            return resp.usage.total_tokens if resp.usage else 0
        except AttributeError:
            return 0

    tf = token_field.strip()

    # Header-based extraction
    if tf.startswith("header:"):
        header_name = tf[len("header:"):].strip()
        if response_headers and header_name in response_headers:
            try:
                return int(response_headers[header_name])
            except (ValueError, TypeError):
                print_warning(f"Could not parse header '{header_name}' as int.")
                return 0
        print_warning(f"Header '{header_name}' not found in response headers.")
        return 0

    # Sum of two dot-path fields: "a.b+c.d"
    if "+" in tf:
        parts = [p.strip() for p in tf.split("+")]
        total = 0
        for part in parts:
            total += _get_nested(resp, part)
        return total

    # Single dot-path field
    return _get_nested(resp, tf)


def _get_nested(obj: Any, dot_path: str) -> int:
    """Traverse a dot-path like 'usage.total_tokens' on an object or dict."""
    parts = dot_path.split(".")
    cur = obj
    for part in parts:
        if cur is None:
            return 0
        if isinstance(cur, dict):
            cur = cur.get(part)
        else:
            cur = getattr(cur, part, None)
    try:
        return int(cur) if cur is not None else 0
    except (ValueError, TypeError):
        return 0


# ── HTTP client builder ───────────────────────────────────────────────────────

def _build_http_client(config: dict):
    """
    Build an httpx.Client with proxy, mTLS, and custom CA support.
    Returns None if no special transport is needed (fall back to openai default).
    """
    needs_custom = any([
        config.get("http_proxy"),
        config.get("mtls_cert"),
        config.get("mtls_ca"),
    ])
    if not needs_custom:
        return None

    try:
        import httpx
    except ImportError:
        import subprocess, sys
        subprocess.run([sys.executable, "-m", "pip", "install", "httpx", "-q"], check=True)
        import httpx

    kwargs: dict[str, Any] = {}

    # HTTP / SOCKS5 proxy
    proxy = config.get("http_proxy")
    if proxy:
        kwargs["proxy"] = proxy
        print_info(f"Using HTTP proxy: {proxy}")

    # mTLS client certificate
    cert_path = config.get("mtls_cert")
    key_path  = config.get("mtls_key")
    ca_path   = config.get("mtls_ca")

    if cert_path and key_path:
        kwargs["cert"] = (cert_path, key_path)
        print_info(f"Using mTLS client cert: {cert_path}")

    if ca_path:
        kwargs["verify"] = ca_path
        print_info(f"Using custom CA bundle: {ca_path}")
    else:
        kwargs.setdefault("verify", True)

    return httpx.Client(**kwargs)


def _build_client(config: dict):
    """Build an OpenAI-compatible client from config, with full gateway support."""
    try:
        from openai import OpenAI
    except ImportError:
        import subprocess, sys
        subprocess.run([sys.executable, "-m", "pip", "install", "openai", "-q"], check=True)
        from openai import OpenAI

    platform = config.get("platform", "custom").lower()
    base_url = get_base_url(platform, config.get("base_url"))
    api_key  = _resolve_api_key(config)

    # Build extra default headers
    default_headers: dict[str, str] = {}
    extra = config.get("extra_headers")
    if extra and isinstance(extra, dict):
        default_headers.update({str(k): str(v) for k, v in extra.items()})
        print_info(f"Injecting {len(extra)} custom header(s): {list(extra.keys())}")

    # Build custom httpx client if needed
    http_client = _build_http_client(config)

    openai_kwargs: dict[str, Any] = {
        "api_key": api_key,
        "base_url": base_url,
        "default_headers": default_headers,
    }
    if http_client is not None:
        openai_kwargs["http_client"] = http_client

    return OpenAI(**openai_kwargs)


# ── API call ──────────────────────────────────────────────────────────────────

def _call_api(client, model: str, prompt: str, token_field: Optional[str] = None) -> int:
    """Make one API call, return tokens consumed (0 on error)."""
    try:
        resp = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=512,
        )
        # Try to get response headers for header-based token extraction
        response_headers: Optional[dict] = None
        if token_field and token_field.startswith("header:"):
            # The openai SDK wraps the raw response; attempt to access it
            try:
                response_headers = dict(resp._raw_response.headers)  # type: ignore[attr-defined]
            except AttributeError:
                response_headers = None

        return _extract_tokens(resp, token_field, response_headers)
    except Exception as exc:
        print_error(f"API call failed: {exc}")
        return 0


# ── Timezone helper ───────────────────────────────────────────────────────────

def _resolve_tz(config: dict):
    """Resolve timezone from config, fall back to local."""
    tz_name = config.get("timezone", "")
    if tz_name and zoneinfo is not None:
        try:
            return zoneinfo.ZoneInfo(tz_name)
        except Exception:
            print_warning(f"Unknown timezone '{tz_name}', using system timezone.")
    return datetime.datetime.now().astimezone().tzinfo


def _daily_target(weekly_target: int, divisor: int) -> int:
    """Compute daily target with ±5% jitter."""
    base = weekly_target / divisor
    return int(base * random.uniform(0.95, 1.05))


# ── Work schedule helpers ─────────────────────────────────────────────────────

def _parse_hhmm(s: str) -> datetime.time:
    h, m = map(int, s.strip().split(":"))
    return datetime.time(h, m)


def _work_segments(work_start: datetime.time, work_end: datetime.time):
    """
    Split the workday into three segments, inferring lunch and dinner breaks.
    Returns list of (start, end, weight).
    Handles short workdays gracefully: if span < 150 min, skip break inference
    and treat the whole period as a single segment.
    """
    s = work_start.hour * 60 + work_start.minute
    e = work_end.hour * 60 + work_end.minute
    # Handle overnight shifts (e.g. 22:00 ~ 06:00)
    if e <= s:
        e += 24 * 60
    span = e - s

    def m2t(m):
        return datetime.time(m // 60 % 24, m % 60)

    # Need at least 150 min to fit lunch (60 min) + dinner (45 min) without overlap
    if span < 150:
        print_info("Work span < 2.5 hours — skipping break inference, treating as single segment.")
        return [(work_start, work_end, 1.0)]

    lunch_s = s + int(span * 0.45)
    lunch_e = lunch_s + 60
    dinner_s = e - 90
    dinner_e = dinner_s + 45

    # Safety check: if lunch_e overlaps dinner_s, collapse to two segments (no dinner break)
    if lunch_e >= dinner_s:
        print_info(f"Inferred lunch  {m2t(lunch_s).strftime('%H:%M')} – {m2t(lunch_e).strftime('%H:%M')}")
        print_info("Work span too short for dinner break — using two segments only.")
        return [
            (work_start,    m2t(lunch_s),  0.45),
            (m2t(lunch_e),  work_end,       0.55),
        ]

    print_info(f"Inferred lunch  {m2t(lunch_s).strftime('%H:%M')} – {m2t(lunch_e).strftime('%H:%M')}")
    print_info(f"Inferred dinner {m2t(dinner_s).strftime('%H:%M')} – {m2t(dinner_e).strftime('%H:%M')}")

    return [
        (work_start,    m2t(lunch_s),  0.40),
        (m2t(lunch_e),  m2t(dinner_s), 0.45),
        (m2t(dinner_e), work_end,       0.15),
    ]


def _current_segment(now_time: datetime.time, segments):
    for start, end, weight in segments:
        if start <= now_time < end:
            return weight
    return None


def _generate_work_prompts(client, model: str, job_desc: str, token_field: Optional[str] = None) -> List[str]:
    """
    Ask the LLM to generate job-relevant prompts.
    For engineering roles, generates prompts with real code context (file paths,
    code snippets, error messages) to mimic Claude Code / Cursor usage patterns.
    For other roles, generates question-style prompts.
    """
    is_eng = _is_engineer_role(job_desc)

    if is_eng:
        meta = _ENGINEER_PROMPT_TEMPLATE.format(job_description=job_desc)
        max_tok = 2000  # code snippets need more tokens
    else:
        meta = _WORK_PROMPT_TEMPLATE.format(job_description=job_desc)
        max_tok = 600

    try:
        resp = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": meta}],
            max_tokens=max_tok,
        )
        raw = (resp.choices[0].message.content or "").strip()

        if is_eng:
            # Split on "---" separator; each chunk is one full prompt
            chunks = [c.strip() for c in raw.split("---") if c.strip()]
            prompts = chunks[:5] if chunks else None
            if not prompts:
                # Fallback: treat each non-empty paragraph as a prompt
                prompts = [p.strip() for p in raw.split("\n\n") if len(p.strip()) > 50]
            return prompts[:5] if prompts else random.sample(RANDOM_PROMPTS, 5)
        else:
            lines = raw.splitlines()
            prompts = [l.strip() for l in lines if l.strip()]
            return prompts[:6] if prompts else random.sample(RANDOM_PROMPTS, 6)

    except Exception as exc:
        print_warning(f"Could not generate work prompts ({exc}), using random pool.")
        return random.sample(RANDOM_PROMPTS, 5 if is_eng else 6)


# ── Public entry points ───────────────────────────────────────────────────────

def run_random_mode(config: dict, config_path: str, dry_run: bool = False) -> None:
    """
    Random mode: consume tokens evenly throughout the day using random prompts.
    Daily target = weekly_target / 7  (±5%).
    """
    tz = _resolve_tz(config)
    state = st.load(config_path)
    token_field = config.get("token_field") or None

    weekly_target = random.randint(config["weekly_min"], config["weekly_max"])
    daily_tgt = _daily_target(weekly_target, 7)
    today = st.today_consumed(state, tz)
    remaining = daily_tgt - today

    print_mode_header("Random Mode", daily_tgt, today, weekly_target)

    if remaining <= 0:
        print_skipped("Daily target already reached.")
        return

    if dry_run:
        print_info(f"[DRY RUN] Would consume ~{remaining:,} tokens. No API calls made.")
        return

    client = _build_client(config)
    model = config.get("model") or get_default_model(config.get("platform", "openai"))
    print_info(f"Using model: {model}")
    if token_field:
        print_info(f"Token field: {token_field}")

    total = 0
    prompts = RANDOM_PROMPTS.copy()
    random.shuffle(prompts)
    pool = prompts * ((remaining // 200) + 5)

    for prompt in pool:
        if total >= remaining:
            break
        tokens = _call_api(client, model, prompt, token_field)
        if tokens:
            total += tokens
            st.record(config_path, state, tokens, tz)
            print_api_call(prompt, tokens, total, remaining)
        if total < remaining:
            sleep = random.randint(10, 60)
            time.sleep(sleep)

    print_success(f"Done! Consumed {total:,} tokens this run.")


def run_work_mode(config: dict, config_path: str, dry_run: bool = False) -> None:
    """
    Work-simulation mode: consume tokens only during working hours,
    weighted by time-of-day. Daily target = weekly_target / 5  (±5%).
    """
    tz = _resolve_tz(config)
    state = st.load(config_path)
    token_field = config.get("token_field") or None

    weekly_target = random.randint(config["weekly_min"], config["weekly_max"])
    daily_tgt = _daily_target(weekly_target, 5)
    today = st.today_consumed(state, tz)
    remaining = daily_tgt - today

    work_start = _parse_hhmm(config["work_start"])
    work_end   = _parse_hhmm(config["work_end"])
    job_desc   = config.get("job_description", "software engineer")

    now = datetime.datetime.now(tz)
    print_mode_header("Work-Simulation Mode", daily_tgt, today, weekly_target)
    print_info(f"Work hours: {work_start.strftime('%H:%M')} – {work_end.strftime('%H:%M')}")
    print_info(f"Job: {job_desc}")

    # Weekday check
    if now.weekday() >= 5:
        print_skipped("Weekend — no work today.")
        return

    segments = _work_segments(work_start, work_end)
    weight = _current_segment(now.time(), segments)

    if weight is None:
        print_skipped(f"Outside working hours ({now.strftime('%H:%M')}).")
        return

    if remaining <= 0:
        print_skipped("Daily target already reached.")
        return

    # Segment target with extra jitter to look organic
    seg_tgt = int(remaining * weight * random.uniform(0.75, 1.25))
    seg_tgt = max(1, min(seg_tgt, remaining))
    print_info(f"Segment weight {weight:.0%} → targeting ~{seg_tgt:,} tokens this session.")

    if dry_run:
        print_info(f"[DRY RUN] Would consume ~{seg_tgt:,} tokens. No API calls made.")
        return

    client = _build_client(config)
    model = config.get("model") or get_default_model(config.get("platform", "openai"))
    print_info(f"Using model: {model}")
    if token_field:
        print_info(f"Token field: {token_field}")

    print_info("Generating work-relevant prompts…")
    work_prompts = _generate_work_prompts(client, model, job_desc, token_field)
    print_success(f"Generated {len(work_prompts)} prompts for '{job_desc}'")

    pool = (work_prompts * 20)
    random.shuffle(pool)

    total = 0
    for prompt in pool:
        if total >= seg_tgt:
            break
        tokens = _call_api(client, model, prompt, token_field)
        if tokens:
            total += tokens
            st.record(config_path, state, tokens, tz)
            print_api_call(prompt, tokens, total, seg_tgt)
        if total < seg_tgt:
            sleep = random.randint(30, 180)
            time.sleep(sleep)

    print_success(f"Session complete! Consumed {total:,} tokens.")
