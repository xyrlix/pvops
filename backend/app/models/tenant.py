"""租户（Tenant）模型.

租户是 SaaS 化顶层隔离单元；同一 Tenant 下的电站、设备、数据彼此可见，
跨 Tenant 的数据查询必须显式注入 tenant 过滤。
"""

from __future__ import annotations

from sqlalchemy import Column, DateTime, Integer, String, Text
from sqlalchemy.sql import func

from app.core.database import Base


class Tenant(Base):
    """租户."""

    __tablename__ = "tenants"

    id = Column(Integer, primary_key=True)
    code = Column(String(64), unique=True, nullable=False, index=True)
    name = Column(String(200), nullable=False)
    status = Column(String(20), nullable=False, server_default="active")
    description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=True)

    def __repr__(self) -> str:
        return f"<Tenant {self.code}>"


__all__ = ["Tenant"]