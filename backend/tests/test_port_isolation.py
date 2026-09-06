import pytest
from app.config import Settings
from app.api.interceptor import validate_target_scope

def test_infrastructure_api_port_below_5000_fails():
    with pytest.raises(ValueError, match="must be between 5000 and 5999"):
        Settings(AUTHTWIN_API_PORT=4999)

def test_infrastructure_api_port_above_5999_fails():
    with pytest.raises(ValueError, match="must be between 5000 and 5999"):
        Settings(AUTHTWIN_API_PORT=6000)

def test_infrastructure_frontend_port_below_5000_fails():
    with pytest.raises(ValueError, match="must be between 5000 and 5999"):
        Settings(AUTHTWIN_FRONTEND_PORT=4999)

def test_infrastructure_frontend_port_above_5999_fails():
    with pytest.raises(ValueError, match="must be between 5000 and 5999"):
        Settings(AUTHTWIN_FRONTEND_PORT=6000)

def test_infrastructure_port_collision_fails():
    with pytest.raises(ValueError, match="cannot be the same"):
        Settings(AUTHTWIN_API_PORT=5173, AUTHTWIN_FRONTEND_PORT=5173)

def test_valid_infrastructure_ports_pass():
    s = Settings(AUTHTWIN_API_PORT=5000, AUTHTWIN_FRONTEND_PORT=5173)
    assert s.AUTHTWIN_API_PORT == 5000
    assert s.AUTHTWIN_FRONTEND_PORT == 5173

def test_target_applications_outside_5000_5999_remain_valid():
    """Verify target applications running on external ports (8001, 8090, 3000) pass target validation."""
    assert validate_target_scope("http://127.0.0.1:8001") == "http://127.0.0.1:8001"
    assert validate_target_scope("http://127.0.0.1:8090") == "http://127.0.0.1:8090"
    assert validate_target_scope("http://127.0.0.1:3000") == "http://127.0.0.1:3000"
