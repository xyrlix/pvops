"""数据提供方抽象层（DataProvider Protocol）.

业务 service 不再直接 `from app.services import mock_data` 或 `repo.method()`，
而是调用 `get_data_provider().method(...)`，由 provider 根据运行模式
(`settings.use_mock_data`) 决定从 mock 生成器还是真实仓库返回数据。

新增数据源只需新增一个实现此 Protocol 的 provider 类并在
`__init__.py:build_provider()` 注册；service 完全无需修改。
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional, Protocol, runtime_checkable


@runtime_checkable
class DataProvider(Protocol):
    """统一数据访问接口.

    所有方法都接受显式参数并返回纯 dict / list；不允许返回 ORM 对象，
    便于 mock 与真实实现互相替换。
    """

    # —— 实时指标 ——

    async def get_latest_station_metrics(
        self, station_id: int, capacity_kw: float = 1000.0
    ) -> Dict[str, Any]: ...

    async def get_metric_history(
        self,
        station_id: int,
        metric: str,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
        points: int = 144,
    ) -> List[Dict[str, Any]]: ...

    # —— 聚合视图 ——

    async def get_station_overview(self, stations: List[Dict[str, Any]]) -> List[Dict[str, Any]]: ...

    async def get_efficiency(
        self, station_id: int, capacity_kw: float = 1000.0
    ) -> Dict[str, Any]: ...

    async def get_loss_breakdown(
        self, station_id: int, capacity_kw: float = 1000.0
    ) -> Dict[str, Any]: ...

    async def get_health_trend(
        self, station_id: int, days: int = 30
    ) -> List[Dict[str, Any]]: ...

    # —— 设备级 ——

    async def get_inverter_comparison(
        self, station_id: int, inverters: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]: ...

    async def get_string_dispersion(
        self, station_id: int, strings: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]: ...


__all__ = ["DataProvider"]