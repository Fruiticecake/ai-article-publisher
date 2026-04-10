"""Unit tests for project_routes.py"""
import pytest
from application.routes.project_routes import router, _project_to_dict, ProjectCreate
from infrastructure.database import ProjectRecord


@pytest.mark.unit
def test_router_exists():
    """Test that router is properly created"""
    assert router is not None
    assert len(router.routes) > 0


@pytest.mark.unit
def test_project_create_model():
    """Test ProjectCreate pydantic model"""
    data = {
        "source": "github",
        "source_id": "12345",
        "full_name": "test/project",
        "html_url": "https://github.com/test/project",
        "description": "Test project",
        "stars": 100,
        "forks": 20,
        "language": "python",
        "topics": ["python", "test"],
    }
    project = ProjectCreate(**data)
    assert project.source == "github"
    assert project.full_name == "test/project"
    assert project.stars == 100
    assert project.topics == ["python", "test"]
    assert project.rank == 0  # default


@pytest.mark.unit
def test_project_to_dict():
    """Test _project_to_dict conversion"""
    # Create a mock ProjectRecord with minimal attributes
    class MockProject:
        id = 1
        source = "github"
        source_id = "12345"
        full_name = "test/project"
        html_url = "https://github.com/test/project"
        description = "Test"
        stars = 100
        forks = 20
        language = "python"
        topics = ["python"]
        rank = 10
        created_at = None
        updated_at = None

    result = _project_to_dict(MockProject())
    assert result["id"] == 1
    assert result["full_name"] == "test/project"
    assert result["stars"] == 100
    assert result["created_at"] is None
