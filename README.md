<div align="center">

<h1>🤫 TrustMeImWorking</h1>

<p><strong>你的公司用 Token 消耗量考核你？<br>那就让 AI 替你"工作"吧。</strong></p>

<p><em>Your company measures productivity by API token usage?<br>Let the AI do the "work" for you.</em></p>

[![Python](https://img.shields.io/badge/python-3.10%2B-blue?logo=python&logoColor=white)](https://python.org)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![Platforms](https://img.shields.io/badge/platforms-25%2B-orange)](#-支持的平台)
[![CI](https://github.com/pengtianhao48-lab/TrustMeImWorking/actions/workflows/ci.yml/badge.svg)](https://github.com/pengtianhao48-lab/TrustMeImWorking/actions)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen)](CONTRIBUTING.md)

[中文](#-中文文档) · [English](#-english-docs)

</div>

---

## 😤 背景故事

> 某天，你的 leader 在周会上说：  
> **"下周开始，大家的 AI 工具使用量要达到 X 万 tokens，这是 KPI 的一部分。"**
>
> 你心想：我每天都在用，但我怎么知道我用了多少？  
> 然后你打开后台一看——  
> **你这周：3,200 tokens。**  
> **同事小王：287,000 tokens。**
>
> 你：？？？

这个工具就是为这种情况而生的。

---

## 🚀 它能做什么

**TrustMeImWorking** 是一个自动化脚本，它会在后台悄悄地帮你调用大模型 API，让你的 Token 消耗数据看起来像一个认真工作的人。

两种模式，任你选择：

| 模式 | 适合谁 | 效果 |
|------|--------|------|
| 🎲 **随机模式** | 只想完成 KPI，不在乎细节 | 全天均匀消耗，问一些随机问题 |
| 💼 **模拟工作模式** | 想让数据看起来"真实可信" | 只在工作时间消耗，问的问题和你的工作高度相关，有午饭晚饭时间，只有工作日才运行 |

---

## 📦 安装（5 分钟搞定）

### 第一步：确认你有 Python

打开终端（Windows 用 PowerShell 或 CMD，Mac/Linux 用 Terminal），依次尝试以下命令，哪个有输出用哪个：

```bash
python --version
# 或者
python3 --version
```

如果任意一条显示 `Python 3.10.x` 或更高版本，继续下一步。  
如果两条都提示"找不到命令"，先去 [python.org](https://www.python.org/downloads/) 下载安装 Python（安装时勾选 **Add to PATH**）。

> **记住你用的是 `python` 还是 `python3`**，后续所有命令都用同一个。

### 第二步：下载项目

```bash
git clone https://github.com/pengtianhao48-lab/TrustMeImWorking.git
cd TrustMeImWorking
```

> 没有 git？去 [git-scm.com](https://git-scm.com) 下载，或者直接点页面右上角的 **Code → Download ZIP** 解压也行。

### 第三步：安装依赖

```bash
pip install -r requirements.txt
# 如果上面报错，试这个：
pip3 install -r requirements.txt
```

看到一堆 `Successfully installed ...` 就说明成功了。

---

## ⚡ 快速上手

### 方式一：交互式向导（推荐新手）

```bash
python tmw.py wizard
# 或者（Mac/Linux 有时需要）
python3 tmw.py wizard
```

它会一步一步问你：用哪个平台、API Key 是多少、每周要消耗多少 tokens……  
跟着填就行，最后自动生成配置文件。

### 方式二：手动配置（推荐老手）

**第一步：生成配置模板**

```bash
# 随机模式
python tmw.py init --config my_config.json --mode random

# 模拟工作模式
python tmw.py init --config my_config.json --mode work

# Mac/Linux 如果 python 不可用，把上面所有 python 换成 python3
```

**第二步：编辑配置文件**

用任意文本编辑器打开 `my_config.json`，填入你的信息：

```jsonc
{
  "platform":   "deepseek",     // 平台名，见下方支持列表
  "api_key":    "sk-xxxxxxxx",  // 你的 API Key（必填）
  "model":      null,           // 留 null 自动选最便宜的模型
  "weekly_min": 50000,          // 每周消耗下限（tokens）
  "weekly_max": 80000,          // 每周消耗上限（tokens）
  "simulate_work": true,        // true=模拟工作，false=随机模式

  // 模拟工作模式才需要填以下字段：
  "job_description": "产品经理，负责需求分析和竞品调研",
  "work_start": "09:30",
  "work_end":   "18:30",
  "timezone":   "Asia/Shanghai"
}
```

**第三步：先 dry-run 测试一下**

```bash
python tmw.py run --config my_config.json --dry-run
```

加了 `--dry-run` 不会真的调用 API，只是告诉你"如果运行，会发生什么"。  
确认逻辑没问题后，去掉 `--dry-run` 正式运行：

```bash
python tmw.py run --config my_config.json
```

> **提示：** 如果你的电脑只有 `python3` 命令，把所有 `python tmw.py` 替换成 `python3 tmw.py` 即可，功能完全一样。

**第四步：设置自动运行（最重要！）**

手动跑一次没意义，要让它每天自动跑才行：

```bash
python tmw.py scheduler --install --config my_config.json
# 或
python3 tmw.py scheduler --install --config my_config.json
```

这会自动设置定时任务，每 30 分钟检查一次，在合适的时间自动消耗 tokens。  
**设置完就不用管了，它会在后台默默工作。**

**第五步：查看消耗统计**

```bash
python tmw.py status --config my_config.json
```

---

## 🔑 去哪里获取 API Key？

| 平台 | 获取地址 | 备注 |
|------|----------|------|
| DeepSeek | [platform.deepseek.com](https://platform.deepseek.com) | 最便宜，强烈推荐 |
| Kimi | [platform.moonshot.cn](https://platform.moonshot.cn) | 国内访问流畅 |
| 通义千问 | [dashscope.aliyun.com](https://dashscope.aliyun.com) | 阿里云，稳定 |
| 智谱 AI | [open.bigmodel.cn](https://open.bigmodel.cn) | 有免费额度 |
| OpenAI | [platform.openai.com](https://platform.openai.com) | 需要梯子 |
| Claude | [console.anthropic.com](https://console.anthropic.com) | 需要梯子 |

> **小贴士：** 模拟消耗时建议选便宜的模型（如 DeepSeek、Kimi），每次调用花费不到 0.01 元，一周下来几块钱搞定。

---

## 🏢 公司用自己的 Gateway？

很多公司不用官方 API，而是自己搭了一个内部 Gateway（统一管理 API Key、记录用量）。这种情况完全支持：

```jsonc
{
  "platform":   "custom",
  "api_key":    "公司给你的内部 Key",
  "base_url":   "https://ai-gateway.yourcompany.com/v1",  // 公司 gateway 地址
  "model":      "gpt-4o-mini",  // 公司 gateway 里的模型名

  // 如果 gateway 要求额外的 Header（问你们的运维）
  "extra_headers": {
    "X-Team-ID":    "your-team",
    "X-Project-ID": "your-project"
  },

  // 如果需要走公司代理
  "http_proxy": "http://proxy.yourcompany.com:8080",

  "weekly_min": 50000,
  "weekly_max": 80000,
  "simulate_work": false
}
```

更多高级配置（mTLS、JWT 动态 Token 等）见 [`examples/`](examples/) 目录。

---

## 💼 模拟工作模式：它有多"像真的"？

以一个后端工程师（09:00~19:00）为例，实际运行时生成的 prompt 长这样：

```
✓ How can I optimize a SQL query in PostgreSQL to reduce latency for fetching large datasets?
✓ What is the best way to implement JWT authentication with token expiration and refresh?
✓ How do I set up SQLAlchemy connection pooling in my FastAPI application?
✓ Can you help me write a Pydantic model schema that validates nested JSON input?
✓ What are common debugging techniques to identify slow API response times?
```

这些 prompt 是**由 AI 根据你的工作描述实时生成的**，每次都不一样，不是固定模板。  
时间分布如下：

```
09:00 ──────────────────────────────────────── 19:00
  │  上午 40%  │ 午饭 │  下午 45%  │ 晚饭 │ 傍晚 15% │
  └────────────┴──────┴────────────┴──────┴──────────┘
  午饭、晚饭时间根据你的上下班时间自动推算，无需手动设置
```

---

## 🌐 支持的平台

```b```bash
python tmw.py platforms   # or: python3 tmw.py platforms
```
```

| 平台 Key | 服务 | 平台 Key | 服务 |
|----------|------|----------|------|
| `openai` | OpenAI GPT 系列 | `deepseek` | DeepSeek |
| `claude` | Anthropic Claude | `qwen` / `tongyi` | 阿里通义千问 |
| `gemini` | Google Gemini | `zhipu` / `glm` | 智谱 AI |
| `kimi` / `moonshot` | Moonshot Kimi | `baidu` / `ernie` | 百度文心 |
| `spark` / `iflytek` | 讯飞星火 | `minimax` | MiniMax |
| `yi` | 零一万物 | `stepfun` | 阶跃星辰 |
| `siliconflow` | 硅基流动 | `groq` | Groq |
| `mistral` | Mistral AI | `cohere` | Cohere |
| `together` | Together AI | `perplexity` | Perplexity |
| `custom` | 任意 OpenAI 兼容接口 | — | — |

---

## 📊 命令速查

```bash
# 如果你的系统只有 python3，把下面所有 python 替换成 python3
python tmw.py wizard                                    # 交互式配置向导
python tmw.py init   --config cfg.json --mode work     # 生成配置模板
python tmw.py run    --config cfg.json                 # 运行一次
python tmw.py run    --config cfg.json --dry-run       # 测试运行（不调用 API）
python tmw.py status --config cfg.json                 # 查看统计
python tmw.py scheduler --install   --config cfg.json  # 安装自动调度
python tmw.py scheduler --uninstall --config cfg.json  # 卸载自动调度
python tmw.py scheduler --status                       # 查看调度状态
python tmw.py platforms                                # 列出所有支持的平台
```

---

## ❓ 常见问题

**Q: 会不会被发现？**  
A: 工具本身只是正常调用 API，和你手动问问题没有区别。模拟工作模式下，prompt 内容和你的工作高度相关，时间分布也符合正常工作节奏。

**Q: 会花很多钱吗？**  
A: 取决于你设置的 token 量和选择的模型。用 DeepSeek 或 Kimi 这类便宜模型，每周 10 万 tokens 大约花 1~3 元。

**Q: 公司用 Claude Code / Codex 统计，能用吗？**  
A: 不能。这两个工具是客户端，token 计量发生在公司 gateway 侧，本工具无法介入。本工具适用于"公司给你一个 API Key，统计这个 Key 的消耗量"的场景。

**Q: 配置文件里的 API Key 安全吗？**  
A: 配置文件存在你本地，不会上传到任何地方。建议不要把配置文件提交到 git 仓库（`.gitignore` 已默认忽略 `config*.json`）。

**Q: 支持 Windows 吗？**  
A: 支持。Windows 下自动调度会使用后台守护进程而非 crontab。

---

## 🤝 贡献

欢迎提 PR！常见的贡献方向：
- 新增平台预设（在 `trustmework/platforms.py` 里加几行）
- 扩充 prompt 库（在 `trustmework/engine.py` 的 `RANDOM_PROMPTS` 里加）
- Bug 修复和文档改进

详见 [CONTRIBUTING.md](CONTRIBUTING.md)。

---

## 📄 许可证

[MIT](LICENSE) — 随便用，但出了事我不负责。

---

<div align="center">

---

## 🇺🇸 English Docs

</div>

### What is this?

Many companies measure employee productivity by **API token consumption**. TrustMeImWorking automatically calls LLM APIs on a schedule to simulate realistic usage patterns — helping you hit your weekly KPI targets without lifting a finger.

### Two Modes

| Mode | Best for | Behavior |
|------|----------|----------|
| 🎲 **Random** | Just need to hit the number | Spreads usage evenly across the day with a built-in prompt pool |
| 💼 **Work Simulation** | Want data that looks genuinely human | Only runs during work hours, uses AI-generated job-relevant prompts, respects lunch/dinner breaks, weekdays only |

### Installation

```bash
# Requires Python 3.10+
git clone https://github.com/pengtianhao48-lab/TrustMeImWorking.git
cd TrustMeImWorking
pip install -r requirements.txt   # or: pip3 install -r requirements.txt
```

### Quick Start

```bash
# If only python3 is available on your system, replace python with python3
python tmw.py wizard                                         # Interactive setup wizard
python tmw.py init --config config.json --mode work          # Generate config template
python tmw.py run  --config config.json --dry-run            # Test (no API calls)
python tmw.py scheduler --install --config config.json       # Install auto-scheduler
python tmw.py status --config config.json                    # Check stats
```

### Config File

```jsonc
{
  "platform":        "deepseek",   // Run: python tmw.py platforms
  "api_key":         "sk-...",     // Your API key
  "base_url":        null,         // Override for corporate gateways
  "model":           null,         // null = cheapest model for the platform
  "weekly_min":      50000,        // Weekly token budget lower bound
  "weekly_max":      80000,        // Weekly token budget upper bound
  "simulate_work":   true,         // true = work-sim, false = random

  // Work-sim mode only:
  "job_description": "Python backend engineer building microservices with FastAPI",
  "work_start":      "09:00",
  "work_end":        "18:00",
  "timezone":        "Asia/Shanghai"
}
```

### Enterprise Gateway

Point `base_url` at your internal gateway and add any required headers:

```jsonc
{
  "platform":      "custom",
  "api_key":       "your-internal-key",
  "base_url":      "https://ai-gateway.corp.com/v1",
  "extra_headers": { "X-Team-ID": "eng", "X-Project-ID": "ai-kpi" },
  "http_proxy":    "http://proxy.corp.com:8080",
  "token_field":   "usage.total_tokens",
  "jwt_helper":    "vault kv get -field=key secret/llm/mykey",
  "mtls_cert":     "/etc/ssl/client.crt",
  "mtls_key":      "/etc/ssl/client.key"
}
```

See [`examples/`](examples/) for ready-to-use templates.

> **Not supported:** Claude Code / Codex CLI session traffic — those tools call the API themselves; token counting happens on the gateway side.

### Work-Simulation Schedule

```
Work hours: 09:00 ──────────────────────────── 18:00
                │                                  │
             Morning   Lunch   Afternoon  Dinner  Evening
             [40%]    [skip]   [45%]     [skip]   [15%]

Lunch & dinner times are auto-inferred from your work_start/work_end.
Prompts are generated by the LLM based on your job_description.
Call intervals: 30–180 seconds (randomized).
Only runs on weekdays (Mon–Fri).
```

---

<div align="center">
<sub>Built with ❤️ for the overworked and under-appreciated.<br>
<i>"I'm not slacking. I'm load testing the API."</i></sub>
</div>
