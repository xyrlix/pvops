"""时序数据模型（SQLite 版本，TDengine 未到位的替代）."""

from sqlalchemy import Column, DateTime, Float, Index, Integer, String
from sqlalchemy.sql import func

from app.core.database import Base


class InverterData(Base):
    """逆变器时序数据."""

    __tablename__ = "inverter_data"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime(timezone=True), nullable=False, index=True)
    station_id = Column(Integer, nullable=False, index=True)
    inverter_id = Column(String(64), nullable=False, index=True)
    active_power_kw = Column(Float, default=0.0)
    dc_voltage_v = Column(Float, default=0.0)
    dc_current_a = Column(Float, default=0.0)
    daily_energy_kwh = Column(Float, default=0.0)
    total_energy_kwh = Column(Float, default=0.0)
    inverter_status = Column(Integer, default=0)
    fault_code = Column(Integer, default=0)
    irradiance_w_m2 = Column(Float, default=0.0)
    ambient_temp_c = Column(Float, default=0.0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        Index("ix_inverter_data_station_time", "station_id", "timestamp"),
    )


class WeatherData(Base):
    """气象站时序数据."""

    __tablename__ = "weather_data"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime(timezone=True), nullable=False, index=True)
    station_id = Column(Integer, nullable=False, index=True)
    device_id = Column(String(64), nullable=False, default="WS001")
    irradiance_w_m2 = Column(Float, default=0.0)
    ambient_temp_c = Column(Float, default=0.0)
    module_temp_c = Column(Float, default=0.0)
    wind_speed_m_s = Column(Float, default=0.0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
