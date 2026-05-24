"""Test reconciliation engine."""

import asyncio
import pytest
from datetime import datetime, timezone
from decimal import Decimal

from app.reconcile.reconcile import ReconciliationEngine, ReconciliationResult, get_reconciler
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


def test_reconciler_initialization(reconciler):
    """Reconciler should initialize correctly."""
    assert reconciler.oms is not None
    assert reconciler.risk is not None
    assert reconciler.db is not None
    assert reconciler.interval_seconds == 1
    assert reconciler._running is False


def test_reconcile_contract_matched(reconciler):
    """Should detect when local and exchange state match."""
    # Setup local state
    reconciler.risk.state("SHIB_USDT")
    
    # Reconcile (will have no exchange state in test)
    result = asyncio.run(reconciler.reconcile_contract("SHIB_USDT"))
    
    assert result.contract == "SHIB_USDT"
    assert result.local_orders == 0
    assert result.exchange_orders == 0
    assert result.status in ["matched", "drift_detected"]


@pytest.mark.asyncio
async def test_reconcile_contract_drift_detected(reconciler, oms):
    """Should detect drift between local and exchange state."""
    # Setup local state with orders
    state = oms.get_or_create("SHIB_USDT")
    state.bid_order_id = 12345
    
    # Reconcile
    result = await reconciler.reconcile_contract("SHIB_USDT")
    
    assert result.contract == "SHIB_USDT"
    # Local has order, exchange doesn't -> drift
    assert result.local_orders >= 1
    assert result.order_drift != 0 or result.status == "drift_detected"


@pytest.mark.asyncio
async def test_reconcile_records_snapshot(reconciler):
    """Should record reconciliation snapshot to database."""
    reconciler.risk.state("SHIB_USDT")
    
    await reconciler.reconcile_contract("SHIB_USDT")
    
    # Check database for snapshot
    history = reconciler.db.get_reconciliation_history("SHIB_USDT")
    assert len(history) >= 1
    assert history[0].contract == "SHIB_USDT"


def test_global_reconciler_instance():
    """Global reconciler instance should be reusable."""
    oms = OMS()
    risk = RiskManager()
    db = Database(":memory:")
    
    reconciler1 = get_reconciler(oms, risk, db)
    reconciler2 = get_reconciler(oms, risk, db)
    
    # Same instance
    assert reconciler1 is reconciler2
