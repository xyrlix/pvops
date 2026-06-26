"""工单接口."""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.schemas.work_order import WorkOrderCreate, WorkOrderResponse, WorkOrderUpdate
from app.services import work_order_service

router = APIRouter(dependencies=[Depends(get_current_user)])


@router.get("", response_model=List[WorkOrderResponse])
async def list_work_orders(
    station_id: Optional[int] = None,
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
) -> List:
    """获取工单列表."""
    return await work_order_service.list_work_orders(db, station_id, status)


@router.post("", response_model=WorkOrderResponse, status_code=status.HTTP_201_CREATED)
async def create_work_order(
    data: WorkOrderCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """创建工单."""
    return await work_order_service.create_work_order(
        db,
        title=data.title,
        description=data.description,
        priority=data.priority,
        assignee=data.assignee,
        created_by=current_user.username,
        station_id=data.station_id,
        alarm_id=data.alarm_id,
    )


@router.get("/{work_order_id}", response_model=WorkOrderResponse)
async def get_work_order(
    work_order_id: int,
    db: AsyncSession = Depends(get_db),
) -> Optional:
    """获取工单详情."""
    work_order = await work_order_service.get_work_order(db, work_order_id)
    if not work_order:
        raise HTTPException(status_code=404, detail="工单不存在")
    return work_order


@router.put("/{work_order_id}", response_model=WorkOrderResponse)
async def update_work_order(
    work_order_id: int,
    data: WorkOrderUpdate,
    db: AsyncSession = Depends(get_db),
):
    """更新工单状态."""
    work_order = await work_order_service.update_work_order_status(
        db, work_order_id, data.status, data.feedback_comment, data.solution
    )
    if not work_order:
        raise HTTPException(status_code=404, detail="工单不存在")
    return work_order


@router.get("/{work_order_id}/timeline")
async def get_work_order_timeline(work_order_id: int):
    """获取工单处理时间线."""
    return await work_order_service.get_work_order_timeline(work_order_id)


@router.post("/{work_order_id}/archive-case")
async def archive_work_order_case(work_order_id: int):
    """将已完成工单沉淀为知识库案例."""
    result = await work_order_service.archive_case(work_order_id)
    if not result:
        raise HTTPException(status_code=400, detail="仅已完成的工单可沉淀案例")
    return result
