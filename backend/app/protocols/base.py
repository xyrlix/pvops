"""协议适配器抽象."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


@dataclass
class CollectorPoint:
    """采集点定义."""

    name: str
    register_type: str  # holding / input / discrete / coil
    address: int
    data_type: str = "float"  # float / int / uint / bool / string
    scale: float = 1.0
    unit: str = ""


class BaseProtocolAdapter(ABC):
    """协议适配器抽象基类."""

    def __init__(self, device_code: str, config: dict[str, Any] | None = None):
        self.device_code = device_code
        self.config = config or {}

    @abstractmethod
    async def connect(self) -> None:
        """建立连接."""
        ...

    @abstractmethod
    async def disconnect(self) -> None:
        """断开连接."""
        ...

    @abstractmethod
    async def read_points(self, points: list[CollectorPoint]) -> dict[str, Any]:
        """按采集点批量读数，返回 {point_name: raw_value}."""
        ...

    @abstractmethod
    async def collect_once(self) -> dict[str, Any]:
        """采集一次完整数据，返回可用于写入仓库的字典."""
        ...
