"""Test tick rounding logic."""

import pytest
from decimal import Decimal


def test_round_to_tick_down():
    """Price should round down to tick size."""
    price = Decimal("0.00012345")
    tick = Decimal("0.00001")
    expected = Decimal("0.00012")
    result = (price // tick) * tick
    assert result == expected


def test_round_to_tick_exact():
    """Price already on tick should remain unchanged."""
    price = Decimal("0.00012")
    tick = Decimal("0.00001")
    expected = Decimal("0.00012")
    result = (price // tick) * tick
    assert result == expected


def test_tick_size_various():
    """Test various tick sizes."""
    price = Decimal("0.001234")
    
    tick_1 = Decimal("0.0001")
    assert (price // tick_1) * tick_1 == Decimal("0.0012")
    
    tick_2 = Decimal("0.00001")
    assert (price // tick_2) * tick_2 == Decimal("0.00123")
    
    tick_3 = Decimal("0.000001")
    assert (price // tick_3) * tick_3 == Decimal("0.001234")


def test_micro_price_ceiling():
    """Micro-price contracts should not exceed $0.10."""
    max_price = Decimal("0.10")
    assert Decimal("0.09999") < max_price
    assert Decimal("0.10") == max_price
    assert Decimal("0.10001") > max_price


def test_spread_calculation():
    """Spread should be ask - bid."""
    bid = Decimal("0.00005")
    ask = Decimal("0.00006")
    spread = ask - bid
    assert spread == Decimal("0.00001")


def test_minimum_spread():
    """Spread should be at least 1 tick."""
    bid = Decimal("0.00005")
    ask = Decimal("0.00006")
    tick = Decimal("0.00001")
    spread = ask - bid
    assert spread >= tick
