"""工单 schema."""

from datetime import datetime

from pydantic import BaseModel


class FeedbackItem(BaseModel):
    """反馈记录项."""

    status: str
    comment: str | None = None
    created_at: datetime


class WorkOrderBase(BaseModel):
    """工单基础 schema."""

    title: str
    description: str | None = None
    priority: str = "medium"
    status: str = "pending"
    assignee: str | None = None
    station_id: int | None = None
    alarm_id: int | None = None


class WorkOrderCreate(WorkOrderBase):
    """创建工单请求."""

    pass


class WorkOrderUpdate(BaseModel):
    """更新工单请求."""

    status: str | None = None
    assignee: str | None = None
    feedback_comment: str | None = None
    solution: str | None = None


class WorkOrderResponse(WorkOrderBase):
    """工单响应."""

    class Config:
        orm_mode = True

    id: int
    created_by: str | None
    feedback: list[FeedbackItem] = []
    created_at: datetime
    updated_at: datetime | None
