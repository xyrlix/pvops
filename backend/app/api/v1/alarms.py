"""告警接口."""

from typing import List, Optional

from fastapi import APIRouter, Body, Depends, Query

from app.core.deps import get_current_user
from app.services import alarm_service

router = APIRouter(dependencies=[Depends(get_current_user)])


@router.get("")
async def list_alarms(
    station_id: Optional[int] = Query(None),
    status: Optional[str] = Query(None),
    limit: int = Query(50),
) -> List[dict]:
    """获取告警列表."""
    return await alarm_service.list_alarms(station_id, status, limit)


@router.get("/summary")
async def get_alarm_summary() -> List[dict]:
    """告警聚合摘要（按规则/电站）."""
    return await alarm_service.get_alarm_summary()


@router.post("/{alarm_id}/ack")
async def acknowledge_alarm(alarm_id: int) -> dict:
    """确认告警."""
    success = await alarm_service.acknowledge_alarm(alarm_id)
    return {"success": success}


@router.post("/{alarm_id}/close")
async def close_alarm(alarm_id: int) -> dict:
    """关闭告警."""
    success = await alarm_service.close_alarm(alarm_id)
    return {"success": success}


@router.post("/{alarm_id}/work-order")
async def create_work_order_from_alarm(
    alarm_id: int,
    assignee: Optional[str] = Body(None),
) -> dict:
    """根据告警创建工单."""
    result = await alarm_service.create_work_order_from_alarm(alarm_id, assignee)
    if result is None:
        return {"success": False, "message": "告警不存在或已有关联工单"}
    return {"success": True, "data": result}


@router.post("/check/{station_id}")
async def check_alarms(station_id: int) -> dict:
    """手动触发告警检查."""
    new_alarms = await alarm_service.check_alarms(station_id)
    return {"new_alarms": len(new_alarms)}
