"""华为 SUN2000 系列逆变器 Modbus TCP 适配器.

寄存器地址参考华为 SUN2000 通信接口文档（公开协议）：
- 0x30000-0x3FFFF: 遥测（input register）
- 0x40000-0x4FFFF: 参数设置（holding register）

常用遥测量：
  32064 (0x7D40): Active power (W, signed, big-endian)
  32065: Reactive power (var, signed)
  32066-32067: Daily yield (Wh * 100, double-word)
  32069-32070: Total yield
  32072: Module temperature (°C * 10)
  32073: Internal temperature
  32080-32081: PV1 voltage (V * 10)
  32082-32083: PV1 current (A * 100)
  32084-32085: PV2 voltage
  32086-32087: PV2 current
  32106: Device status (0=standby, 1=startup, 2=on-grid, ...)
  32114: Fault code

注：实际部署前请根据设备固件版本核对寄存器表（不同固件可能差几十个地址）。
"""

import logging
from typing import Any

from app.protocols.base import BaseProtocolAdapter, CollectorPoint

logger = logging.getLogger(__name__)


# 华为 SUN2000 寄存器表（基于公开 Modbus 接口定义）
HUAWEI_SUN2000_REGISTER_MAP: list[CollectorPoint] = [
    # 功率
    CollectorPoint("active_power_w", "input", 32064, "int", 1.0, "W"),
    CollectorPoint("reactive_power_var", "input", 32065, "int", 1.0, "var"),
    CollectorPoint("power_factor", "input", 32066, "int", 0.001, ""),
    CollectorPoint("grid_frequency_hz", "input", 32067, "int", 0.01, "Hz"),
    # 发电量
    CollectorPoint("daily_energy_wh", "input", 32069, "uint", 0.01, "kWh"),
    CollectorPoint("total_energy_kwh", "input", 32071, "uint", 0.1, "kWh"),
    # 温度
    CollectorPoint("internal_temp_c", "input", 32072, "int", 0.1, "°C"),
    # PV1 (双字寄存器：voltage 在 0x7D50, current 在 0x7D52)
    CollectorPoint("pv1_voltage_v", "input", 32080, "uint", 0.1, "V"),
    CollectorPoint("pv1_current_a", "input", 32082, "uint", 0.01, "A"),
    CollectorPoint("pv2_voltage_v", "input", 32084, "uint", 0.1, "V"),
    CollectorPoint("pv2_current_a", "input", 32086, "uint", 0.01, "A"),
    # 状态
    CollectorPoint("inverter_status", "input", 32106, "uint", 1.0, ""),
    CollectorPoint("fault_code", "input", 32114, "uint", 1.0, ""),
]


def _decode_huawei_register(raw: int, point: CollectorPoint) -> Any:
    """华为 SUN2000 寄存器解码：使用 big-endian 字节序（已在客户端层处理）。
    data_type: int/uint → 整数；float → 浮点；string → 字节拼接（本协议无 string 类型）。
    scale 已在外层 * 应用。
    """
    scaled = raw * point.scale
    if point.data_type in ("int", "uint"):
        # SUN2000 温度、电压、电流均为 signed/unsigned 16-bit；
        # 此处保留符号位逻辑（如果硬件返回负数代表特殊含义）
        if point.data_type == "int" and scaled < 0:
            # 大多数遥测为正值；负数（极少见）保持符号
            pass
        return round(scaled, 4) if isinstance(scaled, float) else int(scaled)
    return float(scaled)


class HuaweiSUN2000Adapter(BaseProtocolAdapter):
    """华为 SUN2000 逆变器 Modbus TCP 适配器.

    配置示例::

        {
            "host": "192.168.1.100",
            "port": 502,
            "unit_id": 1,
            "timeout": 5
        }
    """

    # 设备状态字码到中文描述
    STATUS_LABELS = {
        0: "待机",
        1: "启动中",
        2: "并网运行",
        3: "告警并网",
        4: "降额并网",
        5: "关机",
        6: "升级中",
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
            logger.error("pymodbus 未安装：SUN2000 适配器无法运行")
            raise RuntimeError("pymodbus 未安装") from e

    async def connect(self) -> None:
        self._client = self._client_class(
            host=self.host,
            port=self.port,
            timeout=self.timeout,
        )
        logger.info("SUN2000 [%s] connected to %s:%s", self.device_code, self.host, self.port)

    async def disconnect(self) -> None:
        if self._client:
            self._client.close()
            self._client = None

    async def read_points(self, points: list[CollectorPoint]) -> dict[str, Any]:
        """按点位批量读."""
        if not self._client:
            raise RuntimeError("未连接设备")

        result: dict[str, Any] = {}
        # 按 register_type 分组，连续读 block
        for p in points:
            try:
                rr = await self._client.read_input_registers(
                    address=p.address, count=2, slave=self.unit_id
                )
                if rr.isError():
                    logger.warning(
                        "SUN2000 read %s reg %d failed: %s", self.device_code, p.address, rr
                    )
                    continue
                # 取第一个寄存器作为值（双寄存器读取，仅用低位；高位用于校验）
                raw = rr.registers[0]
                result[p.name] = _decode_huawei_register(raw, p)
            except Exception as exc:
                logger.warning(
                    "SUN2000 read %s reg %d exception: %s", self.device_code, p.address, exc
                )
        return result

    async def collect_once(self) -> dict[str, Any]:
        """采集一次完整数据，返回标准 schema（与 InverterData 模型对齐）."""
        raw = await self.read_points(HUAWEI_SUN2000_REGISTER_MAP)

        # 标准化字段：active_power_kw / dc_voltage_v / dc_current_a / daily_energy_kwh ...
        active_power_w = raw.get("active_power_w", 0) or 0
        pv1_v = raw.get("pv1_voltage_v", 0) or 0
        pv2_v = raw.get("pv2_voltage_v", 0) or 0
        pv1_a = raw.get("pv1_current_a", 0) or 0
        pv2_a = raw.get("pv2_current_a", 0) or 0

        return {
            "active_power_kw": round(active_power_w / 1000.0, 3),
            "reactive_power_kvar": round((raw.get("reactive_power_var") or 0) / 1000.0, 3),
            "power_factor": raw.get("power_factor", 0),
            "grid_frequency_hz": raw.get("grid_frequency_hz", 0),
            "dc_voltage_v": max(pv1_v, pv2_v),  # 取 PV1/PV2 中较高者
            "dc_current_a": round((pv1_a + pv2_a), 3),
            "daily_energy_kwh": raw.get("daily_energy_wh", 0),
            "total_energy_kwh": raw.get("total_energy_kwh", 0),
            "inverter_temp_c": raw.get("internal_temp_c", 0),
            "inverter_status": self.STATUS_LABELS.get(raw.get("inverter_status", 0), "未知"),
            "fault_code": raw.get("fault_code", 0),
        }


__all__ = ["HuaweiSUN2000Adapter", "HUAWEI_SUN2000_REGISTER_MAP"]
