"""Test persistence layer."""

import pytest
from datetime import datetime, timezone
from decimal import Decimal

from app.persistence.sqlite import Database, get_db
from app.persistence.models import (
    FillRecord,
    OrderRecord,
    PositionRecord,
    RiskEventRecord,
    KillSwitchRecord,
    ReconciliationSnapshot,
)


@pytest.fixture
def db():
    """Create a test database."""
    db = Database(":memory:")
    yield db
    # Cleanup happens automatically with in-memory DB


def test_database_initialization(db):
    """Database should initialize with WAL mode."""
    assert db.db_path.name == ":memory:"
    # Tables should exist
    with db.get_connection() as conn:
        cursor = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        )
        tables = [row["name"] for row in cursor.fetchall()]
        assert "fills" in tables
        assert "orders" in tables
        assert "positions" in tables
        assert "risk_events" in tables
        assert "kill_switch_events" in tables
        assert "reconciliation_snapshots" in tables


def test_record_and_retrieve_fill(db):
    """Should record a fill and retrieve it."""
    fill = FillRecord(
        id=1,
        contract="SHIB_USDT",
        side="buy",
        size=10,
        price=Decimal("0.00005"),
        fee=Decimal("0.000001"),
        fill_ts_ms=1234567890,
        recorded_ts=datetime.now(timezone.utc),
        realized_pnl=Decimal("0.0001"),
        order_id=12345,
        trade_id="trade_123",
        is_maker=True,
        dry_run=False,
    )
    
    record_id = db.record_fill(fill)
    assert record_id == 1
    
    fills = db.get_fills_by_contract("SHIB_USDT")
    assert len(fills) == 1
    assert fills[0].contract == "SHIB_USDT"
    assert fills[0].side == "buy"
    assert fills[0].size == 10


def test_record_and_retrieve_order(db):
    """Should record an order and retrieve it."""
    order = OrderRecord(
        id=1,
        contract="SHIB_USDT",
        side="buy",
        size=10,
        price=Decimal("0.00005"),
        order_id=12345,
        client_order_id="client_123",
        placed_ts_ms=1234567890,
        recorded_ts=datetime.now(timezone.utc),
        status="open",
        dry_run=False,
    )
    
    record_id = db.record_order(order)
    assert record_id == 1
    
    open_orders = db.get_open_orders("SHIB_USDT")
    assert len(open_orders) == 1
    assert open_orders[0].status == "open"


def test_update_order_status(db):
    """Should update order status."""
    order = OrderRecord(
        id=1,
        contract="SHIB_USDT",
        side="buy",
        size=10,
        price=Decimal("0.00005"),
        order_id=12345,
        placed_ts_ms=1234567890,
        recorded_ts=datetime.now(timezone.utc),
        status="open",
        dry_run=False,
    )
    
    db.record_order(order)
    db.update_order_status(12345, "filled", fill_size=10, filled_ts_ms=1234567900)
    
    open_orders = db.get_open_orders("SHIB_USDT")
    assert len(open_orders) == 0  # No longer open


def test_record_and_retrieve_position(db):
    """Should record a position snapshot and retrieve it."""
    position = PositionRecord(
        id=1,
        contract="SHIB_USDT",
        net_position=10,
        avg_entry_price=Decimal("0.00005"),
        realized_pnl=Decimal("0.0001"),
        unrealized_pnl=Decimal("0.00005"),
        total_fees=Decimal("0.000001"),
        snapshot_ts=datetime.now(timezone.utc),
        source="local",
    )
    
    record_id = db.record_position(position)
    assert record_id == 1
    
    latest = db.get_latest_position("SHIB_USDT")
    assert latest is not None
    assert latest.net_position == 10
    assert latest.source == "local"


def test_record_and_retrieve_risk_event(db):
    """Should record a risk event and retrieve it."""
    event = RiskEventRecord(
        id=1,
        event_type="daily_loss",
        contract="SHIB_USDT",
        reason="Daily loss limit exceeded",
        net_position=10,
        daily_pnl=Decimal("-10.00"),
        event_ts=datetime.now(timezone.utc),
        global_halt=True,
    )
    
    record_id = db.record_risk_event(event)
    assert record_id == 1
    
    recent_events = db.get_recent_risk_events()
    assert len(recent_events) == 1
    assert recent_events[0].event_type == "daily_loss"
    assert recent_events[0].global_halt is True


def test_record_and_retrieve_kill_switch(db):
    """Should record a kill switch event and retrieve it."""
    event = KillSwitchRecord(
        id=1,
        triggered=True,
        reason="Manual kill switch",
        trigger_source="api",
        event_ts=datetime.now(timezone.utc),
        operator="admin",
    )
    
    record_id = db.record_kill_switch(event)
    assert record_id == 1
    
    latest = db.get_latest_kill_switch()
    assert latest is not None
    assert latest.triggered is True
    assert latest.trigger_source == "api"


def test_record_and_retrieve_reconciliation(db):
    """Should record a reconciliation snapshot and retrieve it."""
    snapshot = ReconciliationSnapshot(
        id=1,
        contract="SHIB_USDT",
        local_orders=2,
        local_fills=5,
        local_position=10,
        exchange_orders=2,
        exchange_fills=5,
        exchange_position=10,
        order_drift=0,
        fill_drift=0,
        position_drift=0,
        snapshot_ts=datetime.now(timezone.utc),
        status="matched",
    )
    
    record_id = db.record_reconciliation(snapshot)
    assert record_id == 1
    
    history = db.get_reconciliation_history("SHIB_USDT")
    assert len(history) == 1
    assert history[0].status == "matched"
    assert history[0].position_drift == 0


def test_global_db_instance():
    """Global database instance should be reusable."""
    db1 = get_db(":memory:")
    db2 = get_db(":memory:")
    # Same instance
    assert db1 is db2
