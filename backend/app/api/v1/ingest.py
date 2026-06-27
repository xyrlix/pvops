"""设备遥测数据接入接口.

支持边缘网关通过 HTTP POST 推送设备数据，写入时序数据库。

认证：所有 ingest 端点要求请求头携带 `X-Gateway-Token`，
与 .env 中的 `INGEST_GATEWAY_TOKEN` 常量时间比较（hmac.compare_digest）。
网关侧应在反代/边缘 SDK 配置此 token，避免在公网裸奔。
"""

from typing import Any

from fastapi import APIRouter, HTTPException, Request, status

from app.collector.runner import CollectorRunner
from app.core.limiter import limiter
from app.core.security import verify_gateway_token

router = APIRouter()


@router.post("/telemetry")
@limiter.limit("600/minute")  # 网关高频推送：每 IP 每分钟 600 条
async def ingest_telemetry(request: Request, payload: dict[str, Any]):
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
    verify_gateway_token(request)

    station_id = payload.get("station_id")
    device_code = payload.get("device_code")
    device_type = payload.get("device_type")
    data = payload.get("data")

    if not station_id or not device_code or not device_type or not data:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="缺少必要字段: station_id, device_code, device_type, data",
        )

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
        raise HTTPException(status_code=500, detail=f"写入失败: {e}") from e
    finally:
        await runner.close()

    return {"success": True, "message": "数据已接收"}


@router.post("/telemetry/batch")
@limiter.limit("60/minute")  # 批量端点更贵，收紧
async def ingest_telemetry_batch(request: Request, payloads: list[dict[str, Any]]):
    """批量接收遥测数据."""
    verify_gateway_token(request)

    if not payloads:
        return {"success": True, "count": 0}

    runner = CollectorRunner(station_id=payloads[0].get("station_id", 0))
    await runner.init()
    failed = []
    try:
        for payload in payloads:
            try:
                await payload_guard(payload)
                await runner._write_payload(payload)
            except Exception as e:
                failed.append({"payload": payload, "error": str(e)})
    finally:
        await runner.close()

    if failed:
        raise HTTPException(
            status_code=status.HTTP_207_MULTI_STATUS,
            detail={"success": len(payloads) - len(failed), "failed": failed},
        )

    return {"success": True, "count": len(payloads)}


def payload_guard(payload: dict[str, Any]) -> None:
    """最小化 payload 形状校验."""
    required = {"station_id", "device_code", "device_type", "data"}
    missing = required - payload.keys()
    if missing:
        raise ValueError(f"missing keys: {sorted(missing)}")
