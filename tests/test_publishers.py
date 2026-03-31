"""测试发布平台和文档生成"""
import pytest
from datetime import datetime
from pathlib import Path
import tempfile
import os

from core.models import PublisherType, Project, SourceType
from adapters.publishers import (
    PublishPayload,
    NotionPublisher,
    CsdnPublisher,
    TelegramPublisher,
    ZhihuPublisher,
    JuejinPublisher,
    XHSPublisher,
    MultiPublisher,
)


class TestPublisherType:
    """测试发布平台类型枚举"""

    def test_publisher_type_values(self):
        """验证发布平台类型值"""
        assert PublisherType.NOTION.value == "notion"
        assert PublisherType.CSDN.value == "csdn"
        assert PublisherType.ZHIHU.value == "zhihu"
        assert PublisherType.JUEJIN.value == "juejin"
        assert PublisherType.TELEGRAM.value == "telegram"
        assert PublisherType.XHS.value == "xhs"

    def test_xhs_added(self):
        """验证小红书平台已添加"""
        assert hasattr(PublisherType, 'XHS')
        assert PublisherType.XHS.value == "xhs"


class TestPublishPayload:
    """测试发布负载"""

    def test_payload_creation(self):
        """验证负载创建"""
        payload = PublishPayload(
            title="Test Title",
            content_markdown="# Test Content",
            source_url="https://github.com/test/repo",
            tags=["python", "ai"],
            metadata={"key": "value"},
        )
        assert payload.title == "Test Title"
        assert payload.source_url == "https://github.com/test/repo"
        assert payload.tags == ["python", "ai"]
        assert payload.metadata == {"key": "value"}

    def test_payload_defaults(self):
        """验证默认参数"""
        payload = PublishPayload(
            title="Test",
            content_markdown="Content",
            source_url="https://example.com",
        )
        assert payload.tags is None
        assert payload.metadata is None


class TestNotionPublisher:
    """测试 Notion 发布器"""

    def test_notion_disabled_without_config(self):
        """验证未配置时禁用"""
        publisher = NotionPublisher("", "")
        assert publisher.enabled is False

    def test_notion_enabled_with_config(self):
        """验证配置后启用"""
        publisher = NotionPublisher("test_token", "test_database_id")
        assert publisher.enabled is True

    def test_notion_name(self):
        """验证名称"""
        publisher = NotionPublisher("token", "db_id")
        assert publisher.name == "Notion"


class TestCsdnPublisher:
    """测试 CSDN 发布器"""

    def test_csdn_disabled_without_config(self):
        """验证未配置时禁用"""
        publisher = CsdnPublisher("", "")
        assert publisher.enabled is False

    def test_csdn_enabled_with_config(self):
        """验证配置后启用"""
        publisher = CsdnPublisher("https://api.csdn.net", "test_token")
        assert publisher.enabled is True


class TestTelegramPublisher:
    """测试 Telegram 发布器"""

    def test_telegram_disabled_without_config(self):
        """验证未配置时禁用"""
        publisher = TelegramPublisher("", "")
        assert publisher.enabled is False

    def test_telegram_enabled_with_config(self):
        """验证配置后启用"""
        publisher = TelegramPublisher("test_bot_token", "test_chat_id")
        assert publisher.enabled is True


class TestZhihuPublisher:
    """测试知乎发布器"""

    def test_zhihu_disabled_without_config(self):
        """验证未配置时禁用"""
        publisher = ZhihuPublisher("")
        assert publisher.enabled is False

    def test_zhihu_enabled_with_config(self):
        """验证配置后启用"""
        publisher = ZhihuPublisher("test_token")
        assert publisher.enabled is True


class TestJuejinPublisher:
    """测试掘金发布器"""

    def test_juejin_disabled_without_config(self):
        """验证未配置时禁用"""
        publisher = JuejinPublisher("")
        assert publisher.enabled is False

    def test_juejin_enabled_with_config(self):
        """验证配置后启用"""
        publisher = JuejinPublisher("test_token")
        assert publisher.enabled is True


class TestXHSPublisher:
    """测试小红书发布器"""

    def test_xhs_disabled_without_config(self):
        """验证未配置时禁用"""
        publisher = XHSPublisher("")
        assert publisher.enabled is False

    def test_xhs_enabled_with_config(self):
        """验证配置后启用"""
        publisher = XHSPublisher("test_cookie")
        assert publisher.enabled is True

    def test_xhs_name(self):
        """验证名称"""
        publisher = XHSPublisher("cookie")
        assert publisher.name == "小红书"

    def test_xhs_format_for_xhs(self):
        """测试内容格式化"""
        publisher = XHSPublisher("cookie")
        payload = PublishPayload(
            title="Test Project",
            content_markdown="This is a test project.",
            source_url="https://github.com/test/repo",
            tags=["python", "ai"],
        )
        formatted = publisher._format_for_xhs(payload)
        assert "Test Project" in formatted
        assert "python" in formatted
        assert "ai" in formatted
        assert "github.com/test/repo" in formatted


class TestMultiPublisher:
    """测试多平台发布管理器"""

    def test_multi_publisher_empty(self):
        """测试空发布器列表"""
        publisher = MultiPublisher([])
        assert publisher.publishers == []

    def test_multi_publisher_with_publishers(self):
        """测试带发布器的初始化"""
        publishers_list = [
            NotionPublisher("token", "db_id"),
            CsdnPublisher("api", "token"),
        ]
        publisher = MultiPublisher(publishers_list)
        assert len(publisher.publishers) == 2

    def test_publish_to_specific_platform(self):
        """测试发布到指定平台"""
        publisher = MultiPublisher([
            NotionPublisher("invalid_token", "db_id"),
        ])
        payload = PublishPayload(
            title="Test",
            content_markdown="Content",
            source_url="https://example.com",
        )
        # 未配置有效的发布器会返回失败（由于是异步方法，这里只验证方法存在）
        assert hasattr(publisher, 'publish_to')
        assert callable(publisher.publish_to)