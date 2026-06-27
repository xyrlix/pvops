"""诊断接口."""

from typing import Any, Dict, List, Optional
from urllib.parse import quote

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.diagnosis_agent import DiagnosisAgent
from app.core.database import AsyncSessionLocal, get_db
from app.core.deps import get_current_user
from app.core.limiter import limiter
from app.models.report import DiagnosisFeedback, DiagnosisReport
from app.schemas.report import DiagnosisReportCreate, DiagnosisReportResponse
from app.services.pdf_service import generate_diagnosis_report_pdf

router = APIRouter(dependencies=[Depends(get_current_user)])


@router.post("/station/{station_id}", response_model=DiagnosisReportResponse)
@limiter.limit("10/minute")  # 诊断重操作（多源数据查询 + LLM）
async def diagnose_station(request: Request, station_id: int) -> DiagnosisReport:
    """对电站进行诊断并生成报告."""
    agent = DiagnosisAgent()
    result = await agent.diagnose_station(station_id)

    async with AsyncSessionLocal() as session:
        report = DiagnosisReport(
            station_id=station_id,
            report_type="station",
            overall_health=result.get("overall_health", 100.0),
            summary=result.get("summary", ""),
            findings=result.get("findings", []),
            suggestions=result.get("suggestions", []),
            created_by="ai_agent",
        )
        session.add(report)
        await session.commit()
        await session.refresh(report)
        return report


@router.get("/reports", response_model=List[DiagnosisReportResponse])
async def list_reports(
    station_id: Optional[int] = None,
    limit: int = 20,
) -> List[DiagnosisReport]:
    """获取诊断报告列表."""
    async with AsyncSessionLocal() as session:
        query = select(DiagnosisReport)
        if station_id:
            query = query.where(DiagnosisReport.station_id == station_id)

        result = await session.execute(
            query.order_by(desc(DiagnosisReport.created_at)).limit(limit)
        )
        return list(result.scalars().all())


@router.get("/reports/{report_id}", response_model=DiagnosisReportResponse)
async def get_report(report_id: int) -> DiagnosisReport:
    """获取诊断报告详情."""
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(DiagnosisReport).where(DiagnosisReport.id == report_id)
        )
        report = result.scalar_one_or_none()
        if not report:
            raise HTTPException(status_code=404, detail="报告不存在")
        return report


@router.get("/reports/{report_id}/pdf")
async def export_report_pdf(report_id: int):
    """导出诊断报告 PDF."""
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(DiagnosisReport).where(DiagnosisReport.id == report_id)
        )
        report = result.scalar_one_or_none()
        if not report:
            raise HTTPException(status_code=404, detail="报告不存在")

        # 关联电站名称
        station_name = f"电站 {report.station_id}"
        if report.station_id:
            from app.models.station import Station

            s = await session.get(Station, report.station_id)
            if s and s.name:
                station_name = s.name

    # 转换 findings 字段名：suggestions -> suggestion（pdf_service 模板用的是单数）
    raw_findings = report.findings or []
    findings_for_pdf: List[Dict[str, Any]] = []
    for item in raw_findings:
        findings_for_pdf.append({
            "title": item.get("title", "未命名"),
            "category": item.get("category", ""),
            "severity": item.get("severity", "info"),
            "evidence": "\n".join(item.get("evidence", []) or []),
            "root_cause": item.get("root_cause", "-"),
            "suggestion": "\n".join(item.get("suggestions", []) or []),
        })

    overall = report.overall_health
    if overall is None:
        health_text = "-"
    elif overall >= 80:
        health_text = f"{overall:.1f}（健康）"
    elif overall >= 60:
        health_text = f"{overall:.1f}（亚健康）"
    else:
        health_text = f"{overall:.1f}（异常）"

    report_dict: Dict[str, Any] = {
        "title": "诊断报告",
        "station_name": station_name,
        "report_id": report.id,
        "created_at": report.created_at.strftime("%Y-%m-%d %H:%M:%S") if report.created_at else "-",
        "diagnosis_time": report.diagnosis_time.strftime("%Y-%m-%d %H:%M:%S") if report.diagnosis_time else "-",
        "overall_health": health_text,
        "summary": report.summary or "（无总结）",
        "findings": findings_for_pdf,
    }
    try:
        pdf_bytes = generate_diagnosis_report_pdf(report_dict)
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e)) from e

    filename = f"diagnosis_report_{report_id}_{station_name}.pdf"
    # RFC 5987 中文文件名编码
    encoded = quote(filename, safe="")
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": (
                f"attachment; filename=\"diagnosis_report_{report_id}.pdf\"; "
                f"filename*=UTF-8''{encoded}"
            )
        },
    )


@router.post("/reports/{report_id}/feedback")
async def create_feedback(report_id: int, data: dict):
    """提交诊断报告反馈."""
    rating = data.get("rating")
    comment = data.get("comment", "")
    if rating not in ("good", "partial", "bad"):
        raise HTTPException(status_code=400, detail="rating 必须是 good/partial/bad")

    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(DiagnosisReport).where(DiagnosisReport.id == report_id)
        )
        report = result.scalar_one_or_none()
        if not report:
            raise HTTPException(status_code=404, detail="报告不存在")

        feedback = DiagnosisFeedback(
            report_id=report_id,
            rating=rating,
            comment=comment,
        )
        session.add(feedback)
        await session.commit()
        await session.refresh(feedback)
        return {
            "id": feedback.id,
            "report_id": feedback.report_id,
            "rating": feedback.rating,
            "comment": feedback.comment,
            "created_at": feedback.created_at.isoformat() if feedback.created_at else None,
        }
