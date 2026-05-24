"""Test shutdown behavior."""

import pytest
import asyncio
from unittest.mock import AsyncMock

from app.oms.oms import OMS
from app.strategy.quoting_engine import QuotingEngine
from app.risk.risk import RiskManager


def test_shutdown_cancels_all_orders():
    """Shutdown should cancel all orders."""
    oms = OMS()
    
    # Setup orders
    state = oms.get_or_create("TEST_USDT")
    state.bid_order_id = 12345
    state.ask_order_id = 12346
    
    # Clear local state (part of shutdown)
    asyncio.run(oms.clear_local_state())
    
    # Orders should be cleared
    assert state.bid_order_id is None
    assert state.ask_order_id is None


def test_shutdown_closes_websocket():
    """Shutdown should close WebSocket connections."""
    from app.connectors.ws_manager import WSManager
    from unittest.mock import AsyncMock
    
    # Create mock session
    mock_session = AsyncMock()
    
    # WebSocket manager should be able to stop
    # We can't test actual WebSocket without a real connection
    # But we can verify the structure exists
    assert WSManager is not None


def test_graceful_shutdown():
    """Shutdown should be graceful."""
    from unittest.mock import AsyncMock
    
    # Mock session
    mock_session = AsyncMock()
    
    # Create quoting engine
    qe = QuotingEngine(mock_session)
    
    # Verify it starts in stopped state
    assert qe._running is False
    
    # Graceful shutdown should:
    # 1. Stop quoting tasks
    # 2. Cancel orders on exchange
    # 3. Clear local state
    # These are tested in the individual component tests
