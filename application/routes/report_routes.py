"""Report routes"""
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from .dependencies import get_db
from infrastructure.database import ReportRecord, ProjectRecord

router = APIRouter(tags=["报告"])


def _report_to_dict(report: ReportRecord) -> dict:
    """Convert report record to dictionary"""
    return {
        "id": report.id,
        "title": report.title,
        "project_id": report.project_id,
        "quality_score": report.quality_score,
        "generated_at": report.generated_at.isoformat() if report.generated_at else None,
        "published_at": report.published_at,
        "insights": report.insights,
    }


@router.get("/api/reports")
async def get_reports(
    limit: int = 20,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
):
    """Get reports list"""
    stmt = (
        select(ReportRecord)
        .order_by(desc(ReportRecord.generated_at))
        .offset(offset)
        .limit(limit)
    )
    result = await db.execute(stmt)
    reports = [_report_to_dict(r) for r in result.scalars().all()]
    return reports


@router.get("/api/reports/{report_id}")
async def get_report(
    report_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Get a single report by ID"""
    stmt = select(ReportRecord).where(ReportRecord.id == report_id)
    result = await db.execute(stmt)
    report = result.scalar_one_or_none()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    return _report_to_dict(report)


@router.get("/api/stats")
async def get_stats(
    db: AsyncSession = Depends(get_db),
):
    """Get dashboard statistics"""
    # Project count
    project_count_stmt = select(ProjectRecord)
    project_count_result = await db.execute(project_count_stmt)
    project_count = len(project_count_result.scalars().all())

    # Report count
    report_count_stmt = select(ReportRecord)
    report_count_result = await db.execute(report_count_stmt)
    report_count = len(report_count_result.scalars().all())

    return {
        "total_projects": project_count,
        "total_reports": report_count,
    }
