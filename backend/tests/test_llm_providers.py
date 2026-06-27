"""LLM Provider 注册表单元测试.

- 内置 provider 列表正确
- 自定义注册/覆盖
- factory 在未注册 provider 时返回 None
- LLMClient/EmbeddingClient 委托给 provider
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

import pytest

from app.llm import factory as llm_factory
from app.llm.factory import LLMClient, EmbeddingClient
from app.llm.providers import registry
from app.llm.providers.base import EmbeddingProvider, LLMProvider


# ─── 内存 mock provider ──────────────────────────────────────


class _MockChatProvider:
    def __init__(self, name: str, reply: str = "mock-reply") -> None:
        self._name = name
        self.reply = reply
        self.last_call: Dict[str, Any] | None = None

    @property
    def name(self) -> str:
        return self._name

    async def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.2,
        timeout: float = 60.0,
        **kwargs: Any,
    ) -> str:
        self.last_call = {"messages": messages, "temperature": temperature, "timeout": timeout}
        return self.reply


class _MockEmbedProvider:
    def __init__(self, name: str, dim: int = 4) -> None:
        self._name = name
        self.dim = dim

    @property
    def name(self) -> str:
        return self._name

    async def embed(
        self,
        texts: List[str],
        timeout: float = 60.0,
        **kwargs: Any,
    ) -> Optional[List[List[float]]]:
        return [[float(i)] * self.dim for i in range(len(texts))]


# ─── Protocol 兼容性 ─────────────────────────────────────────


def test_mock_satisfies_llm_provider_protocol() -> None:
    p = _MockChatProvider("mock")
    assert isinstance(p, LLMProvider)


def test_mock_satisfies_embedding_provider_protocol() -> None:
    p = _MockEmbedProvider("mock")
    assert isinstance(p, EmbeddingProvider)


# ─── 注册表行为 ─────────────────────────────────────────────


def test_list_chat_providers_includes_openai_family() -> None:
    providers = registry.list_chat_providers()
    for expected in ("openai", "deepseek", "kimi", "qwen", "minimax", "custom"):
        assert expected in providers, f"内置 chat provider {expected} 未注册"


def test_list_embed_providers_includes_openai_family() -> None:
    providers = registry.list_embed_providers()
    for expected in ("openai", "deepseek", "qwen", "custom"):
        assert expected in providers


def test_register_chat_provider_override() -> None:
    """覆盖同名 provider 时原工厂被替换."""

    def my_factory(name: str, key: str, url: str, model: str) -> LLMProvider:
        return _MockChatProvider(name, reply="overridden")

    original = registry.get_chat_factory("openai")
    registry.register_chat_provider("openai", my_factory)
    new = registry.get_chat_factory("openai")
    assert new is my_factory
    assert new is not original
    # 恢复
    registry.register_chat_provider("openai", original)


def test_register_custom_provider_then_lookup() -> None:
    """自定义 provider（模拟 Anthropic）注册后能查到."""

    def anthropic_factory(name: str, key: str, url: str, model: str) -> LLMProvider:
        return _MockChatProvider(name, reply=f"anthropic-{key}")

    registry.register_chat_provider("anthropic", anthropic_factory)
    f = registry.get_chat_factory("anthropic")
    assert f is anthropic_factory
    provider = f("anthropic", "sk-test", "https://api.anthropic.com", "claude-3")
    assert provider.name == "anthropic"


# ─── LLMClient / EmbeddingClient 委托 ────────────────────────


@pytest.mark.asyncio
async def test_llm_client_delegates_chat_to_provider() -> None:
    provider = _MockChatProvider("mock", reply="hello from mock")
    client = LLMClient(
        provider_name="mock",
        provider=provider,
        api_key="sk-test",
        base_url="http://example",
        model="mock-1",
    )
    out = await client.chat([{"role": "user", "content": "hi"}], temperature=0.5)
    assert out == "hello from mock"
    assert provider.last_call is not None
    assert provider.last_call["temperature"] == 0.5
    assert provider.last_call["messages"] == [{"role": "user", "content": "hi"}]


@pytest.mark.asyncio
async def test_embedding_client_delegates_embed() -> None:
    provider = _MockEmbedProvider("mock", dim=3)
    client = EmbeddingClient(
        provider_name="mock",
        provider=provider,
        api_key="sk-test",
        base_url="http://example",
        model="emb-1",
    )
    out = await client.embed(["a", "b"])
    assert out == [[0.0, 0.0, 0.0], [1.0, 1.0, 1.0]]


# ─── factory 公开 API 不变 ───────────────────────────────────


def test_get_chat_llm_returns_none_for_unregistered_provider(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """settings.llm_provider 未注册时返回 None 而不抛异常."""

    class _FakeSettings:
        llm_provider = "totally-not-registered"
        llm_api_key = "sk-test"
        llm_base_url = "http://x"
        llm_model = "m"
        embedding_provider = ""
        embedding_api_key = ""
        embedding_base_url = ""
        embedding_model = ""

    monkeypatch.setattr(llm_factory, "get_settings", lambda: _FakeSettings())

    # 注意：llm_factory 模块级的 provider 名是 "totally-not-registered"，
    # 注册表里没有，factory 应该返回 None
    result = llm_factory.get_chat_llm()
    assert result is None


def test_get_embeddings_returns_none_for_unregistered_provider(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class _FakeSettings:
        llm_provider = ""
        llm_api_key = ""
        llm_base_url = ""
        llm_model = ""
        embedding_provider = "totally-not-registered-embed"
        embedding_api_key = "sk-test"
        embedding_base_url = "http://x"
        embedding_model = "m"

    monkeypatch.setattr(llm_factory, "get_settings", lambda: _FakeSettings())

    result = llm_factory.get_embeddings()
    assert result is None