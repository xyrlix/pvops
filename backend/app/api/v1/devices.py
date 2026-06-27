"""设备资产接口."""

from fastapi import APIRouter, Depends, Query

from app.core.deps import get_current_user
from app.schemas.device import DeviceCreate, DeviceResponse, DeviceUpdate
from app.services import device_service

router = APIRouter(dependencies=[Depends(get_current_user)])


@router.get("", response_model=list[DeviceResponse])
async def list_devices(
    station_id: int | None = Query(None),
    device_type: str | None = Query(None),
):
    """列出设备资产."""
    devices = await device_service.list_devices(station_id, device_type)
    return devices


@router.post("", response_model=DeviceResponse)
async def create_device(data: DeviceCreate):
    """创建设备资产."""
    device = await device_service.create_device(data.dict())
    return device


@router.get("/{device_id}", response_model=DeviceResponse)
async def get_device(device_id: int):
    """获取单个设备."""
    device = await device_service.get_device(device_id)
    return device


@router.put("/{device_id}", response_model=DeviceResponse)
async def update_device(device_id: int, data: DeviceUpdate):
    """更新设备资产."""
    device = await device_service.update_device(device_id, data.dict(exclude_unset=True))
    return device


@router.delete("/{device_id}")
async def delete_device(device_id: int):
    """删除设备资产."""
    success = await device_service.delete_device(device_id)
    return {"success": success}


@router.get("/stations/{station_id}/topology")
async def get_station_topology(station_id: int):
    """获取电站设备拓扑树."""
    tree = await device_service.get_station_topology(station_id)
    return tree
