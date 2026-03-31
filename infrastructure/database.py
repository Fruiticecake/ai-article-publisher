"""数据库连接管理"""
from contextlib import asynccontextmanager
from datetime import datetime
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import String, Integer, Float, DateTime, JSON, Boolean


class Base(DeclarativeBase):
    pass


class ProjectRecord(Base):
    """项目数据库记录"""
    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    source: Mapped[str] = mapped_column(String(50), index=True)
    source_id: Mapped[str] = mapped_column(String(200), index=True)
    full_name: Mapped[str] = mapped_column(String(500), index=True)
    html_url: Mapped[str] = mapped_column(String(1000))
    description: Mapped[str] = mapped_column(String(2000))
    stars: Mapped[int] = mapped_column(Integer)
    forks: Mapped[int] = mapped_column(Integer)
    language: Mapped[str] = mapped_column(String(100))
    topics: Mapped[dict] = mapped_column(JSON)
    readme: Mapped[str] = mapped_column(String, nullable=True)
    repo_metadata: Mapped[dict] = mapped_column("metadata", JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    rank: Mapped[int] = mapped_column(Integer)


class ReportRecord(Base):
    """报告数据库记录"""
    __tablename__ = "reports"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(500))
    project_id: Mapped[int] = mapped_column(Integer, nullable=True, index=True)
    content_markdown: Mapped[str] = mapped_column(String)
    generated_at: Mapped[datetime] = mapped_column(DateTime)
    published_at: Mapped[dict] = mapped_column(JSON, nullable=True)
    insights: Mapped[list] = mapped_column(JSON, nullable=True)
    quality_score: Mapped[float] = mapped_column(Float)


class UserRecord(Base):
    """用户数据库记录"""
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    password: Mapped[str] = mapped_column(String(200))
    email: Mapped[str] = mapped_column(String(200), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)


class DatabaseManager:
    """数据库管理器"""

    def __init__(self, database_url: str = "sqlite+aiosqlite:///./auto_publisher.db"):
        self.database_url = database_url
        self.engine = create_async_engine(database_url, echo=False)
        self.async_session_maker = async_sessionmaker(
            self.engine, expire_on_commit=False, class_=AsyncSession
        )

    async def init_db(self) -> None:
        """初始化数据库表"""
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    async def close(self) -> None:
        """关闭数据库连接"""
        await self.engine.dispose()

    @asynccontextmanager
    async def session(self) -> AsyncGenerator[AsyncSession, None]:
        """获取数据库会话上下文"""
        async with self.async_session_maker() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
