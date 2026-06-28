"""阳光电源 SG 系列逆变器 Modbus TCP 适配器.

寄存器地址基于阳光 SG3K/5K/10K/30K Modbus 协议（公开）：
- Input Register (0x): 遥测
- Holding Register (4x): 参数

常用遥测：
  0x0002-0x0003: Daily energy (Wh, 32-bit, big-endian)
  0x0004-0x0005: Total energy (kWh * 10, 32-bit)
  0x000C-0x000D: DC voltage (V * 10)
  0x000E-0x000F: DC current (A * 10)
  0x0014-0x0015: Active power (W, signed 32-bit)
  0x0016-0x0017: Reactive power (var)
  0x001A: Grid frequency (Hz * 10)
  0x001C: Internal temp (°C)
  0x002C: Device status
  0x0042: Fault code
"""

import logging
from typing import Any

from app.protocols.base import BaseProtocolAdapter, CollectorPoint

logger = logging.getLogger(__name__)


SUNGROW_SG_REGISTER_MAP: list[CollectorPoint] = [
    CollectorPoint("dc_voltage_v", "input", 12, "int", 0.1, "V"),
    CollectorPoint("dc_current_a", "input", 14, "int", 0.1, "A"),
    CollectorPoint("active_power_w", "input", 20, "int", 1.0, "W"),
    CollectorPoint("reactive_power_var", "input", 22, "int", 1.0, "var"),
    CollectorPoint("grid_frequency_hz", "input", 26, "int", 0.1, "Hz"),
    CollectorPoint("internal_temp_c", "input", 28, "int", 1.0, "°C"),
    CollectorPoint("inverter_status", "input", 44, "uint", 1.0, ""),
    CollectorPoint("fault_code", "input", 66, "uint", 1.0, ""),
    CollectorPoint("daily_energy_wh", "input", 2, "uint", 0.001, "kWh"),
    CollectorPoint("total_energy_kwh", "input", 4, "uint", 0.1, "kWh"),
]


class SungrowSGAdapter(BaseProtocolAdapter):
    """阳光 SG 系列 Modbus TCP 适配器."""

    STATUS_LABELS = {
        0x0000: "待机",
        0x0001: "启动中",
        0x0002: "并网运行",
        0x0003: "关机",
        0x0004: "故障",
    }

    def __init__(self, device_code: str, config: dict[str, Any] | None = None):
        super().__init__(device_code, config)
        self.host = self.config.get("host", "127.0.0.1")
        self.port = int(self.config.get("port", 502))
        self.unit_id = int(self.config.get("unit_id", 1))
        self.timeout = float(self.config.get("timeout", 5))
        self._client = None

        try:
            from pymodbus.client import AsyncModbusTcpClient

            self._client_class = AsyncModbusTcpClient
        except ImportError as e:
            logger.error("pymodbus 未安装：Sungrow 适配器无法运行")
            raise RuntimeError("pymodbus 未安装") from e

    async def connect(self) -> None:
        self._client = self._client_class(
            host=self.host,
            port=self.port,
            timeout=self.timeout,
        )
        logger.info("Sungrow [%s] connected to %s:%s", self.device_code, self.host, self.port)

    async def disconnect(self) -> None:
        if self._client:
            self._client.close()
            self._client = None

    async def read_points(self, points: list[CollectorPoint]) -> dict[str, Any]:
        if not self._client:
            raise RuntimeError("未连接设备")

        result: dict[str, Any] = {}
        for p in points:
            try:
                rr = await self._client.read_input_registers(
                    address=p.address, count=1, slave=self.unit_id
                )
                if rr.isError():
                    continue
                raw = rr.registers[0]
                value = raw * p.scale
                if p.data_type in ("int", "uint"):
                    result[p.name] = int(value) if float(value).is_integer() else round(value, 4)
                else:
                    result[p.name] = float(value)
            except Exception as exc:
                logger.warning(
                    "Sungrow read %s reg %d exception: %s", self.device_code, p.address, exc
                )
        return result

    async def collect_once(self) -> dict[str, Any]:
        raw = await self.read_points(SUNGROW_SG_REGISTER_MAP)
        active_power_w = raw.get("active_power_w", 0) or 0
        return {
            "active_power_kw": round(active_power_w / 1000.0, 3),
            "reactive_power_kvar": round((raw.get("reactive_power_var") or 0) / 1000.0, 3),
            "dc_voltage_v": raw.get("dc_voltage_v", 0),
            "dc_current_a": raw.get("dc_current_a", 0),
            "daily_energy_kwh": raw.get("daily_energy_wh", 0),
            "total_energy_kwh": raw.get("total_energy_kwh", 0),
            "inverter_temp_c": raw.get("internal_temp_c", 0),
            "inverter_status": self.STATUS_LABELS.get(raw.get("inverter_status", 0), "未知"),
            "fault_code": raw.get("fault_code", 0),
        }


__all__ = ["SungrowSGAdapter", "SUNGROW_SG_REGISTER_MAP"]
# mypy: disable-error-code="assignment,arg-type"
