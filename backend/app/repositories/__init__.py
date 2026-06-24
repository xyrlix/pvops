"""时序数据仓库抽象与实现."""

from app.repositories.base import TimeSeriesRepository
from app.repositories.factory import get_repository

__all__ = ["TimeSeriesRepository", "get_repository"]
