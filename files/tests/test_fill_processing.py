"""Test fill processing."""

import pytest
from decimal import Decimal
from app.risk.risk import Fill, RiskManager
from app.oms.oms import OMS


def test_fill_record():
    """Fill should be recorded correctly."""
    fill = Fill(
        contract="TEST_USDT",
        size=10,
        price=Decimal("0.00005"),
        fee=Decimal("0.000001"),
        ts_ms=1234567890,
    )
    assert fill.size == 10
    assert fill.price == Decimal("0.00005")


def test_fill_pnl_calculation():
    """Fill should calculate PnL correctly."""
    risk = RiskManager()
    
    # Buy fill
    buy_fill = Fill(
        contract="TEST_USDT",
        size=10,
        price=Decimal("0.00005"),
        fee=Decimal("0.000001"),
        ts_ms=1234567890,
    )
    
    # Process fill through risk manager
    risk.on_fill(buy_fill)
    
    # Check position
    state = risk.state("TEST_USDT")
    assert state.net_position == 10  # Long 10
    
    # Check fills recorded
    assert len(state.fills) == 1
    assert state.fills[0].size == 10
    
    # The risk manager accumulates fills for PnL calculation
    # Daily PnL is at the risk manager level
    assert risk.daily_pnl_ <= Decimal("0")  # Fees reduce PnL
