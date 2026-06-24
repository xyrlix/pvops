"""TDengine 服务."""

import logging
from datetime import datetime

from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

_connection = None
_taosws_available = False

try:
    import taosws
    _taosws_available = True
except ImportError:
    logger.warning("taosws 未安装，TDengine 功能将使用模拟数据")


async def get_connection():
    """获取 TDengine 连接."""
    global _connection
    if not _taosws_available:
        raise RuntimeError("taosws 未安装")
    if _connection is None:
        _connection = taosws.connect(
            f"taosws://{settings.tdengine_user}:{settings.tdengine_password}"
            f"@{settings.tdengine_host}:{settings.tdengine_port}"
        )
    return _connection


async def init_database() -> None:
    """初始化 TDengine 数据库和表."""
    try:
        conn = await get_connection()
        cursor = conn.cursor()

        # 创建数据库
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {settings.tdengine_database}")
        cursor.execute(f"USE {settings.tdengine_database}")

        # 创建逆变器数据超级表
        cursor.execute("""
            CREATE STABLE IF NOT EXISTS inverter_data (
                ts TIMESTAMP,
                active_power_kw FLOAT,
                dc_voltage_v FLOAT,
                dc_current_a FLOAT,
                daily_energy_kwh FLOAT,
                total_energy_kwh FLOAT,
                inverter_status INT,
                fault_code INT
            ) TAGS (
                station_id INT,
                inverter_id NCHAR(64)
            )
        """)

        # 创建气象数据超级表
        cursor.execute("""
            CREATE STABLE IF NOT EXISTS weather_data (
                ts TIMESTAMP,
                irradiance_w_m2 FLOAT,
                ambient_temp_c FLOAT,
                module_temp_c FLOAT,
                wind_speed_m_s FLOAT
            ) TAGS (
                station_id INT,
                device_id NCHAR(64)
            )
        """)

        cursor.close()
        logger.info("TDengine 数据库初始化完成")
    except Exception as e:
        logger.warning(f"TDengine 初始化失败（可能已存在）: {e}")


async def close() -> None:
    """关闭连接."""
    global _connection
    if _connection:
        _connection.close()
        _connection = None


async def insert_inverter_data(
    station_id: int,
    inverter_id: str,
    data: dict,
) -> None:
    """插入逆变器数据."""
    conn = await get_connection()
    cursor = conn.cursor()

    sql = f"""
        INSERT INTO {settings.tdengine_database}.inv_{station_id}_{inverter_id}
        USING {settings.tdengine_database}.inverter_data
        TAGS ({station_id}, '{inverter_id}')
        VALUES (
            '{data['timestamp']}',
            {data.get('active_power_kw', 0)},
            {data.get('dc_voltage_v', 0)},
            {data.get('dc_current_a', 0)},
            {data.get('daily_energy_kwh', 0)},
            {data.get('total_energy_kwh', 0)},
            {data.get('inverter_status', 0)},
            {data.get('fault_code', 0)}
        )
    """
    cursor.execute(sql)
    cursor.close()


async def get_latest_station_metrics(station_id: int) -> dict:
    """获取电站最新指标."""
    try:
        conn = await get_connection()
        cursor = conn.cursor()
        cursor.execute(f"""
            SELECT LAST(active_power_kw), LAST(daily_energy_kwh)
            FROM {settings.tdengine_database}.inverter_data
            WHERE station_id = {station_id}
        """)
        row = cursor.fetchone()
        cursor.close()

        if row:
            return {
                "station_id": station_id,
                "timestamp": datetime.now().isoformat(),
                "active_power_kw": float(row[0]) if row[0] else 0.0,
                "daily_energy_kwh": float(row[1]) if row[1] else 0.0,
            }
    except Exception as e:
        logger.warning(f"获取电站指标失败: {e}")

    return {
        "station_id": station_id,
        "timestamp": datetime.now().isoformat(),
        "active_power_kw": 0.0,
        "daily_energy_kwh": 0.0,
    }


async def get_metric_history(
    station_id: int,
    metric: str,
    start: str,
    end: str,
) -> list[dict]:
    """获取指标历史数据."""
    try:
        conn = await get_connection()
        cursor = conn.cursor()
        cursor.execute(f"""
            SELECT _irowts, {metric}
            FROM {settings.tdengine_database}.inverter_data
            WHERE station_id = {station_id}
              AND ts >= '{start}'
              AND ts <= '{end}'
            ORDER BY ts ASC
        """)
        rows = cursor.fetchall()
        cursor.close()

        return [
            {
                "timestamp": str(row[0]),
                "value": float(row[1]) if row[1] is not None else 0.0,
            }
            for row in rows
        ]
    except Exception as e:
        logger.warning(f"获取指标历史失败: {e}")
        return []
