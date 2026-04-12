"""多数据源适配器"""
import logging
from typing import Any

import aiohttp
from infrastructure.resilience import retry_on_failure, with_circuit_breaker
from infrastructure.cache import cache_result

from core.models import SourceType, Project


logger = logging.getLogger(__name__)


class HackerNewsAdapter:
    """Hacker News 数据源适配器"""

    def __init__(self):
        self.base_url = "https://hacker-news.firebaseio.com/v0"

    @retry_on_failure(max_attempts=3)
    @with_circuit_breaker(fail_max=5, name="hacker_news")
    @cache_result(ttl=1800, key_prefix="hn:")
    async def get_top_stories(self, limit: int = 30) -> list[dict]:
        """获取热门故事"""
        # 获取热门故事 ID 列表
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{self.base_url}/topstories.json", timeout=aiohttp.ClientTimeout(total=30)) as resp:
                resp.raise_for_status()
                story_ids = await resp.json()

        # 获取故事详情
        stories = []
        async with aiohttp.ClientSession() as session:
            for story_id in story_ids[:limit]:
                url = f"{self.base_url}/item/{story_id}.json"
                try:
                    async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                        if resp.status == 200:
                            story = await resp.json()
                            if story:
                                stories.append(story)
                except Exception as e:
                    logger.warning(f"获取 Hacker News 故事 {story_id} 失败: {e}")
                    continue

        return stories

    def to_project(self, story: dict, rank: int) -> Project:
        """转换为项目模型"""
        url = story.get("url", "")
        if "github.com" in url:
            # 从 GitHub URL 提取项目信息
            import re
            match = re.search(r"github\.com/([^/]+/[^/]+)", url)
            full_name = match.group(1) if match else "unknown/unknown"
        else:
            full_name = f"hn/{story.get('id', '')}"

        return Project(
            source=SourceType.HACKER_NEWS,
            source_id=str(story.get("id", "")),
            rank=rank,
            full_name=full_name,
            html_url=url,
            description=story.get("title", "")[:200],
            stars=story.get("score", 0),
            forks=story.get("descendants", 0),
            language="Web",
            topics=[],
            readme=f"{story.get('title', '')}\n\n{story.get('text', '') or '无详细内容'}",
        )


class RedditAdapter:
    """Reddit 数据源适配器"""

    def __init__(self):
        self.base_url = "https://www.reddit.com"

    @retry_on_failure(max_attempts=3)
    @with_circuit_breaker(fail_max=5, name="reddit")
    @cache_result(ttl=1800, key_prefix="reddit:")
    async def get_hot_posts(self, subreddit: str = "programming", limit: int = 25) -> list[dict]:
        """获取热门帖子"""
        url = f"{self.base_url}/r/{subreddit}/hot.json"
        headers = {"User-Agent": "githink-pulse-bot/1.0"}

        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total) as resp:
                resp.raise_for_status()
                data = await resp.json()
                return data.get("data", {}).get("children", [])

    def to_project(self, post: dict, rank: int) -> Project:
        """转换为项目模型"""
        data = post.get("data", {})
        url = data.get("url", "")

        if "github.com" in url:
            import re
            match = re.search(r"github\.com/([^/]+/[^/]+)", url)
            full_name = match.group(1) if match else "unknown/unknown"
        else:
            full_name = f"reddit/{data.get('id', '')}"

        return Project(
            source=SourceType.REDDIT,
            source_id=data.get("id", ""),
            rank=rank,
            full_name=full_name,
            html_url=url,
            description=data.get("title", "")[:200],
            stars=data.get("score", 0),
            forks=data.get("num_comments", 0),
            language="Web",
            topics=[],
            readme=f"{data.get('title', '')}\n\n{data.get('selftext', '') or '无详细内容'}",
        )


class ProductHuntAdapter:
    """Product Hunt 数据源适配器"""

    def __init__(self, api_key: str = ""):
        self.base_url = "https://api.producthunt.com/v2"
        self.api_key = api_key

    @retry_on_failure(max_attempts=3)
    @with_circuit_breaker(fail_max=5, name="product_hunt")
    async def get_posts(self, limit: int = 20) -> list[dict]:
        """获取产品帖子"""
        if not self.api_key:
            logger.warning("Product Hunt API key not configured")
            return []

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{self.base_url}/posts",
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=30)
            ) as resp:
                resp.raise_for_status()
                data = await resp.json()
                return data.get("posts", [])[:limit]

    def to_project(self, post: dict, rank: int) -> Project:
        """转换为项目模型"""
        return Project(
            source=SourceType.PRODUCT_HUNT,
            source_id=str(post.get("id", "")),
            rank=rank,
            full_name=post.get("name", "unknown"),
            html_url=post.get("website", post.get("url", "")),
            description=post.get("tagline", "")[:200],
            stars=post.get("votes_count", 0),
            forks=0,
            language="Product",
            topics=[tag.get("name", "") for tag in post.get("topics", [])],
            readme=f"{post.get('name', '')}: {post.get('tagline', '')}\n\n{post.get('description', '') or '无详细内容'}",
        )


class MultiDataSource:
    """多数据源管理器"""

    def __init__(
        self,
        github_adapter: Any,
        hn_adapter: HackerNewsAdapter | None = None,
        reddit_adapter: RedditAdapter | None = None,
        ph_adapter: ProductHuntAdapter | None = None,
    ):
        self.github_adapter = github_adapter
        self.hn_adapter = hn_adapter or HackerNewsAdapter()
        self.reddit_adapter = reddit_adapter or RedditAdapter()
        self.ph_adapter = ph_adapter

    async def fetch_all(self) -> dict[SourceType, list[Project]]:
        """从所有数据源获取项目"""
        results = {}

        # GitHub
        try:
            repos = await self.github_adapter.search_top_starred()
            results[SourceType.GITHUB] = [
                self.github_adapter.to_project(repo, i + 1)
                for i, repo in enumerate(repos)
            ]
        except Exception as e:
            logger.error(f"GitHub 数据源获取失败: {e}")
            results[SourceType.GITHUB] = []

        # Hacker News
        try:
            stories = await self.hn_adapter.get_top_stories()
            results[SourceType.HACKER_NEWS] = [
                self.hn_adapter.to_project(story, i + 1)
                for i, story in enumerate(stories)
            ]
        except Exception as e:
            logger.error(f"Hacker News 数据源获取失败: {e}")
            results[SourceType.HACKER_NEWS] = []

        # Reddit
        try:
            posts = await self.reddit_adapter.get_hot_posts()
            results[SourceType.REDDIT] = [
                self.reddit_adapter.to_project(post, i + 1)
                for i, post in enumerate(posts)
            ]
        except Exception as e:
            logger.error(f"Reddit 数据源获取失败: {e}")
            results[SourceType.REDDIT] = []

        # Product Hunt
        if self.ph_adapter:
            try:
                posts = await self. ph_adapter.get_posts()
                results[SourceType.PRODUCT_HUNT] = [
                    self.ph_adapter.to_project(post, i + 1)
                    for i, post in enumerate(posts)
                ]
            except Exception as e:
                logger.error(f"Product Hunt 数据源获取失败: {e}")
                results[SourceType.PRODUCT_HUNT] = []

        return results
