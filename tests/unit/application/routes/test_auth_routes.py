"""Unit tests for auth_routes.py"""
import pytest
from unittest.mock import AsyncMock, patch

from application.routes.auth_routes import router, LoginRequest, RegisterRequest
from application.auth import AuthService


@pytest.mark.unit
def test_router_exists():
    """Test that router is properly created"""
    assert router is not None
    assert len(router.routes) > 0


@pytest.mark.unit
def test_login_request_model():
    """Test LoginRequest pydantic model"""
    request = LoginRequest(username="testuser", password="testpass")
    assert request.username == "testuser"
    assert request.password == "testpass"


@pytest.mark.unit
def test_register_request_model():
    """Test RegisterRequest pydantic model"""
    request = RegisterRequest(username="testuser", password="testpass", email="test@example.com")
    assert request.username == "testuser"
    assert request.password == "testpass"
    assert request.email == "test@example.com"

    # Email is optional
    request2 = RegisterRequest(username="testuser", password="testpass")
    assert request2.email is None
