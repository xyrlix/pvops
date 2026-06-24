"""设备遥测数据接入接口.

支持边缘网关通过 HTTP POST 推送设备数据，写入时序数据库。
"""

from typing import Any, Dict

from fastapi import APIRouter, HTTPException

from app.collector.runner import CollectorRunner
from app.repositories import get_repository

router = APIRouter()


@router.post("/telemetry")
async def ingest_telemetry(payload: Dict[str, Any]):
    """接收单条或多条设备遥测数据.

    请求体示例:
    {
        "station_id": 1,
        "device_code": "INV001",
        "device_type": "inverter",
        "data": {
            "timestamp": "2024-06-01T12:00:00Z",
            "active_power_kw": 123.4,
            "dc_voltage_v": 620.0,
            ...
        }
    }
    """
    station_id = payload.get("station_id")
    device_code = payload.get("device_code")
    device_type = payload.get("device_type")
    data = payload.get("data")

    if not station_id or not device_code or not device_type or not data:
        raise HTTPException(status_code=422, detail="缺少必要字段: station_id, device_code, device_type, data")

    runner = CollectorRunner(station_id=station_id)
    await runner.init()
    try:
        await runner._write_payload(
            {
                "station_id": station_id,
                "device_code": device_code,
                "device_type": device_type,
                "data": data,
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"写入失败: {e}")
    finally:
        await runner.close()

    return {"success": True, "message": "数据已接收"}


@router.post("/telemetry/batch")
async def ingest_telemetry_batch(payloads: list[Dict[str, Any]]):
    """批量接收遥测数据."""
    if not payloads:
        return {"success": True, "count": 0}

    runner = CollectorRunner(station_id=payloads[0].get("station_id", 0))
    await runner.init()
    failed = []
    try:
        for payload in payloads:
            try:
                await runner._write_payload(payload)
            except Exception as e:
                failed.append({"payload": payload, "error": str(e)})
    finally:
        await runner.close()

    if failed:
        raise HTTPException(status_code=207, detail={"success": len(payloads) - len(failed), "failed": failed})

    return {"success": True, "count": len(payloads)}
