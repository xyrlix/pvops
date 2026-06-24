"""协议适配器工厂."""

import logging
from typing import Any, Dict, Optional

from app.protocols.base import BaseProtocolAdapter

logger = logging.getLogger(__name__)


def create_adapter(
    protocol: str, device_code: str, config: Optional[Dict[str, Any]] = None
) -> BaseProtocolAdapter:
    """根据协议名称创建设备适配器."""
    protocol = (protocol or "simulator").lower()
    config = config or {}

    if protocol == "simulator":
        from app.protocols.simulator import SimulatorAdapter

        return SimulatorAdapter(device_code, config)

    if protocol == "modbus_tcp":
        from app.protocols.modbus_tcp import ModbusTCPAdapter

        return ModbusTCPAdapter(device_code, config)

    if protocol == "modbus_rtu":
        from app.protocols.modbus_rtu import ModbusRTUAdapter

        return ModbusRTUAdapter(device_code, config)

    if protocol == "mqtt_source":
        from app.protocols.mqtt_source import MqttSourceAdapter

        return MqttSourceAdapter(device_code, config)

    raise ValueError(f"不支持的协议类型: {protocol}")
