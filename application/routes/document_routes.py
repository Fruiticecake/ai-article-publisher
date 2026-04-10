"""Document export routes"""
import io
from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import Response, StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .dependencies import get_db, get_current_admin
from application.document_generator import DocumentGenerator
from infrastructure.database import ProjectRecord, ReportRecord
from config_new import SETTINGS

router = APIRouter(tags=["文档导出"])


@router.get("/api/documents/export/markdown/{report_id}")
async def export_markdown(
    report_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Export report as Markdown"""
    stmt = select(ReportRecord).where(ReportRecord.id == report_id)
    result = await db.execute(stmt)
    report = result.scalar_one_or_none()
    if not report:
        raise HTTPException(status_code=404, detail="报告未找到")

    # Get content from database if stored
    content = report.content_markdown if hasattr(report, "content_markdown") else ""

    if not content:
        # Get project for default content
        project_stmt = select(ProjectRecord).where(ProjectRecord.id == report.project_id)
        project_result = await db.execute(project_stmt)
        project = project_result.scalar_one_or_none()
        if project:
            content = f"""# GitHub 项目分析报告：{project.full_name}

- 仓库链接：{project.html_url}
- Star：{project.stars}
- Fork：{project.forks}
- 语言：{project.language}
- 排名：Top {project.rank}

## 项目简介

{project.description}

## 分析建议

- 建议先查看仓库首页的 Issue 与 Discussions，评估社区活跃度。
- 建议重点阅读 README 的快速开始与部署部分，验证可落地性。
- 可将该项目加入候选技术栈，后续结合业务场景做 PoC。

---
*报告生成时间：{report.generated_at.strftime('%Y-%m-%d %H:%M:%S') if report.generated_at else 'N/A'}*
"""

    filename = f"report_{report_id}.md"
    return Response(
        content=content,
        media_type="text/markdown",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.get("/api/documents/export/pdf/{report_id}")
async def export_pdf(
    report_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Export report as PDF"""
    doc_generator = DocumentGenerator(SETTINGS.reports_dir)
    stmt = select(ReportRecord).where(ReportRecord.id == report_id)
    result = await db.execute(stmt)
    report = result.scalar_one_or_none()
    if not report:
        raise HTTPException(status_code=404, detail="报告未找到")

    # Get project info
    project_stmt = select(ProjectRecord).where(ProjectRecord.id == report.project_id)
    project_result = await db.execute(project_stmt)
    project = project_result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="关联项目未找到")

    # Prepare project data
    project_data = {
        'full_name': project.full_name,
        'html_url': project.html_url,
        'stars': project.stars,
        'forks': project.forks,
        'language': project.language,
        'rank': project.rank,
        'topics': project.topics or [],
        'description': project.description,
    }

    insights = report.insights or [] if report.insights else []

    # Generate PDF
    pdf_bytes = doc_generator.create_report_pdf(project_data, insights)

    filename = f"report_{report_id}.pdf"
    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.post("/api/documents/export")
async def export_document(
    project_id: int,
    format: str = "pdf",
    _: dict = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """Export project document (supports PDF and Markdown)"""
    doc_generator = DocumentGenerator(SETTINGS.reports_dir)
    stmt = select(ProjectRecord).where(ProjectRecord.id == project_id)
    result = await db.execute(stmt)
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="项目未找到")

    project_data = {
        'full_name': project.full_name,
        'html_url': project.html_url,
        'stars': project.stars,
        'forks': project.forks,
        'language': project.language,
        'rank': project.rank,
        'topics': project.topics or [],
        'description': project.description,
    }

    insights = []
    if project.readme:
        # Simple extract first few lines as insights
        readme_lines = project.readme.split('\n')[:10]
        insights = [line.strip() for line in readme_lines if line.strip() and not line.startswith('#')]

    if format.lower() == "pdf":
        pdf_bytes = doc_generator.create_report_pdf(project_data, insights)
        filename = f"{project.slug}_{datetime.now().strftime('%Y%m%d')}.pdf"
        return StreamingResponse(
            io.BytesIO(pdf_bytes),
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={filename}"},
        )
    elif format.lower() == "markdown":
        content = f"""# GitHub 项目分析报告：{project.full_name}

- 仓库链接：{project.html_url}
- Star 趋势：https://www.star-history.com/?repos={project.full_name.replace('/', '%2F')}&type=date&legend=top-left
- Star：{project.stars}
- Fork：{project.forks}
- 语言：{project.language}
- 主题：{', '.join(project.topics) if project.topics else '无'}

## 项目简介

{project.description}

## README 解析

{chr(10).join(f'- {insight}' for insight in insights)}

## 预览与建议

- 建议先查看仓库首页的 Issue 与 Discussions，评估社区活跃度。
- 建议重点阅读 README 的快速开始与部署部分，验证可落地性。
- 可将该项目加入候选技术栈，后续结合业务场景做 PoC。

---
*报告生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
"""
        filename = f"{project.slug}_{datetime.now().strftime('%Y%m%d')}.md"
        return Response(
            content=content,
            media_type="text/markdown",
            headers={"Content-Disposition": f"attachment; filename={filename}"},
        )
    else:
        raise HTTPException(status_code=400, detail="不支持的格式，支持 pdf 和 markdown")
