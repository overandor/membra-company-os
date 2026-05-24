"""Test order book functionality."""

import pytest
from decimal import Decimal
from app.market_data.order_book import BBO, OrderBook, registry


def test_bbo_creation():
    """BBO should create correctly."""
    bbo = BBO(
        bid_price=Decimal("0.00005"),
        bid_size=100,
        ask_price=Decimal("0.00006"),
        ask_size=100,
    )
    assert bbo.bid_price == Decimal("0.00005")
    assert bbo.ask_price == Decimal("0.00006")


def test_bbo_mid():
    """BBO mid should be average of bid and ask."""
    bbo = BBO(
        bid_price=Decimal("0.00005"),
        bid_size=100,
        ask_price=Decimal("0.00006"),
        ask_size=100,
    )
    assert bbo.mid == Decimal("0.000055")


def test_bbo_spread():
    """BBO spread should be ask - bid."""
    bbo = BBO(
        bid_price=Decimal("0.00005"),
        bid_size=100,
        ask_price=Decimal("0.00006"),
        ask_size=100,
    )
    assert bbo.spread == Decimal("0.00001")


def test_order_book_registry():
    """OrderBookRegistry should create order books."""
    ob = registry.get_or_create("TEST_USDT")
    assert ob is not None
    assert ob.contract == "TEST_USDT"


def test_order_book_bbo():
    """OrderBook should track BBO."""
    ob = OrderBook("TEST_USDT")
    bbo = ob.on_book_ticker({
        "b": "0.00005",
        "B": "100",
        "a": "0.00006",
        "A": "100",
    })
    assert bbo is not None  # BBO returned
    assert ob.best_bid() == Decimal("0.00005")
    assert ob.best_ask() == Decimal("0.00006")
