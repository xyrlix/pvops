"""设备资产服务."""

from sqlalchemy import select

from app.core.database import AsyncSessionLocal
from app.models.device import Device


async def list_devices(
    station_id: int | None = None, device_type: str | None = None
) -> list[Device]:
    async with AsyncSessionLocal() as session:
        query = select(Device)
        if station_id:
            query = query.where(Device.station_id == station_id)
        if device_type:
            query = query.where(Device.device_type == device_type)
        query = query.order_by(Device.sort_order, Device.id)
        result = await session.execute(query)
        return result.scalars().all()


async def get_device(device_id: int) -> Device | None:
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Device).where(Device.id == device_id))
        return result.scalar_one_or_none()


async def create_device(data: dict) -> Device:
    async with AsyncSessionLocal() as session:
        device = Device(**data)
        session.add(device)
        await session.commit()
        await session.refresh(device)
        return device


async def update_device(device_id: int, data: dict) -> Device | None:
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Device).where(Device.id == device_id))
        device = result.scalar_one_or_none()
        if not device:
            return None
        for key, value in data.items():
            if value is not None or key in data:
                setattr(device, key, value)
        await session.commit()
        await session.refresh(device)
        return device


async def delete_device(device_id: int) -> bool:
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Device).where(Device.id == device_id))
        device = result.scalar_one_or_none()
        if not device:
            return False
        await session.delete(device)
        await session.commit()
        return True


def _build_tree(devices: list[Device], parent_id: int | None = None) -> list[dict]:
    nodes = []
    for device in devices:
        if device.parent_id == parent_id:
            node = {
                "id": device.id,
                "station_id": device.station_id,
                "parent_id": device.parent_id,
                "device_type": device.device_type,
                "device_code": device.device_code,
                "name": device.name,
                "vendor": device.vendor,
                "model": device.model,
                "sn": device.sn,
                "protocol": device.protocol,
                "config": device.config,
                "status": device.status,
                "sort_order": device.sort_order,
                "created_at": device.created_at,
                "children": _build_tree(devices, device.id),
            }
            nodes.append(node)
    return nodes


async def get_station_topology(station_id: int) -> list[dict]:
    devices = await list_devices(station_id=station_id)
    return _build_tree(devices)
