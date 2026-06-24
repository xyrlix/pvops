from __future__ import annotations

import pytest

from app.vectorstore.local import LocalVectorStore


@pytest.mark.asyncio
async def test_local_vector_store_search():
    store = LocalVectorStore()
    await store.add_texts(
        texts=["逆变器温度过高", "组件灰尘遮挡导致发电量下降"],
        metadatas=[{"doc_id": 1, "source": "sop"}, {"doc_id": 2, "source": "faq"}],
        ids=["c1", "c2"],
    )
    results = await store.similarity_search("逆变器发热", k=2)
    assert len(results) > 0
    assert any("逆变器" in r.page_content for r in results)


@pytest.mark.asyncio
async def test_local_vector_store_returns_empty_for_no_match():
    store = LocalVectorStore()
    results = await store.similarity_search("xyz-no-match-123", k=2)
    assert results == []
