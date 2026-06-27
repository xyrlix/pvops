"""LLM / Embeddings 工厂.

向后兼容层：
- ``get_chat_llm()`` 返回 ``LLMClient`` 实例（保留原接口）
- ``get_embeddings()`` 返回 ``EmbeddingClient`` 实例

``LLMClient`` 内部委托给当前选中的 Provider；Provider 由
``app.llm.providers.registry`` 解析。新增非 OpenAI 兼容协议供应商
（Anthropic / Cohere / 本地）只需新增 provider 并在注册表注册，
本文件无需修改。
"""

from __future__ import annotations

import logging
from typing import Dict, List, Optional

from app.core.config import get_settings
from app.llm.config import get_embedding_preset, get_llm_preset
from app.llm.providers.registry import (
    get_chat_factory,
    get_embed_factory,
)

logger = logging.getLogger(__name__)


class LLMClient:
    """统一的聊天客户端门面，委托给具体 provider."""

    def __init__(
        self,
        provider_name: str,
        provider,  # LLMProvider 实例
        api_key: str,
        base_url: str,
        model: str,
    ) -> None:
        self.provider_name = provider_name
        self.provider = provider
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.model = model

    async def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.2,
        timeout: float = 60.0,
    ) -> str:
        return await self.provider.chat(messages, temperature=temperature, timeout=timeout)


class EmbeddingClient:
    """统一的 embedding 门面."""

    def __init__(
        self,
        provider_name: str,
        provider,  # EmbeddingProvider 实例
        api_key: str,
        base_url: str,
        model: str,
    ) -> None:
        self.provider_name = provider_name
        self.provider = provider
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.model = model

    async def embed(self, texts: List[str], timeout: float = 60.0) -> Optional[List[List[float]]]:
        return await self.provider.embed(texts, timeout=timeout)


def _merge_preset(
    provider: str,
    api_key: str,
    base_url: str,
    model: str,
    preset: Optional[Dict[str, str]],
) -> Dict[str, str]:
    """合并用户配置与预置默认值."""
    if preset:
        return {
            "provider": provider,
            "api_key": api_key,
            "base_url": base_url or preset.get("base_url", ""),
            "model": model or preset.get("model", ""),
        }
    return {
        "provider": provider,
        "api_key": api_key,
        "base_url": base_url,
        "model": model,
    }


def get_chat_llm() -> Optional[LLMClient]:
    """获取聊天 LLM 客户端.

    通过 ``providers.registry`` 查找注册工厂；找不到时返回 None 并打 WARNING。
    """
    settings = get_settings()
    provider = (settings.llm_provider or "openai").lower()
    preset = get_llm_preset(provider)
    api_key = settings.llm_api_key

    if not api_key:
        logger.warning("LLM_API_KEY 未配置，聊天功能不可用")
        return None

    kwargs = _merge_preset(
        provider,
        api_key,
        settings.llm_base_url,
        settings.llm_model,
        preset,
    )

    if not kwargs["base_url"] or not kwargs["model"]:
        logger.warning(f"LLM provider {provider} 缺少 base_url 或 model 配置")
        return None

    factory = get_chat_factory(provider)
    if factory is None:
        logger.warning(f"未注册的 LLM provider: {provider}（可用：{get_chat_factory.__name__}）")
        return None

    provider_inst = factory(provider, api_key, kwargs["base_url"], kwargs["model"])
    return LLMClient(
        provider_name=provider,
        provider=provider_inst,
        api_key=api_key,
        base_url=kwargs["base_url"],
        model=kwargs["model"],
    )


def get_embeddings() -> Optional[EmbeddingClient]:
    """获取 Embedding 客户端."""
    settings = get_settings()
    provider = (settings.embedding_provider or settings.llm_provider or "openai").lower()
    preset = get_embedding_preset(provider)
    api_key = settings.embedding_api_key or settings.llm_api_key

    if not api_key:
        logger.warning("EMBEDDING_API_KEY / LLM_API_KEY 未配置，Embedding 不可用")
        return None

    kwargs = _merge_preset(
        provider,
        api_key,
        settings.embedding_base_url,
        settings.embedding_model,
        preset,
    )
    if not kwargs["base_url"] or not kwargs["model"]:
        logger.warning(f"Embedding provider {provider} 缺少 base_url 或 model 配置")
        return None

    factory = get_embed_factory(provider)
    if factory is None:
        logger.warning(f"未注册的 Embedding provider: {provider}")
        return None

    provider_inst = factory(provider, api_key, kwargs["base_url"], kwargs["model"])
    return EmbeddingClient(
        provider_name=provider,
        provider=provider_inst,
        api_key=api_key,
        base_url=kwargs["base_url"],
        model=kwargs["model"],
    )