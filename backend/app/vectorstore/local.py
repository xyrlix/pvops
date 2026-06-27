"""本地向量存储 fallback（基于 SQLite 关键词检索）."""

from __future__ import annotations

import json
import logging
import os
import re

import aiosqlite

from app.vectorstore.base import Document, VectorStore

logger = logging.getLogger(__name__)

DEFAULT_DB = os.path.join(os.path.dirname(__file__), "..", "..", "kb_vectors.db")


class LocalVectorStore(VectorStore):
    """本地 SQLite 关键词检索存储.

    无 PGVector/Embedding 时使用，适合本地开发验证流程。
    """

    def __init__(self, db_path: str | None = None):
        self.db_path = db_path or DEFAULT_DB

    async def init(self) -> None:
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """
                CREATE TABLE IF NOT EXISTS kb_documents (
                    id TEXT PRIMARY KEY,
                    doc_id TEXT,
                    content TEXT,
                    metadata TEXT,
                    created_at TEXT
                )
            """
            )
            await db.execute("CREATE INDEX IF NOT EXISTS idx_kb_doc_id ON kb_documents(doc_id)")
            await db.commit()

    async def is_available(self) -> bool:
        return True

    async def add_texts(
        self,
        texts: list[str],
        metadatas: list[dict] | None = None,
        ids: list[str] | None = None,
    ) -> list[str]:
        metadatas = metadatas or [{} for _ in texts]
        documents = [
            Document(page_content=text, metadata=metadata)
            for text, metadata in zip(texts, metadatas, strict=True)
        ]
        return await self.add_documents(documents, ids=ids)

    async def add_documents(
        self, documents: list[Document], ids: list[str] | None = None
    ) -> list[str]:
        await self.init()
        from datetime import datetime

        if ids is None:
            ids = [f"chunk_{i}" for i in range(len(documents))]

        async with aiosqlite.connect(self.db_path) as db:
            for idx, doc in enumerate(documents):
                await db.execute(
                    """
                    INSERT OR REPLACE INTO kb_documents (id, doc_id, content, metadata, created_at)
                    VALUES (?, ?, ?, ?, ?)
                """,
                    (
                        ids[idx],
                        doc.metadata.get("doc_id", ""),
                        doc.page_content,
                        json.dumps(doc.metadata, ensure_ascii=False),
                        datetime.now().isoformat(),
                    ),
                )
            await db.commit()
        return ids

    def _extract_terms(self, query: str) -> list[str]:
        """提取查询词：中文按字符/二元组，英文按单词."""
        terms = []
        # 中文单字作为基础匹配单元
        for char in query:
            if "\u4e00" <= char <= "\u9fff":
                terms.append(char)
        # 英文/数字单词
        for token in re.findall(r"[a-zA-Z0-9]+", query):
            terms.append(token.lower())
        return list(set(terms))

    async def similarity_search(
        self, query: str, k: int = 4, filter: dict | None = None
    ) -> list[Document]:
        await self.init()
        terms = self._extract_terms(query)
        if not terms:
            return []

        async with (
            aiosqlite.connect(self.db_path) as db,
            db.execute("SELECT id, doc_id, content, metadata FROM kb_documents") as cursor,
        ):
            rows = await cursor.fetchall()

        results = []
        for row in rows:
            content = (row[2] or "").lower()
            score = sum(1 for term in terms if term in content)
            if score > 0:
                metadata = json.loads(row[3] or "{}")
                if filter:
                    match = all(metadata.get(k) == v for k, v in filter.items())
                    if not match:
                        continue
                results.append((score, Document(page_content=row[2], metadata=metadata)))

        results.sort(key=lambda x: x[0], reverse=True)
        return [doc for _, doc in results[:k]]

    async def delete(self, ids: list[str]) -> bool:
        await self.init()
        async with aiosqlite.connect(self.db_path) as db:
            placeholders = ",".join("?" * len(ids))
            await db.execute(f"DELETE FROM kb_documents WHERE id IN ({placeholders})", ids)
            await db.commit()
        return True
