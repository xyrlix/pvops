"""运维报告接口."""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.schemas.report import ReportCreate, ReportResponse
from app.services import report_service

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
