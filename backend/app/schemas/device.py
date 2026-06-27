"""设备资产 Schema."""

from typing import Any

from pydantic import BaseModel


class DeviceBase(BaseModel):
    station_id: int
    parent_id: int | None = None
    device_type: str
    device_code: str
    name: str
    vendor: str | None = None
    model: str | None = None
    sn: str | None = None
    protocol: str | None = "simulator"
    config: dict[str, Any] | None = None
    status: str | None = "active"
    sort_order: int | None = 0


class DeviceCreate(DeviceBase):
    pass


class DeviceUpdate(BaseModel):
    parent_id: int | None = None
    device_type: str | None = None
    device_code: str | None = None
    name: str | None = None
    vendor: str | None = None
    model: str | None = None
    sn: str | None = None
    protocol: str | None = None
    config: dict[str, Any] | None = None
    status: str | None = None
    sort_order: int | None = None


class DeviceResponse(DeviceBase):
    id: int
    created_at: str | None = None

    class Config:
        orm_mode = True


class DeviceTreeNode(DeviceResponse):
    children: list["DeviceTreeNode"] = []


DeviceTreeNode.update_forward_refs()
