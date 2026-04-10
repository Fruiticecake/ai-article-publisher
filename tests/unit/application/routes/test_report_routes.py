"""Unit tests for report_routes.py"""
import pytest
from application.routes.report_routes import router, _report_to_dict
from infrastructure.database import ReportRecord


@pytest.mark.unit
def test_router_exists():
    """Test that router is properly created"""
    assert router is not None
    assert len(router.routes) > 0


@pytest.mark.unit
def test_report_to_dict():
    """Test _report_to_dict conversion"""
    class MockReport:
        id = 1
        title = "Test Report"
        project_id = 42
        quality_score = 85
        generated_at = None
        published_at = None
        insights = None

    result = _report_to_dict(MockReport())
    assert result["id"] == 1
    assert result["title"] == "Test Report"
    assert result["project_id"] == 42
    assert result["quality_score"] == 85
    assert result["generated_at"] is None
