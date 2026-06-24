"""报告模型."""

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.sql import func

from app.core.database import Base


class DiagnosisReport(Base):
    """诊断报告表."""

    __tablename__ = "diagnosis_reports"

    id = Column(Integer, primary_key=True, index=True)
    station_id = Column(Integer, ForeignKey("stations.id"), nullable=False, index=True)
    report_type = Column(String(50), default="station", nullable=False)  # station / device
    device_id = Column(String(64), nullable=True)
    overall_health = Column(Float, default=100.0)
    summary = Column(Text, nullable=True)
    findings = Column(JSON, default=list)
    suggestions = Column(JSON, default=list)
    created_by = Column(String(50), default="system")
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class DiagnosisFeedback(Base):
    """诊断报告反馈."""

    __tablename__ = "diagnosis_feedback"

    id = Column(Integer, primary_key=True, index=True)
    report_id = Column(Integer, ForeignKey("diagnosis_reports.id"), nullable=False, index=True)
    rating = Column(String(20), nullable=False, comment="good / partial / bad")
    comment = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Report(Base):
    """运维报告表（日报/周报/月报）."""

    __tablename__ = "reports"

    id = Column(Integer, primary_key=True, index=True)
    station_id = Column(Integer, ForeignKey("stations.id"), nullable=True, index=True)
    report_type = Column(String(20), nullable=False)  # daily / weekly / monthly
    title = Column(String(200), nullable=False)
    start_date = Column(DateTime(timezone=True), nullable=False)
    end_date = Column(DateTime(timezone=True), nullable=False)
    total_energy_kwh = Column(Float, default=0.0)
    avg_pr = Column(Float, nullable=True)
    avg_health_score = Column(Float, nullable=True)
    alarm_count = Column(Integer, default=0)
    summary = Column(Text, nullable=True)
    details = Column(JSON, default=list)
    created_by = Column(String(50), default="system")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
