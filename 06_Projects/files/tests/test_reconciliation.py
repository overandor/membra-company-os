"""Test reconciliation logic."""

import pytest
from decimal import Decimal

from app.reconcile.reconcile import ReconciliationEngine, ReconciliationResult
from app.oms.oms import OMS
from app.risk.risk import RiskManager
from app.persistence.sqlite import Database


@pytest.fixture
def oms():
    """Create an OMS instance."""
    return OMS()


@pytest.fixture
def risk():
    """Create a RiskManager instance."""
    return RiskManager()


@pytest.fixture
def db():
    """Create a test database."""
    return Database(":memory:")


@pytest.fixture
def reconciler(oms, risk, db):
    """Create a ReconciliationEngine instance."""
    return ReconciliationEngine(oms, risk, db, interval_seconds=1)


def test_order_reconciliation(reconciler, oms):
    """Orders should be reconciled with exchange."""
    # Setup local state with orders
    state = oms.get_or_create("SHIB_USDT")
    state.bid_order_id = 12345
    state.ask_order_id = 12346
    
    # Reconcile will detect drift (local has orders, exchange doesn't)
    import asyncio
    result = asyncio.run(reconciler.reconcile_contract("SHIB_USDT"))
    
    assert result.contract == "SHIB_USDT"
    assert result.local_orders >= 1
    # Should detect drift since exchange has no orders
    assert result.order_drift != 0 or result.status == "drift_detected"


def test_position_reconciliation(reconciler, risk):
    """Positions should be reconciled with exchange."""
    # Setup local position
    risk.state("SHIB_USDT")
    risk.state("SHIB_USDT").net_position = 10
    
    # Reconcile will check position
    import asyncio
    result = asyncio.run(reconciler.reconcile_contract("SHIB_USDT"))
    
    assert result.contract == "SHIB_USDT"
    assert result.local_position == 10
    # Should record snapshot to database
    history = reconciler.db.get_reconciliation_history("SHIB_USDT")
    assert len(history) >= 1

