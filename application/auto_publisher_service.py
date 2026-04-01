"""自动发布服务 - 支持定时发布和手动触发"""
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from adapters.publishers import (
    MultiPublisher, PublishPayload,
    NotionPublisher, CsdnPublisher, TelegramPublisher,
    ZhihuPublisher, JuejinPublisher, XHSPublisher,
)
from core.models import PublisherType
from infrastructure.database import DatabaseManager, ReportRecord, ProjectRecord
from config_new import SETTINGS


logger = logging.getLogger(__name__)


class AutoPublisherService:
    """自动发布服务"""

    def __init__(
        self,
        db_manager: DatabaseManager,
        scheduler: AsyncIOScheduler | None = None,
    ):
        self.db_manager = db_manager
        self.scheduler = scheduler or AsyncIOScheduler()
        self._publishers = None
        self._load_schedule_config()

    def _load_schedule_config(self):
        """加载定时配置"""
        config_path = Path("state/schedule_config.json")
        if config_path.exists():
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    self.schedule_config = json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load schedule config: {e}")
                self.schedule_config = {
                    "enabled": False,
                    "cron": SETTINGS.schedule.cron,
                    "timezone": SETTINGS.schedule.timezone,
                    "platforms": ["notion"],
                }
        else:
            self.schedule_config = {
                "enabled": False,
                "cron": SETTINGS.schedule.cron,
                "timezone": SETTINGS.schedule.timezone,
                "platforms": ["notion"],
            }

    @property
    def publishers(self) -> MultiPublisher:
        """获取多平台发布器（延迟初始化）"""
        if self._publishers is None:
            publishers_list = [
                NotionPublisher(SETTINGS.publisher.notion_token, SETTINGS.publisher.notion_database_id),
                CsdnPublisher(SETTINGS.publisher.csdn_api, SETTINGS.publisher.csdn_token),
                TelegramPublisher(SETTINGS.publisher.telegram_bot_token, SETTINGS.publisher.telegram_chat_id),
                ZhihuPublisher(SETTINGS.publisher.zhihu_token),
                JuejinPublisher(SETTINGS.publisher.juejin_token),
                XHSPublisher(SETTINGS.publisher.xhs_cookie),
            ]
            self._publishers = MultiPublisher(publishers_list)
        return self._publishers

    async def publish_report(
        self,
        report_id: int,
        platforms: list[str] | None = None,
    ) -> dict[str, Any]:
        """发布指定报告到平台"""
        async with self.db_manager.session() as session:
            # 获取报告
            stmt = select(ReportRecord).where(ReportRecord.id == report_id)
            result = await session.execute(stmt)
            report = result.scalar_one_or_none()

            if not report:
                return {"success": False, "error": "报告未找到"}

            # 获取项目信息
            project_stmt = select(ProjectRecord).where(ProjectRecord.id == report.project_id)
            project_result = await session.execute(project_stmt)
            project = project_result.scalar_one_or_none()

            if not project:
                return {"success": False, "error": "关联项目未找到"}

            # 构建发布内容
            content = self._build_report_content(report, project)

            payload = PublishPayload(
                title=report.title,
                content_markdown=content,
                source_url=project.html_url,
                tags=project.topics or [],
                metadata={"report_id": report_id, "project_id": project.id},
            )

            # 确定要发布的平台
            platforms_to_publish = platforms or self.schedule_config.get("platforms", ["notion"])

            # 发布到指定平台
            results = {}
            for platform in platforms_to_publish:
                try:
                    success, result = await self.publishers.publish_to(platform, payload)
                    results[platform] = {
                        "success": success,
                        "result": result,
                        "timestamp": datetime.now().isoformat(),
                    }

                    # 更新报告的发布状态
                    if success:
                        published_at = json.loads(report.published_at) if report.published_at else {}
                        published_at[platform] = datetime.now().isoformat()
                        report.published_at = json.dumps(published_at)
                        await session.commit()

                except Exception as e:
                    logger.error(f"发布到 {platform} 失败: {e}")
                    results[platform] = {
                        "success": False,
                        "result": str(e),
                        "timestamp": datetime.now().isoformat(),
                    }

            return {
                "success": True,
                "report_id": report_id,
                "platforms": results,
            }

    async def publish_latest_reports(
        self,
        count: int = 1,
        platforms: list[str] | None = None,
    ) -> dict[str, Any]:
        """发布最新的 N 个未发布报告"""
        async with self.db_manager.session() as session:
            # 获取最新的报告
            stmt = (
                select(ReportRecord)
                .order_by(desc(ReportRecord.generated_at))
                .limit(count)
            )
            result = await session.execute(stmt)
            reports = result.scalars().all()

            results = []
            for report in reports:
                # 检查是否已发布到所有平台
                published_at = json.loads(report.published_at) if report.published_at else {}
                platforms_to_publish = platforms or self.schedule_config.get("platforms", [])

                # 过滤已发布的平台
                unpublishd_platforms = [
                    p for p in platforms_to_publish
                    if p not in published_at
                ]

                if unpublishd_platforms:
                    result = await self.publish_report(report.id, unpublishd_platforms)
                    results.append(result)

            return {
                "success": True,
                "processed": len(results),
                "results": results,
            }

    async def publish_all_unpublished(
        self,
        platforms: list[str] | None = None,
    ) -> dict[str, Any]:
        """发布所有未发布的报告"""
        async with self.db_manager.session() as session:
            # 获取所有报告
            stmt = select(ReportRecord)
            result = await session.execute(stmt)
            reports = result.scalars().all()

            results = []
            for report in reports:
                # 检查是否已发布到所有平台
                published_at = json.loads(report.published_at) if report.published_at else {}
                platforms_to_publish = platforms or self.schedule_config.get("platforms", [])

                # 过滤已发布的平台
                unpublished_platforms = [
                    p for p in platforms_to_publish
                    if p not in published_at
                ]

                if unpublished_platforms:
                    result = await self.publish_report(report.id, unpublished_platforms)
                    results.append(result)

            return {
                "success": True,
                "processed": len(results),
                "results": results,
            }

    def start_scheduler(self):
        """启动定时任务调度器"""
        if self.schedule_config.get("enabled", False):
            # 添加定时任务
            self.scheduler.add_job(
                self.publish_all_unpublished,
                'cron',
                **self._parse_cron(self.schedule_config["cron"]),
                id='auto_publish_job',
                replace_existing=True,
            )
            self.scheduler.start()
            logger.info(f"自动发布任务已启动，cron: {self.schedule_config['cron']}")
        else:
            logger.info("自动发布任务未启用")

    def stop_scheduler(self):
        """停止调度器"""
        if self.scheduler.running:
            self.scheduler.shutdown()
            logger.info("自动发布调度器已停止")

    def update_schedule_config(
        self,
        cron: str | None = None,
        timezone: str | None = None,
        platforms: list[str] | None = None,
        enabled: bool | None = None,
    ) -> dict[str, Any]:
        """更新定时配置"""
        if cron is not None:
            self.schedule_config["cron"] = cron
        if timezone is not None:
            self.schedule_config["timezone"] = timezone
        if platforms is not None:
            self.schedule_config["platforms"] = platforms
        if enabled is not None:
            self.schedule_config["enabled"] = enabled

        # 保存到文件
        config_path = Path("state/schedule_config.json")
        config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(self.schedule_config, f, ensure_ascii=False, indent=2)

        # 重启调度器
        self.stop_scheduler()
        self.start_scheduler()

        return {
            "success": True,
            "config": self.schedule_config,
        }

    def get_schedule_config(self) -> dict[str, Any]:
        """获取定时配置"""
        return self.schedule_config

    def get_enabled_publishers(self) -> list[dict[str, Any]]:
        """获取已启用的发布器列表"""
        return [
            {
                "name": "Notion",
                "type": "notion",
                "enabled": bool(SETTINGS.publisher.notion_token and SETTINGS.publisher.notion_database_id),
            },
            {
                "name": "CSDN",
                "type": "csdn",
                "enabled": bool(SETTINGS.publisher.csdn_api and SETTINGS.publisher.csdn_token),
            },
            {
                "name": "知乎",
                "type": "zhihu",
                "enabled": bool(SETTINGS.publisher.zhihu_token),
            },
            {
                "name": "掘金",
                "type": "juejin",
                "enabled": bool(SETTINGS.publisher.juejin_token),
            },
            {
                "name": "Telegram",
                "type": "telegram",
                "enabled": bool(SETTINGS.publisher.telegram_bot_token and SETTINGS.publisher.telegram_chat_id),
            },
            {
                "name": "小红书",
                "type": "xhs",
                "enabled": bool(SETTINGS.publisher.xhs_cookie),
            },
        ]

    def _build_report_content(self, report: ReportRecord, project: ProjectRecord) -> str:
        """构建报告内容"""
        content_parts = []

        # 标题
        content_parts.append(f"# {report.title}\n")

        # 项目信息
        content_parts.append("## 项目信息\n")
        content_parts.append(f"- 仓库链接：{project.html_url}\n")
        content_parts.append(f"- Star：{project.stars}\n")
        content_parts.append(f"- Fork：{project.forks}\n")
        content_parts.append(f"- 语言：{project.language}\n")

        if project.topics:
            content_parts.append(f"- 主题：{', '.join(project.topics)}\n")

        # 简介
        content_parts.append("\n## 项目简介\n")
        content_parts.append(f"{project.description}\n")

        # README 解析
        if project.readme:
            content_parts.append("\n## README 解析\n")
            # 提取关键信息
            readme_lines = project.readme.split('\n')[:15]
            for line in readme_lines:
                line = line.strip()
                if line and not line.startswith('#'):
                    content_parts.append(f"- {line}\n")

        # 建议
        content_parts.append("\n## 预览与建议\n")
        content_parts.append("- 建议先查看仓库首页的 Issue 与 Discussions，评估社区活跃度。\n")
        content_parts.append("- 建议重点阅读 README 的快速开始与部署部分，验证可落地性。\n")
        content_parts.append("- 可将该项目加入候选技术栈，后续结合业务场景做 PoC。\n")

        # Star 趋势
        full_name = project.full_name
        if full_name:
            star_history_url = f"https://www.star-history.com/?repos={full_name.replace('/', '%2F')}&type=date&legend=top-left"
            content_parts.append(f"\n## Star 趋势\n")
            content_parts.append(f"- {star_history_url}\n")

        # 生成时间
        content_parts.append(f"\n---\n")
        content_parts.append(f"*报告生成时间：{report.generated_at.strftime('%Y-%m-%d %H:%M:%S') if report.generated_at else 'N/A'}*\n")

        return '\n'.join(content_parts)

    def _parse_cron(self, cron_expr: str) -> dict[str, Any]:
        """解析 cron表达式"""
        # APScheduler cron 格式: minute hour day month day_of_week
        fields = cron_expr.split()
        if len(fields) != 5:
            raise ValueError("无效的 cron 表达式")

        return {
            'minute': fields[0],
            'hour': fields[1],
            'day': fields[2],
            'month': fields[3],
            'day_of_week': fields[4],
            'timezone': self.schedule_config.get('timezone', 'UTC'),
        }
