"""LLM / Embedding Provider 抽象层.

新增非 OpenAI 兼容供应商（如 Anthropic、Cohere、本地 llama.cpp）只需：
1. 继承 ``LLMProvider`` 或 ``EmbeddingProvider`` 实现 chat / embed
2. 在 ``app.llm.providers.registry.register_provider(...)`` 注册

调用方依然使用 ``app.llm.factory.get_chat_llm()`` 拿到 LLMClient，
LLMClient 内部委托给当前选中的 provider。
"""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class LLMProvider(Protocol):
    """聊天模型 Provider 抽象接口."""

    @property
    def name(self) -> str:
        """provider 名称，如 'openai' / 'anthropic' / 'deepseek'."""
        ...

    async def chat(
        self,
        messages: list[dict[str, str]],
        temperature: float = 0.2,
        timeout: float = 60.0,
        **kwargs: Any,
    ) -> str:
        """执行一次聊天调用，返回字符串内容.

        出错时返回友好提示字符串（不抛异常），与现有 LLMClient 行为一致。
        """
        ...


@runtime_checkable
class EmbeddingProvider(Protocol):
    """Embedding Provider 抽象接口."""

    @property
    def name(self) -> str: ...

    async def embed(
        self,
        texts: list[str],
        timeout: float = 60.0,
        **kwargs: Any,
    ) -> list[list[float]] | None:
        """批量嵌入，返回向量列表；失败时返回 None."""
        ...


__all__ = ["LLMProvider", "EmbeddingProvider"]
