"""发布平台适配器 - 异步版本"""
from dataclasses import dataclass
from datetime import datetime
from typing import Protocol, AsyncIterator

import aiohttp
from infrastructure.resilience import retry_on_failure
from core.models import PublisherType


@dataclass
class PublishPayload:
    """发布负载"""
    title: str
    content_markdown: str
    source_url: str
    tags: list[str] | None = None
    metadata: dict | None = None


class Publisher(Protocol):
    """发布器协议"""

    async def publish(self, payload: PublishPayload) -> str:
        """发布内容，返回发布ID或URL"""
        ...

    @property
    def enabled(self) -> bool:
        """是否启用"""
        ...

    @property
    def name(self) -> str:
        """平台名称"""
        ...


class NotionPublisher:
    """Notion 发布器"""

    def __init__(self, token: str, database_id: str):
        self.token = token
        self.database_id = database_id
        self.base_url = "https://api.notion.com/v1"

    @property
    def enabled(self) -> bool:
        return bool(self.token and self.database_id)

    @property
    def name(self) -> str:
        return "Notion"

    @retry_on_failure(max_attempts=2)
    async def publish(self, payload: PublishPayload) -> str:
        if not self.enabled:
            return ""

        url = f"{self.base_url}/pages"
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Notion-Version": "2022-06-28",
            "Content-Type": "application/json",
        }

        text = payload.content_markdown[:1900]
        body = {
            "parent": {"database_id": self.database_id},
            "properties": {
                "Name": {"title": [{"text": {"content": payload.title[:200]}}]},
                "SourceURL": {"url": payload.source_url},
            },
            "children": [
                {
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {"rich_text": [{"type": "text", "text": {"content": text}}]},
                }
            ],
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=body, timeout=aiohttp.ClientTimeout(total=30)) as resp:
                resp.raise_for_status()
                data = await resp.json()
                return data.get("id", "")


class CsdnPublisher:
    """CSDN 发布器"""

    def __init__(self, publish_api: str, token: str):
        self.publish_api = publish_api
        self.token = token

    @property
    def enabled(self) -> bool:
        return bool(self.publish_api and self.token)

    @property
    def name(self) -> str:
        return "CSDN"

    @retry_on_failure(max_attempts=2)
    async def publish(self, payload: PublishPayload) -> str:
        if not self.enabled:
            return ""

        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
        }
        body = {
            "title": payload.title,
            "content_markdown": payload.content_markdown,
            "source_url": payload.source_url,
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(self.publish_api, headers=headers, json=body, timeout=aiohttp.ClientTimeout(total=30)) as resp:
                resp.raise_for_status()
                data = await resp.json()
                return data.get("id", "")


class TelegramPublisher:
    """Telegram Bot 发布器"""

    def __init__(self, bot_token: str, chat_id: str):
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.base_url = f"https://api.telegram.org/bot{bot_token}"

    @property
    def enabled(self) -> bool:
        return bool(self.bot_token and self.chat_id)

    @property
    def name(self) -> str:
        return "Telegram"

    @retry_on_failure(max_attempts=2)
    async def publish(self, payload: PublishPayload) -> str:
        if not self.enabled:
            return ""

        # Telegram 消息限制处理
        message = f"{payload.title}\n\n{payload.content_markdown[:3500]}...\n\n{payload.source_url}"
        url = f"{self.base_url}/sendMessage"
        body = {
            "chat_id": self.chat_id,
            "text": message,
            "parse_mode": "Markdown",
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=body, timeout=aiohttp.ClientTimeout(total=30)) as resp:
                resp.raise_for_status()
                data = await resp.json()
                return str(data.get("message_id", ""))


class ZhihuPublisher:
    """知乎发布器"""

    def __init__(self, token: str):
        self.token = token
        self.base_url = "https://www.zhihu.com/api"

    @property
    def enabled(self) -> bool:
        return bool(self.token)

    @property
    def name(self) -> str:
        return "知乎"

    @retry_on_failure(max_attempts=2)
    async def publish(self, payload: PublishPayload) -> str:
        if not self.enabled:
            return ""

        # 知乎 API 实现
        url = f"{self.base_url}/posts"
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
        }
        body = {
            "title": payload.title,
            "content": payload.content_markdown,
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=body, timeout=aiohttp.ClientTimeout(total=30)) as resp:
                resp.raise_for_status()
                data = await resp.json()
                return data.get("id", "")


class JuejinPublisher:
    """掘金发布器"""

    def __init__(self, token: str):
        self.token = token
        self.base_url = "https://api.juejin.cn"

    @property
    def enabled(self) -> bool:
        return bool(self.token)

    @property
    def name(self) -> str:
        return "掘金"

    @retry_on_failure(max_attempts=2)
    async def publish(self, payload: PublishPayload) -> str:
        if not self.enabled:
            return ""

        # 掘金 API 实现
        url = f"{self.base_url}/content_api/v1/article/publish"
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
        }
        body = {
            "title": payload.title,
            "markdown_content": payload.content_markdown,
            "tags": payload.tags or [],
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=body, timeout=aiohttp.ClientTimeout(total=30)) as resp:
                resp.raise_for_status()
                data = await resp.json()
                return data.get("data", {}).get("article_id", "")


class MultiPublisher:
    """多平台发布管理器"""

    def __init__(self, publishers: list[Publisher] | None = None):
        self.publishers = publishers or []

    async def publish_all(self, payload: PublishPayload) -> dict[PublisherType, tuple[bool, str]]:
        """发布到所有启用的平台"""
        results = {}

        for publisher in self.publishers:
            if publisher.enabled:
                try:
                    url = await publisher.publish(payload)
                    results[PublisherType(publisher.name.lower())] = (True, url)
                except Exception as e:
                    results[PublisherType(publisher.name.lower())] = (False, str(e))

        return results

    async def publish_to(self, publisher_name: str, payload: PublishPayload) -> tuple[bool, str]:
        """发布到指定平台"""
        for publisher in self.publishers:
            if publisher.name.lower() == publisher_name.lower() and publisher.enabled:
                try:
                    url = await publisher.publish(payload)
                    return (True, url)
                except Exception as e:
                    return (False, str(e))
        return (False, "Publisher not found or disabled")
