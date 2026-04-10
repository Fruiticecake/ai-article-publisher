"""Route modules for the dashboard API"""
from .auth_routes import router as auth_router
from .config_routes import router as config_router
from .project_routes import router as project_router
from .report_routes import router as report_router
from .publish_routes import router as publish_router
from .schedule_routes import router as schedule_router
from .document_routes import router as document_router

__all__ = [
    "auth_router",
    "config_router",
    "project_router",
    "report_routes",
    "publish_router",
    "schedule_router",
    "document_router",
]
