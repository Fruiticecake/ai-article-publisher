"""Web Dashboard - FastAPI"""
import logging
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from core.models import Project, Report
from infrastructure.database import DatabaseManager, ProjectRecord, ReportRecord
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession


logger = logging.getLogger(__name__)


class DashboardConfig:
    """Dashboard 配置"""

    def __init__(
        self,
        title: str = "Auto Publisher Dashboard",
        description: str = "GitHub 项目分析与发布平台",
    ):
        self.title = title
        self.description = description


class DashboardAPI:
    """Dashboard API"""

    def __init__(self, db_manager: DatabaseManager, config: DashboardConfig | None = None):
        self.db_manager = db_manager
        self.config = config or DashboardConfig()
        self.app = FastAPI(title=self.config.title)
        self._setup_routes()

    def _setup_routes(self) -> None:
        """设置路由"""

        @self.app.get("/", response_class=HTMLResponse)
        async def root():
            """主页"""
            return self._render_home()

        @self.app.get("/api/projects")
        async def get_projects(
            limit: int = Query(20, ge=1, le=100),
            offset: int = Query(0, ge=0),
        ):
            """获取项目列表"""
            async with self.db_manager.session() as session:
                stmt = (
                    select(ProjectRecord)
                    .order_by(desc(ProjectRecord.created_at))
                    .offset(offset)
                    .limit(limit)
                )
                result = await session.execute(stmt)
                projects = result.scalars().all()
                return [self._project_to_dict(p) for p in projects]

        @self.app.get("/api/projects/{project_id}")
        async def get_project(project_id: int):
            """获取单个项目"""
            async with self.db_manager.session() as session:
                stmt = select(ProjectRecord).where(ProjectRecord.id == project_id)
                result = await session.execute(stmt)
                project = result.scalar_one_or_none()
                if not project:
                    raise HTTPException(status_code=404, detail="Project not found")
                return self._project_to_dict(project)

        @self.app.get("/api/reports")
        async def get_reports(
            limit: int = Query(20, ge=1, le=100),
            offset: int = Query(0, ge=0),
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
                reports = result.scalars().all()
                return [self._report_to_dict(r) for r in reports]

        @self.app.get("/api/reports/{report_id}")
        async def get_report(report_id: int):
            """获取单个报告"""
            async with self.db_manager.session() as session:
                stmt = select(ReportRecord).where(ReportRecord.id == report_id)
                result = await session.execute(stmt)
                report = result.scalar_one_or_none()
                if not report:
                    raise HTTPException(status_code=404, detail="Report not found")
                return self._report_to_dict(report)

        @self.app.get("/api/stats")
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

    def _render_home(self) -> str:
        """渲染主页"""
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>{self.config.title}</title>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
        </head>
        <body>
            <nav class="navbar navbar-dark bg-dark mb-4">
                <div class="container">
                    <a class="navbar-brand" href="/">{self.config.title}</a>
                </div>
            </nav>

            <div class="container">
                <div class="row">
                    <div class="col-md-12">
                        <h1>{self.config.description}</h1>
                        <p>欢迎使用 Auto Publisher Dashboard</p>

                        <div class="card mb-4">
                            <div class="card-header">功能</div>
                            <div class="card-body">
                                <ul>
                                    <li><a href="/api/projects">项目列表 API</a></li>
                                    <li><a href="/api/reports">报告列表 API</a></li>
                                    <li><a href="/api/stats">统计信息 API</a></li>
                                </ul>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </body>
        </html>
        """

    def run(self, host: str = "0.0.0.0", port: int = 8080) -> None:
        """运行服务器"""
        import uvicorn
        uvicorn.run(self.app, host=host, port=port)
