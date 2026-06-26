"""向量存储工厂.

按事件循环缓存实例，与 `app.repositories.factory` 保持一致语义。
优先探测 PGVector；不可用时回退本地 SQLite 关键词检索。
"""

from __future__ import annotations

import asyncio
import logging
import weakref

from app.vectorstore.base import VectorStore

logger = logging.getLogger(__name__)

_loop_stores: "weakref.WeakKeyDictionary[asyncio.AbstractEventLoop, VectorStore]" = (
    weakref.WeakKeyDictionary()
)


async def _build() -> VectorStore:
    """探测可用后端，构造实例."""
    from app.vectorstore.local import LocalVectorStore
    from app.vectorstore.pgvector import PGVectorStore

    pg = PGVectorStore()
    if await pg.is_available():
        logger.info("使用向量存储: PGVector")
        return pg
    local = LocalVectorStore()
    await local.init()
    logger.info("使用向量存储: Local SQLite fallback")
    return local


async def get_vector_store() -> VectorStore:
    """获取当前事件循环对应的向量存储."""
    loop = asyncio.get_running_loop()
    store = _loop_stores.get(loop)
    if store is None:
        store = await _build()
        _loop_stores[loop] = store
    return store


async def close_all_vector_stores() -> None:
    """关闭所有缓存实例（应用 shutdown 时调用）."""
    _loop_stores.clear()
    # 多数实现无 close；保留扩展点


def reset_vector_store() -> None:
    """重置缓存（仅用于测试）."""
    _loop_stores.clear()
