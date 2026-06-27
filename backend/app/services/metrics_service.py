"""指标计算服务."""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.database import AsyncSessionLocal
from app.demo import get_data_provider
from app.models.device import Inverter, StringUnit
from app.models.station import Station
from app.models.timeseries import InverterData, WeatherData
from app.repositories import get_repository
from app.services.health import calculate_health_score

logger = logging.getLogger(__name__)


async def get_latest_station_metrics(station_id: int) -> Dict:
    """获取电站最新指标.

    通过 ``DataProvider`` 获取，provider 内部决定 mock / real。
    当 provider 为 RealDataProvider 且真实数据全 0 时，本函数显式触发
    fallback：填充 ``health_score`` 等计算字段以避免下游 None 异常。
    """
    capacity = await _get_station_capacity_from_db(station_id)
    provider = get_data_provider()
    metrics = await provider.get_latest_station_metrics(station_id, capacity)

    # 真实模式 + 全零数据：补齐 health_score 等下游字段
    if metrics.get("active_power_kw", 0) == 0 and metrics.get("daily_energy_kwh", 0) == 0:
        metrics.setdefault("health_score", 100.0)
        metrics.setdefault("pr", 0.0)
        metrics.setdefault("timestamp", datetime.now().isoformat())
        metrics.setdefault("station_name", f"电站 {station_id}")
    return metrics


async def _get_station_capacity_from_db(station_id: int) -> float:
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Station.capacity_kw).where(Station.id == station_id)
        )
        return float(result.scalar_one_or_none() or 1000)


async def get_metric_history(
    station_id: int,
    metric: str,
    start: Optional[datetime] = None,
    end: Optional[datetime] = None,
) -> List[Dict]:
    """获取指标历史曲线."""
    provider = get_data_provider()
    return await provider.get_metric_history(station_id, metric, start, end)


async def get_daily_energy(station_id: int, date: Optional[datetime] = None) -> float:
    """获取某日发电量（通过统一仓库）."""
    repo = get_repository()
    return await repo.get_daily_energy(station_id, date)


async def insert_inverter_data(data: Dict) -> None:
    """插入逆变器数据（通过统一仓库）."""
    repo = get_repository()
    await repo.insert_inverter_data(
        data.get("station_id", 0),
        data.get("inverter_id", "INV001"),
        data,
    )


async def insert_weather_data(data: Dict) -> None:
    """插入气象数据（通过统一仓库）."""
    repo = get_repository()
    await repo.insert_weather_data(
        data.get("station_id", 0),
        data.get("device_id", "WS001"),
        data,
    )


async def batch_insert_inverter_data(data_list: List[Dict]) -> int:
    """批量插入逆变器数据（通过统一仓库）."""
    repo = get_repository()
    return await repo.batch_insert_inverter_data(data_list)


# ---------------------------------------------------------------------------
# 高级指标（对标竞品大屏）
# ---------------------------------------------------------------------------

DEFAULT_ELECTRICITY_PRICE = 0.42  # 元/kWh（可通过 .env ELECTRICITY_PRICE 覆盖）


_ELECTRICITY_PRICE: Optional[float] = None


def _get_price() -> float:
    """获取电价（优先 env，回退 0.42 元/kWh）."""
    import os
    global _ELECTRICITY_PRICE
    if _ELECTRICITY_PRICE is None:
        try:
            _ELECTRICITY_PRICE = float(os.getenv("ELECTRICITY_PRICE", "0.42"))
        except (ValueError, TypeError):
            _ELECTRICITY_PRICE = 0.42
    return _ELECTRICITY_PRICE


# 温度系数（晶硅典型值 -0.0045 / °C，可通过 .env PV_TEMP_COEFF 覆盖）
_TEMP_COEFF: Optional[float] = None


def _get_temp_coeff() -> float:
    import os
    global _TEMP_COEFF
    if _TEMP_COEFF is None:
        try:
            _TEMP_COEFF = float(os.getenv("PV_TEMP_COEFF", "-0.0045"))
        except (ValueError, TypeError):
            _TEMP_COEFF = -0.0045
    return _TEMP_COEFF


def _pr_with_temp_correction(
    actual_energy_kwh: float,
    irradiance_kwh_m2: float,
    capacity_kw: float,
    avg_module_temp: float = 25.0,
) -> float:
    """PR 温度修正公式（IEEE 1547 / IEC 61724）.

    PR = E_actual / (GHI * P / G_stc)
    PR_corrected = PR / (1 + γ * (T_module - 25))

    其中:
    - E_actual: 实际发电量 (kWh)
    - GHI: 总水平辐射量 (kWh/m²)
    - P: 标称直流容量 (kWp)
    - G_stc: 标准辐照 1 kW/m²
    - γ: 温度系数（默认 -0.0045 / °C）
    - T_module: 组件温度（无实测时 = 环境温度 + 25°C 经验估值）
    """
    if capacity_kw <= 0 or irradiance_kwh_m2 <= 0:
        return 0.0
    # 标准 PR
    theoretical = irradiance_kwh_m2 * capacity_kw
    pr = actual_energy_kwh / theoretical if theoretical > 0 else 0.0
    # 温度修正
    gamma = _get_temp_coeff()
    t_diff = avg_module_temp - 25.0
    correction = 1.0 + gamma * t_diff
    if correction <= 0:
        return pr
    return min(pr / correction, 1.0)  # 上限 1.0


async def _get_station_capacity(session: AsyncSession, station_id: int) -> float:
    result = await session.execute(
        select(Station.capacity_kw).where(Station.id == station_id)
    )
    return float(result.scalar_one_or_none() or 0)


async def get_stations_overview() -> List[Dict]:
    """集团总览：用于气泡图/TOP榜."""
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Station))
        stations = result.scalars().all()

        provider = get_data_provider()

        if not stations:
            # 没有真实电站：演示电站字典喂给 provider（mock 模式会生成随机数；
            # real 模式只透传字段，前端会显示 PvEmpty）。
            station_dicts = [
                {"id": i, "name": f"演示电站 {i}", "capacity_kw": 500.0 * i, "status": "active"}
                for i in range(1, 7)
            ]
            return await provider.get_station_overview(station_dicts)

        overview = []
        for station in stations:
            metrics = await get_latest_station_metrics(station.id)
            capacity = station.capacity_kw or 1
            actual = metrics.get("daily_energy_kwh") or 0
            theoretical = capacity * 5.0
            completion_rate = min(1.0, actual / theoretical) if theoretical > 0 else 0
            loss_kwh = max(0, theoretical - actual)
            loss_cny = loss_kwh * DEFAULT_ELECTRICITY_PRICE

            overview.append(
                {
                    "station_id": station.id,
                    "name": station.name,
                    "capacity_kw": capacity,
                    "daily_energy_kwh": actual,
                    "completion_rate": round(completion_rate, 4),
                    "loss_kwh": round(loss_kwh, 2),
                    "loss_cny": round(loss_cny, 2),
                    "health_score": metrics.get("health_score") or 100,
                    "pr": metrics.get("pr") or 0,
                    "status": station.status,
                }
            )
        return overview


async def get_stations_ranking(metric: str = "health_score", limit: int = 10) -> List[Dict]:
    """电站排名."""
    overview = await get_stations_overview()
    reverse = metric not in ("loss_cny", "loss_kwh")
    overview.sort(key=lambda x: x.get(metric, 0) or 0, reverse=reverse)
    return overview[:limit]


async def get_station_peer_baseline(station_id: int) -> Dict:
    """获取同容量档位的群体基线（中位数 + top quartile）.

    复用 get_stations_overview 拿到全集团快照，喂给 provider.get_peer_baseline 计算。
    """
    overview = await get_stations_overview()
    target = next((s for s in overview if s.get("station_id") == station_id), None)
    if target is None:
        return {
            "capacity_bucket": "未知",
            "sample_size": 0,
            "median_pr": None,
            "median_completion_rate": None,
            "median_health_score": None,
            "median_daily_energy_per_kw": None,
            "top_quartile_pr": None,
            "self": None,
        }
    capacity_kw = target.get("capacity_kw") or 0
    provider = get_data_provider()
    baseline = await provider.get_peer_baseline(overview, capacity_kw)
    baseline["self"] = {
        "station_id": station_id,
        "name": target.get("name"),
        "pr": target.get("pr"),
        "completion_rate": target.get("completion_rate"),
        "health_score": target.get("health_score"),
        "daily_energy_per_kw": (target.get("daily_energy_kwh") or 0) / max(capacity_kw, 1),
    }
    return baseline


async def get_station_peer_ranking(station_id: int, metric: str = "health_score") -> Dict:
    """获取同档位内电站排名（高亮本电站位置）."""
    overview = await get_stations_overview()
    provider = get_data_provider()
    ranking = await provider.get_peer_ranking(overview, metric)
    return {
        "metric": metric,
        "self_rank": next(
            (r for r in ranking if r.get("station_id") == station_id), None
        ),
        "ranking": ranking,
    }


async def get_station_efficiency(station_id: int) -> Dict:
    """电站效率指标（PR 按 IEEE 61724 温度修正，等效小时按实际/装机）."""
    async with AsyncSessionLocal() as session:
        capacity = await _get_station_capacity(session, station_id)
        metrics = await get_latest_station_metrics(station_id)
        daily_energy = metrics.get("daily_energy_kwh") or 0
        pr_raw = metrics.get("pr") or 0

        provider = get_data_provider()
        if daily_energy == 0:
            return await provider.get_efficiency(station_id, capacity)

        # 等效小时 = 实际发电 / 装机容量
        equivalent_hours = daily_energy / capacity if capacity > 0 else 0

        # 估算日总辐照（kWh/m²）：基于 pr_raw 和 daily_energy 反推
        # 当 pr_raw 有值时使用，否则使用默认值
        if pr_raw > 0 and capacity > 0:
            # 从 daily_energy / (pr * capacity) 反推日辐照
            daily_irradiance = daily_energy / (pr_raw * capacity)
        else:
            daily_irradiance = 4.5  # 中国平均等效日照小时（kWh/m²/day）

        # 组件温度估算：环境温度 + 25°C（经验估，无实测时）
        avg_module_temp = metrics.get("avg_module_temp_c", metrics.get("ambient_temp_c", 25)) + 25

        # 温度修正 PR
        pr_corrected = _pr_with_temp_correction(
            daily_energy, daily_irradiance, capacity, avg_module_temp
        )

        system_efficiency = pr_corrected * 100

        return {
            "station_id": station_id,
            "capacity_kw": capacity,
            "daily_energy_kwh": daily_energy,
            "equivalent_hours": round(equivalent_hours, 2),
            "pr": round(pr_corrected, 4),
            "pr_raw": round(pr_raw, 4),
            "system_efficiency": round(system_efficiency, 2),
            "daily_irradiance": round(daily_irradiance, 2),
            "temp_coefficient": _get_temp_coeff(),
        }


async def get_station_losses(station_id: int) -> Dict:
    """损失分解（元/kWh）."""
    async with AsyncSessionLocal() as session:
        capacity = await _get_station_capacity(session, station_id)
        metrics = await get_latest_station_metrics(station_id)
        actual = metrics.get("daily_energy_kwh") or 0
        pr = metrics.get("pr") or 0

        provider = get_data_provider()
        if actual == 0:
            return await provider.get_loss_breakdown(station_id, capacity)

        theoretical = capacity * 5.0
        total_loss = max(0, theoretical - actual)

        # 简化分解
        irradiance_loss = theoretical * 0.15  # 辐照资源损失
        efficiency_loss = max(0, total_loss * (1 - pr)) if pr else 0
        fault_loss = total_loss * 0.1 if metrics.get("health_score", 100) < 80 else 0
        other_loss = max(0, total_loss - irradiance_loss - efficiency_loss - fault_loss)

        price = _get_price()

        def to_cny(kwh: float) -> float:
            return round(kwh * price, 2)

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


async def get_health_trend(station_id: int, days: int = 30) -> List[Dict]:
    """健康度趋势（用于热力图）."""
    async with AsyncSessionLocal() as session:
        end = datetime.now()
        start = end - timedelta(days=days)
        result = await session.execute(
            select(
                func.strftime("%Y-%m-%d", InverterData.timestamp).label("day"),
                func.avg(InverterData.active_power_kw).label("avg_power"),
                func.max(InverterData.irradiance_w_m2).label("max_irradiance"),
                func.max(InverterData.fault_code).label("max_fault"),
            )
            .where(
                InverterData.station_id == station_id,
                InverterData.timestamp >= start,
                InverterData.timestamp <= end,
            )
            .group_by(func.strftime("%Y-%m-%d", InverterData.timestamp))
            .order_by(func.strftime("%Y-%m-%d", InverterData.timestamp))
        )
        rows = result.all()

        if not rows:
            provider = get_data_provider()
            return await provider.get_health_trend(station_id, days)

        data = []
        for row in rows:
            score = 100.0
            if row.max_irradiance and row.max_irradiance > 200:
                if row.avg_power and row.avg_power < row.max_irradiance / 1000 * 1000 * 0.2:
                    score -= 40
            if row.max_fault and row.max_fault > 0:
                score -= 30
            score = max(0, min(100, score))
            data.append({"date": row.day, "health_score": round(score, 1)})
        return data


async def get_inverter_comparison(station_id: int) -> List[Dict]:
    """逆变器群组对比."""
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Inverter).where(Inverter.station_id == station_id)
        )
        inverters = result.scalars().all()

        if not inverters:
            provider = get_data_provider()
            demo_inverters = [
                {"inverter_id": f"INV{i:03d}", "name": f"逆变器 {i}", "capacity_kw": 100.0, "status": "online"}
                for i in range(1, 7)
            ]
            return await provider.get_inverter_comparison(station_id, demo_inverters)

        if not inverters:
            return []

        comparison = []
        for inv in inverters:
            latest = await session.execute(
                select(InverterData)
                .where(
                    InverterData.station_id == station_id,
                    InverterData.inverter_id == inv.inverter_id,
                )
                .order_by(desc(InverterData.id))
                .limit(1)
            )
            record = latest.scalar_one_or_none()

            active_power = record.active_power_kw if record else inv.capacity_kw * (0.5 + 0.3 * hash(inv.inverter_id) % 10 / 10)
            daily_energy = record.daily_energy_kwh if record else inv.capacity_kw * 3.5
            utilization = active_power / inv.capacity_kw if inv.capacity_kw > 0 else 0

            comparison.append(
                {
                    "inverter_id": inv.inverter_id,
                    "name": inv.name,
                    "capacity_kw": inv.capacity_kw,
                    "active_power_kw": round(active_power, 2),
                    "daily_energy_kwh": round(daily_energy, 2),
                    "utilization_rate": round(utilization, 4),
                    "status": inv.status,
                }
            )
        return comparison


async def get_string_dispersion(
    station_id: int, inverter_id: Optional[str] = None
) -> List[Dict]:
    """组串离散率."""
    async with AsyncSessionLocal() as session:
        query = select(StringUnit).where(StringUnit.station_id == station_id)
        if inverter_id:
            query = query.where(StringUnit.inverter_id == inverter_id)
        result = await session.execute(query)
        strings = result.scalars().all()

        if not strings:
            provider = get_data_provider()
            demo_strings = [
                {"string_id": f"STR{i:03d}", "name": f"组串 {i}", "inverter_id": inverter_id or "INV001", "capacity_kw": 10}
                for i in range(1, 13)
            ]
            return await provider.get_string_dispersion(station_id, demo_strings)

        data = []
        for s in strings:
            # 模拟组串电流（带随机离散）
            base = 5.0
            variation = ((hash(s.string_id) % 100) - 50) / 1000  # -0.05 ~ 0.05
            current = base * (1 + variation)
            data.append(
                {
                    "string_id": s.string_id,
                    "name": s.name,
                    "inverter_id": s.inverter_id,
                    "current_a": round(current, 2),
                    "capacity_kw": s.capacity_kw,
                }
            )

        if data:
            values = [d["current_a"] for d in data]
            avg = sum(values) / len(values)
            dispersion = (max(values) - min(values)) / avg if avg > 0 else 0
            for d in data:
                d["avg_current_a"] = round(avg, 2)
                d["dispersion_rate"] = round(dispersion, 4)
        return data
