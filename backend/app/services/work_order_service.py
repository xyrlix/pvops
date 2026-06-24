"""工单服务."""

from datetime import datetime
from typing import Dict, List, Optional

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.work_order import WorkOrder
from app.services import knowledge_service


async def create_work_order(
    session: AsyncSession,
    title: str,
    description: Optional[str] = None,
    priority: str = "medium",
    assignee: Optional[str] = None,
    created_by: Optional[str] = None,
    station_id: Optional[int] = None,
    alarm_id: Optional[int] = None,
) -> WorkOrder:
    """创建工单."""
    work_order = WorkOrder(
        title=title,
        description=description,
        priority=priority,
        assignee=assignee,
        created_by=created_by,
        station_id=station_id,
        alarm_id=alarm_id,
        status="pending",
        feedback=[],
    )
    session.add(work_order)
    await session.commit()
    await session.refresh(work_order)
    return work_order


async def list_work_orders(
    session: AsyncSession,
    station_id: Optional[int] = None,
    status: Optional[str] = None,
    limit: int = 100,
) -> List[WorkOrder]:
    """获取工单列表."""
    query = select(WorkOrder)
    if station_id:
        query = query.where(WorkOrder.station_id == station_id)
    if status:
        query = query.where(WorkOrder.status == status)
    result = await session.execute(query.order_by(desc(WorkOrder.created_at)).limit(limit))
    return list(result.scalars().all())


async def get_work_order(session: AsyncSession, work_order_id: int) -> Optional[WorkOrder]:
    """获取工单详情."""
    result = await session.execute(select(WorkOrder).where(WorkOrder.id == work_order_id))
    return result.scalar_one_or_none()


async def update_work_order_status(
    session: AsyncSession,
    work_order_id: int,
    status: str,
    comment: Optional[str] = None,
    solution: Optional[str] = None,
) -> Optional[WorkOrder]:
    """更新工单状态并追加反馈."""
    result = await session.execute(select(WorkOrder).where(WorkOrder.id == work_order_id))
    work_order = result.scalar_one_or_none()
    if not work_order:
        return None

    work_order.status = status
    if solution:
        work_order.description = f"{work_order.description or ''}\n\n【解决方案】\n{solution}".strip()

    feedback = list(work_order.feedback or [])
    feedback.append(
        {
            "status": status,
            "comment": comment or "",
            "solution": solution or "",
            "created_at": datetime.now().isoformat(),
        }
    )
    work_order.feedback = feedback
    work_order.updated_at = datetime.now()
    await session.commit()
    await session.refresh(work_order)
    return work_order


async def get_work_order_timeline(work_order_id: int) -> List[Dict]:
    """获取工单处理时间线."""
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(WorkOrder).where(WorkOrder.id == work_order_id))
        work_order = result.scalar_one_or_none()
        if not work_order:
            return []

        timeline = [
            {
                "status": "created",
                "comment": "工单创建",
                "created_at": work_order.created_at.isoformat() if work_order.created_at else "",
            }
        ]
        for item in work_order.feedback or []:
            timeline.append(
                {
                    "status": item.get("status"),
                    "comment": item.get("comment") or "",
                    "solution": item.get("solution") or "",
                    "created_at": item.get("created_at") or "",
                }
            )
        return timeline


async def archive_case(work_order_id: int) -> Optional[Dict]:
    """将已完成工单沉淀为知识库案例."""
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(WorkOrder).where(WorkOrder.id == work_order_id))
        work_order = result.scalar_one_or_none()
        if not work_order or work_order.status != "completed":
            return None

        title = f"案例沉淀：{work_order.title}"
        solution_parts = []
        for item in work_order.feedback or []:
            if item.get("solution"):
                solution_parts.append(item["solution"])
        solution = "\n".join(solution_parts) or "暂无详细解决方案"
        content = (
            f"问题：{work_order.title}\n"
            f"描述：{work_order.description or '-'}\n"
            f"解决方案：\n{solution}"
        )

        doc = await knowledge_service.save_case_document(
            title=title,
            content=content,
            station_id=work_order.station_id,
        )
        return {"knowledge_doc_id": doc.id, "title": title}
