"""仓储接口定义"""
from abc import ABC, abstractmethod
from typing import Any

from core.models import Project, Report, QualityMetrics


class ProjectRepository(ABC):
    """项目仓储接口"""

    @abstractmethod
    async def save(self, project: Project) -> None:
        """保存项目"""
        pass

    @abstractmethod
    async def find_by_source_id(self, source: str, source_id: str) -> Project | None:
        """根据来源查找项目"""
        pass

    @abstractmethod
    async def find_recent(self, limit: int = 100) -> list[Project]:
        """查找最近的项目"""
        pass


class ReportRepository(ABC):
    """报告仓储接口"""

    @abstractmethod
    async def save(self, report: Report) -> str:
        """保存报告，返回ID"""
        pass

    @abstractmethod
    async def find_by_id(self, report_id: str) -> Report | None:
        """根据ID查找报告"""
        pass

    @abstractmethod
    async def find_recent(self, limit: int = 100) -> list[Report]:
        """查找最近的报告"""
        pass
