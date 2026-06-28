from __future__ import annotations

import pytest

from app.llm.factory import LLMClient, get_chat_llm


def test_llm_client_without_key_returns_config_prompt():
    client = LLMClient(
        provider_name="openai",
        provider=object(), api_key="", base_url="https://api.openai.com/v1", model="gpt-4"
    )
    response = client.chat(messages=[{"role": "user", "content": "hi"}])
    assert "请配置 LLM API Key" in response


def test_get_chat_llm_returns_client_or_none():
    llm = get_chat_llm()
    assert llm is None or isinstance(llm, LLMClient)


@pytest.mark.asyncio
async def test_llm_client_async_chat_without_key():
    client = LLMClient(
        provider_name="openai",
        provider=object(),
        api_key="",
        base_url="https://api.deepseek.com/v1",
        model="deepseek-chat",
    )
    response = await client.chat(messages=[{"role": "user", "content": "hello"}])
    assert "请配置 LLM API Key" in response
