"""电站接口."""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.tenant import TenantContext, get_current_tenant, scoped_query
from app.models.station import Station
from app.models.user import User
from app.schemas.station import StationCreate, StationResponse, StationUpdate

router = APIRouter(dependencies=[Depends(get_current_user)])


@router.get("", response_model=List[StationResponse])
async def list_stations(
    db: AsyncSession = Depends(get_db),
    tenant: TenantContext = Depends(get_current_tenant),
) -> List[Station]:
    """获取电站列表（仅当前租户可见）."""
    query = scoped_query(select(Station), Station, tenant).order_by(Station.id)
    result = await db.execute(query)
    return list(result.scalars().all())


@router.post("", response_model=StationResponse, status_code=status.HTTP_201_CREATED)
async def create_station(
    station: StationCreate,
    db: AsyncSession = Depends(get_db),
    tenant: TenantContext = Depends(get_current_tenant),
) -> Station:
    """创建电站（自动归属当前租户）."""
    data = station.model_dump()
    data["tenant_id"] = tenant.tenant_id  # 强制覆盖入参中的 tenant_id
    db_station = Station(**data)
    db.add(db_station)
    await db.commit()
    await db.refresh(db_station)
    return db_station


@router.get("/{station_id}", response_model=StationResponse)
async def get_station(
    station_id: int,
    db: AsyncSession = Depends(get_db),
    tenant: TenantContext = Depends(get_current_tenant),
) -> Station:
    """获取电站详情（跨租户返回 404 防越权探测）."""
    query = scoped_query(select(Station), Station, tenant).where(Station.id == station_id)
    station = (await db.execute(query)).scalar_one_or_none()
    if not station:
        raise HTTPException(status_code=404, detail="电站不存在")
    return station


@router.put("/{station_id}", response_model=StationResponse)
async def update_station(
    station_id: int,
    station_update: StationUpdate,
    db: AsyncSession = Depends(get_db),
    tenant: TenantContext = Depends(get_current_tenant),
) -> Station:
    """更新电站."""
    query = scoped_query(select(Station), Station, tenant).where(Station.id == station_id)
    station = (await db.execute(query)).scalar_one_or_none()
    if not station:
        raise HTTPException(status_code=404, detail="电站不存在")

    update_data = station_update.model_dump(exclude_unset=True)
    # 不允许通过 API 改变 tenant_id
    update_data.pop("tenant_id", None)
    for field, value in update_data.items():
        setattr(station, field, value)

    await db.commit()
    await db.refresh(station)
    return station


@router.delete("/{station_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_station(
    station_id: int,
    db: AsyncSession = Depends(get_db),
    tenant: TenantContext = Depends(get_current_tenant),
) -> None:
    """删除电站."""
    query = scoped_query(select(Station), Station, tenant).where(Station.id == station_id)
    station = (await db.execute(query)).scalar_one_or_none()
    if not station:
        raise HTTPException(status_code=404, detail="电站不存在")
    await db.delete(station)
    await db.commit()
