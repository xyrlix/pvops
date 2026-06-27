"""告警接口."""

from typing import List, Optional

from fastapi import APIRouter, Body, Depends, Query

from app.core.deps import get_current_user
from app.core.tenant import TenantContext, get_current_tenant
from app.services import alarm_service

router = APIRouter(dependencies=[Depends(get_current_user)])


@router.get("")
async def list_alarms(
    station_id: Optional[int] = Query(None),
    status: Optional[str] = Query(None),
    limit: int = Query(50),
    tenant: TenantContext = Depends(get_current_tenant),
) -> List[dict]:
    """获取告警列表（仅当前租户）."""
    return await alarm_service.list_alarms(
        station_id, status, limit, tenant_id=tenant.tenant_id
    )


@router.get("/summary")
async def get_alarm_summary(
    tenant: TenantContext = Depends(get_current_tenant),
) -> List[dict]:
    """告警聚合摘要（按规则/电站，仅当前租户）."""
    return await alarm_service.get_alarm_summary(tenant_id=tenant.tenant_id)


@router.post("/{alarm_id}/ack")
async def acknowledge_alarm(
    alarm_id: int,
    tenant: TenantContext = Depends(get_current_tenant),
) -> dict:
    """确认告警."""
    success = await alarm_service.acknowledge_alarm(
        alarm_id, tenant_id=tenant.tenant_id
    )
    return {"success": success}


@router.post("/{alarm_id}/close")
async def close_alarm(
    alarm_id: int,
    tenant: TenantContext = Depends(get_current_tenant),
) -> dict:
    """关闭告警."""
    success = await alarm_service.close_alarm(
        alarm_id, tenant_id=tenant.tenant_id
    )
    return {"success": success}


@router.post("/{alarm_id}/work-order")
async def create_work_order_from_alarm(
    alarm_id: int,
    assignee: Optional[str] = Body(None),
    tenant: TenantContext = Depends(get_current_tenant),
) -> dict:
    """根据告警创建工单."""
    result = await alarm_service.create_work_order_from_alarm(
        alarm_id, assignee, tenant_id=tenant.tenant_id
    )
    if result is None:
        return {"success": False, "message": "告警不存在或已有关联工单"}
    return {"success": True, "data": result}


@router.post("/check/{station_id}")
async def check_alarms(
    station_id: int,
    tenant: TenantContext = Depends(get_current_tenant),
) -> dict:
    """手动触发告警检查（生成的告警自动归属当前 tenant）."""
    new_alarms = await alarm_service.check_alarms(
        station_id, tenant_id=tenant.tenant_id
    )
    return {"new_alarms": len(new_alarms)}
