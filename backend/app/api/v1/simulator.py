"""模拟器数据接入接口."""

from typing import Dict, List

from fastapi import APIRouter

from app.services import alarm_service, metrics_service

router = APIRouter()


@router.post("/inverter")
async def ingest_inverter_data(data: dict) -> dict:
    """接收模拟器发送的逆变器数据."""
    try:
        await metrics_service.insert_inverter_data(data)
        # 异步检查告警
        await alarm_service.check_alarms(data.get("station_id", 0))
        return {"status": "ok", "message": "数据已写入"}
    except Exception as e:
        return {"status": "error", "message": f"数据未存储: {str(e)}"}


@router.post("/inverter/batch")
async def ingest_inverter_batch(data: List[Dict]) -> dict:
    """批量接收逆变器数据."""
    try:
        count = await metrics_service.batch_insert_inverter_data(data)
        if data:
            await alarm_service.check_alarms(data[-1].get("station_id", 0))
        return {"status": "ok", "success": count, "failed": len(data) - count}
    except Exception as e:
        return {"status": "error", "success": 0, "failed": len(data), "message": str(e)}


@router.post("/weather")
async def ingest_weather_data(data: dict) -> dict:
    """接收模拟器发送的气象数据."""
    try:
        await metrics_service.insert_weather_data(data)
        return {"status": "ok", "message": "数据已写入"}
    except Exception as e:
        return {"status": "error", "message": f"数据未存储: {str(e)}"}
