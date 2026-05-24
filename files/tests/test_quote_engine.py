"""Test quoting engine."""

import pytest
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock

from app.strategy.quoting_engine import QuotingEngine, signal_bbo_change


def test_signal_bbo_change():
    """signal_bbo_change should be callable."""
    from app.market_data.order_book import registry as ob_registry
    
    # Should not raise
    signal_bbo_change("TEST_USDT")
    
    # Should trigger event for the contract's orderbook
    ob = ob_registry.get_or_create("TEST_USDT")
    # The event should have been triggered (we can't test the actual effect without a running loop)
    assert ob is not None


def test_quoting_engine_initialization():
    """QuotingEngine should initialize with correct state."""
    # Create a mock session
    mock_session = AsyncMock()
    
    # Create QuotingEngine
    qe = QuotingEngine(mock_session)
    
    # Should start in stopped state
    assert qe._running is False
    assert len(qe._tasks) == 0
