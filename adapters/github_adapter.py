"""GitHub 数据源适配器 - 异步版本"""
from datetime import datetime, timedelta, timezone
from typing import Any

import aiohttp
from infrastructure.resilience import retry_on_failure, with_circuit_breaker
from infrastructure.cache import cache_result

from core.models import SourceType, Project


class GitHubAdapter:
    """GitHub 数据源异步适配器"""

    def __init__(self, token: str = ""):
        self.token = token
        self.base_url = "https://api.github.com"
        self.headers = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "auto-publisher-bot",
        }
        if token:
            self.headers["Authorization"] = f"Bearer {token}"

    @retry_on_failure(max_attempts=3, initial_delay=1.0)
    async def _fetch(self, session: aiohttp.ClientSession, url: str, params: dict | None = None) -> Any:
        """异步获取数据"""
        async with session.get(url, headers=self.headers, params=params, timeout=aiohttp.ClientTimeout(total=30)) as resp:
            if resp.status == 404:
                return None
            resp.raise_for_status()
            return await resp.json()

    @with_circuit_breaker(fail_max=5, name="github_search")
    @cache_result(ttl=1800, key_prefix="github_search:")
    async def search_top_starred(self, days_window: int = 30, per_page: int = 100) -> list[dict]:
        """搜索热门项目"""
        since_date = (datetime.now(timezone.utc) - timedelta(days=days_window)).strftime("%Y-%m-%d")
        query = f"created:>{since_date}"
        url = f"{self.base_url}/search/repositories"
        params = {"q": query, "sort": "stars", "order": "desc", "per_page": per_page, "page": 1}

        async with aiohttp.ClientSession() as session:
            data = await self._fetch(session, url, params)
            return data.get("items", [])

    @retry_on_failure(max_attempts=3)
    async def fetch_repo_readme(self, owner: str, repo: str) -> str:
        """获取仓库 README"""
        url = f"{self.base_url}/repos/{owner}/{repo}/readme"

        async with aiohttp.ClientSession() as session:
            data = await self._fetch(session, url)
            if not data:
                return ""

            download_url = data.get("download_url")
            if not download_url:
                return ""

            async with session.get(download_url, headers=self.headers, timeout=aiohttp.ClientTimeout(total=30)) as resp:
                if resp.status == 404:
                    return ""
                resp.raise_for_status()
                return await resp.text()

    async def fetch_repo_details(self, owner: str, repo: str) -> dict | None:
        """获取仓库详细信息"""
        url = f"{self.base_url}/repos/{owner}/{repo}"
        async with aiohttp.ClientSession() as session:
            return await self._fetch(session, url)

    async def fetch_repo_stats(self, owner: str, repo: str) -> dict | None:
        """获取仓库统计信息"""
        url = f"{self.base_url}/repos/{owner}/{repo}/stats/participation"
        async with aiohttp.ClientSession() as session:
            return await self._fetch(session, url)

    def to_project(self, repo_data: dict, rank: int, readme: str = "") -> Project:
        """转换为项目模型"""
        return Project(
            source=SourceType.GITHUB,
            source_id=str(repo_data.get("id", "")),
            rank=rank,
            full_name=repo_data.get("full_name", ""),
            html_url=repo_data.get("html_url", ""),
            description=repo_data.get("description") or "暂无描述",
            stars=int(repo_data.get("stargazers_count", 0)),
            forks=int(repo_data.get("forks_count", 0)),
            language=repo_data.get("language") or "Unknown",
            topics=repo_data.get("topics") or [],
            readme=readme.strip(),
            created_at=datetime.fromisoformat(repo_data.get("created_at", "").replace("Z", "+00:00")) if repo_data.get("created_at") else None,
            updated_at=datetime.fromisoformat(repo_data.get("updated_at", "").replace("Z", "+00:00")) if repo_data.get("updated_at") else None,
        )
