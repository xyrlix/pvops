"""PGVector 向量存储实现."""

import logging
from typing import List, Optional

from app.core.config import get_settings
from app.vectorstore.base import Document, VectorStore

logger = logging.getLogger(__name__)

_pgvector_available = False
try:
    from langchain_community.vectorstores import PGVector

    _pgvector_available = True
except ImportError:
    logger.warning("langchain_community 未安装，PGVector 不可用")


class PGVectorStore(VectorStore):
    """基于 PostgreSQL + pgvector 的向量存储."""

    def __init__(self, collection_name: str = "pvops_kb"):
        self.collection_name = collection_name
        self._store = None

    def _get_store(self):
        if self._store is not None:
            return self._store
        if not _pgvector_available:
            raise RuntimeError("langchain_community 未安装")

        from langchain_openai import OpenAIEmbeddings

        settings = get_settings()
        from app.llm.factory import get_embeddings

        embeddings = get_embeddings()
        if embeddings is None:
            raise RuntimeError("Embedding 客户端未配置")

        # langchain PGVector 需要同步 embeddings 对象；这里用 OpenAIEmbeddings 包装
        lc_embeddings = OpenAIEmbeddings(
            openai_api_key=embeddings.api_key,
            openai_api_base=embeddings.base_url,
            model=embeddings.model,
        )

        self._store = PGVector(
            connection_string=settings.database_url.replace("+asyncpg", ""),
            embedding_function=lc_embeddings,
            collection_name=self.collection_name,
        )
        return self._store

    async def is_available(self) -> bool:
        if not _pgvector_available:
            return False
        try:
            self._get_store()
            return True
        except Exception as e:
            logger.warning(f"PGVector 不可用: {e}")
            return False

    async def add_documents(
        self, documents: List[Document], ids: Optional[List[str]] = None
    ) -> List[str]:
        store = self._get_store()
        lc_docs = [
            type("LCDocument", (), {"page_content": d.page_content, "metadata": d.metadata})()
            for d in documents
        ]
        return store.add_documents(lc_docs, ids=ids)

    async def similarity_search(
        self, query: str, k: int = 4, filter: Optional[dict] = None
    ) -> List[Document]:
        store = self._get_store()
        results = store.similarity_search(query, k=k, filter=filter)
        return [Document(page_content=r.page_content, metadata=r.metadata) for r in results]

    async def delete(self, ids: List[str]) -> bool:
        store = self._get_store()
        try:
            store.delete(ids)
            return True
        except Exception as e:
            logger.warning(f"PGVector 删除失败: {e}")
            return False
