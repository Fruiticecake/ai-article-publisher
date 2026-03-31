"""主程序 - 增强版"""
import argparse
import asyncio
import logging
from pathlib import Path

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from config_new import SETTINGS
from infrastructure.database import DatabaseManager
from application.services import DailyTaskExecutor
from application.monitoring import get_metrics_collector
from application.quality_service import QualityAnalyzer
from application.llm_service import LLMContentGenerator
from application.dashboard_enhanced import EnhancedDashboardAPI, DashboardConfig
from application.auth import AuthService
from application.project_manager import ProjectManager
from application.notifications import NotificationService
from application.task_queue import TaskQueue, TaskWorker
from adapters.github_adapter import GitHubAdapter
from adapters.publishers import (
    MultiPublisher,
    NotionPublisher,
    CsdnPublisher,
    TelegramPublisher,
    ZhihuPublisher,
    JuejinPublisher,
    XHSPublisher,
)


logging.basicConfig(
    level=getattr(logging, SETTINGS.log_level),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

logger = logging.getLogger(__name__)


async def initialize_database() -> DatabaseManager:
    """初始化数据库"""
    db_manager = DatabaseManager(SETTINGS.database.url)
    await db_manager.init_db()
    logger.info("数据库初始化完成")

    # 创建默认管理员用户
    auth_service = AuthService(db_manager)
    try:
        await auth_service.register(
            username="admin",
            password="admin123",
            email="admin@example.com"
        )
        logger.info("默认管理员用户已创建 (用户名: admin, 密码: admin123)")
    except ValueError as e:
        if "已存在" not in str(e):
            logger.info(f"管理员用户: {e}")

    return db_manager


def create_publishers() -> MultiPublisher:
    """创建发布器"""
    publishers = [
        NotionPublisher(SETTINGS.publisher.notion_token, SETTINGS.publisher.notion_database_id),
        CsdnPublisher(SETTINGS.publisher.csdn_api, SETTINGS.publisher.csdn_token),
        TelegramPublisher(SETTINGS.publisher.telegram_bot_token, SETTINGS.publisher.telegram_chat_id),
        ZhihuPublisher(SETTINGS.publisher.zhihu_token),
        JuejinPublisher(SETTINGS.publisher.juejin_token),
        XHSPublisher(SETTINGS.publisher.xhs_cookie),
    ]

    enabled_publishers = [p for p in publishers if p.enabled]
    logger.info(f"启用的发布平台: {[p.name for p in enabled_publishers]}")

    return MultiPublisher(enabled_publishers)


async def run_once() -> None:
    """执行一次任务"""
    logger.info("开始执行单次任务")

    # 初始化组件
    db_manager = await initialize_database()
    publishers = create_publishers()
    executor = DailyTaskExecutor(
        github_token=SETTINGS.github.token,
        reports_dir=SETTINGS.reports_dir,
        publishers=publishers,
    )

    # 执行任务
    try:
        result = await executor.execute()
        logger.info(f"任务执行成功: {result}")
    except Exception as e:
        logger.error(f"任务执行失败: {e}", exc_info=True)
    finally:
        await db_manager.close()


async def run_scheduled() -> None:
    """运行定时任务"""
    logger.info("启动定时任务模式")

    # 初始化监控
    if SETTINGS.monitoring.enabled:
        get_metrics_collector().start()

    # 初始化数据库
    db_manager = await initialize_database()

    # 创建发布器
    publishers = create_publishers()

    # 创建执行器
    executor = DailyTaskExecutor(
        github_token=SETTINGS.github.token,
        reports_dir=SETTINGS.reports_dir,
        publishers=publishers,
    )

    # 创建调度器
    fields = SETTINGS.schedule.cron.split()
    if len(fields) != 5:
        raise ValueError("SCHEDULE_CRON 必须是 5 段 cron 表达式")

    minute, hour, day, month, day_of_week = fields
    trigger = CronTrigger(
        minute=minute,
        hour=hour,
        day=day,
        month=month,
        day_of_week=day_of_week,
        timezone=SETTINGS.schedule.timezone,
    )

    scheduler = AsyncIOScheduler(timezone=SETTINGS.schedule.timezone)

    async def job():
        try:
            await executor.execute()
        except Exception as e:
            logger.error(f"定时任务执行失败: {e}", exc_info=True)

    scheduler.add_job(job, trigger=trigger, id="daily-github-analysis")
    scheduler.start()

    logger.info(f"定时任务已启动: cron={SETTINGS.schedule.cron}")

    # 启动 Dashboard
    if SETTINGS.monitoring.enabled:
        dashboard_config = DashboardConfig(
            title="Auto Publisher Dashboard",
            description="GitHub 项目分析与发布平台",
            version="2.0.0",
        )
        dashboard = EnhancedDashboardAPI(db_manager, dashboard_config)

        # 在后台运行 Dashboard
        import threading
        dashboard_thread = threading.Thread(
            target=lambda: dashboard.run(port=SETTINGS.monitoring.dashboard_port),
            daemon=True,
        )
        dashboard_thread.start()
        logger.info(f"Dashboard 已启动: http://0.0.0.0:{SETTINGS.monitoring.dashboard_port}")
        logger.info(f"API 文档: http://0.0.0.0:{SETTINGS.monitoring.dashboard_port}/docs")

    try:
        # 保持运行
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        logger.info("接收到中断信号，正在关闭...")
        scheduler.shutdown()
        await db_manager.close()
        logger.info("已关闭")


async def run_dashboard() -> None:
    """仅运行 Dashboard"""
    logger.info("启动 Dashboard 模式")

    db_manager = await initialize_database()

    dashboard_config = DashboardConfig(
        title="Auto Publisher Dashboard",
        description="GitHub 项目分析与发布平台",
        version="2.0.0",
    )
    dashboard = EnhancedDashboardAPI(db_manager, dashboard_config)
    await dashboard.run(port=SETTINGS.monitoring.dashboard_port)


def main() -> None:
    """主函数"""
    parser = argparse.ArgumentParser(description="Auto Publisher - GitHub 项目分析与多平台发布")
    parser.add_argument("--run-once", action="store_true", help="立即执行一次任务并退出")
    parser.add_argument("--dashboard", action="store_true", help="仅运行 Web Dashboard")

    args = parser.parse_args()

    if args.run_once:
        asyncio.run(run_once())
    elif args.dashboard:
        asyncio.run(run_dashboard())
    else:
        asyncio.run(run_scheduled())


if __name__ == "__main__":
    main()
