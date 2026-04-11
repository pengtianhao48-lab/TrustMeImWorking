<div align="center">

<h1>🤫 TrustMeImWorking</h1>

<p><strong>你的公司用 Token 消耗量考核你？<br>那就让 AI 替你"工作"吧。</strong></p>

<p><em>Your company measures productivity by API token usage?<br>Let the AI do the "work" for you.</em></p>

[![Python](https://img.shields.io/badge/python-3.8%2B-blue?logo=python&logoColor=white)](https://python.org)
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

**TrustMeImWorking** 是一个自动化脚本，在后台悄悄地帮你调用大模型 API，让你的 Token 消耗数据看起来像一个认真工作的人。配置一次，永续运行，自动开始和停止。

**三种运行模式：**

| 模式 | 适合谁 | 触发时机 |
|------|--------|---------|
| ⭐ **工作模拟**（推荐） | 想让数据看起来"真实可信" | 仅工作日工作时段，prompt 与职位高度相关，有午饭/晚饭时间 |
| ⚡ **立刻** | 想快速刷完今日配额 | 当日立刻开始；后续每天 00:00 开始，尽快消耗完 |
| 📅 **平均** | 想让消耗时间线看起来自然 | 将今日配额均匀分散到剩余时间，接近 23:59 时恰好消耗完 |

---

## 📦 安装（5 分钟搞定）

### 第一步：确认你有 Python

打开终端（Windows 用 PowerShell 或 CMD，Mac/Linux 用 Terminal），依次尝试以下命令，哪个有输出用哪个：

```bash
python --version
# 或者
python3 --version
```

如果任意一条显示 `Python 3.8.x` 或更高版本，继续下一步。  
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

## ⚡ 快速上手（3 条命令搞定）

```bash
python tmw.py wizard   # 第一步：交互式配置向导，自动生成 config.json
python tmw.py start    # 第二步：启动实时看板，开始自动消耗
python tmw.py logs     # 随时查看详细日志
```

> Mac/Linux 上如果 `python` 不可用，把所有 `python` 换成 `python3` 即可。

---

## 📋 详细说明

### 第一步：运行配置向导

```bash
python tmw.py wizard
```

向导会引导你完成以下配置（支持中文 / English 切换）：

1. **语言选择** — 中文或 English
2. **平台** — 从 25+ 预设平台中选择，或填自定义 URL
3. **API Key** — 你的平台 API Key（仅存本地，不上传）
4. **第三方转接 URL** — 可选，用于公司网关或国内镜像
5. **模型** — 留空自动使用旗舰模型（消耗 token 最多）
6. **每周 Token 预算** — 设置最小/最大范围，每日配额自动计算
7. **运行模式** — 立刻 / 平均 / ⭐ 工作模拟（推荐）
8. **工作时间设置**（工作模拟模式）— 职位描述、上下班时间、时区
9. **企业网关**（可选）— 自定义请求头、HTTP 代理、mTLS、JWT 认证

全部填完后自动生成 `config.json`（固定文件名，无需手动指定）。

### 第二步：启动实时看板

```bash
python tmw.py start
```

启动后会显示实时刷新的看板（每 2 秒更新）：

```
╭─────────────────────────────────────────────────────────────────────╮
│ TrustMeImWorking   平台：DeepSeek         模式：工作模拟             │
│                    运行时长：01m 23s       配置文件：config.json     │
╰─────────────────────────────────────────────────────────────────────╯
╭──────────────────────────── 消耗进度 ───────────────────────────────╮
│ 今日   ████████████████████████░░░░   12,345 / 14,000  (88%)        │
│ 本周   ███████████████████████░░░░░   67,890 / 50,000–80,000        │
╰─────────────────────────────────────────────────────────────────────╯
╭──────────────────────────── 请求进度 ───────────────────────────────╮
│ ● 进行中  本次请求：1,234 / 8,800  (14%)                            │
│ ███░░░░░░░░░░░░░░░░░░░░░░░░░                                        │
│ 今日进度：5,200 / 14,000  (37%)                                     │
│ ██████████░░░░░░░░░░░░░░░░░░                                        │
│ 请求内容：                                                          │
│ How does Kubernetes handle container orchestration and what are     │
│ the key differences between Deployments, StatefulSets, and          │
│ DaemonSets in production environments?                              │
╰─────────────────────────────────────────────────────────────────────╯
╭──────────────────────────── 近 7 天 ────────────────────────────────╮
│  04-05 12,100  04-06 0  04-07 0  04-08 13,400  04-09 0  04-10 0    │
│  04-11 12,345                                                       │
╰─────────────────────────────────────────────────────────────────────╯
╭──────────────────────────── 最近日志 ───────────────────────────────╮
│ [10:32:05]   [2] +550 tk  session_total=1,104/8,800  today=5,200    │
│ [10:32:05]   [2] Prompt: What are the SOLID principles in...        │
│ [10:31:47]   ✔ response  elapsed=16.81s  prompt_tk=38  total_tk=554 │
│ [10:31:47]   [1] +554 tk  session_total=554/8,800  today=4,650      │
╰─────────────────────────────────────────────────────────────────────╯
  按 Ctrl+C 停止   │   python tmw.py logs  查看完整日志
```

**今日完成后**，Session 区域自动变为绿色，显示下次启动时间：

```
╭──────────────────────────── 请求进度 ───────────────────────────────╮
│ ✓ 今日配额已完成！  今日进度：14,000 / 14,000  (100%)               │
│ ████████████████████████████                                        │
│ 下次启动时间：8 小时 30 分后  (04-12 00:00)                         │
╰─────────────────────────────────────────────────────────────────────╯
```

按 **Ctrl+C** 停止看板（同时停止消耗进程）。  
如果想后台静默运行，加 `-b` 参数：

```bash
python tmw.py start -b   # 后台运行，日志写入 config.log
python tmw.py stop       # 停止后台进程
```

### 查看日志

```bash
python tmw.py logs          # 最近 50 行
python tmw.py logs -n 200   # 最近 200 行
```

日志包含每次 API 调用的完整信息：

```
[10:31:47]   [1] Prompt: How does Kubernetes handle container orchestration...
[10:32:04]   ✔ response  elapsed=17.23s  prompt_tk=42  completion_tk=512  total_tk=554
[10:32:04]   └ reply: Kubernetes handles container orchestration by abstracting...
[10:32:04]   [1] +554 tk  session_total=554/8,800  today=4,650
[10:32:04]   Sleeping 86s…
```

---

## ⭐ 工作模拟模式：它有多"像真的"？

工作模拟模式是本工具最核心的功能，也是最推荐的使用方式。

**触发逻辑：**
- 只在**工作日**（周一至周五）运行
- 只在你设定的**工作时段**内触发（如 09:00–18:00）
- 自动跳过午饭和晚饭时间段
- 时间权重分布：上午 40%、下午 45%、傍晚 15%

**Prompt 生成策略：**

工具会根据你填写的职位描述，实时调用 AI 生成高度相关的工作场景 prompt，每次都不一样。

以**后端工程师**为例，生成的 prompt 长这样：

```
I'm seeing that this endpoint in `src/api/users.py` occasionally hangs and
times out when fetching users with lots of associated posts. I suspect it's
caused by the nested queries. Here's the relevant code:

    @router.get("/users/{user_id}")
    def get_user(user_id: int, db: Session = Depends(get_db)):
        user = db.query(User).filter(User.id == user_id).first()
        posts = db.query(Post).filter(Post.user_id == user_id).all()
        return {"user": user, "posts": posts}  # N+1 query issue

How do I fix this with SQLAlchemy eager loading to avoid the N+1 problem?
```

**非工程师角色**（产品经理、设计师、分析师等）生成与工作高度相关的问题式 prompt：

```
What are the emerging trends in our industry that could impact our product roadmap?
Draft a concise update email for the sales team summarizing key product improvements.
Generate a prioritized list of customer feedback themes from our recent NPS survey.
```

**时间分布示意：**

```
09:00 ──────────────────────────────────────── 18:00
  │  上午 40%  │ 午饭 │  下午 45%  │ 晚饭 │ 傍晚 15% │
  └────────────┴──────┴────────────┴──────┴──────────┘
  午饭、晚饭时间根据你的上下班时间自动推算，无需手动设置
```

**下次启动时间预测（工作模拟模式）：**

| 当前时间 | Session 区域显示 |
|---------|----------------|
| 工作日工作时段内 | 正常消耗，显示进度 |
| 工作日下班后（如 19:07） | `14 小时 53 分后发起下次请求  (04-12 09:00)` |
| 周末 | `1 天 13 小时后发起下次请求  (04-14 09:00)` |
| 周五下班后 | `2 天 13 小时后发起下次请求  (04-14 09:00)` |

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

> **小贴士：** 默认会使用各平台最新旗舰模型，每次调用 token 消耗更大，更容易达标。如果想控制费用，可以在 wizard 中手动指定较便宜的模型。

---

## 🏢 公司用自己的 Gateway？

很多公司不用官方 API，而是自己搭了一个内部 Gateway（统一管理 API Key、记录用量）。wizard 的第 3 步和第 8 步支持完整配置：

- **自定义 Base URL**（第 3 步）— 填写公司网关地址，如 `https://ai-gateway.corp.com/v1`
- **自定义请求头**（第 8 步）— 如 `X-Team-ID`、`X-Project-ID`
- **HTTP/HTTPS/SOCKS5 代理** — 如 `http://proxy.corp.com:8080`
- **mTLS 双向认证** — 客户端证书 + 私钥 + CA bundle
- **自定义 token 字段路径** — 默认 `usage.total_tokens`
- **JWT 动态令牌** — shell 命令 + TTL 秒数

---

## 🌐 支持的平台

```bash
python tmw.py platforms
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
python tmw.py wizard          # 交互式配置向导（支持中文/English）
python tmw.py start           # 启动实时看板（前台，Ctrl+C 停止）
python tmw.py start -b        # 后台静默运行
python tmw.py stop            # 停止后台进程
python tmw.py logs            # 查看最近 50 行日志
python tmw.py logs -n 200     # 查看最近 200 行日志
python tmw.py run             # 手动触发一次消耗
python tmw.py run --dry-run   # 测试运行（不调用 API）
python tmw.py status          # 消耗统计 + 进程状态
python tmw.py platforms       # 列出所有支持的平台
```

所有命令默认读取当前目录的 `config.json`，无需每次加 `--config`。  
如果你有多个配置文件，可以用 `--config other.json` 显式指定。

---

## ❓ 常见问题

**Q: 会不会被发现？**  
A: 工具本身只是正常调用 API，和你手动问问题没有区别。工作模拟模式下，prompt 内容和你的工作高度相关，时间分布也符合正常工作节奏。

**Q: 会花很多钱吗？**  
A: 取决于你设置的 token 量和选择的模型。用 DeepSeek 这类便宜模型，每周 10 万 tokens 大约花 1~3 元。

**Q: 公司用 Claude Code / Codex 统计，能用吗？**  
A: 不能。这两个工具是客户端，token 计量发生在公司 gateway 侧，本工具无法介入。本工具适用于"公司给你一个 API Key，统计这个 Key 的消耗量"的场景。

**Q: 配置文件里的 API Key 安全吗？**  
A: 配置文件存在你本地，不会上传到任何地方。建议不要把配置文件提交到 git 仓库（`.gitignore` 已默认忽略 `config*.json`）。

**Q: 支持 Windows 吗？**  
A: 支持。Windows 下使用后台守护进程模式（`start -b`），日志写入 `config.log`。

**Q: 支持哪些 Python 版本？**  
A: Python 3.8 及以上均支持（3.8 / 3.9 / 3.10 / 3.11 / 3.12 均通过 CI 测试）。

---

## 🤝 贡献

欢迎提 PR！常见的贡献方向：
- 新增平台预设（在 `trustmework/platforms.py` 里加几行）
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

Many companies measure employee productivity by **API token consumption**. TrustMeImWorking automatically calls LLM APIs on a schedule to simulate realistic usage patterns — helping you hit your weekly KPI targets without lifting a finger. Configure once, runs forever, starts and stops automatically.

### Three Modes

| Mode | Best for | Trigger |
|------|----------|---------|
| ⭐ **Work Simulation** (recommended) | Want data that looks genuinely human | Weekdays only, during work hours; uses AI-generated job-relevant prompts; respects lunch/dinner breaks |
| ⚡ **Immediate** | Just need to hit the number fast | Starts right now (today); every subsequent day at 00:00 |
| 📅 **Spread** | Want usage spread naturally across the day | Distributes today's quota evenly across remaining hours; reaches target near midnight |

### Installation

```bash
# Requires Python 3.8+
git clone https://github.com/pengtianhao48-lab/TrustMeImWorking.git
cd TrustMeImWorking
pip install -r requirements.txt   # or: pip3 install -r requirements.txt
```

### Quick Start

```bash
python tmw.py wizard   # Interactive setup wizard (EN / 中文)
python tmw.py start    # Start live dashboard + consumption loop
python tmw.py logs     # View detailed logs
```

> Replace `python` with `python3` if needed on your system.

### Commands

```bash
python tmw.py wizard          # Interactive setup wizard
python tmw.py start           # Start foreground live dashboard (Ctrl+C to stop)
python tmw.py start -b        # Start background daemon
python tmw.py stop            # Stop background daemon
python tmw.py logs            # Last 50 log lines
python tmw.py logs -n 200     # Last 200 log lines
python tmw.py run             # Trigger one consumption session manually
python tmw.py run --dry-run   # Dry run (no API calls)
python tmw.py status          # Consumption stats + daemon status
python tmw.py platforms       # List all supported platforms
```

### Work Simulation Schedule

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

### Enterprise Gateway

Run the wizard and configure in Step 3 (custom URL) and Step 8 (gateway options):

- Custom Base URL (e.g. `https://ai-gateway.corp.com/v1`)
- Custom HTTP headers (e.g. `X-Team-ID`, `X-Project-ID`)
- HTTP/HTTPS/SOCKS5 proxy
- mTLS client certificate authentication
- Custom token field path (default: `usage.total_tokens`)
- JWT dynamic token via shell command

> **Not supported:** Claude Code / Codex CLI session traffic — those tools call the API themselves; token counting happens on the gateway side.

---

<div align="center">
<sub>Built with ❤️ for the overworked and under-appreciated.<br>
<i>"I'm not slacking. I'm load testing the API."</i></sub>
</div>
