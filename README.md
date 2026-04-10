<div align="center">

# 🤫 TrustMeImWorking

**Simulate API token consumption to hit your KPI — the smart way.**

[![Python](https://img.shields.io/badge/python-3.10%2B-blue?logo=python)](https://python.org)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![Platforms](https://img.shields.io/badge/platforms-25%2B-orange)](#supported-platforms)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen)](CONTRIBUTING.md)

[English](#english) · [中文](#中文)

</div>

---

## English

### What is this?

Many companies measure employee productivity by **API token consumption**. TrustMeImWorking is a tool that automatically calls LLM APIs on a schedule to simulate realistic usage patterns — helping you hit your weekly KPI targets without manual effort.

Two modes are available:

| Mode | Description |
|------|-------------|
| **Random** | Spreads token usage evenly across the day using a built-in prompt pool |
| **Work Simulation** | Consumes tokens only during working hours, using AI-generated job-relevant prompts, with organic pacing that mimics real work rhythms |

### Features

- **25+ platforms** — OpenAI, Claude, Gemini, Kimi, DeepSeek, Qwen, Zhipu, ERNIE, Spark, and more
- **Enterprise gateway support** — custom headers, HTTP/SOCKS5 proxy, mTLS, JWT auto-refresh, configurable token field
- **Smart scheduling** — auto-detects crontab or falls back to a background daemon
- **Organic behavior** — random intervals, lunch/dinner breaks, weekday-only in work mode
- **Local tracking** — JSON state file records daily and weekly consumption
- **Beautiful CLI** — rich terminal output with progress bars and sparklines
- **Zero config friction** — interactive wizard or one-command template generation

### Quick Start

```bash
# 1. Clone and install
git clone https://github.com/pengtianhao48-lab/TrustMeImWorking
cd TrustMeImWorking
pip install -r requirements.txt

# 2. Run the interactive wizard
python tmw.py wizard

# OR generate a config template manually
python tmw.py init --config config.json --mode work

# 3. Test without calling the API
python tmw.py run --config config.json --dry-run

# 4. Install auto-scheduler (runs every 30 min during work hours)
python tmw.py scheduler --install --config config.json

# 5. Check your stats
python tmw.py status --config config.json
```

### Configuration

```jsonc
{
  "platform":        "deepseek",          // Platform name (see: python tmw.py platforms)
  "api_key":         "sk-...",            // Your API key
  "base_url":        null,                // Override URL for proxies (optional)
  "model":           null,                // null = use platform's cheapest model
  "weekly_min":      50000,               // Weekly token budget lower bound
  "weekly_max":      80000,               // Weekly token budget upper bound
  "simulate_work":   true,                // true = work-sim mode, false = random mode

  // Work-simulation mode only:
  "job_description": "Python backend engineer building microservices",
  "work_start":      "09:00",
  "work_end":        "18:00",
  "timezone":        "Asia/Shanghai"      // Leave empty for system timezone
}
```

> **How the budget works:** A random weekly target is chosen in `[weekly_min, weekly_max]`. Daily quota = weekly ÷ 7 (random) or ÷ 5 (work mode), with ±5% jitter each day.

### Supported Platforms

| Key | Service |
|-----|---------|
| `openai` | OpenAI (GPT series) |
| `claude` / `anthropic` | Anthropic Claude |
| `gemini` | Google Gemini |
| `kimi` / `moonshot` | Moonshot Kimi |
| `deepseek` | DeepSeek |
| `qwen` / `tongyi` | Alibaba Qwen |
| `zhipu` / `glm` | Zhipu AI |
| `baidu` / `ernie` | Baidu ERNIE |
| `spark` / `iflytek` | iFlytek Spark |
| `minimax` | MiniMax |
| `yi` / `lingyiwanwu` | 01.AI Yi |
| `stepfun` | StepFun |
| `siliconflow` | SiliconFlow |
| `groq` | Groq |
| `together` | Together AI |
| `mistral` | Mistral AI |
| `cohere` | Cohere |
| `perplexity` | Perplexity AI |
| `custom` | Any OpenAI-compatible endpoint |

### CLI Reference

```
tmw init       --config PATH [--mode random|work]   Generate config template
tmw wizard                                           Interactive setup
tmw run        --config PATH [--dry-run]             Run a session
tmw status     --config PATH                         Show stats
tmw scheduler  --install   --config PATH             Install auto-scheduler
tmw scheduler  --uninstall --config PATH             Remove scheduler
tmw scheduler  --status    [--config PATH]           Check scheduler status
tmw platforms                                        List all platforms
```

### Enterprise Gateway Support

Many companies route LLM traffic through an internal gateway (LiteLLM, One API, Kong, Azure APIM, or a custom proxy). TrustMeImWorking covers the following gateway scenarios:

| Scenario | Config field | Example |
|----------|-------------|----------|
| Extra auth headers required | `extra_headers` | `{"X-Team-ID": "eng", "X-Project": "ai"}` |
| Traffic must go through corporate HTTP proxy | `http_proxy` | `"http://proxy.corp.com:8080"` |
| Token count in non-standard response field | `token_field` | `"usage.prompt_tokens+usage.completion_tokens"` |
| Token count returned in response header | `token_field` | `"header:X-Tokens-Used"` |
| Short-lived JWT / rotating Bearer token | `jwt_helper` + `jwt_ttl_seconds` | `"vault kv get -field=key secret/llm"` |
| Mutual TLS client certificate required | `mtls_cert` + `mtls_key` | `"/etc/ssl/client.crt"` |
| Custom CA bundle for server verification | `mtls_ca` | `"/etc/ssl/corp-ca.pem"` |

**Gateway config example:**

```jsonc
{
  "platform":      "custom",
  "api_key":       "YOUR-GATEWAY-KEY",
  "base_url":      "https://ai-gateway.corp.com/v1",
  "model":         "gpt-4o-mini",
  "weekly_min":    50000,
  "weekly_max":    80000,

  // Extra headers your gateway requires
  "extra_headers": {
    "X-Team-ID":    "engineering",
    "X-Project-ID": "ai-productivity",
    "X-User-Email": "you@company.com"
  },

  // Route through corporate HTTP proxy
  "http_proxy":    "http://proxy.corp.com:8080",

  // Where to find token count in the response
  // Options: dot-path, dot+dot sum, or "header:Header-Name"
  "token_field":   "usage.total_tokens",

  // Dynamic JWT: run this command to get a fresh token
  "jwt_helper":    "vault kv get -field=api_key secret/llm/mykey",
  "jwt_ttl_seconds": 3600,

  // Mutual TLS
  "mtls_cert":     "/etc/ssl/client.crt",
  "mtls_key":      "/etc/ssl/client.key",
  "mtls_ca":       "/etc/ssl/corp-ca-bundle.pem"
}
```

> See [`examples/config_gateway.json`](examples/config_gateway.json), [`examples/config_proxy.json`](examples/config_proxy.json), and [`examples/config_jwt.json`](examples/config_jwt.json) for ready-to-use templates.

> **Not supported:** Claude Code / Codex CLI session traffic (those tools call the API themselves; token counting happens on the gateway side, not in this client).

### Work-Simulation Logic

```
Working hours: 09:00 ─────────────────────────── 18:00
                  │                                  │
               Morning    Lunch   Afternoon  Dinner  Evening
               [40%]      [skip]  [45%]      [skip]  [15%]
```

- Lunch and dinner times are **automatically inferred** from your work hours
- Prompts are **generated by the LLM itself** based on your job description
- Intervals between calls: **30–180 seconds** (random, mimics human typing)
- Only runs on **weekdays** (Mon–Fri)

---

## 中文

### 这是什么？

很多公司通过 **API Token 消耗量** 来评估员工的工作量。TrustMeImWorking 是一个自动化工具，按计划调用大模型 API，模拟真实的使用模式，帮助你轻松达成每周 KPI 目标。

提供两种运行模式：

| 模式 | 说明 |
|------|------|
| **随机模式** | 使用内置 prompt 库，将 token 消耗均匀分布在全天 |
| **模拟工作模式** | 仅在工作时段内消耗，使用 AI 根据你的工作描述生成真实工作 prompt，节奏自然，模拟真实工作行为 |

### 功能特点

- **25+ 平台支持** — OpenAI、Claude、Gemini、Kimi、DeepSeek、通义千问、智谱、文心、星火等
- **企业 Gateway 支持** — 自定义 Header、HTTP/SOCKS5 代理、mTLS 客户端证书、JWT 自动刷新、Token 字段可配置
- **智能调度** — 自动检测 crontab，不可用时回退到后台守护进程
- **拟人化行为** — 随机间隔、午饭晚饭时段跳过、工作模式仅工作日运行
- **本地记录** — JSON 文件记录每日和每周消耗量
- **美观终端** — rich 彩色输出，进度条和迷你图表
- **零配置门槛** — 交互式向导或一键生成配置模板

### 快速开始

```bash
# 1. 克隆并安装依赖
git clone https://github.com/pengtianhao48-lab/TrustMeImWorking
cd TrustMeImWorking
pip install -r requirements.txt

# 2. 运行交互式向导（推荐）
python tmw.py wizard

# 或者手动生成配置模板
python tmw.py init --config config.json --mode work

# 3. 测试运行（不实际调用 API）
python tmw.py run --config config.json --dry-run

# 4. 安装自动调度（工作时段每 30 分钟自动执行）
python tmw.py scheduler --install --config config.json

# 5. 查看消耗统计
python tmw.py status --config config.json
```

### 配置文件说明

```jsonc
{
  "platform":        "deepseek",          // 平台名称（运行 python tmw.py platforms 查看列表）
  "api_key":         "sk-...",            // 你的 API Key
  "base_url":        null,                // 自定义接口 URL，转接代理时填写（可留空）
  "model":           null,                // null = 使用平台默认最便宜的模型
  "weekly_min":      50000,               // 周消耗量下限（tokens）
  "weekly_max":      80000,               // 周消耗量上限（tokens）
  "simulate_work":   true,                // true = 模拟工作模式，false = 随机模式

  // 仅模拟工作模式需要：
  "job_description": "Python 后端工程师，负责微服务架构和 REST API 开发",
  "work_start":      "09:00",
  "work_end":        "18:00",
  "timezone":        "Asia/Shanghai"      // 留空使用系统时区
}
```

> **消耗逻辑：** 在 `[weekly_min, weekly_max]` 范围内随机选定周目标。每日配额 = 周目标 ÷ 7（随机模式）或 ÷ 5（工作模式），每天额外 ±5% 随机波动。

### 企业 Gateway 支持

很多公司会将 LLM 流量路由到内部 Gateway（LiteLLM、One API、Kong、Azure APIM 或自研代理）。TrustMeImWorking 覆盖以下 Gateway 场景：

| 场景 | 配置字段 | 示例 |
|------|---------|------|
| Gateway 需要额外鉴权 Header | `extra_headers` | `{"X-Team-ID": "eng"}` |
| 出口流量需走企业 HTTP 代理 | `http_proxy` | `"http://proxy.corp.com:8080"` |
| Token 数量在非标准响应字段 | `token_field` | `"usage.prompt_tokens+usage.completion_tokens"` |
| Token 数量在响应 Header 中 | `token_field` | `"header:X-Tokens-Used"` |
| 短期 JWT / 动态 Bearer Token | `jwt_helper` + `jwt_ttl_seconds` | `"vault kv get -field=key secret/llm"` |
| 需要 mTLS 客户端证书 | `mtls_cert` + `mtls_key` | `"/etc/ssl/client.crt"` |
| 自定义 CA 证书验证服务端 | `mtls_ca` | `"/etc/ssl/corp-ca.pem"` |

参考示例配置：[`examples/config_gateway.json`](examples/config_gateway.json)、[`examples/config_proxy.json`](examples/config_proxy.json)、[`examples/config_jwt.json`](examples/config_jwt.json)

> **不支持的场景：** Claude Code / Codex CLI 的会话流量（这两个工具自己调用 API，token 计量发生在 Gateway 侧，本工具无法介入）。

### 模拟工作模式逻辑

```
工作时间: 09:00 ─────────────────────────── 18:00
              │                                  │
           上午段    午饭    下午段    晚饭   傍晚段
           [40%]   [跳过]  [45%]   [跳过]  [15%]
```

- 午饭和晚饭时间根据上下班时间**自动推算**，无需手动配置
- Prompt 由大模型根据你的工作描述**自动生成**，贴近真实工作场景
- 每次调用间隔 **30~180 秒**随机，模拟人工操作节奏
- 仅**工作日**（周一至周五）运行

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). All PRs are welcome — new platform presets, prompt improvements, bug fixes.

## License

[MIT](LICENSE) © TrustMeImWorking Contributors

---

<div align="center">
<sub>Built with ❤️ for the overworked and under-appreciated.</sub>
</div>
