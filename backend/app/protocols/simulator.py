"""模拟器协议适配器."""

import math
import random
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from app.protocols.base import BaseProtocolAdapter, CollectorPoint


class SimulatorAdapter(BaseProtocolAdapter):
    """本地模拟数据适配器，用于无真实设备时的演示."""

    def __init__(self, device_code: str, config: Optional[Dict[str, Any]] = None):
        super().__init__(device_code, config)
        self.capacity_kw = float(self.config.get("capacity_kw", 350.0))
        self._phase = random.random() * 2 * math.pi

    async def connect(self) -> None:
        pass

    async def disconnect(self) -> None:
        pass

    async def read_points(self, points: List[CollectorPoint]) -> Dict[str, Any]:
        return {p.name: self._mock_value(p.name) for p in points}

    async def collect_once(self) -> Dict[str, Any]:
        now = datetime.now(timezone.utc)
        hour = now.hour + now.minute / 60.0
        # 简化日照曲线：6~18 点有辐照
        irradiance = 0.0
        if 6 <= hour <= 18:
            irradiance = 1000 * math.sin(math.pi * (hour - 6) / 12)

        # 功率与辐照成正比，加入随机波动
        power_ratio = (irradiance / 1000) * (0.85 + 0.1 * math.sin(self._phase))
        power_ratio = max(0.0, min(0.98, power_ratio))
        active_power = self.capacity_kw * power_ratio * (0.98 + random.uniform(-0.03, 0.03))

        # 日发电量（简化累加）
        daily_energy = self.capacity_kw * 5.0 * power_ratio * (hour / 24.0)

        self._phase += 0.1

        return {
            "timestamp": now.isoformat(),
            "active_power_kw": round(active_power, 2),
            "dc_voltage_v": round(600 + random.uniform(-10, 10), 2),
            "dc_current_a": round(active_power * 1000 / 600, 2) if active_power > 0 else 0.0,
            "daily_energy_kwh": round(daily_energy, 2),
            "total_energy_kwh": round(daily_energy * 100 + random.uniform(0, 10), 2),
            "inverter_status": 1 if active_power > 1 else 0,
            "fault_code": 0,
            "irradiance_w_m2": round(irradiance, 1),
            "ambient_temp_c": round(25 + random.uniform(-3, 8), 1),
        }

    def _mock_value(self, name: str) -> Any:
        mapping = {
            "active_power_kw": self.capacity_kw * 0.5,
            "dc_voltage_v": 600.0,
            "dc_current_a": 5.0,
            "daily_energy_kwh": self.capacity_kw * 2.5,
            "total_energy_kwh": self.capacity_kw * 1000.0,
            "inverter_status": 1,
            "fault_code": 0,
            "irradiance_w_m2": 600.0,
            "ambient_temp_c": 28.0,
            "module_temp_c": 35.0,
            "wind_speed_m_s": 2.5,
        }
        return mapping.get(name, 0.0)
