"""报告 schema."""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel


class Finding(BaseModel):
    """诊断发现项."""

    category: str
    severity: str
    title: str
    description: str
    evidence: List[str]
    root_cause: str
    suggestions: List[str]


class DiagnosisReportCreate(BaseModel):
    """创建诊断报告请求."""

    station_id: int
    report_type: str = "station"
    device_id: Optional[str] = None


class DiagnosisReportResponse(BaseModel):
    """诊断报告响应."""

    class Config:
        orm_mode = True

    id: int
    station_id: int
    report_type: str
    device_id: Optional[str]
    overall_health: float
    summary: str
    findings: List[Finding]
    suggestions: List[str]
    created_by: str
    created_at: datetime


class ReportCreate(BaseModel):
    """创建运维报告请求."""

    station_id: Optional[int] = None


class ReportResponse(BaseModel):
    """运维报告响应."""

    class Config:
        orm_mode = True

    id: int
    station_id: Optional[int]
    report_type: str
    title: str
    start_date: datetime
    end_date: datetime
    total_energy_kwh: float
    avg_pr: Optional[float]
    avg_health_score: Optional[float]
    alarm_count: int
    summary: str
    details: List[dict]
    created_by: str
    created_at: datetime
