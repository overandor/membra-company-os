"""
DepthOS Micro-Price Market Maker — Configuration
Gate.io Futures · 0–10 cent perpetuals · Top-of-book quoting
"""
from __future__ import annotations
import os
from dataclasses import dataclass, field
from decimal import Decimal
from typing import Dict, List


# ─── Network ────────────────────────────────────────────────────────────────
FUTURES_REST_URL  = "https://fx-api.gateio.ws/api/v4"
FUTURES_WS_URL    = "wss://fx-ws.gateio.ws/v4/ws/usdt"
SETTLE            = "usdt"

# ─── Auth (env-injected — never hardcode) ───────────────────────────────────
# API keys are optional in dry-run mode
API_KEY = os.environ.get("GATE_API_KEY", "")
API_SECRET = os.environ.get("GATE_API_SECRET", "")

# ─── Safety flags ────────────────────────────────────────────────────────────
LIVE_TRADING = os.environ.get("LIVE_TRADING", "0") == "1"
LIVE_TRADING_CONFIRM = os.environ.get("LIVE_TRADING_CONFIRM", "") == "I_UNDERSTAND_RISK"

# ─── Micro-price universe: perpetuals priced 0–10 cents ─────────────────────
# Adjust this list to your actual enabled contracts.
MICRO_CONTRACTS: List[str] = [
    "SHIB_USDT",
    "PEPE_USDT",
    "FLOKI_USDT",
    "BONK_USDT",
    "1000RATS_USDT",
    "XEC_USDT",
]

@dataclass
class ContractSpec:
    """Per-contract trading parameters derived from exchange metadata."""
    name:           str
    tick_size:      Decimal     # minimum price increment
    lot_size:       int         # minimum order size in contracts
    quanto_multiplier: Decimal  # value per contract in USDT
    max_price:      Decimal = Decimal("0.10")   # hard ceiling — micro only


@dataclass
class MMConfig:
    """Market-maker behavioural parameters."""

    # ── Quoting ──────────────────────────────────────────────────────────────
    # How many contracts to quote on each side.
    order_size: int = 1            # start at 1 contract per side

    # Quote refresh: replace order when best price moves by ≥ this many ticks.
    reprice_tick_threshold: int = 1

    # ── Inventory / risk ─────────────────────────────────────────────────────
    # Hard net-position limit per contract (contracts, signed).
    max_inventory_contracts: int  = 50
    # Skew: reduce size on the heavy side when net > this threshold.
    skew_threshold_contracts: int = 20

    # ── Daily loss halt ───────────────────────────────────────────────────────
    daily_loss_limit_usdt: Decimal = Decimal("5.00")

    # ── Timing ───────────────────────────────────────────────────────────────
    heartbeat_interval_s: float = 30.0
    order_ttl_s:          float = 10.0   # cancel and re-post after this age
    reconnect_delay_s:    float  = 2.0
    max_reconnect_attempts: int  = 10

    # ── Gate.io account mode ──────────────────────────────────────────────────
    # "single" = one-way mode; "dual" = hedge mode (long/short separate).
    account_mode: str = "single"

    # ── Misc ─────────────────────────────────────────────────────────────────
    dry_run: bool = False          # True → log orders but never send

    # Contract specs populated at runtime after REST bootstrap.
    contracts: Dict[str, ContractSpec] = field(default_factory=dict)


# Singleton consumed by all modules.
mm_config = MMConfig()
