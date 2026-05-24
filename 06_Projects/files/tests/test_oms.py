"""Test order management system."""

import pytest
from decimal import Decimal

from app.oms.oms import OMS, ContractOrders


def test_contract_orders_creation():
    """ContractOrders should create correctly."""
    co = ContractOrders(contract="TEST_USDT")
    assert co.contract == "TEST_USDT"
    assert co.bid_order_id is None
    assert co.ask_order_id is None


def test_oms_state_tracking():
    """OMS should track state per contract."""
    oms = OMS()
    state = oms.get_or_create("TEST_USDT")
    assert isinstance(state, ContractOrders)


def test_oms_live_order_count():
    """OMS should count live orders."""
    oms = OMS()
    state = oms.get_or_create("TEST_USDT")
    state.bid_order_id = 12345
    assert oms.live_order_count() == 1


@pytest.mark.asyncio
async def test_oms_clear_local_state():
    """OMS should clear local order state without touching exchange."""
    oms = OMS()
    
    state = oms.get_or_create("TEST_USDT")
    
    state.bid_order_id = 12345
    state.ask_order_id = 12346
    state.bid_price = Decimal("0.00005")
    state.ask_price = Decimal("0.00006")
    state.bid_size = 10
    state.ask_size = 10
    
    # Clear local state only
    await oms.clear_local_state()
    
    assert state.bid_order_id is None
    assert state.ask_order_id is None
    assert state.bid_price is None
    assert state.ask_price is None
    assert state.bid_size == 0
    assert state.ask_size == 0


@pytest.mark.asyncio
async def test_oms_cancel_all_integration():
    """OMS cancel_all should call exchange cancel then clear local state."""
    oms = OMS()
    
    state = oms.get_or_create("TEST_USDT")
    
    state.bid_order_id = 12345
    state.ask_order_id = 12346
    
    # In dry-run mode, cancel_all doesn't need a real session
    # This tests the integration flow
    from app.core.config import mm_config
    original_dry_run = mm_config.dry_run
    try:
        mm_config.dry_run = True
        await oms.cancel_all(None)
        assert state.bid_order_id is None
        assert state.ask_order_id is None
    finally:
        mm_config.dry_run = original_dry_run
