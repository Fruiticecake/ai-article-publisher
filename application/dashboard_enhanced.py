"""增强版 Web Dashboard - FastAPI"""
import io
import json
import logging
from pathlib import Path
from typing import Any
from datetime import datetime

from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.responses import Response, StreamingResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from core.models import Project, Report, PublisherType
from infrastructure.database import DatabaseManager, ProjectRecord, ReportRecord
from application.auth import AuthService
from application.project_manager import ProjectManager
from application.notifications import NotificationService
from application.document_generator import DocumentGenerator
from adapters.publishers import (
    MultiPublisher, PublishPayload,
    NotionPublisher, CsdnPublisher, TelegramPublisher,
    ZhihuPublisher, JuejinPublisher,
)
from config_new import SETTINGS


logger = logging.getLogger(__name__)

security = HTTPBearer()


class DashboardConfig:
    """Dashboard 配置"""

    def __init__(
        self,
        title: str = "Auto Publisher Dashboard",
        description: str = "GitHub 项目分析与发布平台",
        version: str = "2.0.0",
    ):
        self.title = title
        self.description = description
        self.version = version


# Pydantic 模型
class LoginRequest(BaseModel):
    username: str
    password: str


class RegisterRequest(BaseModel):
    username: str
    password: str
    email: str | None = None


class ProjectCreate(BaseModel):
    source: str
    source_id: str
    full_name: str
    html_url: str
    description: str
    stars: int
    forks: int
    language: str
    topics: list[str]
    readme: str | None = None
    rank: int = 0


class EnhancedDashboardAPI:
    """增强版 Dashboard API"""

    def __init__(
        self,
        db_manager: DatabaseManager,
        config: DashboardConfig | None = None,
    ):
        self.db_manager = db_manager
        self.config = config or DashboardConfig()
        self.auth_service = AuthService(db_manager)
        self.project_manager = ProjectManager(db_manager)
        self.notification_service = NotificationService()
        self.app = self._create_app()

    def _create_app(self) -> FastAPI:
        """创建 FastAPI 应用"""
        app = FastAPI(
            title=self.config.title,
            description=self.config.description,
            version=self.config.version,
        )

        # CORS 中间件
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

        # 挂载静态文件 (在路由设置之前挂载)
        # 使用绝对路径避免路径问题
        base_path = Path(r"D:\products\auto-publisher")
        frontend_path = base_path / "frontend" / "dist"
        if frontend_path.exists():
            print(f"Mounting frontend from: {frontend_path}")
            app.mount("/dashboard", StaticFiles(directory=str(frontend_path), html=True), name="dashboard")
        else:
            # 如果前端未构建，挂载源目录（仅用于开发）
            dev_path = base_path / "frontend"
            if dev_path.exists():
                print(f"Mounting frontend from dev: {dev_path}")
                app.mount("/dashboard", StaticFiles(directory=str(dev_path), html=True), name="dashboard")

        # 设置路由
        self._setup_routes(app)

        return app

    def _setup_routes(self, app: FastAPI) -> None:
        """设置路由"""

        # 认证相关路由
        @app.post("/api/auth/register", tags=["认证"])
        async def register(
            request: RegisterRequest,
        ) -> dict:
            """注册用户"""
            try:
                user = await self.auth_service.register(
                    username=request.username,
                    password=request.password,
                    email=request.email,
                )
                return {"success": True, "user": user}
            except ValueError as e:
                raise HTTPException(status_code=400, detail=str(e))

        @app.post("/api/auth/login", tags=["认证"])
        async def login(
            request: LoginRequest,
        ) -> dict:
            """登录用户"""
            try:
                result = await self.auth_service.login(
                    username=request.username,
                    password=request.password,
                )
                return {"success": True, **result}
            except ValueError as e:
                raise HTTPException(status_code=401, detail=str(e))

        @app.post("/api/auth/logout", tags=["认证"])
        async def logout() -> dict:
            """登出用户"""
            return {"success": True}

        @app.get("/api/auth/me", tags=["认证"])
        async def get_current_user(
            credentials: HTTPAuthorizationCredentials = Depends(security),
        ) -> dict:
            """获取当前用户"""
            user = await self.auth_service.get_current_user(credentials.credentials)
            if not user:
                raise HTTPException(status_code=401, detail="无效的 Token")
            return {"success": True, "user": user}

        # 项目相关路由
        @app.get("/api/projects", tags=["项目"])
        async def get_projects(
            limit: int = 20,
            offset: int = 0,
            keyword: str | None = None,
            language: str | None = None,
            min_stars: int | None = None,
        ):
            """获取项目列表（支持搜索和过滤）"""
            if keyword or language or min_stars:
                projects = await self.project_manager.search_projects(
                    keyword=keyword,
                    language=language,
                    min_stars=min_stars,
                    limit=limit,
                    offset=offset,
                )
            else:
                async with self.db_manager.session() as session:
                    stmt = (
                        select(ProjectRecord)
                        .order_by(desc(ProjectRecord.stars))
                        .offset(offset)
                        .limit(limit)
                    )
                    result = await session.execute(stmt)
                    projects = [self._project_to_dict(p) for p in result.scalars().all()]
            return projects

        @app.get("/api/projects/{project_id}", tags=["项目"])
        async def get_project(project_id: int):
            """获取单个项目"""
            project = await self.project_manager.get_project(project_id)
            if not project:
                raise HTTPException(status_code=404, detail="Project not found")
            return project

        @app.post("/api/projects", tags=["项目"])
        async def create_project(
            project_data: ProjectCreate,
            credentials: HTTPAuthorizationCredentials = Depends(security),
        ):
            """创建项目（需要认证）"""
            user = await self.auth_service.get_current_user(credentials.credentials)
            if not user or not user.get("is_admin"):
                raise HTTPException(status_code=403, detail="需要管理员权限")

            from core.models import SourceType, Project

            try:
                project = Project(
                    source=SourceType(project_data.source),
                    source_id=project_data.source_id,
                    full_name=project_data.full_name,
                    html_url=project_data.html_url,
                    description=project_data.description,
                    stars=project_data.stars,
                    forks=project_data.forks,
                    language=project_data.language,
                    topics=project_data.topics,
                    readme=project_data.readme,
                    rank=project_data.rank,
                )
                result = await self.project_manager.add_project(project)
                return {"success": True, **result}
            except ValueError as e:
                raise HTTPException(status_code=400, detail=str(e))

        @app.delete("/api/projects/{project_id}", tags=["项目"])
        async def delete_project(
            project_id: int,
            credentials: HTTPAuthorizationCredentials = Depends(security),
        ):
            """删除项目（需要认证）"""
            user = await self.auth_service.get_current_user(credentials.credentials)
            if not user or not user.get("is_admin"):
                raise HTTPException(status_code=403, detail="需要管理员权限")

            success = await self.project_manager.delete_project(project_id)
            if not success:
                raise HTTPException(status_code=404, detail="Project not found")
            return {"success": True}

        # 报告相关路由
        @app.get("/api/reports", tags=["报告"])
        async def get_reports(
            limit: int = 20,
            offset: int = 0,
        ):
            """获取报告列表"""
            async with self.db_manager.session() as session:
                stmt = (
                    select(ReportRecord)
                    .order_by(desc(ReportRecord.generated_at))
                    .offset(offset)
                    .limit(limit)
                )
                result = await session.execute(stmt)
                reports = [self._report_to_dict(r) for r in result.scalars().all()]
            return reports

        @app.get("/api/reports/{report_id}", tags=["报告"])
        async def get_report(report_id: int):
            """获取单个报告"""
            async with self.db.db_manager.session() as session:
                stmt = select(ReportRecord).where(ReportRecord.id == report_id)
                result = await session.execute(stmt)
                report = result.scalar_one_or_none()
                if not report:
                    raise HTTPException(status_code=404, detail="Report not found")
                return self._report_to_dict(report)

        # 统计相关路由
        @app.get("/api/stats", tags=["统计"])
        async def get_stats():
            """获取统计信息"""
            async with self.db_manager.session() as session:
                # 项目统计
                project_count_stmt = select(ProjectRecord).count()
                project_count = (await session.execute(project_count_stmt)).scalar()

                # 报告统计
                report_count_stmt = select(ReportRecord).count()
                report_count = (await session.execute(report_count_stmt)).scalar()

                return {
                    "total_projects": project_count,
                    "total_reports": report_count,
                }

        @app.get("/api/stats/project", tags=["统计"])
        async def get_project_stats():
            """获取项目统计"""
            return await self.project_manager.get_project_statistics()

        # ===== 文档导出相关路由 =====
        @app.get("/api/documents/export/markdown/{report_id}", tags=["文档导出"])
        async def export_markdown(report_id: int):
            """导出报告为 Markdown 格式"""
            async with self.db_manager.session() as session:
                stmt = select(ReportRecord).where(ReportRecord.id == report_id)
                result = await session.execute(stmt)
                report = result.scalar_one_or_none()
                
                if not report:
                    raise HTTPException(status_code=404, detail="报告未找到")
                
                # 从数据库获取报告内容（如果存储了的话）
                content = report.content_markdown if hasattr(report, 'content_markdown') else ""
                
                if not content:
                    # 生成默认内容
                    project_stmt = select(ProjectRecord).where(ProjectRecord.id == report.project_id)
                    project_result = await session.execute(project_stmt)
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
                    headers={"Content-Disposition": f"attachment; filename={filename}"}
                )

        @app.get("/api/documents/export/pdf/{report_id}", tags=["文档导出"])
        async def export_pdf(report_id: int):
            """导出报告为 PDF 格式"""
            doc_generator = DocumentGenerator(SETTINGS.reports_dir)
            
            async with self.db_manager.session() as session:
                stmt = select(ReportRecord).where(ReportRecord.id == report_id)
                result = await session.execute(stmt)
                report = result.scalar_one_or_none()
                
                if not report:
                    raise HTTPException(status_code=404, detail="报告未找到")
                
                # 获取项目信息
                project_stmt = select(ProjectRecord).where(ProjectRecord.id == report.project_id)
                project_result = await session.execute(project_stmt)
                project = project_result.scalar_one_or_none()
                
                if not project:
                    raise HTTPException(status_code=404, detail="关联项目未找到")
                
                # 准备项目数据
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
                
                # 生成 PDF
                pdf_bytes = doc_generator.create_report_pdf(project_data, insights)
                
                filename = f"report_{report_id}.pdf"
                return StreamingResponse(
                    io.BytesIO(pdf_bytes),
                    media_type="application/pdf",
                    headers={"Content-Disposition": f"attachment; filename={filename}"}
                )

        @app.post("/api/documents/export", tags=["文档导出"])
        async def export_document(
            project_id: int,
            format: str = "pdf",
            credentials: HTTPAuthorizationCredentials = Depends(security),
        ):
            """导出项目文档（支持 PDF 和 Markdown）"""
            user = await self.auth_service.get_current_user(credentials.credentials)
            if not user:
                raise HTTPException(status_code=401, detail="需要登录")
            
            doc_generator = DocumentGenerator(SETTINGS.reports_dir)
            
            async with self.db_manager.session() as session:
                stmt = select(ProjectRecord).where(ProjectRecord.id == project_id)
                result = await session.execute(stmt)
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
                    # 简单提取 README 前几行作为 insights
                    readme_lines = project.readme.split('\n')[:10]
                    insights = [line.strip() for line in readme_lines if line.strip() and not line.startswith('#')]
                
                if format.lower() == "pdf":
                    pdf_bytes = doc_generator.create_report_pdf(project_data, insights)
                    filename = f"{project.slug}_{datetime.now().strftime('%Y%m%d')}.pdf"
                    return StreamingResponse(
                        io.BytesIO(pdf_bytes),
                        media_type="application/pdf",
                        headers={"Content-Disposition": f"attachment; filename={filename}"}
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
                        headers={"Content-Disposition": f"attachment; filename={filename}"}
                    )
                else:
                    raise HTTPException(status_code=400, detail="不支持的格式，支持 pdf 和 markdown")

        # ===== 发布平台相关路由 =====
        @app.get("/api/publishers", tags=["发布平台"])
        async def get_publishers():
            """获取所有可用的发布平台及其配置状态"""
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

        @app.post("/api/publish/{report_id}", tags=["发布平台"])
        async def publish_report(
            report_id: int,
            platforms: list[str],
            credentials: HTTPAuthorizationCredentials = Depends(security),
        ):
            """手动发布报告到指定平台"""
            user = await self.auth_service.get_current_user(credentials.credentials)
            if not user:
                raise HTTPException(status_code=401, detail="需要登录")
            
            # 创建发布器
            publishers = [
                NotionPublisher(SETTINGS.publisher.notion_token, SETTINGS.publisher.notion_database_id),
                CsdnPublisher(SETTINGS.publisher.csdn_api, SETTINGS.publisher.csdn_token),
                TelegramPublisher(SETTINGS.publisher.telegram_bot_token, SETTINGS.publisher.telegram_chat_id),
                ZhihuPublisher(SETTINGS.publisher.zhihu_token),
                JuejinPublisher(SETTINGS.publisher.juejin_token),
            ]
            multi_publisher = MultiPublisher(publishers)
            
            # 获取报告内容
            async with self.db_manager.session() as session:
                stmt = select(ReportRecord).where(ReportRecord.id == report_id)
                result = await session.execute(stmt)
                report = result.scalar_one_or_none()
                
                if not report:
                    raise HTTPException(status_code=404, detail="报告未找到")
                
                # 获取项目信息
                project_stmt = select(ProjectRecord).where(ProjectRecord.id == report.project_id)
                project_result = await session.execute(project_stmt)
                project = project_result.scalar_one_or_none()
                
                if not project:
                    raise HTTPException(status_code=404, detail="关联项目未找到")
                
                # 构建发布内容
                content = report.content_markdown if hasattr(report, 'content_markdown') and report.content_markdown else f"""# {report.title}

{project.description}

项目链接：{project.html_url}
"""
            
            payload = PublishPayload(
                title=report.title,
                content_markdown=content,
                source_url=project.html_url if project else "",
                tags=project.topics if project and hasattr(project, 'topics') else None,
            )
            
            # 发布到选定的平台
            results = {}
            for platform in platforms:
                success, result = await multi_publisher.publish_to(platform, payload)
                results[platform] = {
                    "success": success,
                    "result": result,
                    "timestamp": datetime.now().isoformat(),
                }
            
            # 更新报告的发布状态
            async with self.db_manager.session() as session:
                stmt = select(ReportRecord).where(ReportRecord.id == report_id)
                result = await session.execute(stmt)
                report = result.scalar_one_or_none()
                if report:
                    published_at = json.loads(report.published_at) if report.published_at else {}
                    for platform in platforms:
                        published_at[platform] = datetime.now().isoformat()
                    report.published_at = json.dumps(published_at)
                    await session.commit()
            
            return {
                "success": True,
                "report_id": report_id,
                "platforms": results,
            }

        # ===== 定时发布配置相关路由 =====
        @app.get("/api/schedule", tags=["定时任务"])
        async def get_schedule(
            credentials: HTTPAuthorizationCredentials = Depends(security),
        ):
            """获取定时发布配置"""
            user = await self.auth_service.get_current_user(credentials.credentials)
            if not user:
                raise HTTPException(status_code=401, detail="需要登录")
            
            # 从配置读取
            return {
                "enabled": True,
                "cron": SETTINGS.schedule.cron,
                "timezone": SETTINGS.schedule.timezone,
                "platforms": ["notion", "csdn", "zhihu", "juejin", "telegram", "xhs"],
            }

        @app.post("/api/schedule", tags=["定时任务"])
        async def update_schedule(
            cron: str,
            timezone: str = "Asia/Shanghai",
            platforms: list[str] | None = None,
            enabled: bool = True,
            credentials: HTTPAuthorizationCredentials = Depends(security),
        ):
            """更新定时发布配置"""
            user = await self.auth_service.get_current_user(credentials.credentials)
            if not user or not user.get("is_admin"):
                raise HTTPException(status_code=403, detail="需要管理员权限")
            
            # 验证 cron 格式
            fields = cron.split()
            if len(fields) != 5:
                raise HTTPException(status_code=400, detail="无效的 cron 表达式")
            
            # 保存配置到文件（生产环境应该存数据库）
            schedule_config = {
                "cron": cron,
                "timezone": timezone,
                "platforms": platforms or ["notion"],
                "enabled": enabled,
            }
            
            config_path = Path("state/schedule_config.json")
            config_path.parent.mkdir(parents=True, exist_ok=True)
            config_path.write_text(json.dumps(schedule_config, ensure_ascii=False, indent=2), encoding="utf-8")
            
            return {
                "success": True,
                "config": schedule_config,
            }

        @app.post("/api/schedule/trigger", tags=["定时任务"])
        async def trigger_now(
            platforms: list[str] | None = None,
            credentials: HTTPAuthorizationCredentials = Depends(security),
        ):
            """立即触发一次发布任务"""
            user = await self.auth_service.get_current_user(credentials.credentials)
            if not user or not user.get("is_admin"):
                raise HTTPException(status_code=403, detail="需要管理员权限")
            
            # 记录手动触发日志
            logger.info(f"手动触发发布任务，平台: {platforms}")
            
            # 这里可以调用实际的执行逻辑
            # 实际实现中应该调用 DailyTaskExecutor
            
            return {
                "success": True,
                "message": "任务已触发",
                "platforms": platforms or ["notion", "csdn", "zhihu", "juejin", "telegram", "xhs"],
                "timestamp": datetime.now().isoformat(),
            }

        # 主页
        @app.get("/", response_class=HTMLResponse)
        async def root():
            """主页（重定向到前端）"""
            return """
            <!DOCTYPE html>
            <html>
            <head>
                <title>Auto Publisher</title>
                <meta http-equiv="refresh" content="0;url=/dashboard/">
            </head>
            <body>
                <p>正在跳转到 Dashboard...</p>
            </body>
            </html>
            """

        # 健康检查
        @app.get("/health", tags=["系统"])
        async def health_check() -> dict:
            """健康检查"""
            return {
                "status": "healthy",
                "version": self.config.version,
                "timestamp": datetime.utcnow().isoformat(),
            }

    def _project_to_dict(self, project: ProjectRecord) -> dict:
        """转换为字典"""
        return {
            "id": project.id,
            "source": project.source,
            "source_id": project.source_id,
            "full_name": project.full_name,
            "html_url": project.html_url,
            "description": project.description,
            "stars": project.stars,
            "forks": project.forks,
            "language": project.language,
            "topics": project.topics,
            "rank": project.rank,
            "created_at": project.created_at.isoformat() if project.created_at else None,
            "updated_at": project.updated_at.isoformat() if project.updated_at else None,
        }

    def _report_to_dict(self, report: ReportRecord) -> dict:
        """转换为字典"""
        return {
            "id": report.id,
            "title": report.title,
            "project_id": report.project_id,
            "quality_score": report.quality_score,
            "generated_at": report.generated_at.isoformat() if report.generated_at else None,
            "published_at": report.published_at,
            "insights": report.insights,
        }

    async def run(self, host: str = "0.0.0.0", port: int = 8080) -> None:
        """运行服务器"""
        import uvicorn
        config = uvicorn.Config(self.app, host=host, port=port, log_level="info")
        server = uvicorn.Server(config)
        await server.serve()
