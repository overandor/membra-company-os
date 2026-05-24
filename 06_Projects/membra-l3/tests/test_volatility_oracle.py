"""
Tests for MEMBRA L3 Volatility Oracle
"""
import pytest
import time
from membra_l3.volatility_oracle import (
    VolatilityOracle, VolatilitySignal, volatility_oracle,
)


class TestVolatilityOracle:
    @pytest.fixture
    def oracle(self):
        return VolatilityOracle()

    def test_feed_price_adds_data_point(self, oracle):
        oracle.feed_price(1.50, "jupiter", 10000.0)
        assert len(oracle._price_history) == 1
        assert oracle._price_history[0].price_usd == 1.50

    def test_feed_gas_adds_conditions(self, oracle):
        oracle.feed_gas(5000, 1000, False)
        assert len(oracle._gas_history) == 1
        assert oracle._gas_history[0].base_fee_lamports == 5000

    def test_feed_liquidity_updates_snapshot(self, oracle):
        oracle.feed_liquidity("MEMBRA", 50000.0, 2000.0)
        assert oracle._last_liquidity is not None
        assert oracle._last_liquidity.pool_usd == 50000.0

    def test_assess_with_no_data_returns_stale(self, oracle):
        report = oracle.assess(coverage_ratio=3.0)
        assert report.signal == VolatilitySignal.ORACLE_STALE

    def test_assess_with_flat_market_returns_paused(self, oracle):
        # Feed stable prices
        for _ in range(20):
            oracle.feed_price(1.50, "jupiter", 5000.0)
            time.sleep(0.001)
        oracle.feed_gas(5000, 0, False)
        oracle.feed_liquidity("MEMBRA", 50000.0, 5000.0)

        report = oracle.assess(coverage_ratio=3.0)
        assert report.signal == VolatilitySignal.VOLATILITY_PAUSED

    def test_assess_detects_volatility(self, oracle):
        # Feed rising prices
        base_price = 1.00
        for i in range(20):
            price = base_price * (1 + i * 0.005)  # 0.5% per step, 10% total
            oracle.feed_price(price, "jupiter", 5000.0)
            time.sleep(0.001)
        oracle.feed_gas(5000, 0, False)
        oracle.feed_liquidity("MEMBRA", 50000.0, 5000.0)

        report = oracle.assess(coverage_ratio=3.0)
        assert report.signal == VolatilitySignal.VOLATILITY_DETECTED
        assert report.confidence > 0.5

    def test_assess_detects_gas_spike(self, oracle):
        for _ in range(20):
            oracle.feed_price(1.50, "jupiter", 5000.0)
            time.sleep(0.001)
        oracle.feed_gas(5000, 200000, True)  # high priority fee + congested
        oracle.feed_liquidity("MEMBRA", 50000.0, 5000.0)

        report = oracle.assess(coverage_ratio=3.0)
        assert report.signal == VolatilitySignal.GAS_SPIKE

    def test_assess_detects_coverage_warning(self, oracle):
        for _ in range(20):
            oracle.feed_price(1.50, "jupiter", 5000.0)
            time.sleep(0.001)
        oracle.feed_gas(5000, 0, False)
        oracle.feed_liquidity("MEMBRA", 50000.0, 5000.0)

        report = oracle.assess(coverage_ratio=0.5)  # below minimum
        assert report.signal == VolatilitySignal.COVERAGE_WARNING

    def test_assess_detects_liquidity_low(self, oracle):
        for _ in range(20):
            oracle.feed_price(1.50, "jupiter", 5000.0)
            time.sleep(0.001)
        oracle.feed_gas(5000, 0, False)
        oracle.feed_liquidity("MEMBRA", 1000.0, 100.0)  # very low liquidity

        report = oracle.assess(coverage_ratio=3.0)
        assert report.signal == VolatilitySignal.LIQUIDITY_LOW

    def test_can_unlock_rebase_false_when_paused(self, oracle):
        for _ in range(20):
            oracle.feed_price(1.50, "jupiter", 5000.0)
            time.sleep(0.001)
        oracle.feed_gas(5000, 0, False)
        oracle.feed_liquidity("MEMBRA", 50000.0, 5000.0)
        oracle.assess(coverage_ratio=3.0)
        assert oracle.can_unlock_rebase is False  # market is flat

    def test_can_unlock_rebase_true_when_volatile(self, oracle):
        base_price = 1.00
        for i in range(20):
            price = base_price * (1 + i * 0.005)
            oracle.feed_price(price, "jupiter", 5000.0)
            time.sleep(0.001)
        oracle.feed_gas(5000, 0, False)
        oracle.feed_liquidity("MEMBRA", 50000.0, 5000.0)
        oracle.assess(coverage_ratio=3.0)
        assert oracle.can_unlock_rebase is True

    def test_singleton_oracle(self):
        volatility_oracle.feed_price(1.50, "test")
        assert len(volatility_oracle._price_history) >= 1
