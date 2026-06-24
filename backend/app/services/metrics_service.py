"""指标计算服务."""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.database import AsyncSessionLocal
from app.models.device import Inverter, StringUnit
from app.models.station import Station
from app.models.timeseries import InverterData, WeatherData
from app.repositories import get_repository
from app.services.health import calculate_health_score
from app.services import mock_data

logger = logging.getLogger(__name__)


async def get_latest_station_metrics(station_id: int) -> Dict:
    """获取电站最新指标（通过统一仓库，空数据时可选 mock fallback）."""
    repo = get_repository()
    metrics = await repo.get_latest_station_metrics(station_id)
    settings = get_settings()
    if settings.use_mock_data and (metrics.get("active_power_kw") == 0 and metrics.get("daily_energy_kwh") == 0):
        capacity = await _get_station_capacity_from_db(station_id)
        mock = mock_data.mock_latest_station_metrics(station_id, capacity)
        metrics.update(mock)
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
    """获取指标历史（通过统一仓库，空数据时可选 mock fallback）."""
    repo = get_repository()
    data = await repo.get_metric_history(station_id, metric, start, end)
    settings = get_settings()
    if settings.use_mock_data and not data:
        return mock_data.mock_metric_history(station_id, metric, start, end)
    return data


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

DEFAULT_ELECTRICITY_PRICE = 0.42  # 元/kWh


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

        if not stations and get_settings().use_mock_data:
            station_dicts = [
                {"id": i, "name": f"演示电站 {i}", "capacity_kw": 500.0 * i, "status": "active"}
                for i in range(1, 7)
            ]
            return mock_data.mock_station_overview(station_dicts)

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


async def get_station_efficiency(station_id: int) -> Dict:
    """电站效率指标."""
    async with AsyncSessionLocal() as session:
        capacity = await _get_station_capacity(session, station_id)
        metrics = await get_latest_station_metrics(station_id)
        daily_energy = metrics.get("daily_energy_kwh") or 0
        pr = metrics.get("pr") or 0

        if get_settings().use_mock_data and daily_energy == 0:
            return mock_data.mock_efficiency(station_id, capacity)

        equivalent_hours = daily_energy / capacity if capacity > 0 else 0
        system_efficiency = pr * 100  # 简化

        return {
            "station_id": station_id,
            "capacity_kw": capacity,
            "daily_energy_kwh": daily_energy,
            "equivalent_hours": round(equivalent_hours, 2),
            "pr": round(pr, 4),
            "system_efficiency": round(system_efficiency, 2),
        }


async def get_station_losses(station_id: int) -> Dict:
    """损失分解（元/kWh）."""
    async with AsyncSessionLocal() as session:
        capacity = await _get_station_capacity(session, station_id)
        metrics = await get_latest_station_metrics(station_id)
        actual = metrics.get("daily_energy_kwh") or 0
        pr = metrics.get("pr") or 0

        if get_settings().use_mock_data and actual == 0:
            return mock_data.mock_loss_breakdown(station_id, capacity)

        theoretical = capacity * 5.0
        total_loss = max(0, theoretical - actual)

        # 简化分解
        irradiance_loss = theoretical * 0.15  # 辐照资源损失
        efficiency_loss = max(0, total_loss * (1 - pr)) if pr else 0
        fault_loss = total_loss * 0.1 if metrics.get("health_score", 100) < 80 else 0
        other_loss = max(0, total_loss - irradiance_loss - efficiency_loss - fault_loss)

        def to_cny(kwh: float) -> float:
            return round(kwh * DEFAULT_ELECTRICITY_PRICE, 2)

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

        if not rows and get_settings().use_mock_data:
            return mock_data.mock_health_trend(station_id, days)

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

        if not inverters and get_settings().use_mock_data:
            # 生成演示逆变器
            demo_inverters = [
                {"inverter_id": f"INV{i:03d}", "name": f"逆变器 {i}", "capacity_kw": 100.0, "status": "online"}
                for i in range(1, 7)
            ]
            return mock_data.mock_inverter_comparison(station_id, demo_inverters)

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

        if not strings and get_settings().use_mock_data:
            demo_strings = [
                {"string_id": f"STR{i:03d}", "name": f"组串 {i}", "inverter_id": inverter_id or "INV001", "capacity_kw": 10}
                for i in range(1, 13)
            ]
            return mock_data.mock_string_dispersion(station_id, demo_strings)

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
