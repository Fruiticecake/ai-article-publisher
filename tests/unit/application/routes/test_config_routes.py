"""Unit tests for config_routes.py"""
import pytest
from application.routes.config_routes import router, _mask_secret


@pytest.mark.unit
def test_router_exists():
    """Test that router is properly created"""
    assert router is not None
    assert len(router.routes) > 0


@pytest.mark.unit
def test_mask_secret_empty():
    """Test _mask_secret with empty input"""
    assert _mask_secret("") == ""
    assert _mask_secret(None) == ""


@pytest.mark.unit
def test_mask_secret_short():
    """Test _mask_secret with short string that gets fully masked"""
    result = _mask_secret("ab", 2, 2)
    assert result == "**"
    assert len(result) == 2


@pytest.mark.unit
def test_mask_secret_normal():
    """Test _mask_secret with normal length string"""
    # sk-abcdefghij1234 -> sk-**********1234
    result = _mask_secret("sk-abcdefghij1234", 3, 4)
    assert result == "sk-**********1234"
    assert len(result) == len("sk-abcdefghij1234")
    assert result.startswith("sk-")
    assert result.endswith("1234")


@pytest.mark.unit
def test_mask_secret_custom_keep():
    """Test _mask_secret with custom keep lengths"""
    result = _mask_secret("token-12345-abcde", 4, 4)
    assert result.startswith("toke")
    assert result.endswith("bcde")
    assert "*" in result
