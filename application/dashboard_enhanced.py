"""增强版 Web Dashboard - FastAPI"""
import logging
from pathlib import Path
from typing import Any
from datetime import datetime

from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from core.models import Project, Report
from infrastructure.database import DatabaseManager, ProjectRecord, ReportRecord
from application.auth import AuthService
from application.project_manager import ProjectManager
from application.notifications import NotificationService


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
