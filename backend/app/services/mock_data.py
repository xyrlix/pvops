"""确定性模拟数据生成器（**已弃用** — 请使用 ``app.demo.MockDataProvider``）.

保留此文件仅为向后兼容：所有业务调用已迁移到 ``app.demo.get_data_provider()``。
新代码不应再 ``from app.services import mock_data``；后续会移除本模块。
"""

import hashlib
import random
from datetime import datetime, timedelta


def _seed(value: str) -> random.Random:
    """基于字符串生成固定随机数生成器."""
    hashed = hashlib.md5(value.encode("utf-8")).hexdigest()
    return random.Random(hashed)


def mock_latest_station_metrics(station_id: int, capacity_kw: float = 1000.0) -> dict:
    """模拟电站最新实时指标."""
    rng = _seed(f"latest-{station_id}-{datetime.now().strftime('%Y%m%d')}")
    # 白天功率曲线
    hour = datetime.now().hour + datetime.now().minute / 60
    if 6 <= hour <= 18:
        peak = ((hour - 6) / 12) * capacity_kw * 0.85
        active_power_kw = max(0, peak + rng.uniform(-capacity_kw * 0.05, capacity_kw * 0.05))
    else:
        active_power_kw = rng.uniform(0, capacity_kw * 0.02)

    daily_energy_kwh = capacity_kw * rng.uniform(2.5, 4.5)
    pr = rng.uniform(0.78, 0.92)
    health_score = rng.uniform(75, 98)

    return {
        "station_id": station_id,
        "station_name": f"电站 {station_id}",
        "timestamp": datetime.now().isoformat(),
        "active_power_kw": round(active_power_kw, 2),
        "daily_energy_kwh": round(daily_energy_kwh, 2),
        "pr": round(pr, 4),
        "health_score": round(health_score, 1),
    }


def mock_metric_history(
    station_id: int,
    metric: str,
    start: datetime | None = None,
    end: datetime | None = None,
    points: int = 144,
) -> list[dict]:
    """模拟指标历史曲线（功率/辐照/温度等）."""
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
            value = max(0, (hour - 6) / 12 * 1000 + rng.uniform(-50, 50)) if 6 <= hour <= 18 else 0
        elif metric == "daily_energy_kwh":
            value = rng.uniform(2000, 3500)
        elif metric in ("dc_voltage_v", "ambient_temp_c"):
            value = rng.uniform(200, 800) if metric == "dc_voltage_v" else rng.uniform(15, 35)
        else:
            value = rng.uniform(0, 100)
        data.append({"timestamp": ts.isoformat(), "value": round(value, 2)})
    return data


def mock_station_overview(stations: list[dict]) -> list[dict]:
    """模拟集团总览数据（用于气泡图/TOP榜）."""
    overview = []
    for station in stations:
        sid = station["id"]
        capacity = station.get("capacity_kw") or 1000
        rng = _seed(f"overview-{sid}")
        theoretical = capacity * rng.uniform(3.8, 5.2)
        actual = theoretical * rng.uniform(0.75, 0.95)
        completion_rate = actual / theoretical if theoretical > 0 else 0
        loss_kwh = max(0, theoretical - actual)
        loss_cny = loss_kwh * 0.42
        health_score = rng.uniform(65, 99)
        pr = rng.uniform(0.75, 0.92)

        overview.append(
            {
                "station_id": sid,
                "name": station.get("name") or f"电站 {sid}",
                "capacity_kw": round(capacity, 2),
                "daily_energy_kwh": round(actual, 2),
                "completion_rate": round(completion_rate, 4),
                "loss_kwh": round(loss_kwh, 2),
                "loss_cny": round(loss_cny, 2),
                "health_score": round(health_score, 1),
                "pr": round(pr, 4),
                "status": station.get("status") or "active",
            }
        )
    return overview


def mock_health_trend(station_id: int, days: int = 30) -> list[dict]:
    """模拟健康度趋势（用于热力图）."""
    rng = _seed(f"health-{station_id}")
    data = []
    end = datetime.now()
    for i in range(days):
        day = end - timedelta(days=days - 1 - i)
        score = rng.uniform(70, 99)
        data.append({"date": day.strftime("%Y-%m-%d"), "health_score": round(score, 1)})
    return data


def mock_inverter_comparison(station_id: int, inverters: list[dict]) -> list[dict]:
    """模拟逆变器群组对比."""
    result = []
    for idx, inv in enumerate(inverters):
        rng = _seed(f"inv-{station_id}-{inv.get('inverter_id', idx)}")
        capacity = inv.get("capacity_kw") or 100
        active_power = capacity * rng.uniform(0.5, 0.85)
        daily_energy = capacity * rng.uniform(2.5, 4.5)
        utilization = active_power / capacity if capacity > 0 else 0
        result.append(
            {
                "inverter_id": inv.get("inverter_id") or f"INV{idx+1:03d}",
                "name": inv.get("name") or f"逆变器 {idx+1}",
                "capacity_kw": round(capacity, 2),
                "active_power_kw": round(active_power, 2),
                "daily_energy_kwh": round(daily_energy, 2),
                "utilization_rate": round(utilization, 4),
                "status": inv.get("status") or "online",
            }
        )
    return result


def mock_string_dispersion(station_id: int, strings: list[dict]) -> list[dict]:
    """模拟组串电流离散."""
    if not strings:
        return []
    rng = _seed(f"string-{station_id}")
    base = 5.0
    data = []
    for idx, s in enumerate(strings):
        variation = rng.uniform(-0.08, 0.08)
        current = base * (1 + variation)
        data.append(
            {
                "string_id": s.get("string_id") or f"STR{idx+1:03d}",
                "name": s.get("name") or f"组串 {idx+1}",
                "inverter_id": s.get("inverter_id") or "INV001",
                "current_a": round(current, 2),
                "capacity_kw": s.get("capacity_kw") or 10,
            }
        )

    values = [float(d.get("current_a", 0) or 0) for d in data]
    avg = sum(values) / len(values)
    dispersion = (max(values) - min(values)) / avg if avg > 0 else 0
    for d in data:
        d["avg_current_a"] = round(avg, 2)
        d["dispersion_rate"] = round(dispersion, 4)
    return data


def mock_efficiency(station_id: int, capacity_kw: float = 1000.0) -> dict:
    """模拟电站效率指标."""
    rng = _seed(f"eff-{station_id}")
    daily_energy = capacity_kw * rng.uniform(2.5, 4.5)
    pr = rng.uniform(0.78, 0.92)
    equivalent_hours = daily_energy / capacity_kw if capacity_kw > 0 else 0
    system_efficiency = pr * 100
    return {
        "station_id": station_id,
        "capacity_kw": round(capacity_kw, 2),
        "daily_energy_kwh": round(daily_energy, 2),
        "equivalent_hours": round(equivalent_hours, 2),
        "pr": round(pr, 4),
        "system_efficiency": round(system_efficiency, 2),
    }


def mock_loss_breakdown(station_id: int, capacity_kw: float = 1000.0) -> dict:
    """模拟损失分解."""
    rng = _seed(f"loss-{station_id}")
    theoretical = capacity_kw * rng.uniform(3.8, 5.2)
    actual = theoretical * rng.uniform(0.78, 0.92)
    total_loss = max(0, theoretical - actual)

    irradiance_loss = total_loss * rng.uniform(0.25, 0.40)
    efficiency_loss = total_loss * rng.uniform(0.20, 0.35)
    fault_loss = total_loss * rng.uniform(0.05, 0.15)
    other_loss = max(0, total_loss - irradiance_loss - efficiency_loss - fault_loss)

    def to_cny(kwh: float) -> float:
        return round(kwh * 0.42, 2)

    return {
        "station_id": station_id,
        "theoretical_kwh": round(theoretical, 2),
        "actual_kwh": round(actual, 2),
        "total_loss_kwh": round(total_loss, 2),
        "total_loss_cny": to_cny(total_loss),
        "breakdown": [
            {"name": "辐照损失", "kwh": round(irradiance_loss, 2), "cny": to_cny(irradiance_loss)},
            {"name": "效率损失", "kwh": round(efficiency_loss, 2), "cny": to_cny(efficiency_loss)},
            {"name": "故障损失", "kwh": round(fault_loss, 2), "cny": to_cny(fault_loss)},
            {"name": "其他损失", "kwh": round(other_loss, 2), "cny": to_cny(other_loss)},
        ],
    }
