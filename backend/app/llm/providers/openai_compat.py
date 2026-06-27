"""OpenAI 兼容 Provider —— 当前默认实现，覆盖 OpenAI / DeepSeek / Kimi / Qwen / MiniMax 等.

通过 ``app.llm.config.get_llm_preset`` 取得每个 provider 的 base_url + model 默认值。
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any

import requests

from app.llm.providers.base import EmbeddingProvider, LLMProvider

logger = logging.getLogger(__name__)


class OpenAICompatChatProvider(LLMProvider):
    """OpenAI 兼容协议的 chat 客户端."""

    def __init__(self, name: str, api_key: str, base_url: str, model: str) -> None:
        self._name = name
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.model = model

    @property
    def name(self) -> str:
        return self._name

    async def chat(
        self,
        messages: list[dict[str, str]],
        temperature: float = 0.2,
        timeout: float = 60.0,
        **kwargs: Any,
    ) -> str:
        if not self.api_key:
            return "请配置 LLM API Key 以启用 AI 对话功能。"

        def _call() -> dict[str, Any]:
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
            return f"AI 服务暂时不可用，请稍后重试。 ({self._name})"
        except Exception as exc:  # pragma: no cover - defensive
            logger.exception("LLM 响应解析失败")
            return f"AI 响应异常，请稍后重试。 ({exc})"


class OpenAICompatEmbeddingProvider(EmbeddingProvider):
    """OpenAI 兼容协议的 embedding 客户端."""

    def __init__(self, name: str, api_key: str, base_url: str, model: str) -> None:
        self._name = name
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.model = model

    @property
    def name(self) -> str:
        return self._name

    async def embed(
        self,
        texts: list[str],
        timeout: float = 60.0,
        **kwargs: Any,
    ) -> list[list[float]] | None:
        if not self.api_key:
            return None

        def _call() -> dict[str, Any]:
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
