"""LLM Provider 配置."""

from typing import Dict, Optional

# 预置常见 OpenAI 兼容厂商配置
PROVIDER_PRESETS: Dict[str, Dict[str, str]] = {
    "openai": {
        "base_url": "https://api.openai.com/v1",
        "model": "gpt-3.5-turbo",
    },
    "deepseek": {
        "base_url": "https://api.deepseek.com/v1",
        "model": "deepseek-chat",
    },
    "kimi": {
        "base_url": "https://api.moonshot.cn/v1",
        "model": "moonshot-v1-8k",
    },
    "qwen": {
        "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
        "model": "qwen-turbo",
    },
    "minimax": {
        "base_url": "https://api.minimax.chat/v1",
        "model": "abab6.5s-chat",
    },
}

EMBEDDING_PRESETS: Dict[str, Dict[str, str]] = {
    "openai": {
        "base_url": "https://api.openai.com/v1",
        "model": "text-embedding-3-small",
    },
}


def get_llm_preset(provider: str) -> Optional[Dict[str, str]]:
    return PROVIDER_PRESETS.get(provider.lower())


def get_embedding_preset(provider: str) -> Optional[Dict[str, str]]:
    return EMBEDDING_PRESETS.get(provider.lower())
