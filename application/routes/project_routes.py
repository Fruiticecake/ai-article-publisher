"""Project routes"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from .dependencies import get_db, get_current_admin, project_manager
from core.models import Project, SourceType
from infrastructure.database import ProjectRecord

router = APIRouter(tags=["项目"])


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


def _project_to_dict(project: ProjectRecord) -> dict:
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


@router.get("/api/projects")
async def get_projects(
    limit: int = 20,
    offset: int = 0,
    keyword: str | None = None,
    language: str | None = None,
    min_stars: int | None = None,
    db: AsyncSession = Depends(get_db),
):
    """Get projects list with search and filtering"""
    if keyword or language or min_stars:
        projects = await project_manager.search_projects(
            keyword=keyword,
            language=language,
            min_stars=min_stars,
            limit=limit,
            offset=offset,
        )
    else:
        stmt = (
            select(ProjectRecord)
            .order_by(desc(ProjectRecord.stars))
            .offset(offset)
            .limit(limit)
        )
        result = await db.execute(stmt)
        projects = [_project_to_dict(p) for p in result.scalars().all()]
    return projects


@router.get("/api/projects/{project_id}")
async def get_project(project_id: int):
    """Get a single project by ID"""
    project = await project_manager.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@router.post("/api/projects")
async def create_project(
    project_data: ProjectCreate,
    _: dict = Depends(get_current_admin),
):
    """Create a new project (requires admin)"""
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
        result = await project_manager.add_project(project)
        return {"success": True, **result}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/api/projects/{project_id}")
async def delete_project(
    project_id: int,
    _: dict = Depends(get_current_admin),
):
    """Delete a project (requires admin)"""
    success = await project_manager.delete_project(project_id)
    if not success:
        raise HTTPException(status_code=404, detail="Project not found")
    return {"success": True}


@router.get("/api/stats/project")
async def get_project_stats():
    """Get project statistics"""
    return await project_manager.get_project_statistics()
