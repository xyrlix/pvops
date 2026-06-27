"""告警模型."""

from sqlalchemy import Column, DateTime, Integer, String, Text
from sqlalchemy.sql import func

from app.core.database import Base
from app.models.base import TenantScopedMixin


class Alarm(Base, TenantScopedMixin):
    """告警表."""

    __tablename__ = "alarms"

    id = Column(Integer, primary_key=True, index=True)
    station_id = Column(Integer, nullable=False, index=True)
    device_id = Column(String(64), nullable=True)
    level = Column(String(20), default="warning")  # critical / warning / info
    priority = Column(String(20), default="medium")  # urgent / high / medium / low
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    rule_name = Column(String(100), nullable=True)
    status = Column(String(20), default="open")  # open / acknowledged / closed
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    resolved_at = Column(DateTime(timezone=True), nullable=True)
