"""
Core consumption engine — handles both Random and Work-Simulation modes.
"""

from __future__ import annotations

import datetime
import random
import time

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

# ── Work-mode prompt template ─────────────────────────────────────────────────

_WORK_PROMPT_TEMPLATE = """\
You are a {job_description}.
Generate 6 specific, realistic questions you would ask an AI assistant during your typical workday.
Requirements:
- Questions must be directly relevant to your role
- Mix of technical, analytical, and communication tasks
- Each question on its own line, no numbering or bullet points
- Output only the questions, nothing else

Questions:"""


def _build_client(config: dict):
    """Build an OpenAI-compatible client from config."""
    try:
        from openai import OpenAI
    except ImportError:
        import subprocess, sys
        subprocess.run([sys.executable, "-m", "pip", "install", "openai", "-q"], check=True)
        from openai import OpenAI

    platform = config.get("platform", "custom").lower()
    base_url = get_base_url(platform, config.get("base_url"))
    return OpenAI(api_key=config["api_key"], base_url=base_url)


def _call_api(client, model: str, prompt: str) -> int:
    """Make one API call, return tokens consumed (0 on error)."""
    try:
        resp = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=512,
        )
        return resp.usage.total_tokens if resp.usage else 0
    except Exception as exc:
        print_error(f"API call failed: {exc}")
        return 0


def _resolve_tz(config: dict):
    """Resolve timezone from config, fall back to local."""
    import zoneinfo
    tz_name = config.get("timezone", "")
    if tz_name:
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
    """
    s = work_start.hour * 60 + work_start.minute
    e = work_end.hour * 60 + work_end.minute
    span = e - s

    lunch_s = s + int(span * 0.45)
    lunch_e = lunch_s + 60
    dinner_s = e - 90
    dinner_e = dinner_s + 45

    def m2t(m):
        return datetime.time(m // 60 % 24, m % 60)

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


def _generate_work_prompts(client, model: str, job_desc: str) -> list[str]:
    """Ask the LLM to generate job-relevant prompts."""
    meta = _WORK_PROMPT_TEMPLATE.format(job_description=job_desc)
    try:
        resp = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": meta}],
            max_tokens=600,
        )
        lines = (resp.choices[0].message.content or "").strip().splitlines()
        prompts = [l.strip() for l in lines if l.strip()]
        return prompts[:6] if prompts else random.sample(RANDOM_PROMPTS, 6)
    except Exception as exc:
        print_warning(f"Could not generate work prompts ({exc}), using random pool.")
        return random.sample(RANDOM_PROMPTS, 6)


# ── Public entry points ───────────────────────────────────────────────────────

def run_random_mode(config: dict, config_path: str, dry_run: bool = False) -> None:
    """
    Random mode: consume tokens evenly throughout the day using random prompts.
    Daily target = weekly_target / 7  (±5%).
    """
    tz = _resolve_tz(config)
    state = st.load(config_path)

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

    total = 0
    prompts = RANDOM_PROMPTS.copy()
    random.shuffle(prompts)
    pool = prompts * ((remaining // 200) + 5)

    for prompt in pool:
        if total >= remaining:
            break
        tokens = _call_api(client, model, prompt)
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

    print_info("Generating work-relevant prompts…")
    work_prompts = _generate_work_prompts(client, model, job_desc)
    print_success(f"Generated {len(work_prompts)} prompts for '{job_desc}'")

    pool = (work_prompts * 20)
    random.shuffle(pool)

    total = 0
    for prompt in pool:
        if total >= seg_tgt:
            break
        tokens = _call_api(client, model, prompt)
        if tokens:
            total += tokens
            st.record(config_path, state, tokens, tz)
            print_api_call(prompt, tokens, total, seg_tgt)
        if total < seg_tgt:
            sleep = random.randint(30, 180)
            time.sleep(sleep)

    print_success(f"Session complete! Consumed {total:,} tokens.")
