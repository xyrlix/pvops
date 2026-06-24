"""LLM / Embeddings 工厂（OpenAI 兼容接口，基于 requests + asyncio.to_thread）."""

import json
import logging
from typing import Any, Dict, List, Optional

import requests

from app.core.config import get_settings
from app.llm.config import get_embedding_preset, get_llm_preset

logger = logging.getLogger(__name__)


class LLMClient:
    """轻量级 OpenAI 兼容聊天客户端."""

    def __init__(self, provider: str, api_key: str, base_url: str, model: str):
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
        if not self.api_key:
            return "请配置 LLM API Key 以启用 AI 对话功能。"

        import asyncio

        def _call():
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self.model,
                    "messages": messages,
                    "temperature": temperature,
                },
                timeout=timeout,
            )
            response.raise_for_status()
            return response.json()

        try:
            data = await asyncio.to_thread(_call)
            return data["choices"][0]["message"]["content"]
        except requests.exceptions.RequestException as exc:
            logger.warning("LLM 调用失败: %s", exc)
            return f"AI 服务暂时不可用，请稍后重试。 ({self.provider})"
        except Exception as exc:  # pragma: no cover - defensive
            logger.exception("LLM 响应解析失败")
            return f"AI 响应异常，请稍后重试。 ({exc})"

class EmbeddingClient:
    """轻量级 OpenAI 兼容 Embedding 客户端."""

    def __init__(self, api_key: str, base_url: str, model: str):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.model = model

    async def embed(self, texts: List[str], timeout: float = 60.0) -> Optional[List[List[float]]]:
        if not self.api_key:
            return None

        import asyncio

        def _call():
            response = requests.post(
                f"{self.base_url}/embeddings",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={"model": self.model, "input": texts},
                timeout=timeout,
            )
            response.raise_for_status()
            return response.json()

        try:
            data = await asyncio.to_thread(_call)
            return [item["embedding"] for item in data["data"]]
        except Exception as exc:  # pragma: no cover - defensive
            logger.warning("Embedding 调用失败: %s", exc)
            return None


def _build_kwargs(
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
    """获取聊天 LLM 客户端."""
    settings = get_settings()
    provider = (settings.llm_provider or "openai").lower()
    preset = get_llm_preset(provider)
    api_key = settings.llm_api_key

    if not api_key:
        logger.warning("LLM_API_KEY 未配置，聊天功能不可用")
        return None

    kwargs = _build_kwargs(
        provider,
        api_key,
        settings.llm_base_url,
        settings.llm_model,
        preset,
    )

    if not kwargs["base_url"] or not kwargs["model"]:
        logger.warning(f"LLM provider {provider} 缺少 base_url 或 model 配置")
        return None

    return LLMClient(**kwargs)


def get_embeddings() -> Optional[EmbeddingClient]:
    """获取 Embedding 客户端."""
    settings = get_settings()
    provider = (settings.embedding_provider or settings.llm_provider or "openai").lower()
    preset = get_embedding_preset(provider)
    api_key = settings.embedding_api_key or settings.llm_api_key

    if not api_key:
        logger.warning("EMBEDDING_API_KEY / LLM_API_KEY 未配置，Embedding 不可用")
        return None

    kwargs = _build_kwargs(
        provider,
        api_key,
        settings.embedding_base_url,
        settings.embedding_model,
        preset,
    )
    if not kwargs["base_url"] or not kwargs["model"]:
        logger.warning(f"Embedding provider {provider} 缺少 base_url 或 model 配置")
        return None

    return EmbeddingClient(**kwargs)
