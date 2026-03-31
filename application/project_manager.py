"""项目管理服务"""
import logging
from typing import Optional, Any

from sqlalchemy import select, delete, update
from sqlalchemy.ext.asyncio import AsyncSession

from infrastructure.database import DatabaseManager, ProjectRecord
from core.models import Project, SourceType


logger = logging.getLogger(__name__)


class ProjectManager:
    """项目管理器"""

    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager

    async def add_project(self, project: Project) -> dict:
        """添加项目"""
        async with self.db_manager.session() as session:
            # 检查是否已存在
            stmt = select(ProjectRecord).where(
                ProjectRecord.source == project.source.value,
                ProjectRecord.source_id == project.source_id
            )
            result = await session.execute(stmt)
            existing = result.scalar_one_or_none()

            if existing:
                # 更新现有项目
                await session.execute(
                    update(ProjectRecord)
                    .where(ProjectRecord.id == existing.id)
                    .values(
                        stars=project.stars,
                        forks=project.forks,
                        description=project.description,
                        readme=project.readme,
                        updated_at=project.updated_at,
                        metadata=project.metadata,
                    )
                )
                logger.info(f"更新项目: {project.full_name}")
                return {"id": existing.id, "action": "updated"}
            else:
                # 创建新项目
                project_record = ProjectRecord(
                    source=project.source.value,
                    source_id=project.source_id,
                    full_name=project.full_name,
                    html_url=project.html_url,
                    description=project.description,
                    stars=project.stars,
                    forks=project.forks,
                    language=project.language,
                    topics=project.topics,
                    readme=project.readme,
                    created_at=project.created_at,
                    updated_at=project.updated_at,
                    rank=project.rank,
                    metadata=project.metadata,
                )
                session.add(project_record)
                await session.flush()
                logger.info(f"添加项目: {project.full_name}")
                return {"id": project_record.id, "action": "created"}

    async def delete_project(self, project_id: int) -> bool:
        """删除项目"""
        async with self.db_manager.session() as session:
            stmt = delete(ProjectRecord).where(ProjectRecord.id == project_id)
            result = await session.execute(stmt)
            if result.rowcount > 0:
                logger.info(f"删除项目: {project_id}")
                return True
            return False

    async def get_project(self, project_id: int) -> Optional[dict]:
        """获取单个项目"""
        async with self.db_manager.session() as session:
            stmt = select(ProjectRecord).where(ProjectRecord.id == project_id)
            result = await session.execute(stmt)
            project = result.scalar_one_or_none()

            if not project:
                return None

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
                "readme": project.readme,
                "created_at": project.created_at.isoformat() if project.created_at else None,
                "updated_at": project.updated_at.isoformat() if project.updated_at else None,
                "rank": project.rank,
                "metadata": project.metadata,
            }

    async def search_projects(
        self,
        keyword: Optional[str] = None,
        language: Optional[str] = None,
        min_stars: Optional[int] = None,
        limit: int = 20,
        offset: int = 0,
    ) -> list[dict]:
        """搜索项目"""
        async with self.db_manager.session() as session:
            stmt = select(ProjectRecord)

            # 应用过滤条件
            if keyword:
                stmt = stmt.where(ProjectRecord.full_name.ilike(f"%{keyword}%"))
            if language:
                stmt = stmt.where(ProjectRecord.language == language)
            if min_stars:
                stmt = stmt.where(ProjectRecord.stars >= min_stars)

            # 排序和分页
            stmt = stmt.order_by(ProjectRecord.stars.desc()).offset(offset).limit(limit)

            result = await session.execute(stmt)
            projects = result.scalars().all()

            return [
                {
                    "id": p.id,
                    "full_name": p.full_name,
                    "html_url": p.html_url,
                    "description": p.description,
                    "stars": p.stars,
                    "forks": p.forks,
                    "language": p.language,
                    "topics": p.topics,
                    "rank": p.rank,
                }
                for p in projects
            ]

    async def get_project_statistics(self) -> dict:
        """获取项目统计"""
        async with self.db_manager.session() as session:
            # 总数
            count_stmt = select(Project).count()
            total = (await session.execute(count_stmt)).scalar()

            # 按语言分组
            language_stmt = select(ProjectRecord.language).distinct()
            languages = (await session.execute(language_stmt)).scalars().all()

            # 平均 Stars
            avg_stmt = select(ProjectRecord.stars).where(ProjectRecord.stars > 0)
            avg_result = await session.execute(avg_stmt)
            stars = avg_result.scalars().all()
            avg_stars = sum(stars) / len(stars) if stars else 0

            return {
                "total": total,
                "languages": list(languages),
                "average_stars": avg_stars,
            }
