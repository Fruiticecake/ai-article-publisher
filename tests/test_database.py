"""测试数据库管理"""
import pytest
import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from infrastructure.database import DatabaseManager, ProjectRecord, ReportRecord, UserRecord, Base


class TestDatabaseManager:
    """测试数据库管理器"""

    @pytest.mark.asyncio
    async def test_initialize_in_memory_database(self):
        """测试初始化内存数据库"""
        db = DatabaseManager("sqlite+aiosqlite:///:memory:")
        await db.init_db()
        await db.close()
        # 如果到达这里说明初始化成功
        assert True

    @pytest.mark.asyncio
    async def test_session_context_manager_commit(self):
        """测试会话上下文管理器提交"""
        db = DatabaseManager("sqlite+aiosqlite:///:memory:")
        await db.init_db()

        async with db.session() as session:
            # 验证返回类型正确
            assert isinstance(session, AsyncSession)
            # 插入一条测试数据
            project = ProjectRecord(
                source="github",
                source_id="123",
                full_name="test/test",
                html_url="https://github.com/test/test",
                description="Test",
                stars=100,
                forks=10,
                language="Python",
                topics={},
                rank=1,
            )
            session.add(project)

        # 提交后应该能查询到
        async with db.session() as session:
            result = await session.get(ProjectRecord, 1)
            assert result is not None
            assert result.full_name == "test/test"
            assert result.stars == 100

        await db.close()

    @pytest.mark.asyncio
    async def test_session_context_manager_rollback(self):
        """测试会话上下文管理器回滚"""
        db = DatabaseManager("sqlite+aiosqlite:///:memory:")
        await db.init_db()

        try:
            async with db.session() as session:
                project = ProjectRecord(
                    source="github",
                    source_id="456",
                    full_name="test/fail",
                    html_url="https://github.com/test/fail",
                    description="Test fail",
                    stars=50,
                    forks=5,
                    language="Python",
                    topics={},
                    rank=2,
                )
                session.add(project)
                raise ValueError("Intentional error for rollback test")
        except ValueError:
            pass

        # 出错回滚后应该查询不到
        async with db.session() as session:
            result = await session.get(ProjectRecord, 1)
            # 第一条插入失败回滚，应该不存在
            assert result is None

        await db.close()

    @pytest.mark.asyncio
    async def test_default_datetime_values(self):
        """测试 created_at / generated_at 默认值"""
        db = DatabaseManager("sqlite+aiosqlite:///:memory:")
        await db.init_db()

        before = datetime.datetime.utcnow()
        async with db.session() as session:
            project = ProjectRecord(
                source="github",
                source_id="789",
                full_name="test/defaults",
                html_url="https://github.com/test/defaults",
                description="Testing defaults",
                stars=10,
                forks=1,
                language="Python",
                topics={},
                rank=3,
            )
            session.add(project)

        async with db.session() as session:
            result = await session.get(ProjectRecord, 1)
            assert result is not None
            # created_at 应该有默认值
            assert result.created_at is not None
            assert result.created_at >= before

        # 测试 ReportRecord
        async with db.session() as session:
            report = ReportRecord(
                title="Test Report",
                project_id=1,
                content_markdown="# Test",
                quality_score=0.85,
            )
            session.add(report)

        async with db.session() as session:
            result = await session.get(ReportRecord, 1)
            assert result is not None
            assert result.generated_at is not None

        await db.close()

    @pytest.mark.asyncio
    async def test_user_record(self):
        """测试用户表"""
        db = DatabaseManager("sqlite+aiosqlite:///:memory:")
        await db.init_db()

        async with db.session() as session:
            user = UserRecord(
                username="admin",
                password="$2b$12$hashedpasswordhere",
                email="admin@example.com",
                is_active=True,
                is_admin=True,
            )
            session.add(user)

        async with db.session() as session:
            result = await session.get(UserRecord, 1)
            assert result is not None
            assert result.username == "admin"
            assert result.email == "admin@example.com"
            assert result.is_active is True
            assert result.is_admin is True

        await db.close()


class TestDatabaseModels:
    """测试数据库模型定义"""

    def test_table_names(self):
        """测试表名"""
        assert ProjectRecord.__tablename__ == "projects"
        assert ReportRecord.__tablename__ == "reports"
        assert UserRecord.__tablename__ == "users"

    def test_base_class(self):
        """测试基类"""
        assert issubclass(ProjectRecord, Base)
        assert issubclass(ReportRecord, Base)
        assert issubclass(UserRecord, Base)


if __name__ == "__main__":
    import datetime
    pytest.main([__file__, "-v"])
