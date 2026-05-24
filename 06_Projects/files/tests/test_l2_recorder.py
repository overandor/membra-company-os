"""Test L2 market data recorder."""

import pytest
import json
from pathlib import Path

from app.market_data.recorder import L2Recorder, L2Snapshot, TradeEvent


@pytest.fixture
def tmp_path(tmp_path):
    """Create temporary path for testing."""
    return Path(tmp_path)


def test_l2_snapshot_from_ws_message():
    """Should create L2Snapshot from WebSocket message."""
    msg = {
        "result": {
            "s": "SHIB_USDT",
            "t": 1234567890000,
            "bids": [["0.00005", 1000], ["0.000049", 2000]],
            "asks": [["0.00006", 1000], ["0.000061", 2000]],
            "u": 123,
        }
    }
    
    snapshot = L2Snapshot.from_ws_message(msg, "SHIB_USDT")
    
    assert snapshot.contract == "SHIB_USDT"
    assert snapshot.exchange_ts_ms == 1234567890000
    assert len(snapshot.bids) == 2
    assert len(snapshot.asks) == 2
    assert snapshot.bids[0] == {"price": "0.00005", "size": 1000}
    assert snapshot.sequence == 123


def test_l2_snapshot_to_jsonl():
    """Should convert L2Snapshot to JSONL string."""
    snapshot = L2Snapshot(
        timestamp_ms=1234567890000,
        exchange_ts_ms=1234567890000,
        contract="SHIB_USDT",
        message_type="snapshot",
        bids=[{"price": "0.00005", "size": 1000}],
        asks=[{"price": "0.00006", "size": 1000}],
        sequence=1,
    )
    
    jsonl = snapshot.to_jsonl()
    assert "message_type" in jsonl
    assert "SHIB_USDT" in jsonl
    
    data = json.loads(jsonl)
    
    assert data["contract"] == "SHIB_USDT"
    assert data["timestamp_ms"] == 1234567890000
    assert len(data["bids"]) == 1


def test_trade_event_from_ws_message():
    """Should create TradeEvent from WebSocket message."""
    msg = {
        "result": {
            "t": 1234567890000,
            "side": "buy",
            "price": "0.000055",
            "size": 10,
        }
    }
    
    trade = TradeEvent.from_ws_message(msg, "SHIB_USDT")
    
    assert trade.contract == "SHIB_USDT"
    assert trade.side == "buy"
    assert trade.price == "0.000055"
    assert trade.size == 10


def test_trade_event_to_jsonl():
    """Should convert TradeEvent to JSONL string."""
    trade = TradeEvent(
        timestamp_ms=1234567890000,
        exchange_ts_ms=1234567890000,
        contract="SHIB_USDT",
        message_type="trade",
        side="buy",
        price="0.000055",
        size=10,
    )
    
    jsonl = trade.to_jsonl()
    assert "message_type" in jsonl
    assert "SHIB_USDT" in jsonl
    
    data = json.loads(jsonl)
    
    assert data["contract"] == "SHIB_USDT"
    assert data["side"] == "buy"
    assert data["size"] == 10


def test_l2_recorder_initialization(tmp_path):
    """L2Recorder should initialize correctly."""
    recorder = L2Recorder(
        output_dir=tmp_path,
        contracts=["SHIB_USDT"],
        depth_levels=20,
    )
    
    assert recorder.contracts == ["SHIB_USDT"]
    assert recorder.depth_levels == 20
    assert recorder._running is False
