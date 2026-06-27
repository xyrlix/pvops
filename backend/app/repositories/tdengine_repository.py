"""TDengine 时序数据仓库实现."""

import logging
import re
from datetime import datetime, timedelta

from app.core.config import get_settings
from app.repositories.base import TimeSeriesRepository

logger = logging.getLogger(__name__)
settings = get_settings()


def _safe_identifier(value: str) -> str:
    """把任意字符串转成 TDengine 子表名可用的安全标识符."""
    return re.sub(r"[^a-zA-Z0-9_]+", "_", str(value)).strip("_") or "unknown"


class TDengineTimeSeriesRepository(TimeSeriesRepository):
    """基于 TDengine 3.x（taosws）的实现."""

    def __init__(self):
        self._connection = None
        self._taosws_available = False
        try:
            import taosws

            self._taosws = taosws
            self._taosws_available = True
        except ImportError:
            logger.warning("taosws 未安装，TDengine 仓库不可用")

    def _connect(self):
        if not self._taosws_available:
            raise RuntimeError("taosws 未安装")
        if self._connection is None:
            self._connection = self._taosws.connect(
                f"taosws://{settings.tdengine_user}:{settings.tdengine_password}"
                f"@{settings.tdengine_host}:{settings.tdengine_port}"
            )
        return self._connection

    def _cursor(self):
        conn = self._connect()
        return conn.cursor()

    async def init(self) -> None:
        if not self._taosws_available:
            logger.warning("taosws 未安装，跳过 TDengine 初始化")
            return
        try:
            cursor = self._cursor()
            db = settings.tdengine_database
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS {db}")
            cursor.execute(f"USE {db}")

            cursor.execute(
                f"""
                CREATE STABLE IF NOT EXISTS {db}.inverter_data (
                    ts TIMESTAMP,
                    active_power_kw FLOAT,
                    dc_voltage_v FLOAT,
                    dc_current_a FLOAT,
                    daily_energy_kwh FLOAT,
                    total_energy_kwh FLOAT,
                    inverter_status INT,
                    fault_code INT,
                    irradiance_w_m2 FLOAT,
                    ambient_temp_c FLOAT
                ) TAGS (
                    station_id INT,
                    inverter_id NCHAR(64)
                )
            """
            )

            cursor.execute(
                f"""
                CREATE STABLE IF NOT EXISTS {db}.weather_data (
                    ts TIMESTAMP,
                    irradiance_w_m2 FLOAT,
                    ambient_temp_c FLOAT,
                    module_temp_c FLOAT,
                    wind_speed_m_s FLOAT
                ) TAGS (
                    station_id INT,
                    device_id NCHAR(64)
                )
            """
            )

            cursor.execute(
                f"""
                CREATE STABLE IF NOT EXISTS {db}.meter_data (
                    ts TIMESTAMP,
                    active_power_kw FLOAT,
                    reactive_power_kvar FLOAT,
                    forward_active_energy_kwh FLOAT,
                    reverse_active_energy_kwh FLOAT,
                    voltage_v FLOAT,
                    current_a FLOAT,
                    power_factor FLOAT
                ) TAGS (
                    station_id INT,
                    device_id NCHAR(64)
                )
            """
            )
            cursor.close()
            logger.info("TDengine 数据库初始化完成")
        except Exception as e:
            logger.warning(f"TDengine 初始化失败: {e}")

    async def close(self) -> None:
        if self._connection:
            try:
                self._connection.close()
            except Exception as e:
                logger.warning(f"关闭 TDengine 连接失败: {e}")
            self._connection = None

    async def insert_inverter_data(self, station_id: int, inverter_id: str, data: dict) -> None:
        if not self._taosws_available:
            return
        cursor = self._cursor()
        db = settings.tdengine_database
        sub_table = f"inv_{station_id}_{_safe_identifier(inverter_id)}"
        ts = data.get("timestamp", datetime.now().isoformat())
        cursor.execute(
            f"""
            INSERT INTO {db}.{sub_table}
            USING {db}.inverter_data
            TAGS (?, ?)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                station_id,
                inverter_id,
                ts,
                data.get("active_power_kw", 0.0),
                data.get("dc_voltage_v", 0.0),
                data.get("dc_current_a", 0.0),
                data.get("daily_energy_kwh", 0.0),
                data.get("total_energy_kwh", 0.0),
                data.get("inverter_status", 0),
                data.get("fault_code", 0),
                data.get("irradiance_w_m2", 0.0),
                data.get("ambient_temp_c", 0.0),
            ),
        )
        cursor.close()

    async def insert_weather_data(self, station_id: int, device_id: str, data: dict) -> None:
        if not self._taosws_available:
            return
        cursor = self._cursor()
        db = settings.tdengine_database
        sub_table = f"weather_{station_id}_{_safe_identifier(device_id)}"
        ts = data.get("timestamp", datetime.now().isoformat())
        cursor.execute(
            f"""
            INSERT INTO {db}.{sub_table}
            USING {db}.weather_data
            TAGS (?, ?)
            VALUES (?, ?, ?, ?, ?)
        """,
            (
                station_id,
                device_id,
                ts,
                data.get("irradiance_w_m2", 0.0),
                data.get("ambient_temp_c", 0.0),
                data.get("module_temp_c", 0.0),
                data.get("wind_speed_m_s", 0.0),
            ),
        )
        cursor.close()

    async def insert_meter_data(self, station_id: int, device_id: str, data: dict) -> None:
        if not self._taosws_available:
            return
        cursor = self._cursor()
        db = settings.tdengine_database
        sub_table = f"meter_{station_id}_{_safe_identifier(device_id)}"
        ts = data.get("timestamp", datetime.now().isoformat())
        cursor.execute(
            f"""
            INSERT INTO {db}.{sub_table}
            USING {db}.meter_data
            TAGS (?, ?)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                station_id,
                device_id,
                ts,
                data.get("active_power_kw", 0.0),
                data.get("reactive_power_kvar", 0.0),
                data.get("forward_active_energy_kwh", 0.0),
                data.get("reverse_active_energy_kwh", 0.0),
                data.get("voltage_v", 0.0),
                data.get("current_a", 0.0),
                data.get("power_factor", 0.0),
            ),
        )
        cursor.close()

    async def batch_insert_inverter_data(self, data_list: list[dict]) -> int:
        count = 0
        for data in data_list:
            try:
                await self.insert_inverter_data(
                    data.get("station_id", 0),
                    data.get("inverter_id", "INV001"),
                    data,
                )
                count += 1
            except Exception as e:
                logger.warning(f"TDengine 批量插入失败: {e}")
        return count

    async def get_latest_station_metrics(self, station_id: int) -> dict:
        if not self._taosws_available:
            return self._empty_metrics(station_id)
        try:
            cursor = self._cursor()
            db = settings.tdengine_database
            cursor.execute(
                f"""
                SELECT LAST(active_power_kw), LAST(daily_energy_kwh), LAST(irradiance_w_m2)
                FROM {db}.inverter_data
                WHERE station_id = ?
            """,
                (station_id,),
            )
            row = cursor.fetchone()
            cursor.close()
            if row:
                active_power = float(row[0]) if row[0] is not None else 0.0
                daily_energy = float(row[1]) if row[1] is not None else 0.0
                irradiance = float(row[2]) if row[2] is not None else 0.0
                pr = None
                if irradiance > 0:
                    theoretical = irradiance / 1000 * 1000
                    pr = min(1.0, active_power / theoretical) if theoretical > 0 else None
                return {
                    "station_id": station_id,
                    "station_name": f"电站 {station_id}",
                    "timestamp": datetime.now().isoformat(),
                    "active_power_kw": active_power,
                    "daily_energy_kwh": daily_energy,
                    "pr": pr,
                    "health_score": 100.0 if pr is None or pr > 0.3 else 60.0,
                }
        except Exception as e:
            logger.warning(f"获取 TDengine 最新指标失败: {e}")
        return self._empty_metrics(station_id)

    def _empty_metrics(self, station_id: int) -> dict:
        return {
            "station_id": station_id,
            "station_name": "",
            "timestamp": datetime.now().isoformat(),
            "active_power_kw": 0.0,
            "daily_energy_kwh": 0.0,
            "pr": None,
            "health_score": None,
        }

    async def get_metric_history(
        self,
        station_id: int,
        metric: str,
        start: datetime | None = None,
        end: datetime | None = None,
    ) -> list[dict]:
        if not self._taosws_available:
            return []
        if not end:
            end = datetime.now()
        if not start:
            start = end - timedelta(days=1)

        valid_metrics = {
            "active_power_kw",
            "daily_energy_kwh",
            "dc_voltage_v",
            "dc_current_a",
            "irradiance_w_m2",
            "ambient_temp_c",
        }
        if metric not in valid_metrics:
            return []

        try:
            cursor = self._cursor()
            db = settings.tdengine_database
            cursor.execute(
                f"""
                SELECT ts, {metric}
                FROM {db}.inverter_data
                WHERE station_id = ? AND ts >= ? AND ts <= ?
                ORDER BY ts ASC
            """,
                (station_id, start.isoformat(), end.isoformat()),
            )
            rows = cursor.fetchall()
            cursor.close()
            return [
                {"timestamp": str(row[0]), "value": float(row[1]) if row[1] is not None else 0.0}
                for row in rows
            ]
        except Exception as e:
            logger.warning(f"获取 TDengine 历史指标失败: {e}")
            return []

    async def get_daily_energy(self, station_id: int, date: datetime | None = None) -> float:
        if not self._taosws_available:
            return 0.0
        if not date:
            date = datetime.now()
        start = date.replace(hour=0, minute=0, second=0, microsecond=0)
        end = start + timedelta(days=1)
        try:
            cursor = self._cursor()
            db = settings.tdengine_database
            cursor.execute(
                f"""
                SELECT LAST(daily_energy_kwh)
                FROM {db}.inverter_data
                WHERE station_id = ? AND ts >= ? AND ts < ?
            """,
                (station_id, start.isoformat(), end.isoformat()),
            )
            row = cursor.fetchone()
            cursor.close()
            return float(row[0]) if row and row[0] is not None else 0.0
        except Exception as e:
            logger.warning(f"获取 TDengine 日发电量失败: {e}")
            return 0.0
