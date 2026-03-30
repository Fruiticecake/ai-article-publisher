"""测试领域模型"""
import pytest
from datetime import datetime
from core.models import SourceType, PublisherType, Project, Report, QualityMetrics


class TestProject:
    def test_slug_property(self):
        project = Project(
            source=SourceType.GITHUB,
            source_id="123",
            rank=1,
            full_name="owner/repo",
            html_url="https://github.com/owner/repo",
            description="Test",
            stars=100,
            forks=10,
            language="Python",
            topics=["ai", "ml"],
            readme="",
        )
        assert project.slug == "owner_repo"

    def test_activity_score(self):
        project = Project(
            source=SourceType.GITHUB,
            source_id="123",
            rank=1,
            full_name="owner/repo",
            html_url="https://github.com/owner/repo",
            description="Test",
            stars=1000,
            forks=100,
            language="Python",
            topics=["ai", "ml"],
            readme="",
        )
        # 1000 * 1.0 + 100 * 0.5 + 2 * 10.0 = 1000 + 50 + 20 = 1070
        assert project.activity_score == 1070.0


class TestReport:
    def test_report_creation(self):
        report = Report(
            id="1",
            title="Test Report",
            content_markdown="# Test",
            generated_at=datetime.now(),
        )
        assert report.id == "1"
        assert report.title == "Test Report"


class TestQualityMetrics:
    def test_metrics_creation(self):
        metrics = QualityMetrics(
            activity_score=80.0,
            documentation_score=70.0,
            security_score=90.0,
            license_compliance=True,
            overall_score=80.0,
        )
        assert metrics.activity_score == 80.0
        assert metrics.license_compliance is True
