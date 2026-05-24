"""Test risk management functionality."""

import pytest
from decimal import Decimal
from app.risk.risk import RiskManager, Fill, ContractRiskState
from app.core.config import ContractSpec


def test_fill_creation():
    """Fill should create correctly."""
    fill = Fill(
        contract="TEST_USDT",
        size=10,
        price=Decimal("0.00005"),
        fee=Decimal("0.000001"),
        ts_ms=1234567890,
    )
    assert fill.contract == "TEST_USDT"
    assert fill.size == 10


def test_risk_manager_state():
    """RiskManager should track state per contract."""
    rm = RiskManager()
    state = rm.state("TEST_USDT")
    assert isinstance(state, ContractRiskState)
    assert state.net_position == 0


def test_risk_manager_on_fill():
    """RiskManager should update on fill."""
    rm = RiskManager()
    fill = Fill(
        contract="TEST_USDT",
        size=10,
        price=Decimal("0.00005"),
        fee=Decimal("0.000001"),
        ts_ms=1234567890,
    )
    rm.on_fill(fill)
    assert rm.state("TEST_USDT").net_position == 10


def test_inventory_limit():
    """RiskManager should enforce inventory limit."""
    rm = RiskManager()
    rm.state("TEST_USDT").net_position = 50
    spec = ContractSpec(
        name="TEST_USDT",
        tick_size=Decimal("0.000001"),
        lot_size=1,
        quanto_multiplier=Decimal("0.01"),
    )
    # At limit
    assert rm.allowed_buy_size("TEST_USDT", 10) == 0


def test_daily_loss_halt():
    """Daily loss halt should trigger when PnL drops below limit."""
    rm = RiskManager()
    rm.state("TEST_USDT")
    
    # Simulate losses through public API, not direct mutation
    rm.on_pnl_delta("TEST_USDT", Decimal("-10.00"))
    rm.check_daily_loss_halt()
    
    assert rm.global_halted_ is True


def test_skew_reduction():
    """RiskManager should reduce size on heavy side."""
    rm = RiskManager()
    rm.state("TEST_USDT").net_position = 30
    # Skew should reduce buy size
    buy_size = rm.allowed_buy_size("TEST_USDT", 10)
    assert buy_size < 10
