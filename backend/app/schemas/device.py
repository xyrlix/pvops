"""设备资产 Schema."""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class DeviceBase(BaseModel):
    station_id: int
    parent_id: Optional[int] = None
    device_type: str
    device_code: str
    name: str
    vendor: Optional[str] = None
    model: Optional[str] = None
    sn: Optional[str] = None
    protocol: Optional[str] = "simulator"
    config: Optional[Dict[str, Any]] = None
    status: Optional[str] = "active"
    sort_order: Optional[int] = 0


class DeviceCreate(DeviceBase):
    pass


class DeviceUpdate(BaseModel):
    parent_id: Optional[int] = None
    device_type: Optional[str] = None
    device_code: Optional[str] = None
    name: Optional[str] = None
    vendor: Optional[str] = None
    model: Optional[str] = None
    sn: Optional[str] = None
    protocol: Optional[str] = None
    config: Optional[Dict[str, Any]] = None
    status: Optional[str] = None
    sort_order: Optional[int] = None


class DeviceResponse(DeviceBase):
    id: int
    created_at: Optional[str] = None

    class Config:
        orm_mode = True


class DeviceTreeNode(DeviceResponse):
    children: List["DeviceTreeNode"] = []


DeviceTreeNode.update_forward_refs()
