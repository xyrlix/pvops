"""Dashboard 聚合接口."""

from typing import Dict, List

from fastapi import APIRouter, Query

from app.services import dashboard_service

router = APIRouter()


@router.get("/overview")
async def get_overview() -> Dict:
    """总览大屏 KPI."""
    return await dashboard_service.get_dashboard_overview()


@router.get("/stations-overview")
async def get_stations_overview() -> List[Dict]:
    """集团场站分布（气泡图/TOP榜）."""
    return await dashboard_service.get_stations_overview()


@router.get("/risk-top")
async def get_risk_top(limit: int = Query(5)) -> List[Dict]:
    """高风险场站 TOP."""
    return await dashboard_service.get_risk_top_stations(limit)


@router.get("/alarm-stats")
async def get_alarm_stats(station_id: int = Query(None)) -> Dict:
    """告警统计."""
    return await dashboard_service.get_alarm_stats(station_id)


@router.get("/insights")
async def get_insights() -> Dict:
    """AI 洞察文本."""
    return {"insight": await dashboard_service.get_ai_insight()}
