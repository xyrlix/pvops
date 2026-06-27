"""报告 schema."""

from datetime import datetime

from pydantic import BaseModel


class Finding(BaseModel):
    """诊断发现项."""

    category: str
    severity: str
    title: str
    description: str
    evidence: list[str]
    root_cause: str
    suggestions: list[str]


class DiagnosisReportCreate(BaseModel):
    """创建诊断报告请求."""

    station_id: int
    report_type: str = "station"
    device_id: str | None = None


class DiagnosisReportResponse(BaseModel):
    """诊断报告响应."""

    class Config:
        orm_mode = True

    id: int
    station_id: int
    report_type: str
    device_id: str | None
    overall_health: float
    summary: str
    findings: list[Finding]
    suggestions: list[str]
    created_by: str
    created_at: datetime


class ReportCreate(BaseModel):
    """创建运维报告请求."""

    station_id: int | None = None


class ReportResponse(BaseModel):
    """运维报告响应."""

    class Config:
        orm_mode = True

    id: int
    station_id: int | None
    report_type: str
    title: str
    start_date: datetime
    end_date: datetime
    total_energy_kwh: float
    avg_pr: float | None
    avg_health_score: float | None
    alarm_count: int
    summary: str
    details: list[dict]
    created_by: str
    created_at: datetime
