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

# ── i18n string table ─────────────────────────────────────────────────────────

_STRINGS: dict = {
    "en": {
        # header
        "wizard_title":       "TrustMeImWorking — Interactive Setup Wizard",
        "legend":             "Legend:  [required]  [optional]  [default=X]",
        # language step
        "lang_prompt":        "Language / 语言",
        "lang_hint":          "Enter 1 or 'en' for English, 2 or 'zh' for 中文.",
        "lang_opt_en":        "  1) English",
        "lang_opt_zh":        "  2) 中文",
        # generic helpers
        "required_msg":       "This field is required. Please enter a value.",
        "invalid_int":        "Please enter a valid integer.",
        "min_val_msg":        "Must be ≥ {min_val}.",
        "invalid_yn":         "Please enter y or n.",
        "invalid_time":       "Please use HH:MM format (e.g. 09:00).",
        "yes_label":          "yes",
        "no_label":           "no",
        # step titles
        "step1_title":        "Step 1: Platform",
        "step2_title":        "Step 2: API Key",
        "step3_title":        "Step 3: API Base URL / Third-party Relay",
        "step4_title":        "Step 4: Model",
        "step5_title":        "Step 5: Weekly Token Budget",
        "step6_title":        "Step 6: Run Mode",
        "step7_work_title":   "Step 7: Work Schedule",
        "step7_tz_title":     "Step 7: Timezone",
        "step8_title":        "Step 8: Enterprise Gateway / Proxy (optional)",
        # step 1
        "custom_platform":    "Custom / Self-hosted / Third-party relay",
        "platform_prompt":    "Platform name or number",
        "platform_hint":      "Enter the platform key (e.g. openai, deepseek) or its list number.",
        "unknown_platform":   "Unknown platform '{platform}' — treating as custom.",
        # step 2
        "apikey_prompt":      "API Key",
        "apikey_hint":        "Your platform API key (e.g. sk-...). Never committed to git.",
        # step 3
        "relay_help": """
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
  ─────────────────────────────────────────────────────────────────""",
        "custom_url_required":   "  You selected 'custom' — a Base URL is required.",
        "default_url_label":     "  Default URL for {platform}: {url}",
        "override_prompt":       "Use a third-party relay or company gateway instead of the official URL?",
        "override_hint":         "Choose 'y' to enter a custom base URL (relay, proxy, internal gateway).",
        "base_url_prompt":       "Base URL",
        "base_url_hint":         "Must end with /v1 (or equivalent path). See examples above.",
        "relay_url_prompt":      "Relay / Gateway Base URL",
        # step 4
        "model_recommended":     "  Recommended flagship model: {model}",
        "model_prompt":          "Model name",
        "model_hint":            "Leave blank to use the platform default. Flagship models consume the most tokens.",
        # step 5
        "budget_note":           "  The actual weekly target is randomly chosen in [min, max].\n  Daily quota = weekly / 7 (immediate/spread) or / 5 (work), ±5%.",
        "weekly_min_prompt":     "Weekly minimum (tokens)",
        "weekly_min_hint":       "Lower bound of your weekly token target range.",
        "weekly_max_prompt":     "Weekly maximum (tokens)",
        "weekly_max_hint":       "Upper bound. Must be ≥ weekly minimum.",
        # step 6
        "mode_intro":            "  Choose how TrustMeImWorking consumes your daily token budget:\n",
        "mode_opt_immediate":    "  1) immediate  — Start consuming right now (today), then every day at 00:00.\n                  Finishes the daily budget as fast as possible.\n                  Best for: you just want it done quickly.\n",
        "mode_opt_spread":       "  2) spread     — Distribute today's budget evenly across the remaining hours,\n                  then spread each future day's budget across the full 24 h.\n                  Calls are spaced so the quota is reached near midnight.\n                  Best for: natural-looking, time-distributed usage.\n",
        "mode_opt_work":         "  3) work       — Consume only during working hours (weekdays), using\n                  job-relevant prompts and organic pacing.\n                  Best for: mimicking real work activity patterns.\n",
        "mode_prompt":           "Run mode [default=immediate]",
        "mode_hint":             "Enter 1/immediate, 2/spread, or 3/work.",
        "mode_unknown":          "  Unrecognised option, defaulting to 'immediate'.",
        # step 7 work
        "job_desc_prompt":       "Job description",
        "job_desc_hint":         "e.g. 'Python backend engineer', 'data analyst'. Used to generate realistic prompts.",
        "work_start_prompt":     "Work start time [default=09:00]",
        "work_end_prompt":       "Work end time   [default=18:00]",
        "tz_detected":           "  Detected system timezone: {tz}",
        "tz_prompt":             "Timezone",
        "tz_hint":               "IANA name, e.g. Asia/Shanghai. Leave blank to use system timezone.",
        # step 8
        "step8_skip":            "  Skip this section if you connect directly to the platform API.\n",
        "gateway_prompt":        "Configure enterprise gateway or proxy settings?",
        "gateway_hint":          "Choose 'y' for extra headers, HTTP proxy, mTLS, JWT auth, or custom token field.",
        "headers_prompt":        "Add custom HTTP headers? (e.g. X-API-Gateway-Key)",
        "headers_hint":          "Useful for internal gateways that require additional auth headers.",
        "headers_enter":         "  Enter headers one by one. Leave header name blank to finish.",
        "header_name_prompt":    "    Header name  [optional, blank to stop]\n    > ",
        "header_val_prompt":     "    Value for '{name}' [required]\n    > ",
        "proxy_prompt":          "HTTP/HTTPS proxy URL",
        "proxy_hint":            "e.g. http://proxy.corp.com:8080 or socks5://127.0.0.1:1080. Leave blank to skip.",
        "mtls_prompt":           "Use mutual TLS (mTLS)?",
        "mtls_hint":             "Required by some enterprise gateways. You need a client cert + key pair.",
        "mtls_cert_prompt":      "Path to client certificate (.pem)",
        "mtls_cert_hint":        "e.g. /etc/certs/client.crt.pem",
        "mtls_key_prompt":       "Path to client private key (.pem)",
        "mtls_key_hint":         "e.g. /etc/certs/client.key.pem",
        "mtls_ca_prompt":        "Path to CA bundle (.pem)",
        "mtls_ca_hint":          "Optional. Leave blank to use system CA store.",
        "token_field_prompt":    "Token count field path in API response",
        "token_field_hint":      "JSON path, e.g. 'usage.total_tokens' or 'data.usage.tokens'. Leave blank for default.",
        "jwt_prompt":            "JWT helper command",
        "jwt_hint":              "Shell command that prints a fresh bearer token, e.g. 'python gen_token.py'. Leave blank to skip.",
        "jwt_ttl_prompt":        "JWT TTL (seconds)",
        "jwt_ttl_hint":          "How long the token is valid. The tool refreshes automatically before expiry.",
        # finish
        "saved_to":              "Config saved to: {path}",
        "next_steps":            "\nNext steps:\n  1. Start daemon:   python tmw.py start\n  2. Check status:   python tmw.py status\n  3. View logs:      python tmw.py logs\n  4. Stop daemon:    python tmw.py stop\n",
    },
    "zh": {
        # header
        "wizard_title":       "TrustMeImWorking — 交互式配置向导",
        "legend":             "图例：[必填]  [可选]  [默认=X]",
        # language step
        "lang_prompt":        "Language / 语言",
        "lang_hint":          "输入 1 或 'en' 选择 English，输入 2 或 'zh' 选择中文。",
        "lang_opt_en":        "  1) English",
        "lang_opt_zh":        "  2) 中文",
        # generic helpers
        "required_msg":       "此字段为必填项，请输入内容。",
        "invalid_int":        "请输入有效的整数。",
        "min_val_msg":        "必须 ≥ {min_val}。",
        "invalid_yn":         "请输入 y 或 n。",
        "invalid_time":       "请使用 HH:MM 格式（例如 09:00）。",
        "yes_label":          "是",
        "no_label":           "否",
        # step titles
        "step1_title":        "第 1 步：选择平台",
        "step2_title":        "第 2 步：API Key",
        "step3_title":        "第 3 步：API 地址 / 第三方转接",
        "step4_title":        "第 4 步：模型",
        "step5_title":        "第 5 步：每周 Token 预算",
        "step6_title":        "第 6 步：运行模式",
        "step7_work_title":   "第 7 步：工作时间设置",
        "step7_tz_title":     "第 7 步：时区",
        "step8_title":        "第 8 步：企业网关 / 代理（可选）",
        # step 1
        "custom_platform":    "自定义 / 自托管 / 第三方转接",
        "platform_prompt":    "平台名称或编号",
        "platform_hint":      "输入平台标识（如 openai、deepseek）或列表编号。",
        "unknown_platform":   "未知平台 '{platform}'，将作为自定义处理。",
        # step 2
        "apikey_prompt":      "API Key",
        "apikey_hint":        "你的平台 API Key（如 sk-...），不会被提交到 git。",
        # step 3
        "relay_help": """
  什么是"第三方转接"？
  ─────────────────────────────────────────────────────────────────
  转接服务是一个兼容 OpenAI 格式的代理，将你的请求转发给真实的
  LLM API。你保留自己的 API Key，转接服务只是改变了请求的目标地址。
  常见使用场景：

    • 绕过地区限制（如在中国访问 OpenAI）
    • 公司内部网关 / 费用管控代理
    • 多模型聚合器（一个 Key，访问多种模型）
    • 自托管 LLM 服务（Ollama、LM Studio、vLLM 等）

  如何填写 URL：
  ─────────────────────────────────────────────────────────────────
  填写的 URL 是"/chat/completions"之前的"基础路径"。
  几乎所有兼容 OpenAI 格式的转接服务都遵循以下规律：

      https://<转接服务域名>/v1

  常见场景示例：

    场景                           填写的 Base URL
    ─────────────────────────────  ──────────────────────────────────────────
    OpenAI 官方（默认）            https://api.openai.com/v1
    api2d.com 转接                 https://oa.api2d.net/v1
    自建反代                       https://openai-proxy.example.com/v1
    公司内部网关                   https://ai-gateway.corp.com/openai/v1
    Ollama（本地）                 http://localhost:11434/v1
    LM Studio（本地）              http://localhost:1234/v1
    vLLM（本地/云端）              http://your-server:8000/v1
    SiliconFlow（国内镜像）        https://api.siliconflow.cn/v1
    Groq（高速推理）               https://api.groq.com/openai/v1

  注意：工具会自动在末尾追加"/chat/completions"，
        请勿在此处填写该后缀。
  ─────────────────────────────────────────────────────────────────""",
        "custom_url_required":   "  你选择了\u300c自定义\u300d平台，必须填写 Base URL。",
        "default_url_label":     "  {platform} \u7684\u9ed8\u8ba4 URL\uff1a{url}",
        "override_prompt":       "是否使用第三方转接或公司网关替代官方 URL？",
        "override_hint":         "选 'y' 可输入自定义 Base URL（转接服务、代理、内部网关）。",
        "base_url_prompt":       "Base URL",
        "base_url_hint":         "必须以 /v1（或等效路径）结尾，参见上方示例。",
        "relay_url_prompt":      "转接 / 网关 Base URL",
        # step 4
        "model_recommended":     "  推荐旗舰模型：{model}",
        "model_prompt":          "模型名称",
        "model_hint":            "留空使用平台默认模型。旗舰模型消耗 Token 最多。",
        # step 5
        "budget_note":           "  每周实际目标在 [最小值, 最大值] 范围内随机选取。\n  每日配额 = 每周 / 7（立刻/平均模式）或 / 5（工作模拟），±5%。",
        "weekly_min_prompt":     "每周最少 Token 数",
        "weekly_min_hint":       "每周 Token 目标范围的下限。",
        "weekly_max_prompt":     "每周最多 Token 数",
        "weekly_max_hint":       "上限，必须 ≥ 最小值。",
        # step 6
        "mode_intro":            "  选择 TrustMeImWorking 消耗每日 Token 配额的方式：\n",
        "mode_opt_immediate":    "  1) 立刻（immediate）— 今天立刻开始消耗，后续每天 00:00 开始。\n                        尽快消耗完当日配额。\n                        适合：想快速完成消耗的用户。\n",
        "mode_opt_spread":       "  2) 平均（spread）   — 将今日配额均匀分散到今天剩余时间，\n                        后续每天将全天 24 小时均匀消耗。\n                        调用间隔动态计算，确保接近 23:59 时恰好消耗完。\n                        适合：希望使用记录看起来自然分散的用户。\n",
        "mode_opt_work":         "  3) 工作模拟（work） — 仅在工作日的工作时段内消耗，\n                        使用与职位相关的 prompt，模拟真实工作节奏。\n                        适合：希望模仿真实工作使用模式的用户。\n",
        "mode_prompt":           "运行模式 [默认=立刻]",
        "mode_hint":             "输入 1/immediate/立刻、2/spread/平均 或 3/work/工作模拟。",
        "mode_unknown":          "  无法识别的选项，默认使用\u300c立刻\u300d模式。",
        # step 7 work
        "job_desc_prompt":       "职位描述",
        "job_desc_hint":         "例如\u300cPython 后端工程师\u300d、\u300c数据分析师\u300d，用于生成真实感 prompt。",
        "work_start_prompt":     "上班时间 [默认=09:00]",
        "work_end_prompt":       "下班时间 [默认=18:00]",
        "tz_detected":           "  检测到系统时区：{tz}",
        "tz_prompt":             "时区",
        "tz_hint":               "IANA 时区名，如 Asia/Shanghai。留空使用系统时区。",
        # step 8
        "step8_skip":            "  如果直接连接平台 API，可跳过此步骤。\n",
        "gateway_prompt":        "是否配置企业网关或代理？",
        "gateway_hint":          "选 'y' 可设置自定义请求头、HTTP 代理、mTLS、JWT 认证或自定义 Token 字段。",
        "headers_prompt":        "是否添加自定义 HTTP 请求头？（如 X-API-Gateway-Key）",
        "headers_hint":          "适用于需要额外认证头的内部网关。",
        "headers_enter":         "  逐条输入请求头，留空请求头名称即可结束。",
        "header_name_prompt":    "    请求头名称  [可选，留空结束]\n    > ",
        "header_val_prompt":     "    '{name}' 的值 [必填]\n    > ",
        "proxy_prompt":          "HTTP/HTTPS 代理 URL",
        "proxy_hint":            "如 http://proxy.corp.com:8080 或 socks5://127.0.0.1:1080，留空跳过。",
        "mtls_prompt":           "是否使用双向 TLS（mTLS）？",
        "mtls_hint":             "部分企业网关要求，需要客户端证书 + 私钥。",
        "mtls_cert_prompt":      "客户端证书路径（.pem）",
        "mtls_cert_hint":        "如 /etc/certs/client.crt.pem",
        "mtls_key_prompt":       "客户端私钥路径（.pem）",
        "mtls_key_hint":         "如 /etc/certs/client.key.pem",
        "mtls_ca_prompt":        "CA bundle 路径（.pem）",
        "mtls_ca_hint":          "可选，留空使用系统 CA 证书库。",
        "token_field_prompt":    "API 响应中 Token 数量的字段路径",
        "token_field_hint":      "JSON 路径，如 'usage.total_tokens' 或 'data.usage.tokens'，留空使用默认值。",
        "jwt_prompt":            "JWT 动态令牌生成命令",
        "jwt_hint":              "输出 Bearer Token 的 shell 命令，如 'python gen_token.py'，留空跳过。",
        "jwt_ttl_prompt":        "JWT 有效期（秒）",
        "jwt_ttl_hint":          "令牌有效时长，工具会在到期前自动刷新。",
        # finish
        "saved_to":              "配置已保存到：{path}",
        "next_steps":            "\n下一步：\n  1. 启动守护进程：python tmw.py start\n  2. 查看状态：    python tmw.py status\n  3. 查看日志：    python tmw.py logs\n  4. 停止运行：    python tmw.py stop\n",
    },
}

# Active language (set at wizard start)
_LANG = "en"


def _t(key: str, **kwargs) -> str:
    """Translate a string key using the active language."""
    s = _STRINGS[_LANG].get(key, _STRINGS["en"].get(key, key))
    return s.format(**kwargs) if kwargs else s


# ── Low-level prompt helpers ──────────────────────────────────────────────────

def _ask(prompt: str, default=None, required: bool = True, hint: str = "") -> str:
    if default is not None:
        tag = f"[default={default}]"
    elif required:
        tag = "[required]" if _LANG == "en" else "[必填]"
    else:
        tag = "[optional]" if _LANG == "en" else "[可选]"

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
        print(f"    ↳ {_t('required_msg')}")


def _ask_int(prompt: str, default: int, min_val: int = 1, hint: str = "") -> int:
    while True:
        raw = _ask(prompt, default=default, hint=hint)
        try:
            v = int(raw)
            if v >= min_val:
                return v
            print(f"    ↳ {_t('min_val_msg', min_val=min_val)}")
        except ValueError:
            print(f"    ↳ {_t('invalid_int')}")


def _ask_bool(prompt: str, default: bool = False, hint: str = "") -> bool:
    hint_str = f"\n    ↳ {hint}" if hint else ""
    yes_lbl = _t("yes_label")
    no_lbl  = _t("no_label")
    def_lbl = yes_lbl if default else no_lbl
    while True:
        raw = input(f"  {prompt} [default={def_lbl}]{hint_str}\n  > ").strip().lower()
        if not raw:
            return default
        if raw in ("y", "yes", "是", "1"):
            return True
        if raw in ("n", "no", "否", "0"):
            return False
        print(f"    ↳ {_t('invalid_yn')}")


def _ask_time(prompt: str, default: str = "09:00") -> str:
    while True:
        raw = _ask(prompt, default=default)
        try:
            h, m = map(int, raw.split(":"))
            if 0 <= h <= 23 and 0 <= m <= 59:
                return f"{h:02d}:{m:02d}"
        except Exception:
            pass
        print(f"    ↳ {_t('invalid_time')}")


def _section(title: str) -> None:
    print(f"\n── {title} {'─' * max(0, 54 - len(title))}")


# ── Main wizard ───────────────────────────────────────────────────────────────

CONFIG_FILENAME = "config.json"


def run_wizard() -> None:
    global _LANG

    # ── Language selection (before any other output) ──────────────────────────
    print("\n" + "─" * 60)
    print("  TrustMeImWorking — Setup Wizard")
    print("─" * 60)
    print(_STRINGS["en"]["lang_opt_en"])
    print(_STRINGS["en"]["lang_opt_zh"])
    print()
    lang_raw = input("  Language / 语言  [default=1/en]\n  > ").strip().lower()
    if lang_raw in ("2", "zh", "中文", "chinese"):
        _LANG = "zh"
    else:
        _LANG = "en"

    print("\n" + "─" * 60)
    print(f"  {_t('wizard_title')}")
    print("─" * 60)
    print(f"  {_t('legend')}")
    print("─" * 60 + "\n")

    output = CONFIG_FILENAME

    # ── Step 1: Platform ──────────────────────────────────────────────────────
    _section(_t("step1_title"))
    platforms = list_platforms()
    print()
    for i, p in enumerate(platforms, 1):
        display = PLATFORM_DISPLAY_NAMES.get(p, p)
        print(f"  {i:2d}. {p:<16} {display}")
    print(f"  {'--':<3} {'custom':<16} {_t('custom_platform')}")
    print()

    raw_platform = _ask(
        _t("platform_prompt"),
        default="openai",
        hint=_t("platform_hint"),
    )
    try:
        idx = int(raw_platform) - 1
        platform = platforms[idx] if 0 <= idx < len(platforms) else raw_platform.lower()
    except ValueError:
        platform = raw_platform.lower()

    if platform not in PLATFORM_URLS and platform != "custom":
        print_warning(_t("unknown_platform", platform=platform))
        platform = "custom"

    # ── Step 2: API Key ───────────────────────────────────────────────────────
    _section(_t("step2_title"))
    api_key = _ask(
        _t("apikey_prompt"),
        required=True,
        hint=_t("apikey_hint"),
    )

    # ── Step 3: Base URL / Third-party relay ─────────────────────────────────
    _section(_t("step3_title"))
    base_url = None
    relay_help = _t("relay_help")

    if platform == "custom":
        print(_t("custom_url_required"))
        print(relay_help)
        base_url = _ask(
            _t("base_url_prompt"),
            required=True,
            hint=_t("base_url_hint"),
        )
    else:
        default_url = PLATFORM_URLS.get(platform, "")
        print(_t("default_url_label", platform=platform, url=default_url))
        override = _ask_bool(
            _t("override_prompt"),
            default=False,
            hint=_t("override_hint"),
        )
        if override:
            print(relay_help)
            base_url = _ask(
                _t("relay_url_prompt"),
                required=True,
                hint=_t("base_url_hint"),
            )

    # ── Step 4: Model ─────────────────────────────────────────────────────────
    _section(_t("step4_title"))
    default_model = PLATFORM_DEFAULT_MODELS.get(platform, "")
    if default_model:
        print(_t("model_recommended", model=default_model))
    model_raw = _ask(
        _t("model_prompt"),
        default=default_model or None,
        required=False,
        hint=_t("model_hint"),
    )
    model = model_raw if model_raw and model_raw != default_model else None

    # ── Step 5: Weekly Token Budget ───────────────────────────────────────────
    _section(_t("step5_title"))
    print(_t("budget_note"))
    print()
    weekly_min = _ask_int(
        _t("weekly_min_prompt"),
        default=50000,
        min_val=1000,
        hint=_t("weekly_min_hint"),
    )
    weekly_max = _ask_int(
        _t("weekly_max_prompt"),
        default=80000,
        min_val=weekly_min,
        hint=_t("weekly_max_hint"),
    )

    # ── Step 6: Run Mode ──────────────────────────────────────────────────────
    _section(_t("step6_title"))
    print(_t("mode_intro"))
    print(_t("mode_opt_immediate"))
    print(_t("mode_opt_spread"))
    print(_t("mode_opt_work"))

    mode_raw = _ask(
        _t("mode_prompt"),
        default="immediate",
        required=False,
        hint=_t("mode_hint"),
    ).strip().lower()

    if mode_raw in ("1", "immediate", "立刻", ""):
        mode = "immediate"
    elif mode_raw in ("2", "spread", "平均"):
        mode = "spread"
    elif mode_raw in ("3", "work", "工作模拟", "工作"):
        mode = "work"
    else:
        print(_t("mode_unknown"))
        mode = "immediate"

    simulate_work = (mode == "work")

    config = {
        "platform":      platform,
        "api_key":       api_key,
        "base_url":      base_url,
        "model":         model,
        "weekly_min":    weekly_min,
        "weekly_max":    weekly_max,
        "mode":          mode,
        "simulate_work": simulate_work,
    }

    # ── Step 7: Work Schedule / Timezone ─────────────────────────────────────
    if simulate_work:
        _section(_t("step7_work_title"))
        job_desc   = _ask(
            _t("job_desc_prompt"),
            required=True,
            hint=_t("job_desc_hint"),
        )
        work_start = _ask_time(_t("work_start_prompt"), default="09:00")
        work_end   = _ask_time(_t("work_end_prompt"),   default="18:00")
        local_tz   = str(datetime.datetime.now().astimezone().tzinfo)
        print(f"\n{_t('tz_detected', tz=local_tz)}")
        tz = _ask(
            _t("tz_prompt"),
            default="",
            required=False,
            hint=_t("tz_hint"),
        )
        config.update({
            "job_description": job_desc,
            "work_start":      work_start,
            "work_end":        work_end,
            "timezone":        tz,
        })
    else:
        _section(_t("step7_tz_title"))
        local_tz = str(datetime.datetime.now().astimezone().tzinfo)
        print(_t("tz_detected", tz=local_tz))
        tz = _ask(
            _t("tz_prompt"),
            default="",
            required=False,
            hint=_t("tz_hint"),
        )
        config["timezone"] = tz

    # ── Step 8: Enterprise / Gateway options ──────────────────────────────────
    _section(_t("step8_title"))
    print(_t("step8_skip"))

    want_gateway = _ask_bool(
        _t("gateway_prompt"),
        default=False,
        hint=_t("gateway_hint"),
    )

    if want_gateway:
        # Extra headers
        print()
        want_headers = _ask_bool(
            _t("headers_prompt"),
            default=False,
            hint=_t("headers_hint"),
        )
        extra_headers = {}
        if want_headers:
            print(_t("headers_enter"))
            while True:
                hname = input(_t("header_name_prompt")).strip()
                if not hname:
                    break
                hval = input(_t("header_val_prompt", name=hname)).strip()
                if hval:
                    extra_headers[hname] = hval
        config["extra_headers"] = extra_headers if extra_headers else None

        # HTTP proxy
        http_proxy = _ask(
            _t("proxy_prompt"),
            required=False,
            hint=_t("proxy_hint"),
        )
        config["http_proxy"] = http_proxy or None

        # mTLS
        want_mtls = _ask_bool(
            _t("mtls_prompt"),
            default=False,
            hint=_t("mtls_hint"),
        )
        if want_mtls:
            mtls_cert = _ask(_t("mtls_cert_prompt"), required=True,  hint=_t("mtls_cert_hint"))
            mtls_key  = _ask(_t("mtls_key_prompt"),  required=True,  hint=_t("mtls_key_hint"))
            mtls_ca   = _ask(_t("mtls_ca_prompt"),   required=False, hint=_t("mtls_ca_hint"))
            config["mtls_cert"] = mtls_cert
            config["mtls_key"]  = mtls_key
            config["mtls_ca"]   = mtls_ca or None
        else:
            config["mtls_cert"] = None
            config["mtls_key"]  = None
            config["mtls_ca"]   = None

        # Token field
        token_field = _ask(
            _t("token_field_prompt"),
            default="usage.total_tokens",
            required=False,
            hint=_t("token_field_hint"),
        )
        config["token_field"] = token_field or "usage.total_tokens"

        # JWT helper
        jwt_helper = _ask(
            _t("jwt_prompt"),
            required=False,
            hint=_t("jwt_hint"),
        )
        if jwt_helper:
            jwt_ttl = _ask_int(
                _t("jwt_ttl_prompt"),
                default=3600,
                min_val=60,
                hint=_t("jwt_ttl_hint"),
            )
            config["jwt_helper"]      = jwt_helper
            config["jwt_ttl_seconds"] = jwt_ttl
        else:
            config["jwt_helper"]      = None
            config["jwt_ttl_seconds"] = None
    else:
        config["extra_headers"]   = None
        config["http_proxy"]      = None
        config["mtls_cert"]       = None
        config["mtls_key"]        = None
        config["mtls_ca"]         = None
        config["token_field"]     = "usage.total_tokens"
        config["jwt_helper"]      = None
        config["jwt_ttl_seconds"] = None

    # ── Write config ──────────────────────────────────────────────────────────
    config["lang"] = _LANG  # persist language choice
    Path(output).write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")

    print("\n" + "─" * 60)
    print_success(_t("saved_to", path=output))
    print("─" * 60)

    # Detect which python command the user is running
    import subprocess as _sp
    _py = "python3"
    try:
        r = _sp.run(["python3", "--version"], capture_output=True, timeout=3)
        if r.returncode != 0:
            _py = "python"
    except Exception:
        _py = "python"

    from trustmework.i18n import t as _it
    _it_lang = _LANG  # already set above
    from trustmework import i18n as _i18n
    _i18n.set_lang(_LANG)

    print()
    print(f"  {_it('next_steps_title')}")
    print(_it("next_step_start", py=_py))
    print(_it("next_step_logs",  py=_py))
    print(_it("next_step_stop"))
    print()
