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

# Default flagship model for each platform (latest, highest-capability)
# Using the flagship model maximises token consumption per call, which is the goal.
PLATFORM_DEFAULT_MODELS: dict[str, str] = {
    "openai":      "gpt-4o",
    "claude":      "claude-opus-4-5",
    "anthropic":   "claude-opus-4-5",
    "gemini":      "gemini-2.5-pro",
    "kimi":        "moonshot-v1-128k",
    "moonshot":    "moonshot-v1-128k",
    "deepseek":    "deepseek-reasoner",
    "qwen":        "qwen-max",
    "tongyi":      "qwen-max",
    "zhipu":       "glm-4-plus",
    "glm":         "glm-4-plus",
    "baidu":       "ernie-4.5-turbo-128k",
    "ernie":       "ernie-4.5-turbo-128k",
    "spark":       "4.0Ultra",
    "iflytek":     "4.0Ultra",
    "minimax":     "abab6.5s-chat",
    "yi":          "yi-large",
    "lingyiwanwu": "yi-large",
    "stepfun":     "step-2-16k",
    "groq":        "llama-3.3-70b-versatile",
    "together":    "meta-llama/Llama-3.3-70B-Instruct-Turbo",
    "mistral":     "mistral-large-latest",
    "cohere":      "command-r-plus",
    "perplexity":  "llama-3.1-sonar-large-128k-online",
    "siliconflow": "deepseek-ai/DeepSeek-R1",
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
    """Get the default flagship model for a platform."""
    return PLATFORM_DEFAULT_MODELS.get(platform.lower(), "gpt-4o")


def list_platforms() -> list[str]:
    """Return sorted list of supported platform names."""
    return sorted(set(PLATFORM_URLS.keys()) - {"custom"})
