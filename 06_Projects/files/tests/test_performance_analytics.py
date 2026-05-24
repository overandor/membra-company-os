"""Test performance analytics."""

import pytest
from datetime import datetime, timezone
from decimal import Decimal

from app.analytics.performance import PerformanceAnalyzer, PerformanceMetrics
from app.persistence.sqlite import Database
from app.persistence.models import FillRecord


@pytest.fixture
def db():
    """Create a test database."""
    return Database(":memory:")


@pytest.fixture
def analyzer(db):
    """Create a PerformanceAnalyzer instance."""
    return PerformanceAnalyzer(db)


def test_analyzer_initialization(analyzer):
    """PerformanceAnalyzer should initialize correctly."""
    assert analyzer.db is not None


def test_calculate_metrics_no_fills(analyzer):
    """Should return empty metrics when no fills exist."""
    metrics = analyzer.calculate_metrics("TEST_USDT")
    
    assert metrics.total_trades == 0
    assert metrics.total_pnl == Decimal("0")
    assert metrics.win_rate == Decimal("0")


def test_calculate_metrics_with_fills(analyzer):
    """Should calculate metrics from fills."""
    # Add test fills
    fill1 = FillRecord(
        id=1,
        contract="TEST_USDT",
        side="buy",
        size=10,
        price=Decimal("0.00005"),
        fee=Decimal("0.000001"),
        fill_ts_ms=1234567890,
        recorded_ts=datetime.now(timezone.utc),
        realized_pnl=Decimal("0.0001"),
        is_maker=True,
        dry_run=True,
    )
    
    fill2 = FillRecord(
        id=2,
        contract="TEST_USDT",
        side="sell",
        size=10,
        price=Decimal("0.00006"),
        fee=Decimal("0.000001"),
        fill_ts_ms=1234567891,
        recorded_ts=datetime.now(timezone.utc),
        realized_pnl=Decimal("-0.00005"),
        is_maker=True,
        dry_run=True,
    )
    
    analyzer.db.record_fill(fill1)
    analyzer.db.record_fill(fill2)
    
    metrics = analyzer.calculate_metrics("TEST_USDT")
    
    assert metrics.total_trades == 2
    assert metrics.total_pnl == Decimal("0.00005")
    assert metrics.total_fees == Decimal("0.000002")
    assert metrics.winning_trades == 1
    assert metrics.losing_trades == 1
    assert metrics.win_rate == Decimal("0.5")


def test_realized_edge_bps_calculation(analyzer):
    """Should calculate realized edge in basis points."""
    fill = FillRecord(
        id=1,
        contract="TEST_USDT",
        side="buy",
        size=10,
        price=Decimal("0.00005"),
        fee=Decimal("0.000001"),
        fill_ts_ms=1234567890,
        recorded_ts=datetime.now(timezone.utc),
        realized_pnl=Decimal("0.0001"),
        is_maker=True,
        dry_run=True,
    )
    
    analyzer.db.record_fill(fill)
    
    metrics = analyzer.calculate_metrics("TEST_USDT")
    
    # Notional = 0.00005 * 10 = 0.0005
    # Edge = 0.0001 / 0.0005 * 10000 = 2 bps
    assert metrics.realized_edge_bps > Decimal("0")


def test_profit_factor_calculation(analyzer):
    """Should calculate profit factor correctly."""
    # Add winning fill
    fill1 = FillRecord(
        id=1,
        contract="TEST_USDT",
        side="buy",
        size=10,
        price=Decimal("0.00005"),
        fee=Decimal("0.000001"),
        fill_ts_ms=1234567890,
        recorded_ts=datetime.now(timezone.utc),
        realized_pnl=Decimal("0.001"),
        is_maker=True,
        dry_run=True,
    )
    
    # Add losing fill
    fill2 = FillRecord(
        id=2,
        contract="TEST_USDT",
        side="sell",
        size=10,
        price=Decimal("0.00006"),
        fee=Decimal("0.000001"),
        fill_ts_ms=1234567891,
        recorded_ts=datetime.now(timezone.utc),
        realized_pnl=Decimal("-0.0005"),
        is_maker=True,
        dry_run=True,
    )
    
    analyzer.db.record_fill(fill1)
    analyzer.db.record_fill(fill2)
    
    metrics = analyzer.calculate_metrics("TEST_USDT")
    
    # Profit factor = gross_profit / gross_loss = 0.001 / 0.0005 = 2
    assert metrics.profit_factor == Decimal("2")


def test_generate_report(analyzer):
    """Should generate human-readable report."""
    fill = FillRecord(
        id=1,
        contract="TEST_USDT",
        side="buy",
        size=10,
        price=Decimal("0.00005"),
        fee=Decimal("0.000001"),
        fill_ts_ms=1234567890,
        recorded_ts=datetime.now(timezone.utc),
        realized_pnl=Decimal("0.0001"),
        is_maker=True,
        dry_run=True,
    )
    
    analyzer.db.record_fill(fill)
    
    report = analyzer.generate_report("TEST_USDT")
    
    assert "PERFORMANCE REPORT" in report
    assert "TEST_USDT" in report
    assert "Total PnL" in report
    assert "Realized Edge" in report
    assert "Win Rate" in report
