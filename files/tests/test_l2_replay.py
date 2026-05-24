"""Test L2 replay engine."""

import json
import pytest
from decimal import Decimal
from pathlib import Path

from app.backtest.l2_replay import L2ReplayEngine, L2Snapshot, RecordedTrade
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
def l2_replay_engine(oms, risk, db):
    """Create an L2ReplayEngine instance."""
    return L2ReplayEngine(oms, risk, db, latency_ms=50, slippage_bps=5)


def test_l2_snapshot_from_jsonl():
    """Should create L2Snapshot from JSONL line."""
    line = '{"timestamp_ms": 1234567890000, "exchange_ts_ms": 1234567890000, "contract": "SHIB_USDT", "bids": [{"price": "0.00005", "size": 1000}], "asks": [{"price": "0.00006", "size": 1000}]}'
    
    snapshot = L2Snapshot.from_jsonl(line)
    
    assert snapshot.contract == "SHIB_USDT"
    assert snapshot.timestamp_ms == 1234567890000
    assert len(snapshot.bids) == 1
    assert snapshot.bids[0] == {"price": "0.00005", "size": 1000}


def test_l2_snapshot_to_market_snapshot(l2_replay_engine):
    """Should convert L2Snapshot to MarketSnapshot."""
    snapshot = L2Snapshot(
        timestamp_ms=1234567890000,
        exchange_ts_ms=1234567890000,
        contract="SHIB_USDT",
        message_type="snapshot",
        bids=[{"price": "0.00005", "size": 1000}],
        asks=[{"price": "0.00006", "size": 1000}],
    )
    
    market_snapshot = snapshot.to_market_snapshot()
    
    assert market_snapshot.contract == "SHIB_USDT"
    assert market_snapshot.bid_price == Decimal("0.00005")
    assert market_snapshot.ask_price == Decimal("0.00006")
    assert market_snapshot.bid_size == 1000
    assert market_snapshot.ask_size == 1000


def test_recorded_trade_from_jsonl():
    """Should create RecordedTrade from JSONL line."""
    line = '{"timestamp_ms": 1234567890000, "exchange_ts_ms": 1234567890000, "contract": "SHIB_USDT", "side": "buy", "price": "0.000055", "size": 10}'
    
    trade = RecordedTrade.from_jsonl(line)
    
    assert trade.contract == "SHIB_USDT"
    assert trade.side == "buy"
    assert trade.price == "0.000055"
    assert trade.size == 10


def test_l2_replay_engine_initialization(l2_replay_engine):
    """L2ReplayEngine should initialize correctly."""
    assert l2_replay_engine.oms is not None
    assert l2_replay_engine.risk is not None
    assert l2_replay_engine.db is not None
    assert l2_replay_engine.latency_ms == 50
    assert l2_replay_engine.slippage_bps == 5


def test_load_snapshots_from_jsonl(l2_replay_engine, tmp_path):
    """Should load L2 snapshots from JSONL file."""
    # Create test file
    test_file = tmp_path / "test_l2.jsonl"
    with open(test_file, "w") as f:
        for i in range(5):
            snapshot = {
                "timestamp_ms": 1234567890000 + (i * 1000),
                "exchange_ts_ms": 1234567890000 + (i * 1000),
                "contract": "SHIB_USDT",
                "bids": [{"price": "0.00005", "size": 1000}],
                "asks": [{"price": "0.00006", "size": 1000}],
                "sequence": i + 1,
            }
            f.write(json.dumps(snapshot) + "\n")
    
    count = l2_replay_engine.load_snapshots_from_jsonl(test_file)
    assert count == 5
    assert len(l2_replay_engine._snapshots) == 5


def test_calculate_ofi(l2_replay_engine):
    """Should calculate Order Flow Imbalance."""
    snapshot = L2Snapshot(
        timestamp_ms=1234567890000,
        exchange_ts_ms=1234567890000,
        contract="SHIB_USDT",
        message_type="snapshot",
        bids=[{"price": "0.00005", "size": 1000}],
        asks=[{"price": "0.00006", "size": 500}],
    )
    
    ofi = l2_replay_engine._calculate_ofi(snapshot)
    
    # OFI = (1000 - 500) / (1000 + 500) = 0.333
    assert abs(ofi - 0.333) < 0.01
    # Bid-heavy
    assert ofi <= 1.0


def test_calculate_microprice(l2_replay_engine):
    """Should calculate microprice."""
    snapshot = L2Snapshot(
        timestamp_ms=1234567890000,
        exchange_ts_ms=1234567890000,
        contract="SHIB_USDT",
        message_type="snapshot",
        bids=[{"price": "0.00005", "size": 1000}],
        asks=[{"price": "0.00006", "size": 1000}],
    )
    
    microprice = l2_replay_engine._calculate_microprice(snapshot)
    
    # Microprice = (0.00005 * 1000 + 0.00006 * 1000) / 2000 = 0.000055
    assert abs(float(microprice) - 0.000055) < 0.00000155


def test_l2_replay_engine_reset(l2_replay_engine):
    """Should reset replay state."""
    # Add some data
    l2_replay_engine._snapshots = [L2Snapshot(
        timestamp_ms=1234567890,
        exchange_ts_ms=1234567890,
        contract="SHIB_USDT",
        message_type="snapshot",
        bids=[],
        asks=[],
    )]
    l2_replay_engine._trades = [RecordedTrade(
        timestamp_ms=1234567890,
        exchange_ts_ms=1234567890,
        contract="SHIB_USDT",
        message_type="trade",
        side="buy",
        price="0.00005",
        size=10,
    )]
    
    assert len(l2_replay_engine._snapshots) == 1
    assert len(l2_replay_engine._trades) == 1
    
    l2_replay_engine.reset()
    
    assert len(l2_replay_engine._snapshots) == 0
    assert len(l2_replay_engine._trades) == 0
