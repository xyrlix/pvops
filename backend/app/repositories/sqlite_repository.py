"""SQLite 时序数据仓库实现."""

import logging
from datetime import datetime, timedelta

from sqlalchemy import desc, select

from app.core.database import AsyncSessionLocal
from app.models.timeseries import InverterData, MeterData, WeatherData
from app.repositories.base import TimeSeriesRepository

logger = logging.getLogger(__name__)


class SQLiteTimeSeriesRepository(TimeSeriesRepository):
    """基于 SQLAlchemy + SQLite 的实现，用于本地演示."""

    async def init(self) -> None:
        """SQLite 表由 FastAPI lifespan 统一创建，此处无需额外操作."""
        pass

    async def close(self) -> None:
        pass

    async def insert_inverter_data(self, station_id: int, inverter_id: str, data: dict) -> None:
        async with AsyncSessionLocal() as session:
            record = InverterData(
                timestamp=datetime.fromisoformat(data["timestamp"]),
                station_id=station_id,
                inverter_id=inverter_id,
                active_power_kw=data.get("active_power_kw", 0.0),
                dc_voltage_v=data.get("dc_voltage_v", 0.0),
                dc_current_a=data.get("dc_current_a", 0.0),
                daily_energy_kwh=data.get("daily_energy_kwh", 0.0),
                total_energy_kwh=data.get("total_energy_kwh", 0.0),
                inverter_status=data.get("inverter_status", 0),
                fault_code=data.get("fault_code", 0),
                irradiance_w_m2=data.get("irradiance_w_m2", 0.0),
                ambient_temp_c=data.get("ambient_temp_c", 0.0),
            )
            session.add(record)
            await session.commit()

    async def insert_weather_data(self, station_id: int, device_id: str, data: dict) -> None:
        async with AsyncSessionLocal() as session:
            record = WeatherData(
                timestamp=datetime.fromisoformat(data["timestamp"]),
                station_id=station_id,
                device_id=device_id,
                irradiance_w_m2=data.get("irradiance_w_m2", 0.0),
                ambient_temp_c=data.get("ambient_temp_c", 0.0),
                module_temp_c=data.get("module_temp_c", 0.0),
                wind_speed_m_s=data.get("wind_speed_m_s", 0.0),
            )
            session.add(record)
            await session.commit()

    async def insert_meter_data(self, station_id: int, device_id: str, data: dict) -> None:
        async with AsyncSessionLocal() as session:
            record = MeterData(
                timestamp=datetime.fromisoformat(data["timestamp"]),
                station_id=station_id,
                device_id=device_id,
                active_power_kw=data.get("active_power_kw", 0.0),
                reactive_power_kvar=data.get("reactive_power_kvar", 0.0),
                forward_active_energy_kwh=data.get("forward_active_energy_kwh", 0.0),
                reverse_active_energy_kwh=data.get("reverse_active_energy_kwh", 0.0),
                voltage_v=data.get("voltage_v", 0.0),
                current_a=data.get("current_a", 0.0),
                power_factor=data.get("power_factor", 0.0),
            )
            session.add(record)
            await session.commit()

    async def batch_insert_inverter_data(self, data_list: list[dict]) -> int:
        count = 0
        async with AsyncSessionLocal() as session:
            for data in data_list:
                try:
                    record = InverterData(
                        timestamp=datetime.fromisoformat(data["timestamp"]),
                        station_id=data.get("station_id", 0),
                        inverter_id=data.get("inverter_id", "INV001"),
                        active_power_kw=data.get("active_power_kw", 0.0),
                        dc_voltage_v=data.get("dc_voltage_v", 0.0),
                        dc_current_a=data.get("dc_current_a", 0.0),
                        daily_energy_kwh=data.get("daily_energy_kwh", 0.0),
                        total_energy_kwh=data.get("total_energy_kwh", 0.0),
                        inverter_status=data.get("inverter_status", 0),
                        fault_code=data.get("fault_code", 0),
                        irradiance_w_m2=data.get("irradiance_w_m2", 0.0),
                        ambient_temp_c=data.get("ambient_temp_c", 0.0),
                    )
                    session.add(record)
                    count += 1
                except Exception as e:
                    logger.warning(f"批量插入数据失败: {e}")
            await session.commit()
        return count

    async def get_latest_station_metrics(self, station_id: int) -> dict:
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(InverterData)
                .where(InverterData.station_id == station_id)
                .order_by(desc(InverterData.id))
                .limit(1)
            )
            latest_inv = result.scalar_one_or_none()

            result = await session.execute(
                select(WeatherData)
                .where(WeatherData.station_id == station_id)
                .order_by(desc(WeatherData.id))
                .limit(1)
            )
            latest_weather = result.scalar_one_or_none()

            if not latest_inv:
                return {
                    "station_id": station_id,
                    "station_name": "",
                    "timestamp": datetime.now().isoformat(),
                    "active_power_kw": 0.0,
                    "daily_energy_kwh": 0.0,
                    "pr": None,
                    "health_score": None,
                }

            pr = None
            if latest_weather and latest_weather.irradiance_w_m2 > 0:
                theoretical_power = latest_weather.irradiance_w_m2 / 1000 * 1000
                if theoretical_power > 0:
                    pr = min(1.0, latest_inv.active_power_kw / theoretical_power)

            from app.services.health import calculate_health_score

            health_score = calculate_health_score(latest_inv, latest_weather)

            return {
                "station_id": station_id,
                "station_name": f"电站 {station_id}",
                "timestamp": latest_inv.timestamp.isoformat()
                if latest_inv.timestamp
                else datetime.now().isoformat(),
                "active_power_kw": latest_inv.active_power_kw or 0.0,
                "daily_energy_kwh": latest_inv.daily_energy_kwh or 0.0,
                "pr": pr,
                "health_score": health_score,
            }

    async def get_metric_history(
        self,
        station_id: int,
        metric: str,
        start: datetime | None = None,
        end: datetime | None = None,
    ) -> list[dict]:
        if not end:
            end = datetime.now()
        if not start:
            start = end - timedelta(days=1)

        valid_metrics = {
            "active_power_kw": InverterData.active_power_kw,
            "daily_energy_kwh": InverterData.daily_energy_kwh,
            "dc_voltage_v": InverterData.dc_voltage_v,
            "dc_current_a": InverterData.dc_current_a,
            "irradiance_w_m2": InverterData.irradiance_w_m2,
            "ambient_temp_c": InverterData.ambient_temp_c,
        }

        if metric not in valid_metrics:
            return []

        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(InverterData.timestamp, valid_metrics[metric])
                .where(
                    InverterData.station_id == station_id,
                    InverterData.timestamp >= start,
                    InverterData.timestamp <= end,
                )
                .order_by(InverterData.timestamp.asc())
            )
            rows = result.all()

            return [
                {
                    "timestamp": row[0].isoformat() if row[0] else "",
                    "value": float(row[1]) if row[1] is not None else 0.0,
                }
                for row in rows
            ]

    async def get_daily_energy(self, station_id: int, date: datetime | None = None) -> float:
        if not date:
            date = datetime.now()

        start = date.replace(hour=0, minute=0, second=0, microsecond=0)
        end = start + timedelta(days=1)

        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(InverterData.daily_energy_kwh)
                .where(
                    InverterData.station_id == station_id,
                    InverterData.timestamp >= start,
                    InverterData.timestamp < end,
                )
                .order_by(desc(InverterData.timestamp))
                .limit(1)
            )
            row = result.scalar_one_or_none()
            return float(row) if row else 0.0
