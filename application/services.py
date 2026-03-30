"""应用服务"""
import json
import re
import logging
from pathlib import Path
from datetime import datetime
from typing import Any

import aiohttp
from core.models import SourceType, Project, Report, PublisherType
from adapters.github_adapter import GitHubAdapter
from adapters.publishers import MultiPublisher, PublishPayload


logger = logging.getLogger(__name__)


class ProjectSelector:
    """项目选择器"""

    def __init__(self, state_file: Path = Path("state/selection_state.json")):
        self.state_file = state_file
        self.state_file.parent.mkdir(parents=True, exist_ok=True)

    async def pick(self, repos: list[dict]) -> tuple[int, dict]:
        """选择一个项目"""
        if not repos:
            raise ValueError("候选项目列表为空")

        state = self._load_state()
        today = datetime.now().strftime("%Y-%m-%d")

        if state.get("last_date") == today:
            index = int(state.get("last_index", 0))
        else:
            index = int(state.get("last_index", -1)) + 1
            if index >= len(repos):
                index = 0
            self._save_state({"last_date": today, "last_index": index})

        return index, repos[index]

    def _load_state(self) -> dict:
        if not self.state_file.exists():
            return {}
        return json.loads(self.state_file.read_text(encoding="utf-8"))

    def _save_state(self, state: dict) -> None:
        self.state_file.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")


class ProjectAnalyzer:
    """项目分析器"""

    @staticmethod
    def summarize_readme(readme: str) -> list[str]:
        """提取 README 摘要"""
        if not readme:
            return ["未找到 README，建议手动访问仓库查看项目细节。"]

        clean = re.sub(r"```[\s\S]*?```", "", readme)
        clean = re.sub(r"!\[[^\]]*\]\([^)]+\)", "", clean)
        lines = [l.strip() for l in clean.splitlines() if l.strip()]

        bullets: list[str] = []
        for line in lines:
            if line.startswith("#"):
                bullets.append(f"文档章节：{line.lstrip('#').strip()}")
            elif line.startswith("- ") or line.startswith("* "):
                bullets.append(f"功能点：{line[2:].strip()}")
            elif re.search(r"(install|usage|quick start|getting started|deploy)", line, re.I):
                bullets.append(f"使用说明：{line}")
            if len(bullets) >= 6:
                break

        if not bullets:
            bullets = [f"README 摘要：{line}" for line in lines[:4]]
        return bullets

    @staticmethod
    def extract_code_examples(readme: str) -> list[str]:
        """提取代码示例"""
        pattern = r"```(\w+)?\n([\s\S]*?)```"
        matches = re.findall(pattern, readme)
        return [code[1] for code in matches[:5]]


class ReportGenerator:
    """报告生成器"""

    def __init__(self, reports_dir: Path = Path("reports")):
        self.reports_dir = reports_dir
        self.reports_dir.mkdir(parents=True, exist_ok=True)

    def generate(self, project: Project, insights: list[str]) -> Report:
        """生成报告"""
        slug = project.slug
        filename = f"{datetime.now().strftime('%Y-%m-%d')}_{slug}.md"
        path = self.reports_dir / filename

        topics_text = ", ".join(project.topics) if project.topics else "无"
        insight_text = "\n".join([f"- {x}" for x in insights])

        content = (
            f"# GitHub 每日项目分析报告：{project.full_name}\n\n"
            f"- 排行名次：Top {project.rank}\n"
            f"- 仓库链接：{project.html_url}\n"
            f"- Star 趋势：https://www.star-history.com/?repos="
            f"{project.full_name.replace('/', '%2F')}&type=date&legend=top-left\n"
            f"- Star：{project.stars}\n"
            f"- Fork：{project.forks}\n"
            f"- 语言：{project.language}\n"
            f"- 主题：{topics_text}\n\n"
            "## 项目简介\n\n"
            f"{project.description}\n\n"
            "## README 解析\n\n"
            f"{insight_text}\n\n"
            "## 预览与建议\n\n"
            "- 建议先查看仓库首页的 Issue 与 Discussions，评估社区活跃度。\n"
            "- 建议重点阅读 README 的快速开始与部署部分，验证可落地性。\n"
            "- 可将该项目加入候选技术栈，后续结合业务场景做 PoC。\n"
        )

        path.write_text(content, encoding="utf-8")

        return Report(
            title=f"GitHub 每日项目分析 {datetime.now().strftime('%Y-%m-%d')} - {project.full_name}",
            project=project,
            content_markdown=content,
            generated_at=datetime.now(),
            insights=insights,
        )


class DailyTaskExecutor:
    """每日任务执行器"""

    def __init__(
        self,
        github_token: str,
        reports_dir: Path,
        publishers: MultiPublisher,
    ):
        self.github_adapter = GitHubAdapter(token=github_token)
        self.selector = ProjectSelector()
        self.analyzer = ProjectAnalyzer()
        self.report_generator = ReportGenerator(reports_dir)
        self.publisher = publishers

    async def execute(self) -> dict[str, Any]:
        """执行每日任务"""
        logger.info("开始执行每日 GitHub 项目分析任务")

        # 获取热门项目
        repos = await self.github_adapter.search_top_starred(days_window=30, per_page=100)
        logger.info(f"获取到 {len(repos)} 个候选项目")

        # 选择项目
        index, repo = await self.selector.pick(repos)
        logger.info(f"选择排名 Top {index + 1} 的项目: {repo.get('full_name')}")

        # 获取 README
        owner, name = repo["full_name"].split("/", 1)
        readme = await self.github_adapter.fetch_repo_readme(owner, name)

        # 转换为项目模型
        project = self.github_adapter.to_project(repo, rank=index + 1, readme=readme)

        # 分析 README
        insights = self.analyzer.summarize_readme(project.readme)

        # 生成报告
        report = self.report_generator.generate(project, insights)
        logger.info(f"报告已生成: {self.report_generator.reports_dir}")

        # 发布到各平台
        payload = PublishPayload(
            title=report.title,
            content_markdown=report.content_markdown,
            source_url=project.html_url,
        )
        publish_results = await self.publisher.publish_all(payload)

        logger.info(f"发布结果: {publish_results}")

        return {
            "project": project.full_name,
            "report_path": str(self.report_generator.reports_dir),
            "published": {k.value: v for k, v in publish_results.items()},
        }
