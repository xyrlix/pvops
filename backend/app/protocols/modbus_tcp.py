"""Modbus TCP 协议适配器."""

import logging
from datetime import UTC, datetime
from typing import Any

from app.protocols.base import BaseProtocolAdapter, CollectorPoint

logger = logging.getLogger(__name__)


def _decode_value(raw: int, point: CollectorPoint) -> Any:
    value = raw * point.scale
    if point.data_type in ("int", "uint"):
        return int(value)
    return float(value)


class ModbusTCPAdapter(BaseProtocolAdapter):
    """Modbus TCP 适配器."""

    def __init__(self, device_code: str, config: dict[str, Any] | None = None):
        super().__init__(device_code, config)
        self.host = self.config.get("host", "127.0.0.1")
        self.port = int(self.config.get("port", 502))
        self.unit_id = int(self.config.get("unit_id", 1))
        self.timeout = float(self.config.get("timeout", 10))
        self._client = None  # type: ignore[assignment]

        try:
            from pymodbus.client import AsyncModbusTcpClient

            self._client_class = AsyncModbusTcpClient
        except ImportError as e:
            logger.error("pymodbus 未安装，无法使用 Modbus TCP 适配器")
            raise RuntimeError("pymodbus 未安装") from e

    async def connect(self) -> None:
        self._client = self._client_class(  # type: ignore[call-arg]
            host=self.host,
            port=self.port,
            timeout=self.timeout,
        )
        await self._client.connect()  # type: ignore[union-attr]

    async def disconnect(self) -> None:
        if self._client:
            self._client.close()
            self._client = None  # type: ignore[assignment]

    async def read_points(self, points: list[CollectorPoint]) -> dict[str, Any]:
        if not self._client:
            await self.connect()
        result = {}
        for point in points:
            try:
                if point.register_type == "holding":
                    resp = await self._client.read_holding_registers(  # type: ignore[union-attr]
                        point.address, count=1, slave=self.unit_id
                    )
                elif point.register_type == "input":
                    resp = await self._client.read_input_registers(  # type: ignore[union-attr]
                        point.address, count=1, slave=self.unit_id
                    )
                else:
                    logger.warning(f"不支持的寄存器类型: {point.register_type}")
                    continue

                if resp and not resp.isError():
                    result[point.name] = _decode_value(resp.registers[0], point)
                else:
                    logger.warning(f"读取 {point.name} 失败: {resp}")
            except Exception as e:
                logger.warning(f"读取 {point.name} 异常: {e}")
        return result

    async def collect_once(self) -> dict[str, Any]:
        from app.protocols.register_map import DEVICE_REGISTER_MAPS

        device_type = self.config.get("device_type", "inverter")
        points = DEVICE_REGISTER_MAPS.get(device_type, [])
        values = await self.read_points(points)

        return {
            "timestamp": datetime.now(UTC).isoformat(),
            **values,
        }

# mypy: disable-error-code="attr-defined,assignment,union-attr"
