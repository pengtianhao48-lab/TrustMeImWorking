"""
Platform presets for all major LLM providers.
"""

# Base URLs for all supported platforms
PLATFORM_URLS: dict[str, str] = {
    "openai":      "https://api.openai.com/v1",
    "claude":      "https://api.anthropic.com/v1",
    "anthropic":   "https://api.anthropic.com/v1",
    "gemini":      "https://generativelanguage.googleapis.com/v1beta/openai",
    "kimi":        "https://api.moonshot.cn/v1",
    "moonshot":    "https://api.moonshot.cn/v1",
    "deepseek":    "https://api.deepseek.com/v1",
    "qwen":        "https://dashscope.aliyuncs.com/compatible-mode/v1",
    "tongyi":      "https://dashscope.aliyuncs.com/compatible-mode/v1",
    "zhipu":       "https://open.bigmodel.cn/api/paas/v4",
    "glm":         "https://open.bigmodel.cn/api/paas/v4",
    "baidu":       "https://qianfan.baidubce.com/v2",
    "ernie":       "https://qianfan.baidubce.com/v2",
    "spark":       "https://spark-api-open.xf-yun.com/v1",
    "iflytek":     "https://spark-api-open.xf-yun.com/v1",
    "minimax":     "https://api.minimax.chat/v1",
    "yi":          "https://api.lingyiwanwu.com/v1",
    "lingyiwanwu": "https://api.lingyiwanwu.com/v1",
    "stepfun":     "https://api.stepfun.com/v1",
    "groq":        "https://api.groq.com/openai/v1",
    "together":    "https://api.together.xyz/v1",
    "mistral":     "https://api.mistral.ai/v1",
    "cohere":      "https://api.cohere.com/v1",
    "perplexity":  "https://api.perplexity.ai",
    "siliconflow": "https://api.siliconflow.cn/v1",
    "custom":      None,
}

# Default cheapest/fastest model for each platform
PLATFORM_DEFAULT_MODELS: dict[str, str] = {
    "openai":      "gpt-4o-mini",
    "claude":      "claude-3-haiku-20240307",
    "anthropic":   "claude-3-haiku-20240307",
    "gemini":      "gemini-1.5-flash",
    "kimi":        "moonshot-v1-8k",
    "moonshot":    "moonshot-v1-8k",
    "deepseek":    "deepseek-chat",
    "qwen":        "qwen-turbo",
    "tongyi":      "qwen-turbo",
    "zhipu":       "glm-4-flash",
    "glm":         "glm-4-flash",
    "baidu":       "ernie-speed-128k",
    "ernie":       "ernie-speed-128k",
    "spark":       "lite",
    "iflytek":     "lite",
    "minimax":     "abab5.5s-chat",
    "yi":          "yi-lightning",
    "lingyiwanwu": "yi-lightning",
    "stepfun":     "step-1-flash",
    "groq":        "llama-3.1-8b-instant",
    "together":    "meta-llama/Llama-3-8b-chat-hf",
    "mistral":     "mistral-small-latest",
    "cohere":      "command-r",
    "perplexity":  "llama-3.1-sonar-small-128k-online",
    "siliconflow": "Qwen/Qwen2.5-7B-Instruct",
}

# Human-readable display names
PLATFORM_DISPLAY_NAMES: dict[str, str] = {
    "openai":      "OpenAI",
    "claude":      "Anthropic Claude",
    "anthropic":   "Anthropic Claude",
    "gemini":      "Google Gemini",
    "kimi":        "Moonshot Kimi",
    "moonshot":    "Moonshot Kimi",
    "deepseek":    "DeepSeek",
    "qwen":        "Alibaba Qwen (通义千问)",
    "tongyi":      "Alibaba Qwen (通义千问)",
    "zhipu":       "Zhipu AI (智谱)",
    "glm":         "Zhipu AI (智谱)",
    "baidu":       "Baidu ERNIE (文心一言)",
    "ernie":       "Baidu ERNIE (文心一言)",
    "spark":       "iFlytek Spark (讯飞星火)",
    "iflytek":     "iFlytek Spark (讯飞星火)",
    "minimax":     "MiniMax",
    "yi":          "01.AI Yi (零一万物)",
    "lingyiwanwu": "01.AI Yi (零一万物)",
    "stepfun":     "StepFun (阶跃星辰)",
    "groq":        "Groq",
    "together":    "Together AI",
    "mistral":     "Mistral AI",
    "cohere":      "Cohere",
    "perplexity":  "Perplexity AI",
    "siliconflow": "SiliconFlow (硅基流动)",
    "custom":      "Custom / Self-hosted",
}


def get_base_url(platform: str, custom_url: str | None = None) -> str:
    """Resolve the base URL for a given platform."""
    if custom_url:
        return custom_url
    url = PLATFORM_URLS.get(platform.lower())
    if url is None:
        raise ValueError(
            f"Unknown platform '{platform}'. "
            f"Use 'custom' and set base_url, or choose from: {list_platforms()}"
        )
    return url


def get_default_model(platform: str) -> str:
    """Get the default (cheapest) model for a platform."""
    return PLATFORM_DEFAULT_MODELS.get(platform.lower(), "gpt-4o-mini")


def list_platforms() -> list[str]:
    """Return sorted list of supported platform names."""
    return sorted(set(PLATFORM_URLS.keys()) - {"custom"})
