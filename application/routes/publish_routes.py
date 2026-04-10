"""Publishing routes"""
import json
from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .dependencies import get_db, get_current_admin
from adapters.publishers import (
    MultiPublisher, PublishPayload,
    NotionPublisher, CsdnPublisher, TelegramPublisher,
    ZhihuPublisher, JuejinPublisher,
)
from infrastructure.database import ReportRecord, ProjectRecord, DatabaseManager
from application.auto_publisher_service import AutoPublisherService
from config_new import SETTINGS

router = APIRouter(tags=["发布平台"])


@router.get("/api/publishers")
async def get_publishers():
    """Get all available publishing platforms and their configuration status"""
    publishers_info = [
        {
            "name": "Notion",
            "type": "notion",
            "enabled": bool(SETTINGS.publisher.notion_token and SETTINGS.publisher.notion_database_id),
            "description": "发布到 Notion 数据库",
        },
        {
            "name": "CSDN",
            "type": "csdn",
            "enabled": bool(SETTINGS.publisher.csdn_api and SETTINGS.publisher.csdn_token),
            "description": "发布到 CSDN 博客",
        },
        {
            "name": "知乎",
            "type": "zhihu",
            "enabled": bool(SETTINGS.publisher.zhihu_token),
            "description": "发布到知乎",
        },
        {
            "name": "掘金",
            "type": "juejin",
            "enabled": bool(SETTINGS.publisher.juejin_token),
            "description": "发布到掘金",
        },
        {
            "name": "Telegram",
            "type": "telegram",
            "enabled": bool(SETTINGS.publisher.telegram_bot_token and SETTINGS.publisher.telegram_chat_id),
            "description": "通过 Telegram Bot 发送",
        },
        {
            "name": "小红书",
            "type": "xhs",
            "enabled": bool(SETTINGS.publisher.xhs_cookie),
            "description": "发布到小红书",
        },
    ]
    return publishers_info


@router.post("/api/publish/{report_id}")
async def publish_report(
    report_id: int,
    platforms: list[str],
    _: dict = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """Publish a report to specified platforms manually"""
    # Create publishers
    publishers = [
        NotionPublisher(SETTINGS.publisher.notion_token, SETTINGS.publisher.notion_database_id),
        CsdnPublisher(SETTINGS.publisher.csdn_api, SETTINGS.publisher.csdn_token),
        TelegramPublisher(SETTINGS.publisher.telegram_bot_token, SETTINGS.publisher.telegram_chat_id),
        ZhihuPublisher(SETTINGS.publisher.zhihu_token),
        JuejinPublisher(SETTINGS.publisher.juejin_token),
    ]
    multi_publisher = MultiPublisher(publishers)

    # Get report content
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

    # Build content
    content = report.content_markdown if hasattr(report, "content_markdown") and report.content_markdown else f"""# {report.title}

{project.description}

项目链接：{project.html_url}
"""

    payload = PublishPayload(
        title=report.title,
        content_markdown=content,
        source_url=project.html_url if project else "",
        tags=project.topics if project and hasattr(project, "topics") else None,
    )

    # Publish to selected platforms
    results = {}
    for platform in platforms:
        success, result = await multi_publisher.publish_to(platform, payload)
        results[platform] = {
            "success": success,
            "result": result,
            "timestamp": datetime.now().isoformat(),
        }

    # Update published status
    stmt = select(ReportRecord).where(ReportRecord.id == report_id)
    result = await db.execute(stmt)
    report = result.scalar_one_or_none()
    if report:
        published_at = json.loads(report.published_at) if report.published_at else {}
        for platform in platforms:
            published_at[platform] = datetime.now().isoformat()
        report.published_at = json.dumps(published_at)
        await db.commit()

    return {
        "success": True,
        "report_id": report_id,
        "platforms": results,
    }


@router.post("/api/publish/unpublished")
async def publish_all_unpublished(
    platforms: list[str] = None,
    _: dict = Depends(get_current_admin),
):
    """Publish all unpublished reports"""
    from infrastructure.database import DatabaseManager
    db_manager = DatabaseManager(SETTINGS.database.url)
    auto_publisher = AutoPublisherService(db_manager)

    result = await auto_publisher.publish_all_unpublished(platforms=platforms)
    return result
