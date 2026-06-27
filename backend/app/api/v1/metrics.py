"""指标接口."""

import asyncio
import json
from collections.abc import AsyncGenerator
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse

from app.core.deps import get_current_user
from app.schemas.metric import StationMetrics
from app.services import metrics_service

router = APIRouter(dependencies=[Depends(get_current_user)])


@router.get("/station/{station_id}", response_model=StationMetrics)
async def get_station_metrics(station_id: int) -> dict:
    """获取电站实时指标."""
    return await metrics_service.get_latest_station_metrics(station_id)


@router.get("/station/{station_id}/history")
async def get_station_history(
    station_id: int,
    metric: str = Query(..., description="指标名: active_power_kw, daily_energy_kwh 等"),
    start: str | None = Query(None),
    end: str | None = Query(None),
) -> list[dict]:
    """获取电站历史指标."""
    start_dt = datetime.fromisoformat(start) if start else datetime.now() - timedelta(days=1)
    end_dt = datetime.fromisoformat(end) if end else datetime.now()

    return await metrics_service.get_metric_history(station_id, metric, start_dt, end_dt)


async def metrics_stream_generator(station_id: int) -> AsyncGenerator[str, None]:
    """SSE 实时指标流."""
    while True:
        try:
            metrics = await metrics_service.get_latest_station_metrics(station_id)
            yield f"data: {json.dumps(metrics, default=str)}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
        await asyncio.sleep(5)


@router.get("/station/{station_id}/stream")
async def get_metrics_stream(station_id: int) -> StreamingResponse:
    """获取电站实时指标 SSE 流."""
    return StreamingResponse(
        metrics_stream_generator(station_id),
        media_type="text/event-stream",
    )


@router.get("/stations/overview")
async def get_stations_overview() -> list[dict]:
    """集团总览指标（气泡图/TOP榜）."""
    return await metrics_service.get_stations_overview()


@router.get("/stations/ranking")
async def get_stations_ranking(
    metric: str = Query("health_score", description="排序指标"),
    limit: int = Query(10),
) -> list[dict]:
    """电站排名."""
    return await metrics_service.get_stations_ranking(metric, limit)


@router.get("/station/{station_id}/efficiency")
async def get_station_efficiency(station_id: int) -> dict:
    """电站效率指标（等效小时/PR/系统效率）."""
    return await metrics_service.get_station_efficiency(station_id)


@router.get("/station/{station_id}/losses")
async def get_station_losses(station_id: int) -> dict:
    """电站损失分解."""
    return await metrics_service.get_station_losses(station_id)


@router.get("/station/{station_id}/health-trend")
async def get_station_health_trend(
    station_id: int,
    days: int = Query(30),
) -> list[dict]:
    """健康度趋势（热力图）."""
    return await metrics_service.get_health_trend(station_id, days)


@router.get("/station/{station_id}/inverters")
async def get_station_inverters(station_id: int) -> list[dict]:
    """逆变器群组对比."""
    return await metrics_service.get_inverter_comparison(station_id)


@router.get("/station/{station_id}/strings")
async def get_station_strings(
    station_id: int,
    inverter_id: str | None = Query(None),
) -> list[dict]:
    """组串离散率."""
    return await metrics_service.get_string_dispersion(station_id, inverter_id)


@router.get("/station/{station_id}/peer-baseline")
async def get_station_peer_baseline(station_id: int) -> dict:
    """群体基线（同容量档位中位数 + top quartile）.

    对标竞品 V3.2 §F3.3：同区域/同厂家/同容量横向对比。
    """
    return await metrics_service.get_station_peer_baseline(station_id)


@router.get("/station/{station_id}/peer-ranking")
async def get_station_peer_ranking(
    station_id: int,
    metric: str = Query("health_score", description="排序指标"),
) -> dict:
    """同档位内电站排名（高亮本电站）."""
    return await metrics_service.get_station_peer_ranking(station_id, metric)
