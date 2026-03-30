"""报告模板系统"""
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import jinja2
from core.models import Project, Report


@dataclass
class TemplateConfig:
    """模板配置"""
    template_dir: Path
    default_template: str = "default.md.j2"


class TemplateEngine:
    """模板引擎"""

    def __init__(self, config: TemplateConfig | None = None):
        if config:
            self.template_dir = config.template_dir
            self.default_template = config.default_template
        else:
            self.template_dir = Path("templates")
            self.default_template = "default.md.j2"

        self.env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(str(self.template_dir)),
            autoescape=False,
        )

        # 添加自定义过滤器
        self.env.filters['format_stars'] = self._format_stars
        self.env.filters['format_topics'] = self._format_topics

    def _format_stars(self, stars: int) -> str:
        """格式化星数"""
        if stars >= 1000000:
            return f"{stars / 1000000:.1f}M"
        elif stars >= 1000:
            return f"{stars / 1000:.1f}K"
        return str(stars)

    def _format_topics(self, topics: list[str]) -> str:
        """格式化主题"""
        return ", ".join(topics) if topics else "无"

    def render(
        self,
        template_name: str | None = None,
        project: Project | None = None,
        report: Report | None = None,
        **context: Any
    ) -> str:
        """渲染模板"""
        template_name = template_name or self.default_template

        try:
            template = self.env.get_template(template_name)
            return template.render(
                project=project,
                report=report,
                **context
            )
        except jinja2.TemplateNotFound:
            return self._render_default(project, report, context)
        except Exception as e:
            raise RuntimeError(f"Template rendering failed: {e}")

    def _render_default(self, project: Project | None, report: Report | None, context: dict) -> str:
        """渲染默认模板"""
        if not project:
            return ""

        from datetime import datetime

        topics_text = ", ".join(project.topics) if project.topics else "无"
        insights = context.get("insights", [])
        insight_text = "\n".join([f"- {x}" for x in insights])

        return (
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


# 默认模板内容
DEFAULT_TEMPLATE = """# {{ project.full_name }} 项目分析报告

## 基本信息

| 项目 | 内容 |
|------|------|
| 排名 | Top {{ project.rank }} |
| 链接 | [{{ project.html_url }}]({{ project.html_url }}) |
| Stars | {{ project.stars | format_stars }} |
| Forks | {{ project.forks | format_stars }} |
| 语言 | {{ project.language }} |
| 主题 | {{ project.topics | format_topics }} |

## 项目简介

{{ project.description }}

{% if insights %}
## 分析洞察

{% for insight in insights %}
- {{ insight }}
{% endfor %}
{% endif %}

## 技术分析

### 活跃度评分

{{ quality_metrics.activity_score | round(2) }} / 100

### 文档完整度

{{ quality_metrics.documentation_score | round(2) }} / 100

### 安全评分

{{ quality_metrics.security_score | round(2) }} / 100

## Star 趋势图

![Star History](https://www.star-history.com/?repos={{ project.full_name | replace('/', '%2F') }}&type=date&legend=top-left)

## 建议

- 查看 [Issues]({{ project.html_url }}/issues) 了解项目状态
- 查看 [Discussions]({{ project.html_url }}/discussions) 参与社区讨论
- 查看 [Releases]({{ project.html_url }}/releases) 获取最新版本

---

*报告生成时间: {{ generated_at }}*
"""
