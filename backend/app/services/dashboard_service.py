"""Dashboard 聚合数据服务.

优先使用真实数据（Station/Alarm/TSDB），数据不足时调用 mock_data 补齐。
"""

import logging
from typing import Dict, List

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.database import AsyncSessionLocal
from app.models.alarm import Alarm
from app.models.station import Station
from app.services import mock_data, metrics_service

logger = logging.getLogger(__name__)

DEFAULT_ELECTRICITY_PRICE = 0.42


async def _list_stations(session: AsyncSession) -> List[Station]:
    result = await session.execute(select(Station))
    return list(result.scalars().all())


async def get_dashboard_overview() -> Dict:
    """总览大屏顶部 KPI."""
    async with AsyncSessionLocal() as session:
        stations = await _list_stations(session)
        total_capacity = sum((s.capacity_kw or 0) for s in stations)

        # 实时功率 / 日发电：优先用 TSDB，否则 mock
        total_power = 0.0
        total_energy = 0.0
        for s in stations:
            metrics = await metrics_service.get_latest_station_metrics(s.id)
            total_power += metrics.get("active_power_kw") or 0
            total_energy += metrics.get("daily_energy_kwh") or 0

        # 告警统计
        alarm_counts = {"urgent": 0, "high": 0, "medium": 0, "low": 0}
        for s in stations:
            stats = await get_alarm_stats(s.id)
            for k in alarm_counts:
                alarm_counts[k] += stats.get(k, 0)

        online = sum(1 for s in stations if s.status == "active")

        return {
            "station_count": len(stations),
            "online_count": online,
            "offline_count": len(stations) - online,
            "total_capacity_kw": round(total_capacity, 2),
            "total_active_power_kw": round(total_power, 2),
            "total_daily_energy_kwh": round(total_energy, 2),
            "alarm_summary": alarm_counts,
            "system_health": round(85 + (online / max(len(stations), 1)) * 10, 1),
        }


async def get_stations_overview() -> List[Dict]:
    """集团场站分布（气泡图/TOP榜）."""
    async with AsyncSessionLocal() as session:
        stations = await _list_stations(session)
        station_dicts = [
            {
                "id": s.id,
                "name": s.name,
                "capacity_kw": s.capacity_kw or 0,
                "status": s.status or "active",
            }
            for s in stations
        ]

        if not station_dicts:
            # 完全没有电站时给一组演示数据
            station_dicts = [
                {"id": i, "name": f"演示电站 {i}", "capacity_kw": 500.0 * i, "status": "active"}
                for i in range(1, 7)
            ]

        settings = get_settings()
        if settings.use_mock_data:
            return mock_data.mock_station_overview(station_dicts)

        # 真实数据路径：复用 metrics_service 中的 overview 计算
        return await metrics_service.get_stations_overview()


async def get_risk_top_stations(limit: int = 5) -> List[Dict]:
    """高风险场站 TOP."""
    overview = await get_stations_overview()
    overview.sort(key=lambda x: x.get("health_score", 100))
    return overview[:limit]


async def get_alarm_stats(station_id: int = None) -> Dict:
    """告警统计."""
    async with AsyncSessionLocal() as session:
        query = select(Alarm.level, func.count(Alarm.id)).where(Alarm.status == "open")
        if station_id:
            query = query.where(Alarm.station_id == station_id)
        result = await session.execute(query.group_by(Alarm.level))
        rows = result.all()

        mapping = {"critical": "urgent", "warning": "high", "info": "medium"}
        stats = {"urgent": 0, "high": 0, "medium": 0, "low": 0}
        for level, count in rows:
            key = mapping.get(level, "medium")
            stats[key] = count
        return stats


async def get_ai_insight() -> str:
    """生成 AI 洞察文本."""
    overview = await get_stations_overview()
    if not overview:
        return "正在分析集团电站运行数据..."

    total = len(overview)
    abnormal = sum(1 for s in overview if (s.get("health_score") or 100) < 80)
    total_loss = sum(s.get("loss_cny", 0) for s in overview)
    worst = min(overview, key=lambda x: x.get("health_score", 100))

    return (
        f"集团共 {total} 座场站，{abnormal} 座健康度低于 80 分，"
        f"今日预计损失金额 ¥{total_loss:.0f}。"
        f"建议优先处理 [{worst.get('name')}]（健康度 {worst.get('health_score', 0):.0f} 分）。"
    )
