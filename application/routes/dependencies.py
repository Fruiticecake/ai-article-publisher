"""Shared dependencies for route modules"""
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from config_new import SETTINGS
from application.auth import AuthService
from application.project_manager import ProjectManager
from application.auto_publisher_service import AutoPublisherService
from infrastructure.database import DatabaseManager

security = HTTPBearer()
db_manager = DatabaseManager(SETTINGS.database.url)
auth_service = AuthService(db_manager)
project_manager = ProjectManager(db_manager)
auto_publisher = AutoPublisherService(db_manager)


async def get_db() -> AsyncSession:
    """Get a database session"""
    async with db_manager.session() as session:
        yield session


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
) -> dict:
    """Get the current authenticated user"""
    user = await auth_service.get_current_user(credentials.credentials)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的 Token",
        )
    return user


async def get_current_admin(
    current_user: Annotated[dict, Depends(get_current_user)],
) -> dict:
    """Get the current authenticated user and verify it's an admin"""
    if not current_user.get("is_admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要管理员权限",
        )
    return current_user
