"""文档生成服务 - 支持 Markdown 和 PDF 导出"""
import io
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    PageBreak,
    Table,
    TableStyle,
    Image,
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY

logger = logging.getLogger(__name__)


class DocumentGenerator:
    """文档生成器"""

    def __init__(self, output_dir: Path | None = None):
        self.output_dir = output_dir or Path("reports")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.styles = self._create_styles()

    def _create_styles(self) -> dict:
        """创建样式"""
        styles = getSampleStyleSheet()
        
        # 自定义标题样式
        styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=styles['Title'],
            fontSize=24,
            textColor=colors.HexColor('#1a1a2e'),
            spaceAfter=20,
            alignment=TA_CENTER,
        ))
        
        # 自定义副标题样式
        styles.add(ParagraphStyle(
            name='CustomHeading1',
            parent=styles['Heading1'],
            fontSize=18,
            textColor=colors.HexColor('#16213e'),
            spaceAfter=12,
            spaceBefore=12,
        ))
        
        # 自定义副标题样式
        styles.add(ParagraphStyle(
            name='CustomHeading2',
            parent=styles['Heading2'],
            fontSize=14,
            textColor=colors.HexColor('#0f3460'),
            spaceAfter=8,
            spaceBefore=8,
        ))
        
        # 正文样式
        styles.add(ParagraphStyle(
            name='CustomBody',
            parent=styles['Normal'],
            fontSize=11,
            textColor=colors.HexColor('#333333'),
            alignment=TA_JUSTIFY,
            spaceAfter=10,
            leading=16,
        ))
        
        # 信息表格样式
        styles.add(ParagraphStyle(
            name='InfoLabel',
            parent=styles['Normal'],
            fontSize=10,
            textColor=colors.HexColor('#666666'),
        ))
        
        styles.add(ParagraphStyle(
            name='InfoValue',
            parent=styles['Normal'],
            fontSize=10,
            textColor=colors.HexColor('#1a1a2e'),
        ))
        
        return styles

    def markdown_to_pdf(self, markdown_content: str, title: str, output_filename: str | None = None) -> bytes:
        """将 Markdown 内容转换为 PDF"""
        if not output_filename:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_filename = f"report_{timestamp}.pdf"
        
        output_path = self.output_dir / output_filename
        
        doc = SimpleDocTemplate(
            str(output_path),
            pagesize=A4,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=72,
        )
        
        story = []
        
        # 解析 Markdown 并构建 PDF 内容
        lines = markdown_content.split('\n')
        
        for line in lines:
            line = line.strip()
            if not line:
                story.append(Spacer(1, 10))
                continue
            
            # 处理标题
            if line.startswith('# '):
                # 主标题
                title_text = line[2:].strip()
                story.append(Paragraph(title_text, self.styles['CustomTitle']))
                story.append(Spacer(1, 20))
            elif line.startswith('## '):
                # 二级标题
                heading_text = line[3:].strip()
                story.append(Paragraph(heading_text, self.styles['CustomHeading1']))
            elif line.startswith('### '):
                # 三级标题
                heading_text = line[4:].strip()
                story.append(Paragraph(heading_text, self.styles['CustomHeading2']))
            elif line.startswith('- ') or line.startswith('* '):
                # 列表项
                bullet_text = line[2:].strip()
                # 处理粗体和斜体
                bullet_text = self._format_text(bullet_text)
                story.append(Paragraph(f"• {bullet_text}", self.styles['CustomBody']))
            elif line.startswith('|'):
                # 表格 - 简化处理
                continue
            elif line.startswith('```'):
                # 代码块 - 跳过
                continue
            elif line.startswith('!['):
                # 图片 - 跳过
                continue
            elif line.startswith('http'):
                # 链接
                story.append(Paragraph(f'<link href="{line}">{line}</link>', self.styles['CustomBody']))
            else:
                # 常规文本
                formatted_text = self._format_text(line)
                story.append(Paragraph(formatted_text, self.styles['CustomBody']))
        
        # 构建 PDF
        doc.build(story)
        logger.info(f"PDF 已生成: {output_path}")
        
        return output_path.read_bytes()

    def _format_text(self, text: str) -> str:
        """格式化文本，支持粗体和斜体"""
        # 处理粗体 **text**
        text = text.replace('**', '<b>', 1)
        text = text.replace('**', '</b>', 1)
        # 处理多个粗体
        while '**' in text:
            text = text.replace('**', '<b>', 1)
            text = text.replace('**', '</b>', 1)
        
        # 处理斜体 *text*
        text = text.replace('*', '<i>', 1)
        text = text.replace('*', '</i>', 1)
        
        return text

    def create_report_pdf(self, project_data: dict[str, Any], insights: list[str]) -> bytes:
        """创建项目分析报告 PDF"""
        # 构建内容
        content_parts = []
        
        # 标题
        content_parts.append(f"# GitHub 项目分析报告：{project_data.get('full_name', 'Unknown')}\n")
        
        # 基本信息
        content_parts.append("## 项目信息\n")
        content_parts.append(f"- 仓库链接：{project_data.get('html_url', 'N/A')}\n")
        content_parts.append(f"- Star：{project_data.get('stars', 0)}\n")
        content_parts.append(f"- Fork：{project_data.get('forks', 0)}\n")
        content_parts.append(f"- 语言：{project_data.get('language', 'N/A')}\n")
        content_parts.append(f"- 排名：Top {project_data.get('rank', 'N/A')}\n")
        
        if project_data.get('topics'):
            topics = ', '.join(project_data['topics'])
            content_parts.append(f"- 主题：{topics}\n")
        
        # 简介
        content_parts.append("\n## 项目简介\n")
        content_parts.append(f"{project_data.get('description', '暂无描述')}\n")
        
        # 解析结果
        if insights:
            content_parts.append("\n## README 解析\n")
            for insight in insights:
                content_parts.append(f"- {insight}\n")
        
        # 建议
        content_parts.append("\n## 预览与建议\n")
        content_parts.append("- 建议先查看仓库首页的 Issue 与 Discussions，评估社区活跃度。\n")
        content_parts.append("- 建议重点阅读 README 的快速开始与部署部分，验证可落地性。\n")
        content_parts.append("- 可将该项目加入候选技术栈，后续结合业务场景做 PoC。\n")
        
        # Star 历史链接
        full_name = project_data.get('full_name', '')
        if full_name:
            star_history_url = f"https://www.star-history.com/?repos={full_name.replace('/', '%2F')}&type=date&legend=top-left"
            content_parts.append(f"\n## Star 趋势\n")
            content_parts.append(f"- {star_history_url}\n")
        
        # 生成时间
        content_parts.append(f"\n---\n")
        content_parts.append(f"*报告生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n")
        
        markdown_content = '\n'.join(content_parts)
        title = f"GitHub 项目分析 - {project_data.get('full_name', 'Report')}"
        
        return self.markdown_to_pdf(markdown_content, title)

    def save_pdf(self, pdf_bytes: bytes, filename: str) -> Path:
        """保存 PDF 到文件"""
        output_path = self.output_dir / filename
        output_path.write_bytes(pdf_bytes)
        return output_path