"""测试文档生成器"""
import pytest
import tempfile
import os
from pathlib import Path

from application.document_generator import DocumentGenerator


class TestDocumentGenerator:
    """测试文档生成器"""

    @pytest.fixture
    def temp_dir(self):
        """创建临时目录"""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    def generator(self, temp_dir):
        """创建文档生成器实例"""
        return DocumentGenerator(output_dir=temp_dir)

    def test_generator_initialization(self, generator, temp_dir):
        """测试生成器初始化"""
        assert generator.output_dir == temp_dir
        assert temp_dir.exists()

    def test_markdown_to_pdf_basic(self, generator):
        """测试基础 Markdown 转 PDF"""
        markdown = """# Test Title

## Introduction

This is a test content.

- Point 1
- Point 2

## Conclusion

End of document.
"""
        pdf_bytes = generator.markdown_to_pdf(
            markdown,
            "Test Report",
            "test_report.pdf"
        )
        assert pdf_bytes is not None
        assert len(pdf_bytes) > 0

    def test_markdown_to_pdf_with_headings(self, generator):
        """测试多级标题"""
        markdown = """# Main Title

## Section 1

### Subsection 1.1

Content here.

## Section 2

More content.
"""
        pdf_bytes = generator.markdown_to_pdf(
            markdown,
            "Multi Heading Test",
            "headings_test.pdf"
        )
        assert pdf_bytes is not None

    def test_markdown_to_pdf_with_lists(self, generator):
        """测试列表"""
        markdown = """# List Test

- Item 1
- Item 2
- Item 3

* Another item
* Yet another
"""
        pdf_bytes = generator.markdown_to_pdf(
            markdown,
            "List Test",
            "list_test.pdf"
        )
        assert pdf_bytes is not None

    def test_create_report_pdf(self, generator):
        """测试创建报告 PDF"""
        project_data = {
            'full_name': 'test/repo',
            'html_url': 'https://github.com/test/repo',
            'stars': 1000,
            'forks': 100,
            'language': 'Python',
            'rank': 1,
            'topics': ['python', 'ai', 'ml'],
            'description': 'A test repository for testing purposes.',
        }
        insights = [
            'Feature: Easy to use',
            'Feature: Well documented',
            'Usage: pip install test',
        ]

        pdf_bytes = generator.create_report_pdf(project_data, insights)
        assert pdf_bytes is not None
        assert len(pdf_bytes) > 0

    def test_create_report_pdf_with_minimal_data(self, generator):
        """测试最小数据创建报告"""
        project_data = {
            'full_name': 'minimal/repo',
            'html_url': '',
            'stars': 0,
            'forks': 0,
            'language': '',
            'rank': 0,
            'topics': [],
            'description': '',
        }

        pdf_bytes = generator.create_report_pdf(project_data, [])
        assert pdf_bytes is not None

    def test_save_pdf(self, generator, temp_dir):
        """测试保存 PDF"""
        test_content = b"%PDF-1.4 test content"
        filename = "saved_test.pdf"

        saved_path = generator.save_pdf(test_content, filename)
        assert saved_path.exists()
        assert saved_path.read_bytes() == test_content
        assert saved_path.name == filename

    def test_output_directory_creation(self):
        """测试输出目录自动创建"""
        with tempfile.TemporaryDirectory() as tmpdir:
            new_dir = Path(tmpdir) / "nested" / "dir"
            generator = DocumentGenerator(output_dir=new_dir)
            assert new_dir.exists()


class TestDocumentGeneratorStyles:
    """测试样式配置"""

    def test_styles_created(self):
        """测试样式创建"""
        generator = DocumentGenerator()
        assert generator.styles is not None
        assert 'CustomTitle' in generator.styles
        assert 'CustomHeading1' in generator.styles
        assert 'CustomHeading2' in generator.styles
        assert 'CustomBody' in generator.styles


class TestFormatText:
    """测试文本格式化"""

    def test_format_text_bold(self):
        """测试粗体格式化"""
        generator = DocumentGenerator()
        result = generator._format_text("This is **bold** text")
        assert "<b>bold</b>" in result

    def test_format_text_italic(self):
        """测试斜体格式化"""
        generator = DocumentGenerator()
        result = generator._format_text("This is *italic* text")
        assert "<i>italic</i>" in result

    def test_format_text_mixed(self):
        """测试混合格式化"""
        generator = DocumentGenerator()
        result = generator._format_text("**Bold** and *italic*")
        assert "<b>Bold</b>" in result
        assert "<i>italic</i>" in result