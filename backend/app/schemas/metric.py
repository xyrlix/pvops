"""指标 schema."""

from typing import Optional

from pydantic import BaseModel


class MetricPoint(BaseModel):
    """单个指标数据点."""

    timestamp: str
    value: float


class StationMetrics(BaseModel):
    """电站指标."""

    station_id: int
    station_name: str
    timestamp: str
    active_power_kw: float
    daily_energy_kwh: float
    pr: Optional[float] = None
    health_score: Optional[float] = None
