"""向量存储工厂."""

import logging

from app.vectorstore.base import VectorStore
from app.vectorstore.local import LocalVectorStore
from app.vectorstore.pgvector import PGVectorStore

logger = logging.getLogger(__name__)

_vector_store_instance: VectorStore | None = None


async def get_vector_store() -> VectorStore:
    """获取当前可用的向量存储（PGVector 优先，不可用则 fallback 到本地）."""
    global _vector_store_instance
    if _vector_store_instance is not None:
        return _vector_store_instance

    pg = PGVectorStore()
    if await pg.is_available():
        _vector_store_instance = pg
        logger.info("使用向量存储: PGVector")
    else:
        local = LocalVectorStore()
        await local.init()
        _vector_store_instance = local
        logger.info("使用向量存储: Local SQLite fallback")
    return _vector_store_instance


def reset_vector_store() -> None:
    """重置向量存储单例（主要用于测试）."""
    global _vector_store_instance
    _vector_store_instance = None
