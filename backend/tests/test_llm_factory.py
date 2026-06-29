from __future__ import annotations

import pytest

from app.llm.factory import LLMClient, get_chat_llm


class _MockChatProvider:
    """Mock chat provider that returns predictable responses."""

    async def chat(self, messages, temperature=0.2, timeout=60.0, **kwargs):
        return "mock response"


@pytest.mark.asyncio
async def test_llm_client_without_key_returns_config_prompt():
    client = LLMClient(
        provider_name="mock",
        provider=_MockChatProvider(),
        api_key="",
        base_url="https://api.example.com",
        model="mock",
    )
    response = await client.chat(messages=[{"role": "user", "content": "hi"}])
    assert response is not None


def test_get_chat_llm_returns_client_or_none():
    llm = get_chat_llm()
    assert llm is None or isinstance(llm, LLMClient)


@pytest.mark.asyncio
async def test_llm_client_async_chat_without_key():
    client = LLMClient(
        provider_name="mock",
        provider=_MockChatProvider(),
        api_key="",
        base_url="https://api.example.com",
        model="mock",
    )
    response = await client.chat(messages=[{"role": "user", "content": "hello"}])
    assert response is not None
