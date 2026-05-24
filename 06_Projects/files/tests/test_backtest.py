"""Test backtest engine."""

import pytest
from decimal import Decimal

from app.backtest.engine import BacktestEngine
from app.backtest.metrics import BacktestMetrics, Trade
from app.core.config import ContractSpec


def test_backtest_metrics_creation():
    """BacktestMetrics should create correctly."""
    metrics = BacktestMetrics()
    assert metrics.total_trades == 0
    assert metrics.total_pnl == Decimal("0")


def test_backtest_metrics_add_trade():
    """BacktestMetrics should track trades."""
    metrics = BacktestMetrics()
    trade = Trade(
        timestamp=1234567890,
        contract="TEST_USDT",
        side="buy",
        price=Decimal("0.00005"),
        size=10,
        fee=Decimal("0.000001"),
        pnl=Decimal("0.0001"),
    )
    metrics.add_trade(trade)
    assert metrics.total_trades == 1
    assert metrics.winning_trades == 1
    assert metrics.total_pnl == Decimal("0.0001")


def test_backtest_engine_creation():
    """BacktestEngine should create correctly."""
    engine = BacktestEngine()
    assert engine.risk is not None
    assert engine.oms is not None
    assert len(engine.snapshots) == 0


def test_backtest_generate_synthetic_data():
    """BacktestEngine should generate synthetic data."""
    engine = BacktestEngine()
    engine.generate_synthetic_data("TEST_USDT", num_snapshots=100)
    assert len(engine.snapshots) == 100
    assert engine.snapshots[0].contract == "TEST_USDT"


def test_backtest_run_with_synthetic_data():
    """BacktestEngine should run with synthetic data."""
    engine = BacktestEngine()
    engine.generate_synthetic_data("TEST_USDT", num_snapshots=100)
    
    specs = {
        "TEST_USDT": ContractSpec(
            name="TEST_USDT",
            tick_size=Decimal("0.000001"),
            lot_size=1,
            quanto_multiplier=Decimal("0.01"),
        )
    }
    
    metrics = engine.run_backtest(
        contracts=["TEST_USDT"],
        specs=specs,
        duration_seconds=60,
    )
    
    assert metrics is not None
    assert metrics.total_trades >= 0
    assert metrics.duration_seconds is not None
