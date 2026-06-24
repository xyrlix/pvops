"""电站接口."""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.station import Station
from app.schemas.station import StationCreate, StationResponse, StationUpdate

router = APIRouter()


@router.get("", response_model=List[StationResponse])
async def list_stations(db: AsyncSession = Depends(get_db)) -> List[Station]:
    """获取电站列表."""
    result = await db.execute(select(Station).order_by(Station.id))
    return list(result.scalars().all())


@router.post("", response_model=StationResponse, status_code=status.HTTP_201_CREATED)
async def create_station(station: StationCreate, db: AsyncSession = Depends(get_db)) -> Station:
    """创建电站."""
    db_station = Station(**station.model_dump())
    db.add(db_station)
    await db.commit()
    await db.refresh(db_station)
    return db_station


@router.get("/{station_id}", response_model=StationResponse)
async def get_station(station_id: int, db: AsyncSession = Depends(get_db)) -> Station:
    """获取电站详情."""
    result = await db.execute(select(Station).where(Station.id == station_id))
    station = result.scalar_one_or_none()
    if not station:
        raise HTTPException(status_code=404, detail="电站不存在")
    return station


@router.put("/{station_id}", response_model=StationResponse)
async def update_station(
    station_id: int,
    station_update: StationUpdate,
    db: AsyncSession = Depends(get_db),
) -> Station:
    """更新电站."""
    result = await db.execute(select(Station).where(Station.id == station_id))
    station = result.scalar_one_or_none()
    if not station:
        raise HTTPException(status_code=404, detail="电站不存在")

    update_data = station_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(station, field, value)

    await db.commit()
    await db.refresh(station)
    return station


@router.delete("/{station_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_station(station_id: int, db: AsyncSession = Depends(get_db)) -> None:
    """删除电站."""
    result = await db.execute(select(Station).where(Station.id == station_id))
    station = result.scalar_one_or_none()
    if not station:
        raise HTTPException(status_code=404, detail="电站不存在")
    await db.delete(station)
    await db.commit()
