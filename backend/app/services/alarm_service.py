"""告警服务."""

import logging
from datetime import datetime, timedelta

from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal
from app.models.alarm import Alarm
from app.models.timeseries import InverterData
from app.models.work_order import WorkOrder

logger = logging.getLogger(__name__)


def _level_to_priority(level: str) -> str:
    return {"critical": "urgent", "warning": "high", "info": "medium"}.get(level, "medium")


async def check_alarms(station_id: int, tenant_id: int | None = None) -> list[Alarm]:
    """检查并生成告警（生成的告警归属指定 tenant）."""
    new_alarms = []

    async with AsyncSessionLocal() as session:
        # 获取最近数据
        result = await session.execute(
            select(InverterData)
            .where(InverterData.station_id == station_id)
            .order_by(desc(InverterData.id))
            .limit(10)
        )
        recent_data = result.scalars().all()

        if not recent_data:
            return []

        latest = recent_data[0]

        # 规则 1：白天有辐照但功率为 0
        if latest.irradiance_w_m2 > 200 and latest.active_power_kw < 1:
            alarm = await _create_or_update_alarm(
                session,
                station_id,
                latest.inverter_id,
                "critical",
                "发电异常：辐照充足但无功率",
                f"逆变器 {latest.inverter_id} 辐照 {latest.irradiance_w_m2:.1f} W/m²，但功率为 {latest.active_power_kw:.2f} kW",
                "power_zero_when_sunny",
                tenant_id=tenant_id,
            )
            if alarm:
                new_alarms.append(alarm)

        # 规则 2：故障码非 0
        if latest.fault_code and latest.fault_code > 0:
            alarm = await _create_or_update_alarm(
                session,
                station_id,
                latest.inverter_id,
                "critical",
                f"逆变器故障码：{latest.fault_code}",
                f"逆变器 {latest.inverter_id} 上报故障码 {latest.fault_code}",
                "fault_code",
            )
            if alarm:
                new_alarms.append(alarm)

        # 规则 3：PR 过低（白天）
        if latest.irradiance_w_m2 > 500:
            theoretical = latest.irradiance_w_m2 / 1000 * 1000
            pr = latest.active_power_kw / theoretical if theoretical > 0 else 1
            if pr < 0.5:
                alarm = await _create_or_update_alarm(
                    session,
                    station_id,
                    latest.inverter_id,
                    "warning",
                    "PR 偏低",
                    f"逆变器 {latest.inverter_id} PR 为 {pr*100:.1f}%，低于 50%",
                    "low_pr",
                    tenant_id=tenant_id,
                )
                if alarm:
                    new_alarms.append(alarm)

        await session.commit()

    return new_alarms


async def _create_or_update_alarm(
    session: AsyncSession,
    station_id: int,
    device_id: str,
    level: str,
    title: str,
    description: str,
    rule_name: str,
    tenant_id: int | None = None,
) -> Alarm | None:
    """创建或更新告警（避免重复）."""
    one_hour_ago = datetime.now() - timedelta(hours=1)
    query = _apply_tenant_filter(
        select(Alarm).where(
            Alarm.station_id == station_id,
            Alarm.device_id == device_id,
            Alarm.rule_name == rule_name,
            Alarm.status.in_(["open", "acknowledged"]),
            Alarm.created_at >= one_hour_ago,
        ),
        tenant_id,
    )
    result = await session.execute(query.order_by(desc(Alarm.id)).limit(1))
    existing = result.scalar_one_or_none()

    if existing:
        existing.description = description
        existing.created_at = datetime.now()
        return None

    alarm = Alarm(
        station_id=station_id,
        device_id=device_id,
        level=level,
        priority=_level_to_priority(level),
        title=title,
        description=description,
        rule_name=rule_name,
        tenant_id=tenant_id,
        status="open",
    )
    session.add(alarm)
    return alarm


def _apply_tenant_filter(query, tenant_id: int | None):
    """给 alarm query 注入 tenant_id 过滤；tenant_id=None 时跳过（超管）."""
    if tenant_id is None:
        return query
    return query.where(Alarm.tenant_id == tenant_id)


async def list_alarms(
    station_id: int | None = None,
    status: str | None = None,
    limit: int = 50,
    tenant_id: int | None = None,
) -> list[dict]:
    """获取告警列表（按 tenant 过滤）."""
    async with AsyncSessionLocal() as session:
        query = _apply_tenant_filter(select(Alarm), tenant_id)
        if station_id:
            query = query.where(Alarm.station_id == station_id)
        if status:
            query = query.where(Alarm.status == status)

        result = await session.execute(query.order_by(desc(Alarm.created_at)).limit(limit))
        alarms = result.scalars().all()

        return [
            {
                "id": a.id,
                "station_id": a.station_id,
                "device_id": a.device_id,
                "level": a.level,
                "priority": a.priority,
                "title": a.title,
                "description": a.description,
                "rule_name": a.rule_name,
                "status": a.status,
                "created_at": a.created_at.isoformat() if a.created_at else "",
            }
            for a in alarms
        ]


async def get_alarm_summary(tenant_id: int | None = None) -> list[dict]:
    """按规则聚合未处理告警（按 tenant 过滤）."""
    async with AsyncSessionLocal() as session:
        query = _apply_tenant_filter(
            select(
                Alarm.rule_name,
                Alarm.level,
                Alarm.station_id,
                func.count(Alarm.id).label("count"),
                func.max(Alarm.created_at).label("latest_at"),
            ).where(Alarm.status.in_(["open", "acknowledged"])),
            tenant_id,
        )
        result = await session.execute(
            query.group_by(Alarm.rule_name, Alarm.level, Alarm.station_id).order_by(desc("count"))
        )
        rows = result.all()
        return [
            {
                "rule_name": row.rule_name or "未知规则",
                "level": row.level,
                "station_id": row.station_id,
                "count": row.count,
                "latest_at": row.latest_at.isoformat() if row.latest_at else "",
            }
            for row in rows
        ]


async def acknowledge_alarm(alarm_id: int, tenant_id: int | None = None) -> bool:
    """确认告警（跨租户返回 False）."""
    async with AsyncSessionLocal() as session:
        query = _apply_tenant_filter(select(Alarm), tenant_id).where(Alarm.id == alarm_id)
        result = await session.execute(query)
        alarm = result.scalar_one_or_none()
        if not alarm or alarm.status == "closed":
            return False
        alarm.status = "acknowledged"
        await session.commit()
        return True


async def close_alarm(alarm_id: int, tenant_id: int | None = None) -> bool:
    """关闭告警（跨租户返回 False）."""
    async with AsyncSessionLocal() as session:
        query = _apply_tenant_filter(select(Alarm), tenant_id).where(Alarm.id == alarm_id)
        result = await session.execute(query)
        alarm = result.scalar_one_or_none()
        if not alarm:
            return False
        alarm.status = "closed"
        alarm.resolved_at = datetime.now()
        await session.commit()
        return True


async def create_work_order_from_alarm(
    alarm_id: int,
    assignee: str | None = None,
    tenant_id: int | None = None,
) -> dict | None:
    """根据告警创建工单（跨租户返回 None）."""
    async with AsyncSessionLocal() as session:
        alarm_q = _apply_tenant_filter(select(Alarm), tenant_id).where(Alarm.id == alarm_id)
        result = await session.execute(alarm_q)
        alarm = result.scalar_one_or_none()
        if not alarm:
            return None

        # 避免重复创建：已有未关闭关联工单则返回
        wo_q = _apply_tenant_filter(
            select(WorkOrder).where(
                WorkOrder.alarm_id == alarm_id,
                WorkOrder.status.in_(["pending", "in_progress"]),
            ),
            tenant_id,
        )
        existing = await session.execute(wo_q)
        if existing.scalar_one_or_none():
            return None

        if alarm.status == "open":
            alarm.status = "acknowledged"

        work_order = WorkOrder(
            title=f"处理告警：{alarm.title}",
            description=alarm.description,
            priority=alarm.priority or _level_to_priority(alarm.level),
            assignee=assignee,
            station_id=alarm.station_id,
            alarm_id=alarm.id,
            tenant_id=tenant_id,
            status="pending",
            feedback=[],
        )
        session.add(work_order)
        await session.commit()
        await session.refresh(work_order)
        return {
            "work_order_id": work_order.id,
            "alarm_id": alarm.id,
            "status": work_order.status,
        }
