"""领域模型定义"""
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any


class SourceType(Enum):
    """数据源类型"""
    GITHUB = "github"
    HACKER_NEWS = "hacker_news"
    REDDIT = "reddit"
    PRODUCT_HUNT = "product_hunt"


class PublisherType(Enum):
    """发布平台类型"""
    NOTION = "notion"
    CSDN = "csdn"
    ZHIHU = "zhihu"
    JUEJIN = "juejin"
    TELEGRAM = "telegram"


@dataclass
class Project:
    """项目领域模型"""
    source: SourceType
    source_id: str
    rank: int
    full_name: str
    html_url: str
    description: str
    stars: int
    forks: int
    language: str
    topics: list[str]
    readme: str
    created_at: datetime | None = None
    updated_at: datetime | None = None
    metadata: dict[str, Any] | None = None

    @property
    def slug(self) -> str:
        return self.full_name.replace("/", "_")

    @property
    def activity_score(self) -> float:
        """计算活跃度分数"""
        star_weight = 1.0
        fork_weight = 0.5
        topic_weight = 10.0
        return (self.stars * star_weight +
                self.forks * fork_weight +
                len(self.topics) * topic_weight)


@dataclass
class Report:
    """报告领域模型"""
    id: str | None = None
    title: str = ""
    project: Project | None = None
    content_markdown: str = ""
    generated_at: datetime | None = None
    published_at: dict[PublisherType, datetime] | None = None
    insights: list[str] | None = None
    quality_score: float = 0.0


@dataclass
class QualityMetrics:
    """质量指标"""
    activity_score: float
    documentation_score: float
    security_score: float
    license_compliance: bool
    vulnerabilities: list[dict[str, Any]] | None = None
    overall_score: float = 0.0
