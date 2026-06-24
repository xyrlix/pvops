#!/usr/bin/env python3
"""Lightweight smoke test runnable without pytest."""
from __future__ import annotations

import asyncio
import sys

sys.path.insert(0, "backend")
sys.path.insert(0, "backend/.apt-libs/usr/lib/python3/dist-packages")

from app.llm.factory import LLMClient, get_chat_llm
from app.vectorstore.local import LocalVectorStore


async def test_llm_factory() -> None:
    client = LLMClient(provider="openai", api_key="", base_url="https://api.openai.com/v1", model="gpt-4")
    response = await client.chat(messages=[{"role": "user", "content": "hi"}])
    assert "请配置 LLM API Key" in response, response
    print("LLM factory OK")


async def test_vector_store() -> None:
    store = LocalVectorStore()
    await store.add_texts(
        texts=["逆变器温度过高"],
        metadatas=[{"doc_id": 1}],
        ids=["c1"],
    )
    results = await store.similarity_search("逆变器发热", k=2)
    assert any("逆变器" in r.page_content for r in results), results
    print("Vector store OK")


async def main() -> None:
    await test_llm_factory()
    await test_vector_store()
    print("All sanity checks passed.")


if __name__ == "__main__":
    asyncio.run(main())
