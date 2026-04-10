"""Unit tests for dependencies.py"""
import pytest
from application.routes.dependencies import get_db, get_current_user, get_current_admin


@pytest.mark.unit
def test_get_db_exists():
    """Test that get_db generator exists"""
    # Just verify it's a generator function
    assert callable(get_db)


@pytest.mark.unit
def test_get_current_user_exists():
    """Test that get_current_user dependency exists"""
    assert callable(get_current_user)


@pytest.mark.unit
def test_get_current_admin_exists():
    """Test that get_current_admin dependency exists"""
    assert callable(get_current_admin)
