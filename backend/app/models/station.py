"""电站模型."""

from sqlalchemy import Column, DateTime, Float, Integer, String
from sqlalchemy.sql import func

from app.core.database import Base


class Station(Base):
    """电站表."""

    __tablename__ = "stations"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, comment="电站名称")
    code = Column(String(50), unique=True, index=True, comment="电站编码")
    capacity_kw = Column(Float, nullable=False, comment="装机容量(kW)")
    location = Column(String(200), nullable=True, comment="位置")
    longitude = Column(Float, nullable=True, comment="经度")
    latitude = Column(Float, nullable=True, comment="纬度")
    contact_name = Column(String(50), nullable=True, comment="联系人")
    contact_phone = Column(String(20), nullable=True, comment="联系电话")
    status = Column(String(20), default="active", comment="状态")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
