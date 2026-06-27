"""MockDataProvider —— 仅用于本地演示与离线开发.

确定性随机（基于 station_id + metric + 日期），刷新后数据稳定。
生产部署必须使用 RealDataProvider 或在 settings.use_mock_data=False
时通过 get_data_provider() 切换。
"""

from __future__ import annotations

import hashlib
import random
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from app.demo.provider import DataProvider


def _seed(value: str) -> random.Random:
    """基于字符串生成固定随机数生成器（同一输入同一输出）."""
    hashed = hashlib.md5(value.encode("utf-8")).hexdigest()
    return random.Random(hashed)


class MockDataProvider(DataProvider):
    """生成器式 provider，每个方法对应原 mock_data 中的同名函数."""

    async def get_latest_station_metrics(
        self, station_id: int, capacity_kw: float = 1000.0
    ) -> Dict[str, Any]:
        rng = _seed(f"latest-{station_id}-{datetime.now().strftime('%Y%m%d')}")
        hour = datetime.now().hour + datetime.now().minute / 60
        if 6 <= hour <= 18:
            peak = ((hour - 6) / 12) * capacity_kw * 0.85
            active_power_kw = max(0, peak + rng.uniform(-capacity_kw * 0.05, capacity_kw * 0.05))
        else:
            active_power_kw = rng.uniform(0, capacity_kw * 0.02)
        return {
            "station_id": station_id,
            "station_name": f"电站 {station_id}",
            "timestamp": datetime.now().isoformat(),
            "active_power_kw": round(active_power_kw, 2),
            "daily_energy_kwh": round(capacity_kw * rng.uniform(2.5, 4.5), 2),
            "pr": round(rng.uniform(0.78, 0.92), 4),
            "health_score": round(rng.uniform(75, 98), 1),
        }

    async def get_metric_history(
        self,
        station_id: int,
        metric: str,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
        points: int = 144,
    ) -> List[Dict[str, Any]]:
        if end is None:
            end = datetime.now()
        if start is None:
            start = end - timedelta(days=1)
        rng = _seed(f"history-{station_id}-{metric}")
        delta = (end - start) / max(points - 1, 1)
        data = []
        for i in range(points):
            ts = start + delta * i
            hour = ts.hour + ts.minute / 60
            if metric == "active_power_kw":
                if 6 <= hour <= 18:
                    peak = ((hour - 6) / 12) * 800
                    value = max(0, peak + rng.uniform(-40, 40))
                else:
                    value = rng.uniform(0, 10)
            elif metric == "irradiance_w_m2":
                value = (
                    max(0, ((hour - 6) / 12) * 1000 + rng.uniform(-50, 50))
                    if 6 <= hour <= 18
                    else 0
                )
            elif metric == "daily_energy_kwh":
                value = rng.uniform(2000, 3500)
            elif metric == "dc_voltage_v":
                value = rng.uniform(200, 800)
            elif metric == "ambient_temp_c":
                value = rng.uniform(15, 35)
            else:
                value = rng.uniform(0, 100)
            data.append({"timestamp": ts.isoformat(), "value": round(value, 2)})
        return data

    async def get_station_overview(
        self, stations: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        overview = []
        for station in stations:
            sid = station["id"]
            capacity = station.get("capacity_kw") or 1000
            rng = _seed(f"overview-{sid}")
            theoretical = capacity * rng.uniform(3.8, 5.2)
            actual = theoretical * rng.uniform(0.75, 0.95)
            completion_rate = actual / theoretical if theoretical > 0 else 0
            overview.append(
                {
                    "station_id": sid,
                    "name": station.get("name") or f"电站 {sid}",
                    "capacity_kw": round(capacity, 2),
                    "daily_energy_kwh": round(actual, 2),
                    "completion_rate": round(completion_rate, 4),
                    "loss_kwh": round(max(0, theoretical - actual), 2),
                    "loss_cny": round(max(0, theoretical - actual) * 0.42, 2),
                    "health_score": round(rng.uniform(65, 99), 1),
                    "pr": round(rng.uniform(0.75, 0.92), 4),
                    "status": station.get("status") or "active",
                }
            )
        return overview

    async def get_efficiency(
        self, station_id: int, capacity_kw: float = 1000.0
    ) -> Dict[str, Any]:
        rng = _seed(f"eff-{station_id}")
        daily_energy = capacity_kw * rng.uniform(2.5, 4.5)
        pr = rng.uniform(0.78, 0.92)
        return {
            "station_id": station_id,
            "capacity_kw": round(capacity_kw, 2),
            "daily_energy_kwh": round(daily_energy, 2),
            "equivalent_hours": round(daily_energy / capacity_kw, 2) if capacity_kw else 0,
            "pr": round(pr, 4),
            "system_efficiency": round(pr * 100, 2),
        }

    async def get_loss_breakdown(
        self, station_id: int, capacity_kw: float = 1000.0
    ) -> Dict[str, Any]:
        rng = _seed(f"loss-{station_id}")
        theoretical = capacity_kw * rng.uniform(3.8, 5.2)
        actual = theoretical * rng.uniform(0.78, 0.92)
        total_loss = max(0, theoretical - actual)
        irradiance_loss = total_loss * rng.uniform(0.25, 0.40)
        efficiency_loss = total_loss * rng.uniform(0.20, 0.35)
        fault_loss = total_loss * rng.uniform(0.05, 0.15)
        other_loss = max(0, total_loss - irradiance_loss - efficiency_loss - fault_loss)
        return {
            "station_id": station_id,
            "theoretical_kwh": round(theoretical, 2),
            "actual_kwh": round(actual, 2),
            "total_loss_kwh": round(total_loss, 2),
            "total_loss_cny": round(total_loss * 0.42, 2),
            "breakdown": [
                {"name": "辐照损失", "kwh": round(irradiance_loss, 2), "cny": round(irradiance_loss * 0.42, 2)},
                {"name": "效率损失", "kwh": round(efficiency_loss, 2), "cny": round(efficiency_loss * 0.42, 2)},
                {"name": "故障损失", "kwh": round(fault_loss, 2), "cny": round(fault_loss * 0.42, 2)},
                {"name": "其他损失", "kwh": round(other_loss, 2), "cny": round(other_loss * 0.42, 2)},
            ],
        }

    async def get_health_trend(
        self, station_id: int, days: int = 30
    ) -> List[Dict[str, Any]]:
        rng = _seed(f"health-{station_id}")
        data = []
        end = datetime.now()
        for i in range(days):
            day = end - timedelta(days=days - 1 - i)
            data.append({
                "date": day.strftime("%Y-%m-%d"),
                "health_score": round(rng.uniform(70, 99), 1),
            })
        return data

    async def get_inverter_comparison(
        self, station_id: int, inverters: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        result = []
        for idx, inv in enumerate(inverters):
            rng = _seed(f"inv-{station_id}-{inv.get('inverter_id', idx)}")
            capacity = inv.get("capacity_kw") or 100
            active_power = capacity * rng.uniform(0.5, 0.85)
            daily_energy = capacity * rng.uniform(2.5, 4.5)
            result.append(
                {
                    "inverter_id": inv.get("inverter_id") or f"INV{idx+1:03d}",
                    "name": inv.get("name") or f"逆变器 {idx+1}",
                    "capacity_kw": round(capacity, 2),
                    "active_power_kw": round(active_power, 2),
                    "daily_energy_kwh": round(daily_energy, 2),
                    "utilization_rate": round(active_power / capacity, 4) if capacity else 0,
                    "status": inv.get("status") or "online",
                }
            )
        return result

    async def get_string_dispersion(
        self, station_id: int, strings: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        if not strings:
            return []
        rng = _seed(f"string-{station_id}")
        base = 5.0
        data = []
        for idx, s in enumerate(strings):
            current = base * (1 + rng.uniform(-0.08, 0.08))
            data.append(
                {
                    "string_id": s.get("string_id") or f"STR{idx+1:03d}",
                    "name": s.get("name") or f"组串 {idx+1}",
                    "inverter_id": s.get("inverter_id") or "INV001",
                    "current_a": round(current, 2),
                    "capacity_kw": s.get("capacity_kw") or 10,
                }
            )
        values = [d["current_a"] for d in data]
        avg = sum(values) / len(values)
        dispersion = (max(values) - min(values)) / avg if avg > 0 else 0
        for d in data:
            d["avg_current_a"] = round(avg, 2)
            d["dispersion_rate"] = round(dispersion, 4)
        return data