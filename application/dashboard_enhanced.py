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
from application.auto_publisher_service import AutoPublisherService
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
        self.auto_publisher_service = AutoPublisherService(db_manager)
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

        # 配置 MIME 类型，修复 JavaScript 文件被识别为 JSON 的问题
        import mimetypes
        mimetypes.add_type('application/javascript', '.js')

        # 设置 API 路由优先 - all /api/* routes are handled first
        self._setup_routes(app)

        # SPA frontend routing - handle all non-API requests
        # For static files (JS/CSS/assets with extensions), serve them directly if they exist
        # For any other path (frontend routes like /login, /publish), serve index.html
        # so React Router can handle client-side routing correctly
        base_path = Path(r"D:\products\auto-publisher")
        frontend_dist = base_path / "frontend" / "dist"

        @app.get("/{full_path:path}", response_class=HTMLResponse)
        async def serve_spa(full_path: str):
            """Serve SPA: static files or index.html for client-side routing"""

            # If it's a request for a static file (has file extension)
            # Try to serve it directly from dist directory
            if '.' in full_path and not full_path.endswith('.html'):
                static_path = frontend_dist / full_path
                if static_path.exists() and static_path.is_file():
                    # Guess content type based on extension
                    content_type, _ = mimetypes.guess_type(str(static_path))
                    content_type = content_type or 'application/octet-stream'
                    with open(static_path, "rb") as f:
                        return Response(content=f.read(), media_type=content_type)

            # For root path or any frontend route (no extension)
            # Serve index.html to let React Router handle client-side routing
            index_path = frontend_dist / "index.html"
            if not index_path.exists():
                # Try development path
                index_path = base_path / "frontend" / "index.html"

            if index_path.exists():
                with open(index_path, "r", encoding="utf-8") as f:
                    return HTMLResponse(content=f.read())
            else:
                raise HTTPException(status_code=404, detail="Frontend not built. Please run npm run build in frontend directory.")

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
            async with self.db_manager.session() as session:
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
                project_count_stmt = select(ProjectRecord)
                project_count_result = await session.execute(project_count_stmt)
                project_count = len(project_count_result.scalars().all())

                # 报告统计
                report_count_stmt = select(ReportRecord)
                report_count_result = await session.execute(report_count_stmt)
                report_count = len(report_count_result.scalars().all())

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
        def get_schedule(
            credentials: HTTPAuthorizationCredentials = Depends(security),
        ):
            """获取定时发布配置"""
            # 从 auto_publisher_service 获取配置
            config = self.auto_publisher_service.get_schedule_config()
            config["enabled_publishers"] = self.auto_publisher_service.get_enabled_publishers()
            return config

        @app.post("/api/schedule", tags=["定时任务"])
        async def update_schedule(
            cron: str = None,
            timezone: str = None,
            platforms: list[str] = None,
            enabled: bool = None,
            credentials: HTTPAuthorizationCredentials = Depends(security),
        ):
            """更新定时发布配置"""
            user = await self.auth_service.get_current_user(credentials.credentials)
            if not user or not user.get("is_admin"):
                raise HTTPException(status_code=403, detail="需要管理员权限")

            # 验证 cron 格式
            if cron:
                fields = cron.split()
                if len(fields) != 5:
                    raise HTTPException(status_code=400, detail="无效的 cron 表达式")

            result = self.auto_publisher_service.update_schedule_config(
                cron=cron,
                timezone=timezone,
                platforms=platforms,
                enabled=enabled,
            )

            return result

        @app.post("/api/schedule/trigger", tags=["定时任务"])
        async def trigger_now(
            platforms: list[str] = None,
            count: int = 1,
            credentials: HTTPAuthorizationCredentials = Depends(security),
        ):
            """立即触发一次发布任务"""
            user = await self.auth_service.get_current_user(credentials.credentials)
            if not user or not user.get("is_admin"):
                raise HTTPException(status_code=403, detail="需要管理员权限")

            # 记录手动触发日志
            logger.info(f"手动触发发布任务，平台: {platforms}, 数量: {count}")

            # 调用自动发布服务
            result = await self.auto_publisher_service.publish_latest_reports(
                count=count,
                platforms=platforms,
            )

            return result

        @app.post("/api/publish/unpublished", tags=["发布平台"])
        async def publish_all_unpublished(
            platforms: list[str] = None,
            credentials: HTTPAuthorizationCredentials = Depends(security),
        ):
            """发布所有未发布的报告"""
            user = await self.auth_service.get_current_user(credentials.credentials)
            if not user:
                raise HTTPException(status_code=401, detail="需要登录")

            result = await self.auto_publisher_service.publish_all_unpublished(platforms=platforms)
            return result

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

        # 系统配置相关路由
        @app.get("/api/config/publishers", tags=["配置"])
        async def get_publisher_config(
            credentials: HTTPAuthorizationCredentials = Depends(security),
        ):
            """获取发布平台配置"""
            user = await self.auth_service.get_current_user(credentials.credentials)
            if not user or not user.get("is_admin"):
                raise HTTPException(status_code=403, detail="需要管理员权限")

            return {
                "notion_token": SETTINGS.publisher.notion_token,
                "notion_database_id": SETTINGS.publisher.notion_database_id,
                "csdn_api": SETTINGS.publisher.csdn_api,
                "csdn_token": SETTINGS.publisher.csdn_token,
                "zhihu_token": SETTINGS.publisher.zhihu_token,
                "juejin_token": SETTINGS.publisher.juejin_token,
                "telegram_bot_token": SETTINGS.publisher.telegram_bot_token,
                "telegram_chat_id": SETTINGS.publisher.telegram_chat_id,
                "xhs_cookie": SETTINGS.publisher.xhs_cookie,
            }

        @app.post("/api/config/publishers", tags=["配置"])
        async def update_publisher_config(
            notion_token: str = None,
            notion_database_id: str = None,
            csdn_api: str = None,
            csdn_token: str = None,
            zhihu_token: str = None,
            juejin_token: str = None,
            telegram_bot_token: str = None,
            telegram_chat_id: str = None,
            xhs_cookie: str = None,
            credentials: HTTPAuthorizationCredentials = Depends(security),
        ):
            """更新发布平台配置"""
            user = await self.auth_service.get_current_user(credentials.credentials)
            if not user or not user.get("is_admin"):
                raise HTTPException(status_code=403, detail="需要管理员权限")

            try:
                # 读取现有 .env 文件
                env_path = Path(".env")
                env_content = {}
                if env_path.exists():
                    with open(env_path, "r", encoding="utf-8") as f:
                        for line in f:
                            line = line.strip()
                            if line and not line.startswith("#") and "=" in line:
                                key, value = line.split("=", 1)
                                env_content[key.strip()] = value.strip()

                # 更新字段
                if notion_token is not None:
                    env_content["NOTION_TOKEN"] = notion_token
                    SETTINGS.publisher.notion_token = notion_token
                if notion_database_id is not None:
                    env_content["NOTION_DATABASE_ID"] = notion_database_id
                    SETTINGS.publisher.notion_database_id = notion_database_id
                if csdn_api is not None:
                    env_content["CSDN_PUBLISH_API"] = csdn_api
                    SETTINGS.publisher.csdn_api = csdn_api
                if csdn_token is not None:
                    env_content["CSDN_TOKEN"] = csdn_token
                    SETTINGS.publisher.csdn_token = csdn_token
                if zhihu_token is not None:
                    env_content["ZHIHU_TOKEN"] = zhihu_token
                    SETTINGS.publisher.zhihu_token = zhihu_token
                if juejin_token is not None:
                    env_content["JUEJIN_TOKEN"] = juejin_token
                    SETTINGS.publisher.juejin_token = juejin_token
                if telegram_bot_token is not None:
                    env_content["TELEGRAM_BOT_TOKEN"] = telegram_bot_token
                    SETTINGS.publisher.telegram_bot_token = telegram_bot_token
                if telegram_chat_id is not None:
                    env_content["TELEGRAM_CHAT_ID"] = telegram_chat_id
                    SETTINGS.publisher.telegram_chat_id = telegram_chat_id
                if xhs_cookie is not None:
                    env_content["XHS_COOKIE"] = xhs_cookie
                    SETTINGS.publisher.xhs_cookie = xhs_cookie

                # 写回 .env 文件
                with open(env_path, "w", encoding="utf-8") as f:
                    for key, value in env_content.items():
                        f.write(f"{key}={value}\n")

                return {
                    "success": True,
                    "message": "配置已保存，部分配置可能需要重启服务器后生效",
                }
            except Exception as e:
                logger.error(f"保存配置失败: {e}")
                raise HTTPException(status_code=500, detail=f"保存配置失败: {str(e)}")

        @app.get("/api/config/llm", tags=["配置"])
        async def get_llm_config(
            credentials: HTTPAuthorizationCredentials = Depends(security),
        ):
            """获取 LLM 配置"""
            user = await self.auth_service.get_current_user(credentials.credentials)
            if not user or not user.get("is_admin"):
                raise HTTPException(status_code=403, detail="需要管理员权限")

            return {
                "api_key": SETTINGS.llm.api_key,
                "model": SETTINGS.llm.model,
                "enabled": SETTINGS.llm.enabled,
            }

        @app.post("/api/config/llm", tags=["配置"])
        async def update_llm_config(
            api_key: str = None,
            model: str = None,
            enabled: bool = None,
            credentials: HTTPAuthorizationCredentials = Depends(security),
        ):
            """更新 LLM 配置"""
            user = await self.auth_service.get_current_user(credentials.credentials)
            if not user or not user.get("is_admin"):
                raise HTTPException(status_code=403, detail="需要管理员权限")

            try:
                env_path = Path(".env")
                env_content = {}
                if env_path.exists():
                    with open(env_path, "r", encoding="utf-8") as f:
                        for line in f:
                            line = line.strip()
                            if line and not line.startswith("#") and "=" in line:
                                key, value = line.split("=", 1)
                                env_content[key.strip()] = value.strip()

                if api_key is not None:
                    env_content["LLM_API_KEY"] = api_key
                    SETTINGS.llm.api_key = api_key
                if model is not None:
                    env_content["LLM_MODEL"] = model
                    SETTINGS.llm.model = model
                if enabled is not None:
                    env_content["LLM_ENABLED"] = str(enabled).lower()
                    SETTINGS.llm.enabled = enabled

                with open(env_path, "w", encoding="utf-8") as f:
                    for key, value in env_content.items():
                        f.write(f"{key}={value}\n")

                return {
                    "success": True,
                    "message": "LLM 配置已保存",
                }
            except Exception as e:
                logger.error(f"保存 LLM 配置失败: {e}")
                raise HTTPException(status_code=500, detail=f"保存配置失败: {str(e)}")

        # GitHub 配置
        @app.get("/api/config/github", tags=["配置"])
        async def get_github_config(
            credentials: HTTPAuthorizationCredentials = Depends(security),
        ):
            """获取 GitHub 配置"""
            user = await self.auth_service.get_current_user(credentials.credentials)
            if not user or not user.get("is_admin"):
                raise HTTPException(status_code=403, detail="需要管理员权限")

            return {
                "token": SETTINGS.github.token,
                "fetch_count": SETTINGS.github.fetch_count,
                "days_window": SETTINGS.github.days_window,
            }

        @app.post("/api/config/github", tags=["配置"])
        async def update_github_config(
            token: str = None,
            fetch_count: int = None,
            days_window: int = None,
            credentials: HTTPAuthorizationCredentials = Depends(security),
        ):
            """更新 GitHub 配置"""
            user = await self.auth_service.get_current_user(credentials.credentials)
            if not user or not user.get("is_admin"):
                raise HTTPException(status_code=403, detail="需要管理员权限")

            try:
                env_path = Path(".env")
                env_content = {}
                if env_path.exists():
                    with open(env_path, "r", encoding="utf-8") as f:
                        for line in f:
                            line = line.strip()
                            if line and not line.startswith("#") and "=" in line:
                                key, value = line.split("=", 1)
                                env_content[key.strip()] = value.strip()

                if token is not None:
                    env_content["GITHUB_TOKEN"] = token
                    SETTINGS.github.token = token
                if fetch_count is not None:
                    env_content["GITHUB_FETCH_COUNT"] = str(fetch_count)
                    SETTINGS.github.fetch_count = fetch_count
                if days_window is not None:
                    env_content["GITHUB_DAYS_WINDOW"] = str(days_window)
                    SETTINGS.github.days_window = days_window

                with open(env_path, "w", encoding="utf-8") as f:
                    for key, value in env_content.items():
                        f.write(f"{key}={value}\n")

                return {
                    "success": True,
                    "message": "GitHub 配置已保存",
                }
            except Exception as e:
                logger.error(f"保存 GitHub 配置失败: {e}")
                raise HTTPException(status_code=500, detail=f"保存配置失败: {str(e)}")

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
