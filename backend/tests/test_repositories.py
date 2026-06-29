"""时序数据仓库测试."""

import pytest

from app.core.config import get_settings
from app.repositories.factory import get_repository, reset_repository
from app.repositories.sqlite_repository import SQLiteTimeSeriesRepository
from app.repositories.tdengine_repository import TDengineTimeSeriesRepository


@pytest.fixture(autouse=True)
def reset_repo():
    """每个测试前重置仓库单例."""
    reset_repository()
    yield
    reset_repository()


@pytest.mark.asyncio
async def test_factory_returns_sqlite_by_default():
    """默认配置返回 SQLite 仓库."""
    settings = get_settings()
    original = settings.tsdb_backend
    try:
        settings.tsdb_backend = "sqlite"
        repo = get_repository()
        assert isinstance(repo, SQLiteTimeSeriesRepository)
    finally:
        settings.tsdb_backend = original


@pytest.mark.asyncio
async def test_factory_returns_tdengine_when_configured():
    """配置 tdengine 时返回 TDengine 仓库对象（taosws 可能未安装）."""
    settings = get_settings()
    original = settings.tsdb_backend
    try:
        settings.tsdb_backend = "tdengine"
        repo = get_repository()
        assert isinstance(repo, TDengineTimeSeriesRepository)
    finally:
        settings.tsdb_backend = original
