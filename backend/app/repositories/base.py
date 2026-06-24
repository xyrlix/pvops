"""时序数据仓库抽象接口."""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, List, Optional


class TimeSeriesRepository(ABC):
    """时序数据仓库抽象.

    统一 SQLite / TDengine 等底层存储的读写行为。
    """

    @abstractmethod
    async def init(self) -> None:
        """初始化存储（建库/建表/建超级表）."""
        ...

    @abstractmethod
    async def close(self) -> None:
        """关闭连接."""
        ...

    @abstractmethod
    async def insert_inverter_data(
        self, station_id: int, inverter_id: str, data: Dict
    ) -> None:
        """写入一条逆变器时序数据."""
        ...

    @abstractmethod
    async def insert_weather_data(
        self, station_id: int, device_id: str, data: Dict
    ) -> None:
        """写入一条气象站时序数据."""
        ...

    @abstractmethod
    async def batch_insert_inverter_data(self, data_list: List[Dict]) -> int:
        """批量写入逆变器数据，返回成功条数."""
        ...

    @abstractmethod
    async def get_latest_station_metrics(self, station_id: int) -> Dict:
        """获取电站最新指标."""
        ...

    @abstractmethod
    async def get_metric_history(
        self,
        station_id: int,
        metric: str,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
    ) -> List[Dict]:
        """获取指定指标历史."""
        ...

    @abstractmethod
    async def get_daily_energy(
        self, station_id: int, date: Optional[datetime] = None
    ) -> float:
        """获取某日发电量（取当天最后一条 daily_energy_kwh）."""
        ...
