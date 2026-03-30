"""LLM 内容生成服务"""
import logging
from typing import Any

import aiohttp
from anthropic import AsyncAnthropic

from core.models import Project


logger = logging.getLogger(__name__)


class LLMContentGenerator:
    """LLM 内容生成器"""

    def __init__(self, api_key: str, model: str = "claude-3-5-sonnet-20241022"):
        self.api_key = api_key
        self.model = model
        self.client = AsyncAnthropic(api_key=api_key)

    async def generate_deep_analysis(self, project: Project) -> dict[str, Any]:
        """生成深度分析"""
        prompt = f"""
        分析以下 GitHub 项目，提供深度见解：

        项目名称: {project.full_name}
        描述: {project.description}
        语言: {project.language}
        Stars: {project.stars}
        Forks: {project.forks}
        主题: {', '.join(project.topics)}

        README 内容:
        {project.readme[:5000]}

        请提供以下分析（JSON 格式）:
        1. 核心功能概述
        2. 技术栈分析
        3. 潜在应用场景
        4. 优缺点分析
        5. 推荐指数（1-10）
        """

        try:
            message = await self.client.messages.create(
                model=self.model,
                max_tokens=4000,
                messages=[{"role": "user", "content": prompt}],
            )
            return {"content": message.content[0].text}
        except Exception as e:
            logger.error(f"LLM 生成失败: {e}")
            return {"error": str(e)}

    async def generate_insights(self, project: Project) -> list[str]:
        """生成项目洞察"""
        analysis = await self.generate_deep_analysis(project)
        if "error" in analysis:
            return []

        insights_text = analysis.get("content", "")
        # 简单解析，实际应该使用结构化输出
        return [f"AI 分析: {insights_text[:200]}..."]

    async def generate_comparison(self, projects: list[Project]) -> str:
        """生成项目对比分析"""
        if not projects:
            return ""

        project_summaries = "\n".join([
            f"- {p.full_name}: {p.description} (Stars: {p.stars})"
            for p in projects[:5]
        ])

        prompt = f"""
        对比以下 GitHub 项目，提供推荐建议：

        {project_summaries}

        请分析各项目的优缺点，并给出适用场景建议。
        """

        try:
            message = await self.client.messages.create(
                model=self.model,
                max_tokens=2000,
                messages=[{"role": "user", "content": prompt}],
            )
            return message.content[0].text
        except Exception as e:
            logger.error(f"对比分析生成失败: {e}")
            return ""
