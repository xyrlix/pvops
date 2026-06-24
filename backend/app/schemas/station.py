"""电站 schema."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class StationBase(BaseModel):
    """电站基础 schema."""

    name: str
    code: str
    capacity_kw: float
    location: Optional[str] = None
    longitude: Optional[float] = None
    latitude: Optional[float] = None
    contact_name: Optional[str] = None
    contact_phone: Optional[str] = None
    status: str = "active"


class StationCreate(StationBase):
    """创建电站 schema."""

    pass


class StationUpdate(BaseModel):
    """更新电站 schema."""

    name: Optional[str] = None
    capacity_kw: Optional[float] = None
    location: Optional[str] = None
    longitude: Optional[float] = None
    latitude: Optional[float] = None
    contact_name: Optional[str] = None
    contact_phone: Optional[str] = None
    status: Optional[str] = None


class StationResponse(StationBase):
    """电站响应 schema."""

    class Config:
        orm_mode = True

    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
