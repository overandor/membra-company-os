"""Test API health endpoints."""

import pytest
from fastapi.testclient import TestClient
from app.api.server import app


def test_health_endpoint():
    """GET /health should return 200."""
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "live_trading" in data


def test_ready_endpoint():
    """GET /ready should return 200 when system is ready."""
    from app.core.config import mm_config
    from app.core.config import ContractSpec
    from decimal import Decimal
    
    client = TestClient(app)
    
    # Load test contracts
    original_contracts = mm_config.contracts
    try:
        mm_config.contracts = {
            "TEST_USDT": ContractSpec(
                name="TEST_USDT",
                tick_size=Decimal("0.000001"),
                lot_size=1,
                quanto_multiplier=Decimal("0.01"),
                max_price=Decimal("0.10"),
            )
        }
        
        response = client.get("/ready")
        assert response.status_code == 200
        data = response.json()
        assert data["ready"] is True
    finally:
        mm_config.contracts = original_contracts


def test_ready_endpoint_with_kill_switch():
    """GET /ready should return False when kill switch is active."""
    import app.api.server as server_module
    from app.core.config import mm_config, ContractSpec
    from decimal import Decimal
    
    client = TestClient(app)
    original_state = server_module._kill_switch_active
    original_contracts = mm_config.contracts
    
    try:
        # Load test contracts first
        mm_config.contracts = {
            "TEST_USDT": ContractSpec(
                name="TEST_USDT",
                tick_size=Decimal("0.000001"),
                lot_size=1,
                quanto_multiplier=Decimal("0.01"),
                max_price=Decimal("0.10"),
            )
        }
        
        # Set kill switch at module level
        server_module._kill_switch_active = True
        
        response = client.get("/ready")
        assert response.status_code == 200
        data = response.json()
        assert data["ready"] is False
        assert "Kill switch is active" in data["reason"]
    finally:
        server_module._kill_switch_active = original_state
        mm_config.contracts = original_contracts


def test_ready_endpoint_with_risk_halt():
    """GET /ready should return False when risk is halted."""
    from app.api.server import risk
    from app.core.config import mm_config, ContractSpec
    from decimal import Decimal
    
    client = TestClient(app)
    original_halted = risk.global_halted_
    original_contracts = mm_config.contracts
    
    try:
        # Load test contracts first
        mm_config.contracts = {
            "TEST_USDT": ContractSpec(
                name="TEST_USDT",
                tick_size=Decimal("0.000001"),
                lot_size=1,
                quanto_multiplier=Decimal("0.01"),
                max_price=Decimal("0.10"),
            )
        }
        
        risk.trigger_global_halt("test_halt")
        response = client.get("/ready")
        assert response.status_code == 200
        data = response.json()
        assert data["ready"] is False
        assert "Global risk halt" in data["reason"]
    finally:
        if original_halted:
            pass  # Keep it halted if it was
        else:
            risk.reset_global_halt()
        mm_config.contracts = original_contracts


def test_metrics_endpoint():
    """GET /metrics should return 200."""
    client = TestClient(app)
    response = client.get("/metrics")
    assert response.status_code == 200
    data = response.json()
    assert "live_orders" in data


def test_kill_switch():
    """POST /kill-switch should activate kill switch."""
    client = TestClient(app)
    response = client.post("/kill-switch")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True


def test_cancel_all():
    """POST /cancel-all should cancel all orders."""
    client = TestClient(app)
    response = client.post("/cancel-all")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
