"""诊断接口."""

from typing import List, Optional

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

    report_dict = {
        "station_name": f"电站 {report.station_id}",
        "created_at": str(report.created_at),
        "summary": report.summary,
        "findings": report.findings or [],
    }
    try:
        pdf_bytes = generate_diagnosis_report_pdf(report_dict)
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e)) from e

    filename = f"diagnosis_report_{report_id}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
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
