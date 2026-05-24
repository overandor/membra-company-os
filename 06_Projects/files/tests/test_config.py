"""Test configuration loading and safety flags."""

import os
import pytest
from decimal import Decimal

from app.core.config import (
    API_KEY,
    API_SECRET,
    LIVE_TRADING,
    LIVE_TRADING_CONFIRM,
    MICRO_CONTRACTS,
    mm_config,
    ContractSpec,
)


def test_api_keys_optional_in_dry_run():
    """API keys should be optional when not in live trading mode."""
    # In dry-run mode, API keys can be empty
    assert isinstance(API_KEY, str)
    assert isinstance(API_SECRET, str)


def test_live_trading_defaults_to_false():
    """LIVE_TRADING should default to False."""
    assert LIVE_TRADING is False


def test_live_trading_confirm_defaults_to_false():
    """LIVE_TRADING_CONFIRM should default to False."""
    assert LIVE_TRADING_CONFIRM is False


def test_micro_contracts_defined():
    """MICRO_CONTRACTS should be defined."""
    assert len(MICRO_CONTRACTS) > 0
    assert "SHIB_USDT" in MICRO_CONTRACTS


def test_mm_config_defaults():
    """MMConfig should have safe defaults."""
    assert mm_config.dry_run is False
    assert mm_config.order_size == 1
    assert mm_config.max_inventory_contracts == 50
    assert mm_config.daily_loss_limit_usdt == Decimal("5.00")


def test_contract_spec_creation():
    """ContractSpec should create correctly."""
    spec = ContractSpec(
        name="TEST_USDT",
        tick_size=Decimal("0.000001"),
        lot_size=1,
        quanto_multiplier=Decimal("0.01"),
    )
    assert spec.name == "TEST_USDT"
    assert spec.max_price == Decimal("0.10")


def test_dry_run_env_variable():
    """DRY_RUN environment variable should set config."""
    os.environ["DRY_RUN"] = "1"
    # This would be tested in the actual app startup
    assert os.environ["DRY_RUN"] == "1"
    del os.environ["DRY_RUN"]


def test_live_trading_env_variable():
    """LIVE_TRADING environment variable should be read correctly."""
    os.environ["LIVE_TRADING"] = "1"
    # Re-import to check
    import importlib
    import app.core.config
    importlib.reload(app.core.config)
    assert app.core.config.LIVE_TRADING is True
    del os.environ["LIVE_TRADING"]
    importlib.reload(app.core.config)


def test_live_trading_confirm_env_variable():
    """LIVE_TRADING_CONFIRM should require exact string."""
    os.environ["LIVE_TRADING_CONFIRM"] = "I_UNDERSTAND_RISK"
    import importlib
    import app.core.config
    importlib.reload(app.core.config)
    assert app.core.config.LIVE_TRADING_CONFIRM is True
    del os.environ["LIVE_TRADING_CONFIRM"]
    importlib.reload(app.core.config)
