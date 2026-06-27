"""Dashboard 聚合接口."""

from fastapi import APIRouter, Depends, Query

from app.core.deps import get_current_user
from app.services import dashboard_service

router = APIRouter(dependencies=[Depends(get_current_user)])


@router.get("/overview")
async def get_overview() -> dict:
    """总览大屏 KPI."""
    return await dashboard_service.get_dashboard_overview()


@router.get("/stations-overview")
async def get_stations_overview() -> list[dict]:
    """集团场站分布（气泡图/TOP榜）."""
    return await dashboard_service.get_stations_overview()


@router.get("/risk-top")
async def get_risk_top(limit: int = Query(5)) -> list[dict]:
    """高风险场站 TOP."""
    return await dashboard_service.get_risk_top_stations(limit)


@router.get("/alarm-stats")
async def get_alarm_stats(station_id: int = Query(None)) -> dict:
    """告警统计."""
    return await dashboard_service.get_alarm_stats(station_id)


@router.get("/insights")
async def get_insights() -> dict:
    """AI 洞察文本."""
    return {"insight": await dashboard_service.get_ai_insight()}
