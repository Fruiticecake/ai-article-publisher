"""增强版 Web Dashboard - FastAPI"""
import io
import json
import logging
from pathlib import Path
from typing import Any
from datetime import datetime

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
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
from .routes import (
    auth_router,
    config_router,
    project_router,
    report_router,
    publish_router,
    schedule_router,
    document_router,
)


logger = logging.getLogger(__name__)


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
class LoginRequest:
    username: str
    password: str


class RegisterRequest:
    username: str
    password: str
    email: str | None = None


class ProjectCreate:
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
            allow_origins=SETTINGS.cors.get_origins(),
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
        # Get project root based on this file's location
        current_file = Path(__file__).resolve()
        base_path = current_file.parent.parent  # project root
        frontend_dist = base_path / "frontend" / "dist"

        @app.get("/{full_path:path}", response_class=HTMLResponse)
        async def serve_spa(full_path: str):
            """Serve SPA: static files or index.html for client-side routing"""

            # If it's a request for a static file (has file extension)
            # Try to serve it directly from dist directory
            if '.' in full_path and not full_path.endswith('.html'):
                static_path = (frontend_dist / full_path).resolve()
                frontend_dist_abs = frontend_dist.resolve()
                # Prevent path traversal: ensure the requested file is within frontend_dist
                if (static_path.exists() and static_path.is_file() and
                        frontend_dist_abs in static_path.parents or static_path.parent == frontend_dist_abs):
                    # Guess content type based on extension
                    content_type, _ = mimetypes.guess_type(str(static_path))
                    content_type = content_type or 'application/octet-stream'
                    with open(static_path, "rb") as f:
                        return io.Response(content=f.read(), media_type=content_type)

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
        """Setup routes - imported from modular route modules"""
        # Include all modular routers
        app.include_router(auth_router)
        app.include_router(config_router)
        app.include_router(project_router)
        app.include_router(report_router)
        app.include_router(publish_router)
        app.include_router(schedule_router)
        app.include_router(document_router)

        # Root route - redirect to frontend
        @app.get("/", response_class=HTMLResponse)
        async def root():
            """Root page (redirect to frontend)"""
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

        # Health check
        @app.get("/health", tags=["系统"])
        async def health_check() -> dict:
            """Health check"""
            return {
                "status": "healthy",
                "version": self.config.version,
                "timestamp": datetime.utcnow().isoformat(),
            }

    def _project_to_dict(self, project: ProjectRecord) -> dict:
        """Convert project record to dictionary"""
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

    async def run(self, host: str = None, port: int = None) -> None:
        """Run server"""
        import uvicorn
        host = host or SETTINGS.monitoring.dashboard_host
        port = port or SETTINGS.monitoring.dashboard_port
        config = uvicorn.Config(self.app, host=host, port=port, log_level="info")
        server = uvicorn.Server(config)
        await server.serve()
