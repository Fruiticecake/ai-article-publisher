"""自动发布服务测试"""
import json
import pytest
from datetime import datetime
from pathlib import Path

from application.auto_publisher_service import AutoPublisherService
from infrastructure.database import DatabaseManager, ReportRecord, ProjectRecord
from core.models import SourceType
from pytest_asyncio import fixture as pytest_asyncio_fixture


@pytest_asyncio_fixture
async def db_manager():
    """创建测试数据库"""
    db = DatabaseManager("sqlite+aiosqlite:///:memory:")
    await db.init_db()
    yield db
    await db.close()


@pytest_asyncio_fixture
async def auto_publisher_service(db_manager):
    """创建自动发布服务"""
    service = AutoPublisherService(db_manager)
    yield service


@pytest.mark.asyncio
async def test_get_enabled_publishers(auto_publisher_service):
    """测试获取启用的发布器"""
    publishers = auto_publisher_service.get_enabled_publishers()

    # 验证返回结构
    assert isinstance(publishers, list)
    assert len(publishers) >= 6

    # 验证每个发布器的结构
    for publisher in publishers:
        assert "name" in publisher
        assert "type" in publisher
        assert "enabled" in publisher
        assert isinstance(publisher["enabled"], bool)


@pytest.mark.asyncio
async def test_get_schedule_config(auto_publisher_service):
    """测试获取定时配置"""
    config = auto_publisher_service.get_schedule_config()

    # 验证配置结构
    assert "enabled" in config
    assert "cron" in config
    assert "timezone" in config
    assert "platforms" in config
    assert isinstance(config["platforms"], list)


@pytest.mark.asyncio
async def test_update_schedule_config(auto_publisher_service):
    """测试更新定时配置"""
    # 更新配置
    result = auto_publisher_service.update_schedule_config(
        cron="*/5 * * * *",
        timezone="Asia/Shanghai",
        platforms=["notion", "telegram"],
        enabled=True,
    )

    # 验证更新结果
    assert result["success"] is True
    assert result["config"]["cron"] == "*/5 * * * *"
    assert result["config"]["timezone"] == "Asia/Shanghai"
    assert result["config"]["platforms"] == ["notion", "telegram"]
    assert result["config"]["enabled"] is True


@pytest.mark.asyncio
async def test_publish_report_not_found(auto_publisher_service):
    """测试发布不存在的报告"""
    result = await auto_publisher_service.publish_report(report_id=999999)

    # 验证失败结果
    assert result["success"] is False
    assert "error" in result


@pytest.mark.asyncio
async def test_publish_all_unpublished(db_manager, auto_publisher_service):
    """测试发布所有未发布的报告"""
    # 创建测试数据
    async with db_manager.session() as session:
        project = ProjectRecord(
            source=SourceType.GITHUB.value,
            source_id="test_repo",
            full_name="test/test_repo",
            html_url="https://github.com/test/test_repo",
            description="Test repository",
            stars=100,
            forks=10,
            language="Python",
            topics=["test", "demo"],
            readme="# Test README\n\nThis is a test repository.",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            rank=1,
        )
        session.add(project)
        await session.commit()

        report = ReportRecord(
            project_id=project.id,
            title="Test Report",
            content_markdown="# Test Report\n\nTest content.",
            quality_score=0.85,
            generated_at=datetime.utcnow(),
            published_at="{}",
        )
        session.add(report)
        await session.commit()

    # 测试发布（因为没有配置真实的 API Token，应该失败但代码能正常执行）
    result = await auto_publisher_service.publish_all_unpublished(platforms=["notion"])

    # 验证结果结构
    assert "success" in result
    assert "processed" in result
    assert isinstance(result["results"], list)


@pytest.mark.asyncio
async def test_publish_latest_reports(db_manager, auto_publisher_service):
    """测试发布最新报告"""
    # 创建多个测试报告
    async with db_manager.session() as session:
        project = ProjectRecord(
            source=SourceType.GITHUB.value,
            source_id="test_repo2",
            full_name="test/test_repo2",
            html_url="https://github.com/test/test_repo2",
            description="Test repository 2",
            stars=200,
            forks=20,
            language="TypeScript",
            topics=["test2"],
            readme="# Test README 2",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            rank=2,
        )
        session.add(project)
        await session.commit()

        for i in range(3):
            report = ReportRecord(
                project_id=project.id,
                title=f"Test Report {i}",
                content_markdown=f"# Test Report {i}\n\nContent {i}.",
                quality_score=0.8 + (i * 0.05),
                generated_at=datetime.now(),
                published_at="{}",
            )
            session.add(report)
        await session.commit()

    # 测试发布最新 2 个报告
    result = await auto_publisher_service.publish_latest_reports(count=2)

    # 验证结果
    assert "success" in result
    assert "processed" in result


@pytest.mark.asyncio
async def test_schedule_config_persistence(auto_publisher_service):
    """测试配置持久化"""
    # 修改配置
    auto_publisher_service.update_schedule_config(
        cron="0 0 * * *",
        timezone="UTC",
        platforms=["telegram"],
        enabled=False,
    )

    # 验证文件存在
    config_path = Path("state/schedule_config.json")
    if config_path.exists():
        with open(config_path, 'r', encoding='utf-8') as f:
            saved_config = json.load(f)

        assert saved_config["cron"] == "0 0 * * *"
        assert saved_config["timezone"] == "UTC"
        assert saved_config["platforms"] == ["telegram"]
        assert saved_config["enabled"] is False


def test_parse_cron():
    """测试 cron 表达式解析"""
    import asyncio
    async def test():
        db = DatabaseManager("sqlite+aiosqlite:///:memory:")
        await db.init_db()
        service = AutoPublisherService(db)

        # 测试标准 cron 表达式
        result = service._parse_cron("0 9 * * 1-5")
        assert result["minute"] == "0"
        assert result["hour"] == "9"
        assert result["day"] == "*"
        assert result["month"] == "*"
        assert result["day_of_week"] == "1-5"

        # 测试每分钟执行
        result = service._parse_cron("*/5 * * * *")
        assert result["minute"] == "*/5"
        assert result["hour"] == "*"

    asyncio.run(test())


def test_build_report_content():
    """测试报告内容构建"""
    import asyncio
    async def test():
        db = DatabaseManager("sqlite+aiosqlite:///:memory:")
        await db.init_db()
        service = AutoPublisherService(db)

        # 创建模拟数据
        class MockProject:
            full_name = "test/mock_repo"
            html_url = "https://github.com/test/mock_repo"
            stars = 1000
            forks = 100
            language = "Python"
            topics = ["ai", "ml"]
            description = "A mock repository for testing"
            readme = "# Mock README\n\n## Introduction\n\nThis is a test."

        class MockReport:
            title = "Mock Report"
            generated_at = datetime.utcnow()

        content = service._build_report_content(MockReport(), MockProject())

        # 验证内容包含必要元素
        assert "# Mock Report" in content
        assert "test/mock_repo" in content
        assert "Star：1000" in content
        assert "Fork：100" in content
        assert "Python" in content
        assert "A mock repository for testing" in content
        assert "## Star 趋势" in content

    asyncio.run(test())


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
