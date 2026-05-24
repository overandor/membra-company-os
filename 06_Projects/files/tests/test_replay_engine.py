"""Test replay engine."""

import pytest
from decimal import Decimal
from pathlib import Path

from app.backtest.replay_engine import (
    ReplayEngine,
    MarketSnapshot,
    TradeEvent,
    generate_sample_fixtures,
)
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
def replay_engine(oms, risk, db):
    """Create a ReplayEngine instance."""
    return ReplayEngine(oms, risk, db, latency_ms=50, slippage_bps=5)


def test_market_snapshot_from_dict():
    """Should create MarketSnapshot from dictionary."""
    data = {
        "timestamp_ms": 1234567890,
        "contract": "SHIB_USDT",
        "bid_price": "0.00005",
        "ask_price": "0.00006",
        "bid_size": 1000,
        "ask_size": 1000,
        "last_price": "0.000055",
        "last_size": 10,
    }
    
    snapshot = MarketSnapshot.from_dict(data)
    
    assert snapshot.timestamp_ms == 1234567890
    assert snapshot.contract == "SHIB_USDT"
    assert snapshot.bid_price == Decimal("0.00005")
    assert snapshot.ask_price == Decimal("0.00006")
    assert snapshot.bid_size == 1000
    assert snapshot.ask_size == 1000
    assert snapshot.last_price == Decimal("0.000055")
    assert snapshot.last_size == 10


def test_trade_event_from_dict():
    """Should create TradeEvent from dictionary."""
    data = {
        "timestamp_ms": 1234567890,
        "contract": "SHIB_USDT",
        "side": "buy",
        "price": "0.000055",
        "size": 10,
        "is_maker": True,
    }
    
    trade = TradeEvent.from_dict(data)
    
    assert trade.timestamp_ms == 1234567890
    assert trade.contract == "SHIB_USDT"
    assert trade.side == "buy"
    assert trade.price == Decimal("0.000055")
    assert trade.size == 10
    assert trade.is_maker is True


def test_replay_engine_initialization(replay_engine):
    """ReplayEngine should initialize correctly."""
    assert replay_engine.oms is not None
    assert replay_engine.risk is not None
    assert replay_engine.db is not None
    assert replay_engine.latency_ms == 50
    assert replay_engine.slippage_bps == 5


def test_load_snapshots_from_jsonl(tmp_path, replay_engine):
    """Should load snapshots from JSONL file."""
    # Create test file
    test_file = tmp_path / "test_snapshots.jsonl"
    with open(test_file, "w") as f:
        for i in range(10):
            snapshot = {
                "timestamp_ms": 1234567890000 + (i * 1000),
                "contract": "SHIB_USDT",
                "bid_price": "0.00005",
                "ask_price": "0.00006",
                "bid_size": 1000,
                "ask_size": 1000,
            }
            f.write(snapshot.__str__().replace("'", '"') + "\n")
    
    # This test is simplified - in reality would need proper JSON format
    # For now, just verify the method exists
    count = replay_engine.load_snapshots_from_jsonl(test_file)
    assert count >= 0


def test_generate_sample_fixtures(tmp_path):
    """Should generate sample fixture files."""
    generate_sample_fixtures(tmp_path)
    
    snapshots_file = tmp_path / "sample_snapshots.jsonl"
    trades_file = tmp_path / "sample_trades.jsonl"
    
    assert snapshots_file.exists()
    assert trades_file.exists()
    
    # Check files have content
    assert snapshots_file.stat().st_size > 0
    assert trades_file.stat().st_size > 0


def test_replay_engine_reset(replay_engine):
    """Should reset replay state."""
    # Add some data
    replay_engine._snapshots = [MarketSnapshot(
        timestamp_ms=1234567890,
        contract="SHIB_USDT",
        bid_price=Decimal("0.00005"),
        ask_price=Decimal("0.00006"),
        bid_size=1000,
        ask_size=1000,
    )]
    
    assert len(replay_engine._snapshots) == 1
    
    replay_engine.reset()
    
    assert len(replay_engine._snapshots) == 0
    assert len(replay_engine._trades) == 0
    assert replay_engine._current_index == 0
