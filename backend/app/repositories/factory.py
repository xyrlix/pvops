"""仓库工厂."""

import logging

from app.core.config import get_settings
from app.repositories.base import TimeSeriesRepository
from app.repositories.sqlite_repository import SQLiteTimeSeriesRepository
from app.repositories.tdengine_repository import TDengineTimeSeriesRepository

logger = logging.getLogger(__name__)

_repo_instance: TimeSeriesRepository | None = None


def get_repository() -> TimeSeriesRepository:
    """获取当前配置的时序数据仓库（单例）."""
    global _repo_instance
    if _repo_instance is not None:
        return _repo_instance

    backend = get_settings().tsdb_backend.lower()
    if backend == "tdengine":
        _repo_instance = TDengineTimeSeriesRepository()
        logger.info("使用时序仓库: TDengine")
    else:
        _repo_instance = SQLiteTimeSeriesRepository()
        logger.info("使用时序仓库: SQLite")
    return _repo_instance


def reset_repository() -> None:
    """重置仓库单例（主要用于测试）."""
    global _repo_instance
    _repo_instance = None
