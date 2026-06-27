"""电站 schema."""

from datetime import datetime

from pydantic import BaseModel


class StationBase(BaseModel):
    """电站基础 schema."""

    name: str
    code: str
    capacity_kw: float
    location: str | None = None
    longitude: float | None = None
    latitude: float | None = None
    contact_name: str | None = None
    contact_phone: str | None = None
    status: str = "active"


class StationCreate(StationBase):
    """创建电站 schema."""

    pass


class StationUpdate(BaseModel):
    """更新电站 schema."""

    name: str | None = None
    capacity_kw: float | None = None
    location: str | None = None
    longitude: float | None = None
    latitude: float | None = None
    contact_name: str | None = None
    contact_phone: str | None = None
    status: str | None = None


class StationResponse(StationBase):
    """电站响应 schema."""

    class Config:
        orm_mode = True

    id: int
    created_at: datetime
    updated_at: datetime | None = None
