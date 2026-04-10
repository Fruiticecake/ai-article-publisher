"""Schedule routes"""
import logging
from fastapi import APIRouter, HTTPException, Depends

from .dependencies import get_current_admin, auto_publisher

logger = logging.getLogger(__name__)
router = APIRouter(tags=["定时任务"])


@router.get("/api/schedule")
def get_schedule(
    _: dict = Depends(get_current_admin),
) -> dict:
    """Get schedule configuration"""
    config = auto_publisher.get_schedule_config()
    config["enabled_publishers"] = auto_publisher.get_enabled_publishers()
    return config


@router.post("/api/schedule")
async def update_schedule(
    cron: str = None,
    timezone: str = None,
    platforms: list[str] = None,
    enabled: bool = None,
    _: dict = Depends(get_current_admin),
):
    """Update schedule configuration"""
    # Validate cron format
    if cron:
        fields = cron.split()
        if len(fields) != 5:
            raise HTTPException(status_code=400, detail="无效的 cron 表达式")

    result = auto_publisher.update_schedule_config(
        cron=cron,
        timezone=timezone,
        platforms=platforms,
        enabled=enabled,
    )

    return result


@router.post("/api/schedule/trigger")
async def trigger_now(
    platforms: list[str] = None,
    count: int = 1,
    _: dict = Depends(get_current_admin),
):
    """Trigger a publish run immediately"""
    logger.info(f"手动触发发布任务，平台: {platforms}, 数量: {count}")

    result = await auto_publisher.publish_latest_reports(
        count=count,
        platforms=platforms,
    )

    return result
