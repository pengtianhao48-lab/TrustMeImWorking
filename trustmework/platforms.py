"""
Platform presets for all major LLM providers.
Default models are verified against official documentation as of April 2026.
"""
from __future__ import annotations
from typing import Dict, List, Optional

# Base URLs for all supported platforms
PLATFORM_URLS: Dict[str, str] = {
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

# Default flagship model for each platform.
# All model IDs verified against official API documentation (April 2026).
# Using the flagship model maximises token consumption per call — which is the goal.
#
# Sources:
#   OpenAI:      https://developers.openai.com/api/docs/models  → gpt-5.4
#   Claude:      https://docs.anthropic.com/en/docs/about-claude/models/overview → claude-opus-4-6
#   Gemini:      https://ai.google.dev/gemini-api/docs/models  → gemini-3.1-pro-preview
#   Kimi:        https://platform.moonshot.cn/docs/api/chat    → kimi-k2.5
#   DeepSeek:    https://api-docs.deepseek.com/quick_start/pricing → deepseek-reasoner (DeepSeek-V3.2)
#   Qwen:        https://help.aliyun.com/zh/model-studio/models → qwen3-235b-a22b
#   Zhipu:       https://docs.bigmodel.cn/cn/guide/models/text/glm-5.1 → glm-5.1
#   Baidu ERNIE: https://ai.baidu.com/ai-doc/AISTUDIO/Mmhslv9lf → ernie-5.0-thinking-preview
#   Spark:       https://doc-en.302.ai/207705124e0 → 4.0Ultra
PLATFORM_DEFAULT_MODELS: Dict[str, str] = {
    # OpenAI — gpt-5.4 is the current flagship (April 2026)
    "openai":      "gpt-5.4",
    # Anthropic Claude — claude-opus-4-6 is the most intelligent broadly available model
    "claude":      "claude-opus-4-6",
    "anthropic":   "claude-opus-4-6",
    # Google Gemini — gemini-3.1-pro-preview is the latest frontier model
    "gemini":      "gemini-3.1-pro-preview",
    # Moonshot Kimi — kimi-k2.5 is the latest flagship with multimodal support
    "kimi":        "kimi-k2.5",
    "moonshot":    "kimi-k2.5",
    # DeepSeek — deepseek-reasoner maps to DeepSeek-V3.2 (thinking mode, highest capability)
    "deepseek":    "deepseek-reasoner",
    # Alibaba Qwen — qwen3-235b-a22b is the largest Qwen3 MoE flagship
    "qwen":        "qwen3-235b-a22b",
    "tongyi":      "qwen3-235b-a22b",
    # Zhipu AI — glm-5.1 is the latest flagship (April 2026), aligns with Claude Opus 4.6
    "zhipu":       "glm-5.1",
    "glm":         "glm-5.1",
    # Baidu ERNIE — ernie-5.0-thinking-preview is the latest flagship thinking model
    "baidu":       "ernie-5.0-thinking-preview",
    "ernie":       "ernie-5.0-thinking-preview",
    # iFlytek Spark — 4.0Ultra is the highest tier
    "spark":       "4.0Ultra",
    "iflytek":     "4.0Ultra",
    # MiniMax — abab6.5s-chat is the current flagship
    "minimax":     "abab6.5s-chat",
    # 01.AI Yi — yi-large is the flagship
    "yi":          "yi-large",
    "lingyiwanwu": "yi-large",
    # StepFun — step-2-16k is the flagship
    "stepfun":     "step-2-16k",
    # Groq — llama-3.3-70b-versatile is the largest available
    "groq":        "llama-3.3-70b-versatile",
    # Together AI — DeepSeek-R1 is the most capable available
    "together":    "deepseek-ai/DeepSeek-R1",
    # Mistral AI — mistral-large-latest always points to the latest large model
    "mistral":     "mistral-large-latest",
    # Cohere — command-r-plus is the flagship
    "cohere":      "command-r-plus",
    # Perplexity — sonar-pro is the flagship reasoning+search model
    "perplexity":  "sonar-pro",
    # SiliconFlow — DeepSeek-R1 is the most capable hosted model
    "siliconflow": "deepseek-ai/DeepSeek-R1",
}

# Human-readable display names
PLATFORM_DISPLAY_NAMES: Dict[str, str] = {
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


def get_base_url(platform: str, custom_url: Optional[str] = None) -> str:  # noqa
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
    return PLATFORM_DEFAULT_MODELS.get(platform.lower(), "gpt-5.4")


def list_platforms() -> List[str]:
    """Return sorted list of supported platform names."""
    return sorted(set(PLATFORM_URLS.keys()) - {"custom"})
