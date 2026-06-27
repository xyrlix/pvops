"""仓库工厂.

按事件循环缓存时序数据仓库实例。每个 event loop 独立持有一个
实例，避免 `uvicorn --reload` 或 pytest-asyncio 在多 loop 场景下
旧 `AsyncEngine` 绑定到已关闭 loop 导致的 `RuntimeError`。

调用方用法：`get_repository()` 同步返回实例。
lifespan 应在启动时调用 `await initialize_repository()` 完成 schema 初始化，
期间会自动尝试 TDengine，失败则 fallback SQLite。
"""

from __future__ import annotations

import asyncio
import logging
import weakref

from app.core.config import get_settings
from app.repositories.base import TimeSeriesRepository
from app.repositories.sqlite_repository import SQLiteTimeSeriesRepository

logger = logging.getLogger(__name__)

_loop_repos: weakref.WeakKeyDictionary[asyncio.AbstractEventLoop, TimeSeriesRepository] = (
    weakref.WeakKeyDictionary()
)


def _build_sync(backend: str) -> TimeSeriesRepository:
    """同步构造仓库实例（不做 schema 初始化）."""
    if backend == "tdengine":
        from app.repositories.tdengine_repository import TDengineTimeSeriesRepository

        return TDengineTimeSeriesRepository()
    return SQLiteTimeSeriesRepository()


def get_repository() -> TimeSeriesRepository:
    """同步获取当前事件循环的仓库实例。重复调用返回同一实例。

    若本 loop 尚未初始化，返回一个尚未 init() 的实例——调用方可继续
    使用读取接口（无 schema 依赖），写入则依赖 lifespan 已完成的初始化。
    """
    loop = asyncio.get_running_loop()
    repo = _loop_repos.get(loop)
    if repo is None:
        backend = get_settings().tsdb_backend.lower()
        repo = _build_sync(backend)
        _loop_repos[loop] = repo
        logger.info("初始化时序仓库（同步）: %s (backend=%s)", type(repo).__name__, backend)
    return repo


async def initialize_repository() -> TimeSeriesRepository:
    """在 lifespan 启动阶段调用：构造仓库并执行 init()。

    若 TDengine 不可用，自动 fallback SQLite。返回已初始化的实例。
    """
    repo = get_repository()
    backend = get_settings().tsdb_backend.lower()
    if backend == "tdengine" and not isinstance(repo, SQLiteTimeSeriesRepository):
        try:
            await repo.init()
            return repo
        except Exception as exc:
            logger.warning("TDengine 初始化失败: %s；fallback SQLite", exc)
            # 替换当前 loop 的仓库实例为 SQLite
            new_repo = SQLiteTimeSeriesRepository()
            _loop_repos[asyncio.get_running_loop()] = new_repo
            return new_repo

    # SQLite 不需要 async init；ensure create_all 已由迁移模块完成
    return repo


async def close_all_repositories() -> None:
    """关闭所有已缓存的仓库实例（应用 shutdown 时调用）."""
    for _loop, repo in list(_loop_repos.items()):
        try:
            await repo.close()
        except Exception:  # pragma: no cover - best-effort cleanup
            logger.exception("关闭 %s 失败", type(repo).__name__)
    _loop_repos.clear()


def reset_repository() -> None:
    """重置仓库缓存（仅用于测试）."""
    _loop_repos.clear()
