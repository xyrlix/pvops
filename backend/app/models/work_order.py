"""工单模型."""

from sqlalchemy import Column, DateTime, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.sql import func

from app.core.database import Base


class WorkOrder(Base):
    """工单表."""

    __tablename__ = "work_orders"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False, comment="工单标题")
    description = Column(Text, nullable=True, comment="问题描述")
    priority = Column(String(20), default="medium", comment="优先级 urgent/high/medium/low")
    status = Column(String(20), default="pending", comment="状态 pending/in_progress/completed")
    assignee = Column(String(100), nullable=True, comment="负责人")
    created_by = Column(String(100), nullable=True, comment="创建人")
    station_id = Column(Integer, ForeignKey("stations.id"), nullable=True, comment="关联电站")
    alarm_id = Column(Integer, ForeignKey("alarms.id"), nullable=True, comment="关联告警")
    feedback = Column(JSON, default=list, comment="处理反馈记录")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
