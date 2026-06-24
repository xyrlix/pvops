"""工单 schema."""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel


class FeedbackItem(BaseModel):
    """反馈记录项."""

    status: str
    comment: Optional[str] = None
    created_at: datetime


class WorkOrderBase(BaseModel):
    """工单基础 schema."""

    title: str
    description: Optional[str] = None
    priority: str = "medium"
    status: str = "pending"
    assignee: Optional[str] = None
    station_id: Optional[int] = None
    alarm_id: Optional[int] = None


class WorkOrderCreate(WorkOrderBase):
    """创建工单请求."""

    pass


class WorkOrderUpdate(BaseModel):
    """更新工单请求."""

    status: Optional[str] = None
    assignee: Optional[str] = None
    feedback_comment: Optional[str] = None
    solution: Optional[str] = None


class WorkOrderResponse(WorkOrderBase):
    """工单响应."""

    class Config:
        orm_mode = True

    id: int
    created_by: Optional[str]
    feedback: List[FeedbackItem] = []
    created_at: datetime
    updated_at: Optional[datetime]
