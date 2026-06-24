"""报告生成服务."""

from datetime import datetime, timedelta
from typing import Dict, List, Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal
from app.models.report import Report
from app.models.timeseries import InverterData
from app.services import alarm_service


async def generate_report(
    report_type: str,
    station_id: Optional[int] = None,
    created_by: str = "system",
) -> Report:
    """生成日报/周报/月报."""
    now = datetime.now()
    if report_type == "daily":
        start = now.replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=1)
        end = start + timedelta(days=1)
        title = f"日报 {start.strftime('%Y-%m-%d')}"
    elif report_type == "weekly":
        end = now.replace(hour=0, minute=0, second=0, microsecond=0)
        start = end - timedelta(days=7)
        title = f"周报 {start.strftime('%m.%d')}-{end.strftime('%m.%d')}"
    elif report_type == "monthly":
        end = now.replace(hour=0, minute=0, second=0, microsecond=0)
        start = end.replace(day=1) - timedelta(days=1)
        start = start.replace(day=1)
        title = f"月报 {start.strftime('%Y-%m')}"
    else:
        raise ValueError(f"不支持的报告类型: {report_type}")

    stats = await _calculate_stats(station_id, start, end)
    alarms = await alarm_service.list_alarms(station_id=station_id, status=None, limit=1000)
    alarm_count = len([a for a in alarms if start <= datetime.fromisoformat(a["created_at"]) < end])

    summary = (
        f"本周期总发电量 {stats['total_energy_kwh']:.2f} kWh，"
        f"平均 PR {stats['avg_pr'] * 100:.1f}% 。"
        f"共产生 {alarm_count} 条告警。"
    )

    async with AsyncSessionLocal() as session:
        report = Report(
            station_id=station_id,
            report_type=report_type,
            title=title,
            start_date=start,
            end_date=end,
            total_energy_kwh=stats["total_energy_kwh"],
            avg_pr=stats["avg_pr"],
            avg_health_score=stats["avg_health_score"],
            alarm_count=alarm_count,
            summary=summary,
            details=stats["daily_details"],
            created_by=created_by,
        )
        session.add(report)
        await session.commit()
        await session.refresh(report)
        return report


async def _calculate_stats(
    station_id: Optional[int],
    start: datetime,
    end: datetime,
) -> Dict:
    """计算周期统计."""
    async with AsyncSessionLocal() as session:
        query = select(
            func.strftime("%Y-%m-%d", InverterData.timestamp).label("day"),
            func.max(InverterData.daily_energy_kwh).label("daily_energy"),
            func.avg(InverterData.active_power_kw).label("avg_power"),
        ).where(
            InverterData.timestamp >= start,
            InverterData.timestamp < end,
        )
        if station_id:
            query = query.where(InverterData.station_id == station_id)

        result = await session.execute(
            query.group_by(func.strftime("%Y-%m-%d", InverterData.timestamp))
            .order_by(func.strftime("%Y-%m-%d", InverterData.timestamp))
        )
        rows = result.all()

    total_energy = sum(float(row.daily_energy or 0) for row in rows)
    daily_details = [
        {
            "date": row.day,
            "daily_energy_kwh": float(row.daily_energy or 0),
            "avg_power_kw": float(row.avg_power or 0),
        }
        for row in rows
    ]

    # 平均 PR：仅取白天有辐照的数据点
    avg_pr = await _calculate_avg_pr(station_id, start, end)
    avg_health = None

    return {
        "total_energy_kwh": total_energy,
        "avg_pr": avg_pr,
        "avg_health_score": avg_health,
        "daily_details": daily_details,
    }


async def _calculate_avg_pr(
    station_id: Optional[int],
    start: datetime,
    end: datetime,
) -> float:
    """计算平均 PR（简化版）."""
    async with AsyncSessionLocal() as session:
        query = select(
            InverterData.active_power_kw,
            InverterData.irradiance_w_m2,
        ).where(
            InverterData.timestamp >= start,
            InverterData.timestamp < end,
            InverterData.irradiance_w_m2 > 100,
        )
        if station_id:
            query = query.where(InverterData.station_id == station_id)

        result = await session.execute(query)
        rows = result.all()

        if not rows:
            return 0.0

        pr_values = []
        for row in rows:
            theoretical = row.irradiance_w_m2 / 1000 * 1000
            if theoretical > 0:
                pr_values.append(min(1.0, row.active_power_kw / theoretical))

        return sum(pr_values) / len(pr_values) if pr_values else 0.0


async def get_report(session: AsyncSession, report_id: int) -> Optional[Report]:
    """获取单条报告."""
    result = await session.execute(select(Report).where(Report.id == report_id))
    return result.scalar_one_or_none()


async def list_reports(
    session: AsyncSession,
    station_id: Optional[int] = None,
    report_type: Optional[str] = None,
    limit: int = 50,
) -> List[Report]:
    """获取报告列表."""
    query = select(Report)
    if station_id:
        query = query.where(Report.station_id == station_id)
    if report_type:
        query = query.where(Report.report_type == report_type)
    result = await session.execute(query.order_by(Report.created_at.desc()).limit(limit))
    return list(result.scalars().all())
