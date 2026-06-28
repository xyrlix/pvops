"""采集器运行器."""

import asyncio
import logging
from typing import Any

from app.collector.local_queue import LocalQueue
from app.protocols import create_adapter
from app.repositories import get_repository
from app.services import device_service

logger = logging.getLogger(__name__)


class CollectorRunner:
    """按电站-设备配置轮询采集."""

    def __init__(self, station_id: int, interval: int = 5):
        self.station_id = station_id
        self.interval = interval
        self.repo = get_repository()
        self.queue = LocalQueue()

    async def init(self) -> None:
        await self.repo.init()
        await self.queue.init()

    async def close(self) -> None:
        await self.repo.close()

    async def run_once(self) -> None:
        devices = await device_service.list_devices(
            station_id=self.station_id,
        )
        target_types = {"inverter", "weather_station", "meter"}
        devices = [d for d in devices if d.device_type in target_types and d.status == "active"]

        failed: list[dict[str, Any]] = []

        for device in devices:
            data: dict[str, Any] = {}
            try:
                adapter = create_adapter(
                    device.protocol or "simulator", device.device_code, device.config or {}
                )
                await adapter.connect()
                data = await adapter.collect_once()
                await adapter.disconnect()

                payload = {
                    "station_id": self.station_id,
                    "device_code": device.device_code,
                    "device_type": device.device_type,
                    "data": data,
                }
                await self._write_payload(payload)
            except Exception as e:
                logger.warning(f"采集设备 {device.device_code} 失败: {e}")
                failed.append(
                    {
                        "station_id": self.station_id,
                        "device_code": device.device_code,
                        "device_type": device.device_type,
                        "data": data,
                    }
                )

        for payload in failed:
            await self.queue.enqueue(payload)

        await self._flush_queue()

    async def _write_payload(self, payload: dict[str, Any]) -> None:
        device_type = payload.get("device_type")
        data = payload["data"]
        if device_type == "inverter":
            await self.repo.insert_inverter_data(
                payload["station_id"], payload["device_code"], data
            )
        elif device_type == "weather_station":
            await self.repo.insert_weather_data(payload["station_id"], payload["device_code"], data)
        elif device_type == "meter":
            await self.repo.insert_meter_data(payload["station_id"], payload["device_code"], data)

    async def _flush_queue(self) -> None:
        payloads = await self.queue.dequeue_all()
        if not payloads:
            return
        logger.info(f"尝试补发 {len(payloads)} 条缓存数据")
        for payload in payloads:
            try:
                await self._write_payload(payload)
            except Exception as e:
                logger.warning(f"补发失败，重新入队: {e}")
                await self.queue.enqueue(payload)

    async def run_forever(self) -> None:
        await self.init()
        try:
            while True:
                await self.run_once()
                await asyncio.sleep(self.interval)
        except asyncio.CancelledError:
            logger.info("采集器收到取消信号，正在退出")
        finally:
            await self.close()


# mypy: disable-error-code="arg-type"
