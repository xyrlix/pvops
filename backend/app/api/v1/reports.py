"""运维报告接口."""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.schemas.report import ReportCreate, ReportResponse
from app.services import pdf_service, report_service

router = APIRouter()


@router.get("", response_model=List[ReportResponse])
async def list_reports(
    station_id: Optional[int] = None,
    report_type: Optional[str] = None,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
) -> List:
    """获取报告列表."""
    return await report_service.list_reports(db, station_id, report_type, limit)


@router.post("/generate/{report_type}", response_model=ReportResponse)
async def generate_report(
    report_type: str,
    data: ReportCreate,
    current_user: User = Depends(get_current_user),
):
    """生成日报/周报/月报."""
    if report_type not in ("daily", "weekly", "monthly"):
        raise HTTPException(status_code=400, detail="报告类型必须是 daily/weekly/monthly")
    return await report_service.generate_report(
        report_type, data.station_id, created_by=current_user.username
    )


@router.get("/{report_id}/pdf")
async def export_report_pdf(report_id: int, db: AsyncSession = Depends(get_db)):
    """导出运维报告 PDF."""
    report = await report_service.get_report(db, report_id)
    if not report:
        raise HTTPException(status_code=404, detail="报告不存在")

    report_dict = ReportResponse.from_orm(report).dict()
    pdf_bytes = pdf_service.generate_operation_report_pdf(report_dict)
    filename = f"{report.report_type}_report_{report.id}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )
