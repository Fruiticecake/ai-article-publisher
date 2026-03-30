"""质量检测服务"""
import logging
import re
from typing import Any

import aiohttp
from core.models import Project, QualityMetrics


logger = logging.getLogger(__name__)


class QualityAnalyzer:
    """项目质量分析器"""

    def __init__(self, github_token: str = ""):
        self.github_token = github_token
        self.base_url = "https://api.github.com"

    async def analyze(self, project: Project) -> QualityMetrics:
        """分析项目质量"""
        activity_score = self._calculate_activity_score(project)
        documentation_score = self._calculate_documentation_score(project)
        security_score, vulnerabilities = await self._analyze_security(project)
        license_compliance = await self._check_license(project)

        overall_score = (
            activity_score * 0.4 +
            documentation_score * 0.3 +
            security_score * 0.3
        )

        return QualityMetrics(
            activity_score=activity_score,
            documentation_score=documentation_score,
            security_score=security_score,
            license_compliance=license_compliance,
            vulnerabilities=vulnerabilities,
            overall_score=overall_score,
        )

    def _calculate_activity_score(self, project: Project) -> float:
        """计算活跃度分数 (0-100)"""
        score = 0.0

        # Stars 分数
        if project.stars > 10000:
            score += 40
        elif project.stars > 1000:
            score += 30
        elif project.stars > 100:
            score += 20
        elif project.stars > 10:
            score += 10

        # Forks 分数
        if project.forks > 1000:
            score += 30
        elif project.forks > 100:
            score += 20
        elif project.forks > 10:
            score += 10

        # Topics 分数
        score += min(len(project.topics) * 3, 30)

        return min(score, 100)

    def _calculate_documentation_score(self, project: Project) -> float:
        """计算文档完整度分数 (0-100)"""
        if not project.readme:
            return 0.0

        score = 0.0

        # 检查关键章节
        patterns = [
            r"(#|\b)(installation|install|getting started|quick start)",
            r"(#|\b)usage",
            r"(#|\b)api",
            r"(#|\b)examples?",
            r"(#|\b)contributing",
            r"(#|\b)license",
        ]

        readme_lower = project.readme.lower()
        for pattern in patterns:
            if re.search(pattern, readme_lower):
                score += 100 / len(patterns)

        return min(score, 100)

    async def _analyze_security(self, project: Project) -> tuple[float, list[dict]]:
        """分析安全问题"""
        # 这里可以集成 GitHub Security Advisories 或其他安全扫描工具
        # 简化版实现
        vulnerabilities = []

        # 检查 README 中的常见安全问题
        readme_lower = project.readme.lower()
        if "TODO: add security" in readme_lower or "TODO security" in readme_lower:
            vulnerabilities.append({
                "type": "incomplete",
                "message": "文档中提到安全功能尚未完成"
            })

        if "hardcoded" in readme_lower and ("password" in readme_lower or "secret" in readme_lower):
            vulnerabilities.append({
                "type": "potential_risk",
                "message": "文档可能提到硬编码的敏感信息"
            })

        # 计算安全分数
        score = 100 - len(vulnerabilities) * 20
        return max(score, 0), vulnerabilities

    async def _check_license(self, project: Project) -> bool:
        """检查许可证合规性"""
        # 检查 README 中是否有许可证信息
        if not project.readme:
            return False

        readme_lower = project.readme.lower()
        license_patterns = [
            r"mit license",
            r"apache license",
            r"gnu (general public license|gpl)",
            r"bsd license",
            r"isc license",
        ]

        for pattern in license_patterns:
            if re.search(pattern, readme_lower):
                return True

        return False
