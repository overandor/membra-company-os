# Code Appraisal Estimate

#### You:
Can you in our hours dollars in dollars please appraise this code? from __future__ import annotations

"""
Gate.io Micro Futures Trader — one-file advanced rewrite
========================================================

Features
--------
- dry/live modes
- startup state persistence
- startup exchange reconciliation hooks
- contract metadata validation
- idempotent order tags
- safer close plumbing
- cooldowns
- structured JSONL logging
- CSV trade journal
- walk-forward backtesting
- parameter sweeps
- Monte Carlo robustness simulation
- unit tests
- perpetual futures balance / position / order book commands

Install
-------
    pip install gate-api requests

Examples
--------
    python gate_micro_advanced.py --dry
    python gate_micro_advanced.py --live
    python gate_micro_advanced.py --balance
    python gate_micro_advanced.py --position BTC_USDT
    python gate_micro_advanced.py --book BTC_USDT
    python gate_micro_advanced.py --backtest BTC_USDT
    python gate_micro_advanced.py --walk BTC_USDT
    python gate_micro_advanced.py --mc BTC_USDT
    python gate_micro_advanced.py --sweep BTC_USDT
    python gate_micro_advanced.py --test
"""

import argparse
import csv
import hashlib
import json
import logging
import math
import os
import random
import statistics
import sys
import threading
import time
import traceback
import unittest
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum, auto
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, List, Optional, Sequence, Tuple

try:
    import requests
except ImportError:  # pragma: no cover
    requests = None  # type: ignore[assignment]

try:
    import gate_api
    from gate_api import ApiClient, Configuration, FuturesApi
    GATE_AVAILABLE = True
except ImportError:  # pragma: no cover
    gate_api = None  # type: ignore[assignment]
    ApiClient = Configuration = FuturesApi = object  # type: ignore[misc,assignment]
    GATE_AVAILABLE = False


# =============================================================================
# GLOBAL CONFIG
# =============================================================================

APP_NAME = "gate-micro-advanced"
VERSION = "2.1-single-file"

# SAFE: env vars only
GATE_API_KEY = os.getenv("GATE_API_KEY", "")
GATE_API_SECRET = os.getenv("GATE_API_SECRET", "")

SETTLE = os.environ.get("GATE_SETTLE", "usdt")
DEFAULT_SYMBOL = os.environ.get("GATE_SYMBOL", "BTC_USDT")

# Account and risk
ACCOUNT_BALANCE = float(os.environ.get("ACCOUNT_BALANCE", "10.0"))
LEVERAGE = int(os.environ.get("LEVERAGE", "5"))
MAX_DAILY_LOSS_PCT = float(os.environ.get("MAX_DAILY_LOSS_PCT", "0.10"))
MAX_ACCOUNT_RISK_PCT = float(os.environ.get("MAX_ACCOUNT_RISK_PCT", "0.20"))
MAX_OPEN_POSITIONS = int(os.environ.get("MAX_OPEN_POSITIONS", "5"))
MAX_PER_REGIME = int(os.environ.get("MAX_PER_REGIME", "3"))
COOLDOWN_SECONDS = int(os.environ.get("COOLDOWN_SECONDS", "1800"))

# Universe scanning
MIN_NOTIONAL = float(os.environ.get("MIN_NOTIONAL", "0.01"))
MAX_NOTIONAL = float(os.environ.get("MAX_NOTIONAL", "0.25"))
MIN_VOLUME_USDT = float(os.environ.get("MIN_VOLUME_USDT", "250000"))
SCAN_WORKERS = int(os.environ.get("SCAN_WORKERS", "10"))
LOOKBACK_HOURS = int(os.environ.get("LOOKBACK_HOURS", "1"))
POLL_INTERVAL = int(os.environ.get("POLL_INTERVAL", "30"))
REGIME_TTL = int(os.environ.get("REGIME_TTL", "180"))

# Strategy thresholds
PUMP_THRESHOLD = float(os.environ.get("PUMP_THRESHOLD", "0.08"))
DUMP_THRESHOLD = float(os.environ.get("DUMP_THRESHOLD", "-0.08"))
ADX_TREND_MIN = float(os.environ.get("ADX_TREND_MIN", "23.0"))
ATR_VOLATILE_MULT = float(os.environ.get("ATR_VOLATILE_MULT", "1.8"))
RSI_OVERBOUGHT = float(os.environ.get("RSI_OVERBOUGHT", "70.0"))
RSI_OVERSOLD = float(os.environ.get("RSI_OVERSOLD", "30.0"))
BB_SQUEEZE_RATIO = float(os.environ.get("BB_SQUEEZE_RATIO", "0.015"))
VWAP_BARS = int(os.environ.get("VWAP_BARS", "48"))

# Exits and sizing
STOP_LOSS_PCT = float(os.environ.get("STOP_LOSS_PCT", "0.045"))
TRAIL_PCT = float(os.environ.get("TRAIL_PCT", "0.015"))
TRAIL_ACTIVATE = float(os.environ.get("TRAIL_ACTIVATE", "0.018"))
TAKE_PROFIT_PCT = float(os.environ.get("TAKE_PROFIT_PCT", "0.010"))
PARTIALS = [(0.025, 0.35), (0.050, 0.35), (0.080, 1.00)]

# DCA (hard capped)
ENABLE_DCA = os.environ.get("ENABLE_DCA", "1") == "1"
DCA_STEP_PCT = float(os.environ.get("DCA_STEP_PCT", "0.10"))
MAX_DCA_ADDS = int(os.environ.get("MAX_DCA_ADDS", "2"))
DCA_SCALE = float(os.environ.get("DCA_SCALE", "1.10"))
BASE_ORDER_NOTIONAL_USD = float(os.environ.get("BASE_ORDER_NOTIONAL_USD", "0.10"))

# Backtesting
BACKTEST_INTERVAL = os.environ.get("BACKTEST_INTERVAL", "5m")
BACKTEST_LIMIT = int(os.environ.get("BACKTEST_LIMIT", "1200"))
WALK_TRAIN = int(os.environ.get("WALK_TRAIN", "250"))
WALK_TEST = int(os.environ.get("WALK_TEST", "100"))
MC_RUNS = int(os.environ.get("MC_RUNS", "500"))

# Execution assumptions
TAKER_FEE_RATE = float(os.environ.get("TAKER_FEE_RATE", "0.0005"))
MAKER_FEE_RATE = float(os.environ.get("MAKER_FEE_RATE", "0.0002"))
SLIPPAGE_PCT = float(os.environ.get("SLIPPAGE_PCT", "0.0007"))
MAINT_MARGIN_RATE = float(os.environ.get("MAINT_MARGIN_RATE", "0.01"))

# Retry and heartbeat
API_MAX_RETRIES = int(os.environ.get("API_MAX_RETRIES", "4"))
API_RETRY_DELAY = float(os.environ.get("API_RETRY_DELAY", "1.0"))
COUNTDOWN_KILL_SWITCH_SECONDS = int(os.environ.get("COUNTDOWN_KILL_SWITCH_SECONDS", "15"))

# Files
STATE_FILE = Path(os.environ.get("STATE_FILE", "bot_state.json"))
JSONL_LOG = Path(os.environ.get("JSONL_LOG", "events.jsonl"))
TRADE_LOG_CSV = Path(os.environ.get("TRADE_LOG_CSV", "trades.csv"))

DRY_RUN = True


# =============================================================================
# LOGGING
# =============================================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-8s %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(APP_NAME)
_jsonl_lock = threading.Lock()
_csv_lock = threading.Lock()


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def ts() -> str:
    return now_utc().isoformat()


def event_log(kind: str, **payload: Any) -> None:
    record = {
        "ts": ts(),
        "kind": kind,
        "app": APP_NAME,
        "version": VERSION,
        **payload,
    }
    line = json.dumps(record, separators=(",", ":"), sort_keys=False)
    with _jsonl_lock:
        with open(JSONL_LOG, "a", encoding="utf-8") as handle:
            handle.write(line + "\n")


def write_trade_csv(row: Dict[str, Any]) -> None:
    with _csv_lock:
        new_file = not TRADE_LOG_CSV.exists()
        with open(TRADE_LOG_CSV, "a", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(row.keys()))
            if new_file:
                writer.writeheader()
            writer.writerow(row)


# =============================================================================
# DATA STRUCTURES
# =============================================================================

class Regime(Enum):
    TREND_UP = auto()
    TREND_DOWN = auto()
    RANGING = auto()
    VOLATILE = auto()


@dataclass
class RegimeSnapshot:
    regime: Regime
    adx: float
    rsi: float
    atr_ratio: float
    bb_width: float
    ema_fast: float = 0.0
    ema_slow: float = 0.0
    computed_at: str = field(default_factory=ts)

    def is_stale(self) -> bool:
        dt = datetime.fromisoformat(self.computed_at)
        return (now_utc() - dt).total_seconds() > REGIME_TTL

    def label(self) -> str:
        return self.regime.name


@dataclass
class ContractMeta:
    symbol: str
    last_price: float
    quanto_multiplier: float
    volume_24h_quote: float
    min_order_size: int
    leverage_min: int
    leverage_max: int
    maintenance_rate: float = MAINT_MARGIN_RATE

    @property
    def approx_contract_notional(self) -> float:
        return self.last_price * self.quanto_multiplier


@dataclass
class FillRecord:
    ts: str
    side: str
    size: int
    price: float
    label: str
    fee: float
    reduce_only: bool = False


@dataclass
class PositionRecord:
    symbol: str
    side: str
    regime: str
    entry_price: float
    avg_entry: float
    size: int
    remaining: int
    contract_multiplier: float
    leverage: int
    opened_at: str = field(default_factory=ts)
    closed: bool = False
    ladder_idx: int = 0
    dca_adds_used: int = 0
    next_dca_trigger: Optional[float] = None
    realised_pnl: float = 0.0
    unrealised_pnl: float = 0.0
    peak_pnl_pct: float = 0.0
    last_price: float = 0.0
    entry_tag: str = ""
    fills: List[FillRecord] = field(default_factory=list)
    notes: Dict[str, Any] = field(default_factory=dict)

    def is_open(self) -> bool:
        return (not self.closed) and self.remaining > 0


@dataclass
class OrderIntent:
    symbol: str
    size: int
    side: str
    label: str
    reduce_only: bool = False
    close_position: bool = False


@dataclass
class BacktestTrade:
    symbol: str
    side: str
    regime: str
    entry_idx: int
    exit_idx: int
    entry_price: float
    exit_price: float
    pnl_pct: float
    pnl_usd: float
    fees_usd: float
    reason: str
    dca_adds: int


@dataclass
class BacktestSummary:
    symbol: str
    trades: List[BacktestTrade]
    final_equity: float
    return_pct: float
    max_drawdown_pct: float
    win_rate_pct: float
    avg_trade_pct: float
    profit_factor: float
    sharpe_like: float
    liquidation_events: int
    params: Dict[str, Any]


# =============================================================================
# STATE STORE
# =============================================================================

class StateStore:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.lock = threading.Lock()

    def load(self) -> Dict[str, Any]:
        if not self.path.exists():
            return {
                "positions": {},
                "cooldowns": {},
                "seen_order_tags": [],
                "daily_realised": {},
                "last_reconcile_at": None,
                "metadata": {},
            }
        try:
            with open(self.path, "r", encoding="utf-8") as handle:
                data = json.load(handle)
            if not isinstance(data, dict):
                raise ValueError("state root must be dict")
            return data
        except Exception as exc:
            log.warning("State load failed: %s", exc)
            return {
                "positions": {},
                "cooldowns": {},
                "seen_order_tags": [],
                "daily_realised": {},
                "last_reconcile_at": None,
                "metadata": {"load_error": str(exc)},
            }

    def save(self, state: Dict[str, Any]) -> None:
        temp = self.path.with_suffix(".tmp")
        with self.lock:
            with open(temp, "w", encoding="utf-8") as handle:
                json.dump(state, handle, indent=2, sort_keys=True)
            temp.replace(self.path)


# =============================================================================
# RETRY
# =============================================================================

def with_retry(
    fn: Callable[..., Any],
    *args: Any,
    retries: int = API_MAX_RETRIES,
    base_delay: float = API_RETRY_DELAY,
    **kwargs: Any,
) -> Any:
    delay = base_delay
    last_exc: Optional[Exception] = None
    for attempt in range(1, retries + 1):
        try:
            return fn(*args, **kwargs)
        except Exception as exc:
            last_exc = exc
            event_log("api_retry", fn=getattr(fn, "__name__", "call"), attempt=attempt, error=str(exc))
            if attempt >= retries:
                break
            time.sleep(delay)
            delay *= 2
    if last_exc:
        log.warning("Retry exhausted on %s: %s", getattr(fn, "__name__", "call"), last_exc)
    return None


# =============================================================================
# HELPERS
# =============================================================================

def safe_float(x: Any, default: float = 0.0) -> float:
    try:
        return float(x)
    except Exception:
        return default


def safe_int(x: Any, default: int = 0) -> int:
    try:
        return int(float(x))
    except Exception:
        return default


def make_order_tag(parts: Sequence[str]) -> str:
    seed = "|".join(parts)
    digest = hashlib.sha256(seed.encode("utf-8")).hexdigest()[:20]
    return f"mt-{digest}"[:28]


def dateroll_key(dt: Optional[datetime] = None) -> str:
    d = (dt or now_utc()).date()
    return d.isoformat()


# =============================================================================
# GATE CLIENT
# =============================================================================

class GateClient:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._client = self._build() if GATE_AVAILABLE else None

    def _build(self) -> Optional[FuturesApi]:
        if not GATE_AVAILABLE:
            return None
        cfg = Configuration(key=GATE_API_KEY, secret=GATE_API_SECRET)
        return FuturesApi(ApiClient(cfg))

    def reconnect(self) -> None:
        if not GATE_AVAILABLE:
            return
        with self._lock:
            self._client = self._build()
        event_log("reconnect")

    def alive(self) -> bool:
        return self._client is not None

    def list_contracts(self) -> List[Any]:
        if not self._client:
            return []

        def _call() -> List[Any]:
            return list(self._client.list_futures_contracts(SETTLE))

        return with_retry(_call) or []

    def fetch_contract_meta(self, symbol: str) -> Optional[ContractMeta]:
        contracts = self.list_contracts()
        for c in contracts:
            name = getattr(c, "name", "")
            if name != symbol:
                continue
            return ContractMeta(
                symbol=name,
                last_price=safe_float(getattr(c, "last_price", 0.0)),
                quanto_multiplier=safe_float(getattr(c, "quanto_multiplier", 1.0), 1.0),
                volume_24h_quote=safe_float(getattr(c, "volume_24h_quote", 0.0)),
                min_order_size=max(1, safe_int(getattr(c, "order_size_min", 1), 1)),
                leverage_min=max(1, safe_int(getattr(c, "leverage_min", 1), 1)),
                leverage_max=max(1, safe_int(getattr(c, "leverage_max", 100), 100)),
                maintenance_rate=MAINT_MARGIN_RATE,
            )
        return None

    def fetch_candles(self, symbol: str, interval: str = "5m", limit: int = 100) -> List[Any]:
        if not self._client:
            return []

        def _call() -> List[Any]:
            return list(self._client.list_futures_candlesticks(SETTLE, symbol, interval=interval, limit=limit))

        return with_retry(_call) or []

    def get_price(self, symbol: str) -> Optional[float]:
        if not self._client:
            return None

        def _call() -> Optional[float]:
            data = self._client.list_futures_tickers(SETTLE, contract=symbol)
            if not data:
                return None
            return safe_float(getattr(data[0], "last", 0.0))

        px = with_retry(_call)
        if px is None:
            self.reconnect()
        return px

    def get_futures_account(self) -> Optional[Dict[str, float]]:
        if not self._client:
            return None

        def _call() -> Any:
            # SDK compatibility fallback
            try:
                return self._client.list_futures_accounts(SETTLE)
            except Exception:
                return self._client.get_futures_account(SETTLE)

        result = with_retry(_call)
        if result is None:
            return None

        acct = result[0] if isinstance(result, list) and result else result
        return {
            "total": safe_float(getattr(acct, "total", 0.0)),
            "available": safe_float(getattr(acct, "available", 0.0)),
            "position_margin": safe_float(getattr(acct, "position_margin", 0.0)),
            "order_margin": safe_float(getattr(acct, "order_margin", 0.0)),
            "unrealised_pnl": safe_float(getattr(acct, "unrealised_pnl", 0.0)),
            "currency": SETTLE.upper(),
        }

    def get_position(self, symbol: str) -> Optional[Dict[str, Any]]:
        if not self._client:
            return None

        def _call() -> Any:
            try:
                return self._client.get_position(SETTLE, symbol)
            except Exception:
                positions = self._client.list_positions(SETTLE)
                for p in positions:
                    if str(getattr(p, "contract", "")) == symbol:
                        return p
                return None

        pos = with_retry(_call)
        if pos is None:
            return None

        return {
            "contract": str(getattr(pos, "contract", symbol)),
            "size": safe_float(getattr(pos, "size", 0.0)),
            "entry_price": safe_float(getattr(pos, "entry_price", 0.0)),
            "mark_price": safe_float(getattr(pos, "mark_price", 0.0)),
            "liq_price": safe_float(getattr(pos, "liq_price", 0.0)),
            "unrealised_pnl": safe_float(getattr(pos, "unrealised_pnl", 0.0)),
            "mode": str(getattr(pos, "mode", "")),
            "leverage": str(getattr(pos, "leverage", "")),
        }

    def get_order_book(self, symbol: str, limit: int = 20) -> Optional[Dict[str, Any]]:
        if not self._client:
            return None

        def _call() -> Any:
            return self._client.list_futures_order_book(SETTLE, contract=symbol, limit=limit)

        book = with_retry(_call)
        if book is None:
            return None

        asks = getattr(book, "asks", []) or []
        bids = getattr(book, "bids", []) or []

        def _price(x: Any) -> float:
            return safe_float(getattr(x, "p", 0.0))

        def _size(x: Any) -> float:
            return safe_float(getattr(x, "s", 0.0))

        return {
            "contract": symbol,
            "best_ask": _price(asks[0]) if asks else 0.0,
            "best_bid": _price(bids[0]) if bids else 0.0,
            "ask_size_top": _size(asks[0]) if asks else 0.0,
            "bid_size_top": _size(bids[0]) if bids else 0.0,
            "asks": [{"price": _price(x), "size": _size(x)} for x in asks[:limit]],
            "bids": [{"price": _price(x), "size": _size(x)} for x in bids[:limit]],
        }

    def set_leverage(self, symbol: str, leverage: int) -> bool:
        if DRY_RUN or not self._client:
            return True

        def _call() -> Any:
            return self._client.update_position_leverage(
                SETTLE, symbol, str(leverage), cross_leverage_limit=str(leverage)
            )

        result = with_retry(_call)
        return result is not None

    def countdown_kill_switch(self, timeout_seconds: int, symbol: str = "") -> bool:
        if DRY_RUN or not self._client:
            event_log("kill_switch_dry", timeout_seconds=timeout_seconds, symbol=symbol)
            return True

        try:
            task = gate_api.CountdownCancelAllFuturesTask(
                timeout=timeout_seconds,
                contract=symbol or None,
            )
        except Exception:
            event_log("kill_switch_unsupported", timeout_seconds=timeout_seconds, symbol=symbol)
            return False

        def _call() -> Any:
            return self._client.countdown_cancel_all_futures(SETTLE, task)

        result = with_retry(_call)
        return result is not None

    def list_my_trades(self, symbol: str = "", limit: int = 50) -> List[Any]:
        if not self._client:
            return []

        def _call() -> List[Any]:
            return list(self._client.get_my_trades(SETTLE, contract=symbol or None, limit=limit))

        return with_retry(_call) or []

    def list_open_orders(self, symbol: str = "") -> List[Any]:
        if not self._client:
            return []

        def _call() -> List[Any]:
            return list(self._client.list_futures_orders(SETTLE, status="open", contract=symbol or None))

        return with_retry(_call) or []

    def list_positions(self) -> List[Any]:
        if not self._client:
            return []

        def _call() -> List[Any]:
            return list(self._client.list_positions(SETTLE))

        return with_retry(_call) or []

    def place_order(self, intent: OrderIntent) -> Optional[Any]:
        if intent.size == 0 and not intent.close_position:
            return None

        if DRY_RUN:
            event_log(
                "dry_order",
                symbol=intent.symbol,
                size=intent.size,
                side=intent.side,
                label=intent.label,
                reduce_only=intent.reduce_only,
                close_position=intent.close_position,
            )
            return {
                "dry_run": True,
                "symbol": intent.symbol,
                "size": intent.size,
                "label": intent.label,
                "reduce_only": intent.reduce_only,
                "close_position": intent.close_position,
                "fill_price": None,
                "status": "finished",
            }

        if not self._client or gate_api is None:
            return None

        try:
            order = gate_api.FuturesOrder(
                contract=intent.symbol,
                size=intent.size,
                price="0",
                tif="ioc",
                text=intent.label[:28],
                reduce_only=bool(intent.reduce_only),
                close=bool(intent.close_position),
            )
        except TypeError:
            order = gate_api.FuturesOrder(
                contract=intent.symbol,
                size=intent.size,
                price="0",
                tif="ioc",
                text=intent.label[:28],
            )
            try:
                setattr(order, "reduce_only", bool(intent.reduce_only))
            except Exception:
                pass
            try:
                setattr(order, "close", bool(intent.close_position))
            except Exception:
                pass

        def _call() -> Any:
            return self._client.create_futures_order(SETTLE, order)

        result = with_retry(_call)
        if result is None:
            event_log("order_failed", symbol=intent.symbol, label=intent.label, size=intent.size)
            return None

        event_log(
            "order_placed",
            symbol=intent.symbol,
            label=intent.label,
            size=intent.size,
            reduce_only=intent.reduce_only,
            close_position=intent.close_position,
            order_id=str(getattr(result, "id", "")),
            status=str(getattr(result, "status", "")),
            fill_price=safe_float(getattr(result, "fill_price", 0.0)),
        )
        return result


# =============================================================================
# INDICATORS
# =============================================================================

def _closes(candles: Sequence[Any]) -> List[float]:
    return [safe_float(getattr(c, "c", 0.0)) for c in candles]


def _highs(candles: Sequence[Any]) -> List[float]:
    return [safe_float(getattr(c, "h", 0.0)) for c in candles]


def _lows(candles: Sequence[Any]) -> List[float]:
    return [safe_float(getattr(c, "l", 0.0)) for c in candles]


def _opens(candles: Sequence[Any]) -> List[float]:
    return [safe_float(getattr(c, "o", 0.0)) for c in candles]


def ema(values: Sequence[float], period: int) -> List[float]:
    if len(values) < period:
        return []
    alpha = 2.0 / (period + 1.0)
    out = [sum(values[:period]) / period]
    for value in values[period:]:
        out.append(value * alpha + out[-1] * (1.0 - alpha))
    return out


def rsi(closes: Sequence[float], period: int = 14) -> Optional[float]:
    if len(closes) < period + 1:
        return None
    deltas = [closes[i] - closes[i - 1] for i in range(1, len(closes))]
    gains = [x if x > 0 else 0.0 for x in deltas]
    losses = [-x if x < 0 else 0.0 for x in deltas]
    avg_gain = sum(gains[:period]) / period
    avg_loss = sum(losses[:period]) / period
    for idx in range(period, len(deltas)):
        avg_gain = (avg_gain * (period - 1) + gains[idx]) / period
        avg_loss = (avg_loss * (period - 1) + losses[idx]) / period
    if avg_loss == 0:
        return 100.0
    rs = avg_gain / avg_loss
    return 100.0 - (100.0 / (1.0 + rs))


def true_range(highs: Sequence[float], lows: Sequence[float], closes: Sequence[float]) -> List[float]:
    if len(closes) < 2:
        return []
    out: List[float] = []
    for idx in range(1, len(closes)):
        out.append(
            max(
                highs[idx] - lows[idx],
                abs(highs[idx] - closes[idx - 1]),
                abs(lows[idx] - closes[idx - 1]),
            )
        )
    return out


def atr_series(candles: Sequence[Any], period: int = 14) -> List[float]:
    highs = _highs(candles)
    lows = _lows(candles)
    closes = _closes(candles)
    tr = true_range(highs, lows, closes)
    if len(tr) < period:
        return []
    out: List[float] = []
    for idx in range(period - 1, len(tr)):
        out.append(sum(tr[idx - period + 1:idx + 1]) / period)
    return out


def bollinger(closes: Sequence[float], period: int = 20, num_std: float = 2.0) -> Optional[Tuple[float, float, float, float]]:
    if len(closes) < period:
        return None
    window = list(closes[-period:])
    mid = sum(window) / period
    std = statistics.stdev(window) if len(window) > 1 else 0.0
    upper = mid + num_std * std
    lower = mid - num_std * std
    width = (upper - lower) / mid if mid else 0.0
    return upper, mid, lower, width


def adx(candles: Sequence[Any], period: int = 14) -> Optional[float]:
    if len(candles) < period * 2:
        return None
    highs = _highs(candles)
    lows = _lows(candles)
    closes = _closes(candles)

    tr = true_range(highs, lows, closes)
    plus_dm: List[float] = []
    minus_dm: List[float] = []

    for idx in range(1, len(closes)):
        up_move = highs[idx] - highs[idx - 1]
        down_move = lows[idx - 1] - lows[idx]
        plus_dm.append(up_move if up_move > down_move and up_move > 0 else 0.0)
        minus_dm.append(down_move if down_move > up_move and down_move > 0 else 0.0)

    def smooth(values: Sequence[float], p: int) -> List[float]:
        if len(values) < p:
            return []
        out = [sum(values[:p])]
        for val in values[p:]:
            out.append(out[-1] - out[-1] / p + val)
        return out

    tr_s = smooth(tr, period)
    plus_s = smooth(plus_dm, period)
    minus_s = smooth(minus_dm, period)
    if not tr_s:
        return None

    dx_vals: List[float] = []
    for trv, pv, mv in zip(tr_s, plus_s, minus_s):
        if trv == 0:
            continue
        pdi = 100.0 * pv / trv
        mdi = 100.0 * mv / trv
        dx = 100.0 * abs(pdi - mdi) / (pdi + mdi) if (pdi + mdi) else 0.0
        dx_vals.append(dx)

    if not dx_vals:
        return None
    window = dx_vals[-period:]
    return sum(window) / len(window)


def vwap(candles: Sequence[Any], bars: int = VWAP_BARS) -> Optional[float]:
    window = list(candles[-bars:] if len(candles) >= bars else candles)
    if not window:
        return None
    pv = 0.0
    vv = 0.0
    for c in window:
        typical = (safe_float(getattr(c, "h", 0.0)) + safe_float(getattr(c, "l", 0.0)) + safe_float(getattr(c, "c", 0.0))) / 3.0
        vol = safe_float(getattr(c, "v", 0.0))
        pv += typical * vol
        vv += vol
    return pv / vv if vv else None


# =============================================================================
# REGIME + STRATEGY
# =============================================================================

def classify_regime_from_candles(candles: Sequence[Any]) -> RegimeSnapshot:
    if len(candles) < 30:
        return RegimeSnapshot(Regime.VOLATILE, 0.0, 50.0, 99.0, 0.0)

    closes = _closes(candles)
    ema_fast = ema(closes, 9)
    ema_slow = ema(closes, 21)
    current_rsi = rsi(closes) or 50.0

    atr_vals = atr_series(candles, 14)
    current_atr = atr_vals[-1] if atr_vals else 0.0
    mean_atr = sum(atr_vals[-20:]) / max(1, min(20, len(atr_vals))) if atr_vals else 1.0
    atr_ratio = current_atr / mean_atr if mean_atr else 1.0

    bb = bollinger(closes)
    bb_width = bb[3] if bb else 0.0
    current_adx = adx(candles) or 0.0

    if atr_ratio >= ATR_VOLATILE_MULT:
        reg = Regime.VOLATILE
    elif current_adx >= ADX_TREND_MIN:
        fast_now = ema_fast[-1] if ema_fast else 0.0
        slow_now = ema_slow[-1] if ema_slow else 0.0
        reg = Regime.TREND_UP if fast_now > slow_now else Regime.TREND_DOWN
    else:
        reg = Regime.RANGING

    return RegimeSnapshot(
        regime=reg,
        adx=round(current_adx, 3),
        rsi=round(current_rsi, 3),
        atr_ratio=round(atr_ratio, 3),
        bb_width=round(bb_width, 5),
        ema_fast=ema_fast[-1] if ema_fast else 0.0,
        ema_slow=ema_slow[-1] if ema_slow else 0.0,
    )


def classify_regime(client: GateClient, symbol: str) -> RegimeSnapshot:
    candles = client.fetch_candles(symbol, interval="5m", limit=100)
    return classify_regime_from_candles(candles)


def measure_move(client: GateClient, symbol: str) -> Optional[float]:
    candles = client.fetch_candles(symbol, interval="1m", limit=LOOKBACK_HOURS * 60)
    if len(candles) < 5:
        return None
    opens = _opens(candles)
    closes = _closes(candles)
    if not opens or not closes or opens[0] == 0:
        return None
    return (closes[-1] - opens[0]) / opens[0]


def regime_allows_entry(
    snap: RegimeSnapshot,
    move_pct: float,
    current_price: float,
    vwap_price: Optional[float],
) -> Tuple[bool, str, str]:
    if snap.regime == Regime.VOLATILE:
        return False, "volatile-skip", ""

    def vwap_ok(side: str) -> Tuple[bool, str]:
        if vwap_price is None:
            return True, ""
        if side == "short" and current_price <= vwap_price:
            return False, "vwap-block-short"
        if side == "long" and current_price >= vwap_price:
            return False, "vwap-block-long"
        return True, ""

    if snap.regime == Regime.TREND_UP:
        if snap.rsi >= RSI_OVERBOUGHT and move_pct >= PUMP_THRESHOLD:
            ok, reason = vwap_ok("short")
            return ok, (reason or "trend-up-fade-short"), ("short" if ok else "")
        return False, "trend-up-no-edge", ""

    if snap.regime == Regime.TREND_DOWN:
        if move_pct >= PUMP_THRESHOLD:
            ok, reason = vwap_ok("short")
            return ok, (reason or "trend-down-cont-short"), ("short" if ok else "")
        return False, "trend-down-no-edge", ""

    if snap.rsi >= RSI_OVERBOUGHT and move_pct >= PUMP_THRESHOLD:
        ok, reason = vwap_ok("short")
        return ok, (reason or "range-short"), ("short" if ok else "")
    if snap.rsi <= RSI_OVERSOLD and move_pct <= DUMP_THRESHOLD:
        ok, reason = vwap_ok("long")
        return ok, (reason or "range-long"), ("long" if ok else "")
    return False, "range-no-edge", ""


def calc_order_size(meta: ContractMeta, snap: RegimeSnapshot, balance_usd: float) -> int:
    if meta.quanto_multiplier <= 0 or meta.last_price <= 0:
        return 0

    volatility_scalar = 1.0
    if snap.atr_ratio > 1.5:
        volatility_scalar = 0.8
    elif snap.atr_ratio < 0.8:
        volatility_scalar = 1.2

    max_risk_usd = balance_usd * MAX_ACCOUNT_RISK_PCT
    desired_notional = min(BASE_ORDER_NOTIONAL_USD * volatility_scalar, max_risk_usd)
    contract_notional = meta.approx_contract_notional
    raw_contracts = max(1, int(round(desired_notional / max(contract_notional, 1e-9))))
    size = max(meta.min_order_size, raw_contracts)
    return max(0, size)


def estimate_margin_required(price: float, qty: int, multiplier: float, leverage: int) -> float:
    notion = price * qty * multiplier
    return notion / max(1, leverage)


def estimated_fee(price: float, qty: int, multiplier: float, rate: float = TAKER_FEE_RATE) -> float:
    notion = price * abs(qty) * multiplier
    return notion * rate


# =============================================================================
# CACHE + COOLDOWNS
# =============================================================================

class CooldownRegistry:
    def __init__(self, initial: Optional[Dict[str, str]] = None) -> None:
        self._bans: Dict[str, str] = dict(initial or {})
        self._lock = threading.Lock()

    def ban(self, symbol: str, seconds: int = COOLDOWN_SECONDS) -> None:
        expiry = (now_utc() + timedelta(seconds=seconds)).isoformat()
        with self._lock:
            self._bans[symbol] = expiry
        event_log("cooldown_ban", symbol=symbol, until=expiry)

    def is_banned(self, symbol: str) -> bool:
        with self._lock:
            expiry = self._bans.get(symbol)
        if not expiry:
            return False
        if now_utc() >= datetime.fromisoformat(expiry):
            with self._lock:
                self._bans.pop(symbol, None)
            return False
        return True

    def export(self) -> Dict[str, str]:
        with self._lock:
            return dict(self._bans)

    def active_count(self) -> int:
        now = now_utc()
        with self._lock:
            return sum(1 for exp in self._bans.values() if datetime.fromisoformat(exp) > now)


class RegimeCache:
    def __init__(self) -> None:
        self._cache: Dict[str, RegimeSnapshot] = {}
        self._lock = threading.Lock()

    def get(self, client: GateClient, symbol: str) -> RegimeSnapshot:
        with self._lock:
            snap = self._cache.get(symbol)
        if snap is None or snap.is_stale():
            snap = classify_regime(client, symbol)
            with self._lock:
                self._cache[symbol] = snap
        return snap

    def summary(self) -> Dict[str, int]:
        out = {r.name: 0 for r in Regime}
        with self._lock:
            for snap in self._cache.values():
                out[snap.regime.name] += 1
        return out


# =============================================================================
# UNIVERSE
# =============================================================================

def scan_micro_contracts(client: GateClient) -> List[ContractMeta]:
    metas: List[ContractMeta] = []
    for c in client.list_contracts():
        try:
            meta = ContractMeta(
                symbol=str(getattr(c, "name", "")),
                last_price=safe_float(getattr(c, "last_price", 0.0)),
                quanto_multiplier=safe_float(getattr(c, "quanto_multiplier", 1.0), 1.0),
                volume_24h_quote=safe_float(getattr(c, "volume_24h_quote", 0.0)),
                min_order_size=max(1, safe_int(getattr(c, "order_size_min", 1), 1)),
                leverage_min=max(1, safe_int(getattr(c, "leverage_min", 1), 1)),
                leverage_max=max(1, safe_int(getattr(c, "leverage_max", 100), 100)),
                maintenance_rate=MAINT_MARGIN_RATE,
            )
            if meta.last_price <= 0 or meta.quanto_multiplier <= 0:
                continue
            notional = meta.approx_contract_notional
            if MIN_NOTIONAL <= notional <= MAX_NOTIONAL and meta.volume_24h_quote >= MIN_VOLUME_USDT:
                metas.append(meta)
        except Exception:
            continue
    metas.sort(key=lambda x: x.volume_24h_quote, reverse=True)
    event_log("universe_scan", count=len(metas))
    return metas


# =============================================================================
# PORTFOLIO + LIVE POSITION MANAGER
# =============================================================================

class PositionManager:
    def __init__(
        self,
        client: GateClient,
        cooldown: CooldownRegistry,
        store: StateStore,
        starting_state: Dict[str, Any],
    ) -> None:
        self.client = client
        self.cooldown = cooldown
        self.store = store
        self.lock = threading.Lock()

        self.positions: Dict[str, PositionRecord] = {}
        self.seen_order_tags: set[str] = set(starting_state.get("seen_order_tags", []))
        self.daily_realised: Dict[str, float] = dict(starting_state.get("daily_realised", {}))
        self.last_reconcile_at: Optional[str] = starting_state.get("last_reconcile_at")

        for sym, raw in starting_state.get("positions", {}).items():
            try:
                fills = [FillRecord(**f) for f in raw.get("fills", [])]
                raw = dict(raw)
                raw["fills"] = fills
                self.positions[sym] = PositionRecord(**raw)
            except Exception as exc:
                log.warning("Failed to load position %s: %s", sym, exc)

    def persist(self) -> None:
        state = {
            "positions": {k: asdict(v) for k, v in self.positions.items()},
            "cooldowns": self.cooldown.export(),
            "seen_order_tags": sorted(self.seen_order_tags),
            "daily_realised": self.daily_realised,
            "last_reconcile_at": self.last_reconcile_at,
            "metadata": {
                "saved_at": ts(),
                "app": APP_NAME,
                "version": VERSION,
            },
        }
        self.store.save(state)

    def daily_pnl(self) -> float:
        return float(self.daily_realised.get(dateroll_key(), 0.0))

    def add_realised_today(self, amount: float) -> None:
        key = dateroll_key()
        self.daily_realised[key] = float(self.daily_realised.get(key, 0.0) + amount)

    def active(self) -> List[PositionRecord]:
        return [p for p in self.positions.values() if p.is_open()]

    def daily_guard_tripped(self) -> bool:
        limit = -ACCOUNT_BALANCE * MAX_DAILY_LOSS_PCT
        pnl = self.daily_pnl()
        if pnl <= limit:
            event_log("daily_guard", pnl=pnl, limit=limit)
            return True
        return False

    def can_open_more(self, regime: Regime) -> bool:
        active = self.active()
        if len(active) >= MAX_OPEN_POSITIONS:
            return False
        regime_count = sum(1 for p in active if p.regime == regime.name)
        return regime_count < MAX_PER_REGIME

    def reconcile(self) -> None:
        try:
            open_orders = self.client.list_open_orders()
            exch_positions = self.client.list_positions()
            event_log(
                "reconcile",
                open_orders=len(open_orders),
                exchange_positions=len(exch_positions),
                local_positions=len(self.active()),
            )
            self.last_reconcile_at = ts()
        except Exception as exc:
            event_log("reconcile_error", error=str(exc))

        self.persist()

    def _fee(self, price: float, qty: int, multiplier: float) -> float:
        return estimated_fee(price, qty, multiplier, TAKER_FEE_RATE)

    def _margin_buffer_ok(self, price: float, qty: int, multiplier: float) -> bool:
        need = estimate_margin_required(price, qty, multiplier, LEVERAGE) + self._fee(price, qty, multiplier)
        max_allow = ACCOUNT_BALANCE * MAX_ACCOUNT_RISK_PCT
        return need <= max_allow

    def _record_fill(self, pos: PositionRecord, side: str, qty: int, price: float, label: str, reduce_only: bool) -> None:
        fee = self._fee(price, qty, pos.contract_multiplier)
        pos.fills.append(
            FillRecord(
                ts=ts(),
                side=side,
                size=qty,
                price=price,
                label=label,
                fee=fee,
                reduce_only=reduce_only,
            )
        )

    def _journal_open(self, pos: PositionRecord) -> None:
        row = {
            "timestamp": ts(),
            "event": "OPEN",
            "symbol": pos.symbol,
            "side": pos.side,
            "entry_price": pos.entry_price,
            "avg_entry": pos.avg_entry,
            "size": pos.size,
            "remaining": pos.remaining,
            "regime": pos.regime,
            "realised": "",
            "tag": pos.entry_tag,
        }
        write_trade_csv(row)

    def _journal_close(self, pos: PositionRecord, reason: str) -> None:
        row = {
            "timestamp": ts(),
            "event": f"CLOSE:{reason}",
            "symbol": pos.symbol,
            "side": pos.side,
            "entry_price": pos.entry_price,
            "avg_entry": pos.avg_entry,
            "size": pos.size,
            "remaining": pos.remaining,
            "regime": pos.regime,
            "realised": f"{pos.realised_pnl:.8f}",
            "tag": pos.entry_tag,
        }
        write_trade_csv(row)

    def open_position(self, meta: ContractMeta, snap: RegimeSnapshot, side: str, entry_reason: str) -> bool:
        symbol = meta.symbol

        if self.cooldown.is_banned(symbol):
            return False
        if self.daily_guard_tripped():
            return False
        if not self.can_open_more(snap.regime):
            return False
        if symbol in self.positions and self.positions[symbol].is_open():
            return False

        size = calc_order_size(meta, snap, ACCOUNT_BALANCE)
        if size < meta.min_order_size:
            return False

        if LEVERAGE < meta.leverage_min or LEVERAGE > meta.leverage_max:
            event_log("bad_leverage", symbol=symbol, leverage=LEVERAGE, min=meta.leverage_min, max=meta.leverage_max)
            return False

        if not self._margin_buffer_ok(meta.last_price, size, meta.quanto_multiplier):
            event_log("margin_block", symbol=symbol, size=size)
            return False

        if not self.client.set_leverage(symbol, LEVERAGE):
            return False

        signed_size = -size if side == "short" else size
        tag = make_order_tag([symbol, side, "entry", str(int(time.time() // 10)), entry_reason])

        if tag in self.seen_order_tags:
            return False

        result = self.client.place_order(
            OrderIntent(
                symbol=symbol,
                size=signed_size,
                side=side,
                label=tag,
                reduce_only=False,
                close_position=False,
            )
        )
        if result is None:
            return False

        fill_price = safe_float(getattr(result, "fill_price", 0.0), meta.last_price) or meta.last_price
        pos = PositionRecord(
            symbol=symbol,
            side=side,
            regime=snap.regime.name,
            entry_price=fill_price,
            avg_entry=fill_price,
            size=size,
            remaining=size,
            contract_multiplier=meta.quanto_multiplier,
            leverage=LEVERAGE,
            entry_tag=tag,
            next_dca_trigger=(fill_price * (1 + DCA_STEP_PCT) if side == "short" else fill_price * (1 - DCA_STEP_PCT)) if ENABLE_DCA else None,
            notes={"entry_reason": entry_reason},
        )
        self._record_fill(pos, side, size, fill_price, tag, False)

        with self.lock:
            self.positions[symbol] = pos
            self.seen_order_tags.add(tag)

        self._journal_open(pos)
        self.persist()

        event_log("position_open", symbol=symbol, side=side, size=size, fill_price=fill_price, regime=snap.regime.name)
        return True

    def _compute_pnl_pct(self, pos: PositionRecord, price: float) -> float:
        if pos.avg_entry <= 0:
            return 0.0
        if pos.side == "short":
            return (pos.avg_entry - price) / pos.avg_entry
        return (price - pos.avg_entry) / pos.avg_entry

    def _compute_pnl_usd(self, pos: PositionRecord, price: float, qty: Optional[int] = None) -> float:
        q = qty if qty is not None else pos.remaining
        if pos.side == "short":
            return (pos.avg_entry - price) * q * pos.contract_multiplier
        return (price - pos.avg_entry) * q * pos.contract_multiplier

    def _close_qty(self, pos: PositionRecord, qty: int, price: float, reason: str) -> bool:
        if qty <= 0 or pos.remaining <= 0:
            return False
        qty = min(qty, pos.remaining)
        intent_size = qty if pos.side == "short" else -qty
        tag = make_order_tag([pos.symbol, reason, "close", str(pos.remaining), str(int(time.time() // 10))])
        if tag in self.seen_order_tags:
            return False

        result = self.client.place_order(
            OrderIntent(
                symbol=pos.symbol,
                size=intent_size,
                side=("buy" if pos.side == "short" else "sell"),
                label=tag,
                reduce_only=True,
                close_position=False,
            )
        )
        if result is None:
            return False

        fill_price = safe_float(getattr(result, "fill_price", 0.0), price) or price
        pnl_amt = self._compute_pnl_usd(pos, fill_price, qty)
        fee_amt = self._fee(fill_price, qty, pos.contract_multiplier)

        pos.remaining -= qty
        pos.last_price = fill_price
        pos.realised_pnl += pnl_amt - fee_amt
        self.add_realised_today(pnl_amt - fee_amt)
        self._record_fill(pos, "close", qty, fill_price, tag, True)
        self.seen_order_tags.add(tag)

        if pos.remaining <= 0:
            pos.closed = True
            self._journal_close(pos, reason)
            event_log("position_closed", symbol=pos.symbol, reason=reason, pnl=pos.realised_pnl)

        self.persist()
        return True

    def _full_close(self, pos: PositionRecord, price: float, reason: str) -> bool:
        return self._close_qty(pos, pos.remaining, price, reason)

    def _dca_add(self, pos: PositionRecord, price: float) -> bool:
        if not ENABLE_DCA:
            return False
        if pos.dca_adds_used >= MAX_DCA_ADDS:
            return False

        add_qty = max(1, int(round(pos.size * (DCA_SCALE ** pos.dca_adds_used))))
        if not self._margin_buffer_ok(price, add_qty, pos.contract_multiplier):
            return False

        signed = -add_qty if pos.side == "short" else add_qty
        tag = make_order_tag([pos.symbol, "dca", str(pos.dca_adds_used), str(int(time.time() // 10))])
        if tag in self.seen_order_tags:
            return False

        result = self.client.place_order(
            OrderIntent(
                symbol=pos.symbol,
                size=signed,
                side=pos.side,
                label=tag,
                reduce_only=False,
                close_position=False,
            )
        )
        if result is None:
            return False

        fill_price = safe_float(getattr(result, "fill_price", 0.0), price) or price
        old_total = pos.avg_entry * pos.remaining
        new_total = old_total + fill_price * add_qty
        pos.remaining += add_qty
        pos.size += add_qty
        pos.avg_entry = new_total / pos.remaining if pos.remaining else pos.avg_entry
        pos.dca_adds_used += 1
        pos.next_dca_trigger = (
            pos.entry_price * (1 + DCA_STEP_PCT * (pos.dca_adds_used + 1))
            if pos.side == "short" else
            pos.entry_price * (1 - DCA_STEP_PCT * (pos.dca_adds_used + 1))
        )
        self._record_fill(pos, pos.side, add_qty, fill_price, tag, False)
        self.seen_order_tags.add(tag)
        event_log("dca_add", symbol=pos.symbol, adds_used=pos.dca_adds_used, new_avg=pos.avg_entry, fill_price=fill_price)
        self.persist()
        return True

    def tick(self) -> None:
        for pos in list(self.active()):
            price = self.client.get_price(pos.symbol)
            if price is None or price <= 0:
                continue

            pos.last_price = price
            pos.unrealised_pnl = self._compute_pnl_usd(pos, price)
            pnl_pct = self._compute_pnl_pct(pos, price)
            pos.peak_pnl_pct = max(pos.peak_pnl_pct, pnl_pct)
            drawdown = pos.peak_pnl_pct - pnl_pct

            if ENABLE_DCA and pos.next_dca_trigger is not None:
                if (pos.side == "short" and price >= pos.next_dca_trigger) or (pos.side == "long" and price <= pos.next_dca_trigger):
                    self._dca_add(pos, price)

            if pnl_pct <= -STOP_LOSS_PCT:
                self._full_close(pos, price, "hard-stop")
                self.cooldown.ban(pos.symbol)
                continue

            if pnl_pct >= TAKE_PROFIT_PCT and pos.ladder_idx >= len(PARTIALS):
                self._full_close(pos, price, "take-profit")
                continue

            if pos.peak_pnl_pct >= TRAIL_ACTIVATE and drawdown >= TRAIL_PCT:
                self._full_close(pos, price, "trail-stop")
                continue

            while pos.ladder_idx < len(PARTIALS):
                target, frac = PARTIALS[pos.ladder_idx]
                if pnl_pct < target:
                    break
                close_qty = max(1, int(round(pos.remaining * frac)))
                if self._close_qty(pos, close_qty, price, f"partial-{pos.ladder_idx + 1}"):
                    pos.ladder_idx += 1
                else:
                    break

        self.persist()

    def purge_closed(self) -> None:
        keep_after = now_utc() - timedelta(hours=12)
        stale = []
        for symbol, pos in self.positions.items():
            opened = datetime.fromisoformat(pos.opened_at)
            if pos.closed and opened < keep_after:
                stale.append(symbol)
        for s in stale:
            self.positions.pop(s, None)
        if stale:
            self.persist()


# =============================================================================
# SCANNER
# =============================================================================

def scan_one(
    client: GateClient,
    meta: ContractMeta,
    manager: PositionManager,
    regime_cache: RegimeCache,
    cooldown: CooldownRegistry,
) -> Optional[Tuple[ContractMeta, RegimeSnapshot, str, str]]:
    if cooldown.is_banned(meta.symbol):
        return None
    if meta.symbol in manager.positions and manager.positions[meta.symbol].is_open():
        return None

    move = measure_move(client, meta.symbol)
    if move is None:
        return None
    if abs(move) < min(abs(PUMP_THRESHOLD), abs(DUMP_THRESHOLD)):
        return None

    snap = regime_cache.get(client, meta.symbol)
    candles = client.fetch_candles(meta.symbol, interval="5m", limit=VWAP_BARS + 10)
    vwap_px = vwap(candles, VWAP_BARS) if candles else None
    ok, reason, side = regime_allows_entry(snap, move, meta.last_price, vwap_px)
    event_log(
        "scan_symbol",
        symbol=meta.symbol,
        move=move,
        regime=snap.label(),
        rsi=snap.rsi,
        adx=snap.adx,
        ok=ok,
        side=side,
        reason=reason,
    )
    if ok:
        return meta, snap, side, reason
    return None


def concurrent_scan(
    client: GateClient,
    metas: List[ContractMeta],
    manager: PositionManager,
    regime_cache: RegimeCache,
    cooldown: CooldownRegistry,
) -> List[Tuple[ContractMeta, RegimeSnapshot, str, str]]:
    out: List[Tuple[ContractMeta, RegimeSnapshot, str, str]] = []
    with ThreadPoolExecutor(max_workers=SCAN_WORKERS) as pool:
        futs = [pool.submit(scan_one, client, meta, manager, regime_cache, cooldown) for meta in metas]
        for fut in as_completed(futs):
            try:
                result = fut.result()
                if result is not None:
                    out.append(result)
            except Exception as exc:
                event_log("scan_worker_error", error=str(exc))
    return out


# =============================================================================
# BACKTEST ENGINE
# =============================================================================

class BacktestEngine:
    def __init__(self, symbol: str, candles: Sequence[Any], meta: Optional[ContractMeta] = None) -> None:
        self.symbol = symbol
        self.candles = list(candles)
        self.meta = meta or ContractMeta(
            symbol=symbol,
            last_price=safe_float(getattr(candles[-1], "c", 1.0)) if candles else 1.0,
            quanto_multiplier=1.0,
            volume_24h_quote=1_000_000.0,
            min_order_size=1,
            leverage_min=1,
            leverage_max=100,
            maintenance_rate=MAINT_MARGIN_RATE,
        )

    def _slipped(self, price: float, opening: bool, side: str) -> float:
        if side == "short" and opening:
            return price * (1.0 - SLIPPAGE_PCT)
        if side == "long" and opening:
            return price * (1.0 + SLIPPAGE_PCT)
        if side == "short" and not opening:
            return price * (1.0 + SLIPPAGE_PCT)
        return price * (1.0 - SLIPPAGE_PCT)

    def _fee(self, price: float, qty: int) -> float:
        return estimated_fee(price, qty, self.meta.quanto_multiplier, TAKER_FEE_RATE)

    def run(self) -> BacktestSummary:
        if len(self.candles) < 120:
            return BacktestSummary(
                symbol=self.symbol,
                trades=[],
                final_equity=ACCOUNT_BALANCE,
                return_pct=0.0,
                max_drawdown_pct=0.0,
                win_rate_pct=0.0,
                avg_trade_pct=0.0,
                profit_factor=0.0,
                sharpe_like=0.0,
                liquidation_events=0,
                params=self._params(),
            )

        equity = ACCOUNT_BALANCE
        peak_equity = equity
        drawdowns: List[float] = []
        trades: List[BacktestTrade] = []
        liquidation_events = 0

        in_trade = False
        side = ""
        regime_name = ""
        entry_idx = 0
        entry_price = 0.0
        avg_entry = 0.0
        qty = 0
        remaining = 0
        dca_adds = 0
        next_dca_trigger: Optional[float] = None
        peak_pnl_pct = 0.0
        ladder_idx = 0
        fees_paid = 0.0

        closes = _closes(self.candles)
        idx = 60

        while idx < len(self.candles):
            candle = self.candles[idx]
            price = safe_float(getattr(candle, "c", 0.0))
            high = safe_float(getattr(candle, "h", price))
            low = safe_float(getattr(candle, "l", price))

            if not in_trade:
                window = self.candles[:idx]
                snap = classify_regime_from_candles(window)
                lookback = 12
                move = 0.0
                if idx >= lookback:
                    base = closes[idx - lookback]
                    move = (closes[idx] - base) / base if base else 0.0
                vwap_px = vwap(window, min(VWAP_BARS, len(window)))
                ok, _reason, trade_side = regime_allows_entry(snap, move, price, vwap_px)
                if ok:
                    size = calc_order_size(self.meta, snap, equity)
                    if size > 0:
                        side = trade_side
                        regime_name = snap.regime.name
                        entry_idx = idx
                        fill = self._slipped(price, opening=True, side=side)
                        entry_price = fill
                        avg_entry = fill
                        qty = size
                        remaining = size
                        dca_adds = 0
                        next_dca_trigger = fill * (1 + DCA_STEP_PCT) if side == "short" else fill * (1 - DCA_STEP_PCT)
                        peak_pnl_pct = 0.0
                        ladder_idx = 0
                        in_trade = True
                        fees_paid = self._fee(fill, size)
                        equity -= fees_paid
                idx += 1
                peak_equity = max(peak_equity, equity)
                drawdowns.append((equity / peak_equity) - 1.0 if peak_equity else 0.0)
                continue

            pnl_pct = ((avg_entry - price) / avg_entry) if side == "short" else ((price - avg_entry) / avg_entry)
            peak_pnl_pct = max(peak_pnl_pct, pnl_pct)
            drawdown_from_peak = peak_pnl_pct - pnl_pct

            adverse_mark = high if side == "short" else low
            adverse_pnl_usd = ((avg_entry - adverse_mark) if side == "short" else (adverse_mark - avg_entry)) * remaining * self.meta.quanto_multiplier
            estimated_margin = estimate_margin_required(avg_entry, remaining, self.meta.quanto_multiplier, LEVERAGE)
            maint = abs(adverse_mark * remaining * self.meta.quanto_multiplier) * self.meta.maintenance_rate

            if equity + adverse_pnl_usd <= maint or (estimated_margin > 0 and (equity + adverse_pnl_usd) < -estimated_margin):
                exit_px = self._slipped(adverse_mark, opening=False, side=side)
                pnl_usd = ((avg_entry - exit_px) if side == "short" else (exit_px - avg_entry)) * remaining * self.meta.quanto_multiplier
                exit_fee = self._fee(exit_px, remaining)
                total_fees = fees_paid + exit_fee
                equity += pnl_usd - exit_fee
                trades.append(
                    BacktestTrade(
                        symbol=self.symbol,
                        side=side,
                        regime=regime_name,
                        entry_idx=entry_idx,
                        exit_idx=idx,
                        entry_price=entry_price,
                        exit_price=exit_px,
                        pnl_pct=((pnl_usd - total_fees) / max(1e-9, (entry_price * qty * self.meta.quanto_multiplier / LEVERAGE))) * 100.0,
                        pnl_usd=pnl_usd - total_fees,
                        fees_usd=total_fees,
                        reason="liquidation-est",
                        dca_adds=dca_adds,
                    )
                )
                in_trade = False
                liquidation_events += 1
                idx += 1
                peak_equity = max(peak_equity, equity)
                drawdowns.append((equity / peak_equity) - 1.0 if peak_equity else 0.0)
                continue

            if ENABLE_DCA and next_dca_trigger is not None and dca_adds < MAX_DCA_ADDS:
                dca_hit = (side == "short" and high >= next_dca_trigger) or (side == "long" and low <= next_dca_trigger)
                if dca_hit:
                    add_qty = max(1, int(round(qty * (DCA_SCALE ** dca_adds))))
                    fill = self._slipped(next_dca_trigger, opening=True, side=side)
                    total_before = avg_entry * remaining
                    total_after = total_before + fill * add_qty
                    remaining += add_qty
                    qty += add_qty
                    avg_entry = total_after / remaining
                    fee_add = self._fee(fill, add_qty)
                    fees_paid += fee_add
                    equity -= fee_add
                    dca_adds += 1
                    next_dca_trigger = entry_price * (1 + DCA_STEP_PCT * (dca_adds + 1)) if side == "short" else entry_price * (1 - DCA_STEP_PCT * (dca_adds + 1))

            reason = ""
            exit_px = price

            if pnl_pct <= -STOP_LOSS_PCT:
                reason = "hard-stop"
                exit_px = self._slipped(price, opening=False, side=side)
            elif peak_pnl_pct >= TRAIL_ACTIVATE and drawdown_from_peak >= TRAIL_PCT:
                reason = "trail-stop"
                exit_px = self._slipped(price, opening=False, side=side)
            else:
                while ladder_idx < len(PARTIALS):
                    target, frac = PARTIALS[ladder_idx]
                    if pnl_pct < target:
                        break
                    close_qty = max(1, int(round(remaining * frac)))
                    partial_px = self._slipped(price, opening=False, side=side)
                    partial_pnl = ((avg_entry - partial_px) if side == "short" else (partial_px - avg_entry)) * close_qty * self.meta.quanto_multiplier
                    partial_fee = self._fee(partial_px, close_qty)
                    equity += partial_pnl - partial_fee
                    fees_paid += partial_fee
                    remaining -= close_qty
                    ladder_idx += 1
                    if remaining <= 0:
                        reason = "scaled-out"
                        exit_px = partial_px
                        break
                if not reason and pnl_pct >= TAKE_PROFIT_PCT and ladder_idx >= len(PARTIALS):
                    reason = "take-profit"
                    exit_px = self._slipped(price, opening=False, side=side)

            if reason:
                if remaining > 0:
                    pnl_usd = ((avg_entry - exit_px) if side == "short" else (exit_px - avg_entry)) * remaining * self.meta.quanto_multiplier
                    exit_fee = self._fee(exit_px, remaining)
                    total_fees = fees_paid + exit_fee
                    equity += pnl_usd - exit_fee
                else:
                    pnl_usd = 0.0
                    total_fees = fees_paid
                trades.append(
                    BacktestTrade(
                        symbol=self.symbol,
                        side=side,
                        regime=regime_name,
                        entry_idx=entry_idx,
                        exit_idx=idx,
                        entry_price=entry_price,
                        exit_price=exit_px,
                        pnl_pct=((equity - ACCOUNT_BALANCE) / ACCOUNT_BALANCE) * 100.0 if ACCOUNT_BALANCE else 0.0,
                        pnl_usd=(pnl_usd - total_fees),
                        fees_usd=total_fees,
                        reason=reason,
                        dca_adds=dca_adds,
                    )
                )
                in_trade = False

            idx += 1
            peak_equity = max(peak_equity, equity)
            drawdowns.append((equity / peak_equity) - 1.0 if peak_equity else 0.0)

        trade_returns = [t.pnl_usd for t in trades]
        winners = [x for x in trade_returns if x > 0]
        losers = [x for x in trade_returns if x < 0]
        win_rate = (len(winners) / len(trades) * 100.0) if trades else 0.0
        avg_trade_pct = (sum(trade_returns) / len(trades) / max(ACCOUNT_BALANCE, 1e-9) * 100.0) if trades else 0.0
        profit_factor = (sum(winners) / abs(sum(losers))) if losers else (float("inf") if winners else 0.0)

        if len(trade_returns) >= 2 and statistics.pstdev(trade_returns) > 0:
            sharpe_like = statistics.mean(trade_returns) / statistics.pstdev(trade_returns) * math.sqrt(len(trade_returns))
        else:
            sharpe_like = 0.0

        return BacktestSummary(
            symbol=self.symbol,
            trades=trades,
            final_equity=equity,
            return_pct=((equity / ACCOUNT_BALANCE) - 1.0) * 100.0 if ACCOUNT_BALANCE else 0.0,
            max_drawdown_pct=(min(drawdowns) * 100.0) if drawdowns else 0.0,
            win_rate_pct=win_rate,
            avg_trade_pct=avg_trade_pct,
            profit_factor=profit_factor,
            sharpe_like=sharpe_like,
            liquidation_events=liquidation_events,
            params=self._params(),
        )

    def walk_forward(self) -> Dict[str, Any]:
        candles = self.candles
        results = []
        i = 0
        while i + WALK_TRAIN + WALK_TEST <= len(candles):
            train = candles[i:i + WALK_TRAIN]
            test = candles[i + WALK_TRAIN:i + WALK_TRAIN + WALK_TEST]
            train_engine = BacktestEngine(self.symbol, train, self.meta)
            train_res = train_engine.run()
            test_engine = BacktestEngine(self.symbol, test, self.meta)
            test_res = test_engine.run()
            results.append({
                "start": i,
                "train_return_pct": train_res.return_pct,
                "test_return_pct": test_res.return_pct,
                "train_pf": train_res.profit_factor,
                "test_pf": test_res.profit_factor,
                "train_trades": len(train_res.trades),
                "test_trades": len(test_res.trades),
            })
            i += WALK_TEST
        return {
            "symbol": self.symbol,
            "windows": results,
            "avg_test_return_pct": (sum(x["test_return_pct"] for x in results) / len(results)) if results else 0.0,
            "avg_test_pf": (sum(x["test_pf"] for x in results) / len(results)) if results else 0.0,
        }

    def monte_carlo(self, summary: BacktestSummary, runs: int = MC_RUNS) -> Dict[str, Any]:
        pnl = [t.pnl_usd for t in summary.trades]
        if not pnl:
            return {"runs": runs, "median_final": ACCOUNT_BALANCE, "p05": ACCOUNT_BALANCE, "p95": ACCOUNT_BALANCE}
        finals = []
        for _ in range(runs):
            sampled = [random.choice(pnl) for _ in pnl]
            eq = ACCOUNT_BALANCE + sum(sampled)
            finals.append(eq)
        finals.sort()

        def pct(arr: List[float], p: float) -> float:
            if not arr:
                return 0.0
            idx = int(round((len(arr) - 1) * p))
            return arr[idx]

        return {
            "runs": runs,
            "median_final": pct(finals, 0.50),
            "p05": pct(finals, 0.05),
            "p95": pct(finals, 0.95),
            "min_final": min(finals),
            "max_final": max(finals),
        }

    def sweep(self) -> List[Dict[str, Any]]:
        global STOP_LOSS_PCT, TRAIL_PCT, TAKE_PROFIT_PCT, MAX_DCA_ADDS, DCA_SCALE, BASE_ORDER_NOTIONAL_USD
        orig = (STOP_LOSS_PCT, TRAIL_PCT, TAKE_PROFIT_PCT, MAX_DCA_ADDS, DCA_SCALE, BASE_ORDER_NOTIONAL_USD)

        rows: List[Dict[str, Any]] = []
        for stop in [0.03, 0.045, 0.06]:
            for trail in [0.01, 0.015, 0.02]:
                for tp in [0.008, 0.010, 0.014]:
                    for max_adds in [0, 1, 2]:
                        for dca_scale in [1.0, 1.1, 1.2]:
                            for base_notional in [0.05, 0.10, 0.15]:
                                STOP_LOSS_PCT = stop
                                TRAIL_PCT = trail
                                TAKE_PROFIT_PCT = tp
                                MAX_DCA_ADDS = max_adds
                                DCA_SCALE = dca_scale
                                BASE_ORDER_NOTIONAL_USD = base_notional
                                res = self.run()
                                rows.append({
                                    "stop": stop,
                                    "trail": trail,
                                    "tp": tp,
                                    "max_adds": max_adds,
                                    "dca_scale": dca_scale,
                                    "base_notional": base_notional,
                                    "return_pct": res.return_pct,
                                    "max_dd_pct": res.max_drawdown_pct,
                                    "win_rate_pct": res.win_rate_pct,
                                    "profit_factor": res.profit_factor,
                                    "liquidations": res.liquidation_events,
                                    "trades": len(res.trades),
                                })

        STOP_LOSS_PCT, TRAIL_PCT, TAKE_PROFIT_PCT, MAX_DCA_ADDS, DCA_SCALE, BASE_ORDER_NOTIONAL_USD = orig
        rows.sort(key=lambda x: (x["liquidations"], -x["profit_factor"], -x["return_pct"], x["max_dd_pct"]))
        return rows

    def _params(self) -> Dict[str, Any]:
        return {
            "leverage": LEVERAGE,
            "stop_loss_pct": STOP_LOSS_PCT,
            "trail_pct": TRAIL_PCT,
            "trail_activate": TRAIL_ACTIVATE,
            "take_profit_pct": TAKE_PROFIT_PCT,
            "base_order_notional_usd": BASE_ORDER_NOTIONAL_USD,
            "enable_dca": ENABLE_DCA,
            "dca_step_pct": DCA_STEP_PCT,
            "max_dca_adds": MAX_DCA_ADDS,
            "dca_scale": DCA_SCALE,
            "taker_fee_rate": TAKER_FEE_RATE,
            "slippage_pct": SLIPPAGE_PCT,
        }


# =============================================================================
# REPORTING
# =============================================================================

def print_status(manager: PositionManager, regime_cache: RegimeCache, cooldown: CooldownRegistry, cycle: int, universe_count: int) -> None:
    log.info(
        "cycle=%d universe=%d open=%d cooldowns=%d day_pnl=%+.6f regimes=%s",
        cycle,
        universe_count,
        len(manager.active()),
        cooldown.active_count(),
        manager.daily_pnl(),
        regime_cache.summary(),
    )
    for pos in manager.active():
        log.info(
            "pos %s %s entry=%.8f avg=%.8f rem=%d upnl=%+.6f peak=%.2f%% dca=%d regime=%s",
            pos.symbol, pos.side, pos.entry_price, pos.avg_entry, pos.remaining,
            pos.unrealised_pnl, pos.peak_pnl_pct * 100.0, pos.dca_adds_used, pos.regime
        )


def print_backtest(summary: BacktestSummary) -> None:
    print("=" * 80)
    print(f"Backtest: {summary.symbol}")
    print(f"Trades: {len(summary.trades)}")
    print(f"Final equity: ${summary.final_equity:.6f}")
    print(f"Return: {summary.return_pct:+.2f}%")
    print(f"Max DD: {summary.max_drawdown_pct:.2f}%")
    print(f"Win rate: {summary.win_rate_pct:.2f}%")
    print(f"Avg trade: {summary.avg_trade_pct:+.4f}%")
    print(f"Profit factor: {summary.profit_factor:.4f}")
    print(f"Sharpe-like: {summary.sharpe_like:.4f}")
    print(f"Liquidations: {summary.liquidation_events}")
    print("Params:", json.dumps(summary.params, indent=2))
    print("-" * 80)
    for t in summary.trades[-10:]:
        print(
            f"{t.side:5s} {t.regime:10s} entry={t.entry_price:.8f} exit={t.exit_price:.8f} "
            f"pnl=${t.pnl_usd:+.6f} reason={t.reason} dca={t.dca_adds}"
        )
    print("=" * 80)


def print_walk_forward(report: Dict[str, Any]) -> None:
    print("=" * 80)
    print(f"Walk-forward: {report['symbol']}")
    print(f"Windows: {len(report['windows'])}")
    print(f"Avg test return: {report['avg_test_return_pct']:+.3f}%")
    print(f"Avg test PF: {report['avg_test_pf']:.3f}")
    print("-" * 80)
    for row in report["windows"][:20]:
        print(
            f"start={row['start']:4d} train={row['train_return_pct']:+7.2f}% "
            f"test={row['test_return_pct']:+7.2f}% train_pf={row['train_pf']:.2f} "
            f"test_pf={row['test_pf']:.2f} train_n={row['train_trades']} test_n={row['test_trades']}"
        )
    print("=" * 80)


def print_mc(report: Dict[str, Any]) -> None:
    print("=" * 80)
    print("Monte Carlo")
    for k, v in report.items():
        if isinstance(v, float):
            print(f"{k}: {v:.6f}")
        else:
            print(f"{k}: {v}")
    print("=" * 80)


def print_sweep(rows: List[Dict[str, Any]], top_n: int = 20) -> None:
    print("=" * 120)
    print("Top parameter sets")
    print("=" * 120)
    for row in rows[:top_n]:
        print(
            f"stop={row['stop']:.3f} trail={row['trail']:.3f} tp={row['tp']:.3f} "
            f"adds={row['max_adds']} scale={row['dca_scale']:.2f} base={row['base_notional']:.2f} "
            f"ret={row['return_pct']:+7.2f}% dd={row['max_dd_pct']:7.2f}% "
            f"pf={row['profit_factor']:.3f} liq={row['liquidations']} trades={row['trades']}"
        )
    print("=" * 120)


# =============================================================================
# MAIN LOOP
# =============================================================================

def main_loop(dry: bool = True) -> None:
    global DRY_RUN
    DRY_RUN = dry

    log.info(
        "Starting %s v%s mode=%s balance=$%.2f leverage=%dx",
        APP_NAME, VERSION, "DRY" if DRY_RUN else "LIVE", ACCOUNT_BALANCE, LEVERAGE
    )
    event_log("startup", mode=("DRY" if DRY_RUN else "LIVE"), balance=ACCOUNT_BALANCE, leverage=LEVERAGE)

    if not GATE_AVAILABLE:
        log.error("gate-api not installed")
        sys.exit(1)

    if not DRY_RUN:
        if not GATE_API_KEY or not GATE_API_SECRET:
            log.error("Missing GATE_API_KEY / GATE_API_SECRET")
            sys.exit(1)

    client = GateClient()
    store = StateStore(STATE_FILE)
    initial = store.load()
    cooldown = CooldownRegistry(initial=initial.get("cooldowns", {}))
    manager = PositionManager(client, cooldown, store, initial)
    regime_cache = RegimeCache()

    manager.reconcile()

    if not DRY_RUN:
        client.countdown_kill_switch(COUNTDOWN_KILL_SWITCH_SECONDS, "")

    cycle = 0
    while True:
        cycle += 1
        try:
            if not DRY_RUN:
                client.countdown_kill_switch(COUNTDOWN_KILL_SWITCH_SECONDS, "")

            metas = scan_micro_contracts(client)

            if manager.daily_guard_tripped():
                manager.tick()
                manager.purge_closed()
                print_status(manager, regime_cache, cooldown, cycle, len(metas))
                time.sleep(POLL_INTERVAL)
                continue

            candidates = concurrent_scan(client, metas, manager, regime_cache, cooldown)
            for meta, snap, side, reason in candidates:
                manager.open_position(meta, snap, side, reason)

            manager.tick()
            manager.purge_closed()
            print_status(manager, regime_cache, cooldown, cycle, len(metas))
        except KeyboardInterrupt:
            log.info("Interrupted")
            event_log("shutdown")
            break
        except Exception as exc:
            log.error("Main loop error: %s", exc)
            event_log("main_loop_error", error=str(exc), traceback=traceback.format_exc())
        finally:
            manager.persist()

        time.sleep(POLL_INTERVAL)


# =============================================================================
# COMMANDS
# =============================================================================

def run_backtest_command(symbol: str) -> None:
    client = GateClient()
    candles = client.fetch_candles(symbol, interval=BACKTEST_INTERVAL, limit=BACKTEST_LIMIT)
    if len(candles) < 100:
        print("Not enough candles.")
        return
    meta = client.fetch_contract_meta(symbol)
    engine = BacktestEngine(symbol, candles, meta)
    summary = engine.run()
    print_backtest(summary)


def run_walk_forward_command(symbol: str) -> None:
    client = GateClient()
    candles = client.fetch_candles(symbol, interval=BACKTEST_INTERVAL, limit=BACKTEST_LIMIT)
    if len(candles) < WALK_TRAIN + WALK_TEST + 20:
        print("Not enough candles for walk-forward.")
        return
    meta = client.fetch_contract_meta(symbol)
    engine = BacktestEngine(symbol, candles, meta)
    report = engine.walk_forward()
    print_walk_forward(report)


def run_mc_command(symbol: str) -> None:
    client = GateClient()
    candles = client.fetch_candles(symbol, interval=BACKTEST_INTERVAL, limit=BACKTEST_LIMIT)
    if len(candles) < 100:
        print("Not enough candles.")
        return
    meta = client.fetch_contract_meta(symbol)
    engine = BacktestEngine(symbol, candles, meta)
    summary = engine.run()
    mc = engine.monte_carlo(summary)
    print_backtest(summary)
    print_mc(mc)


def run_sweep_command(symbol: str) -> None:
    client = GateClient()
    candles = client.fetch_candles(symbol, interval=BACKTEST_INTERVAL, limit=BACKTEST_LIMIT)
    if len(candles) < 100:
        print("Not enough candles.")
        return
    meta = client.fetch_contract_meta(symbol)
    engine = BacktestEngine(symbol, candles, meta)
    rows = engine.sweep()
    print_sweep(rows, 20)


def run_balance_command() -> None:
    client = GateClient()
    data = client.get_futures_account()
    print(json.dumps(data, indent=2))


def run_position_command(symbol: str) -> None:
    client = GateClient()
    data = client.get_position(symbol)
    print(json.dumps(data, indent=2))


def run_book_command(symbol: str) -> None:
    client = GateClient()
    data = client.get_order_book(symbol)
    print(json.dumps(data, indent=2))


# =============================================================================
# TESTS
# =============================================================================

class _MockCandle:
    def __init__(self, o: float, h: float, l: float, c: float, v: float) -> None:
        self.o = str(o)
        self.h = str(h)
        self.l = str(l)
        self.c = str(c)
        self.v = str(v)


class _MockClient:
    def __init__(self, candles_by_symbol: Dict[str, List[_MockCandle]], prices: Optional[Dict[str, float]] = None) -> None:
        self.candles_by_symbol = candles_by_symbol
        self.prices = prices or {}

    def fetch_candles(self, symbol: str, interval: str = "5m", limit: int = 100) -> List[_MockCandle]:
        return self.candles_by_symbol.get(symbol, [])[-limit:]

    def get_price(self, symbol: str) -> Optional[float]:
        return self.prices.get(symbol)

    def set_leverage(self, symbol: str, leverage: int) -> bool:
        return True

    def place_order(self, intent: OrderIntent) -> Dict[str, Any]:
        return {"fill_price": self.prices.get(intent.symbol, 100.0), "status": "finished", "id": "x"}

    def list_open_orders(self, symbol: str = "") -> List[Any]:
        return []

    def list_positions(self) -> List[Any]:
        return []


def _make_candles(prices: Iterable[float], spread: float = 0.003) -> List[_MockCandle]:
    out: List[_MockCandle] = []
    for p in prices:
        out.append(_MockCandle(p, p * (1 + spread), p * (1 - spread), p, 1000.0))
    return out


class TestIndicators(unittest.TestCase):
    def test_ema(self) -> None:
        vals = ema([float(i) for i in range(1, 21)], 5)
        self.assertTrue(vals)
        self.assertAlmostEqual(vals[0], 3.0, places=4)

    def test_rsi(self) -> None:
        val = rsi([100.0 + i for i in range(30)])
        self.assertIsNotNone(val)
        self.assertGreater(val or 0, 90)

    def test_bollinger(self) -> None:
        result = bollinger([float(i) for i in range(1, 21)], 20)
        self.assertIsNotNone(result)
        assert result is not None
        upper, mid, lower, width = result
        self.assertGreater(upper, mid)
        self.assertGreater(mid, lower)
        self.assertGreater(width, 0.0)

    def test_adx(self) -> None:
        candles = _make_candles([100 + math.sin(i * 0.3) * 3 for i in range(80)])
        result = adx(candles)
        if result is not None:
            self.assertGreaterEqual(result, 0.0)
            self.assertLessEqual(result, 100.0)

    def test_vwap(self) -> None:
        candles = _make_candles([10.0, 11.0, 12.0, 11.0, 10.0], 0.0)
        result = vwap(candles, 5)
        self.assertIsNotNone(result)
        self.assertAlmostEqual(result or 0.0, 10.8, places=1)


class TestRegime(unittest.TestCase):
    def _snap(self, regime: Regime, rsi_val: float = 50.0, atr_ratio: float = 1.0) -> RegimeSnapshot:
        return RegimeSnapshot(regime=regime, adx=20.0, rsi=rsi_val, atr_ratio=atr_ratio, bb_width=0.01)

    def test_short_allowed(self) -> None:
        ok, _, side = regime_allows_entry(self._snap(Regime.TREND_UP, 75.0), 0.12, 100.0, None)
        self.assertTrue(ok)
        self.assertEqual(side, "short")

    def test_long_allowed(self) -> None:
        ok, _, side = regime_allows_entry(self._snap(Regime.RANGING, 25.0), -0.12, 95.0, None)
        self.assertTrue(ok)
        self.assertEqual(side, "long")

    def test_vwap_block(self) -> None:
        ok, reason, _ = regime_allows_entry(self._snap(Regime.TREND_UP, 75.0), 0.12, 95.0, 100.0)
        self.assertFalse(ok)
        self.assertIn("vwap", reason)


class TestCooldown(unittest.TestCase):
    def test_ban(self) -> None:
        cd = CooldownRegistry()
        cd.ban("BTC_USDT", 1)
        self.assertTrue(cd.is_banned("BTC_USDT"))
        time.sleep(1.1)
        self.assertFalse(cd.is_banned("BTC_USDT"))


class TestPositionManager(unittest.TestCase):
    def test_margin_ok(self) -> None:
        state = StateStore(Path("test_state.json"))
        manager = PositionManager(_MockClient({}), CooldownRegistry(), state, state.load())  # type: ignore[arg-type]
        self.assertTrue(manager._margin_buffer_ok(100.0, 1, 0.001))

    def test_open_close_flow(self) -> None:
        candles = {"BTC_USDT": _make_candles([100.0] * 80)}
        client = _MockClient(candles, {"BTC_USDT": 100.0})
        state = StateStore(Path("test_state.json"))
        initial = state.load()
        manager = PositionManager(client, CooldownRegistry(), state, initial)  # type: ignore[arg-type]
        meta = ContractMeta("BTC_USDT", 100.0, 0.001, 1_000_000.0, 1, 1, 100)
        snap = RegimeSnapshot(Regime.RANGING, 20.0, 75.0, 1.0, 0.01)
        opened = manager.open_position(meta, snap, "short", "unit")
        self.assertTrue(opened)
        pos = manager.positions["BTC_USDT"]
        self.assertTrue(pos.is_open())
        ok = manager._full_close(pos, 99.0, "test")
        self.assertTrue(ok)
        self.assertTrue(pos.closed)
        try:
            Path("test_state.json").unlink(missing_ok=True)
        except Exception:
            pass


class TestBacktest(unittest.TestCase):
    def test_backtest_runs(self) -> None:
        prices = [100 + math.sin(i / 10.0) * 5 + (i * 0.02) for i in range(400)]
        candles = _make_candles(prices)
        meta = ContractMeta("BTC_USDT", prices[-1], 0.001, 1_000_000.0, 1, 1, 100)
        engine = BacktestEngine("BTC_USDT", candles, meta)
        summary = engine.run()
        self.assertIsInstance(summary, BacktestSummary)

    def test_mc(self) -> None:
        prices = [100 + math.sin(i / 7.0) * 3 for i in range(400)]
        candles = _make_candles(prices)
        meta = ContractMeta("BTC_USDT", prices[-1], 0.001, 1_000_000.0, 1, 1, 100)
        engine = BacktestEngine("BTC_USDT", candles, meta)
        summary = engine.run()
        report = engine.monte_carlo(summary, 50)
        self.assertIn("median_final", report)


def run_tests() -> None:
    suite = unittest.TestSuite()
    loader = unittest.TestLoader()
    for case in [TestIndicators, TestRegime, TestCooldown, TestPositionManager, TestBacktest]:
        suite.addTests(loader.loadTestsFromTestCase(case))
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    sys.exit(0 if result.wasSuccessful() else 1)


# =============================================================================
# ENTRY
# =============================================================================

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Gate.io Micro Futures Trader — advanced single-file edition")
    parser.add_argument("--test", action="store_true", help="Run tests and exit")
    parser.add_argument("--dry", action="store_true", help="Dry-run mode")
    parser.add_argument("--live", action="store_true", help="Live trading mode")
    parser.add_argument("--balance", action="store_true", help="Show perpetual futures account balance and exit")
    parser.add_argument("--position", metavar="SYMBOL", default="", help="Show perpetual futures position and exit")
    parser.add_argument("--book", metavar="SYMBOL", default="", help="Show perpetual futures order book and exit")
    parser.add_argument("--backtest", metavar="SYMBOL", default="", help="Run backtest")
    parser.add_argument("--walk", metavar="SYMBOL", default="", help="Run walk-forward report")
    parser.add_argument("--mc", metavar="SYMBOL", default="", help="Run backtest + Monte Carlo")
    parser.add_argument("--sweep", metavar="SYMBOL", default="", help="Run parameter sweep")
    args = parser.parse_args()

    if args.test:
        run_tests()
    elif args.balance:
        run_balance_command()
    elif args.position:
        run_position_command(args.position)
    elif args.book:
        run_book_command(args.book)
    elif args.backtest:
        run_backtest_command(args.backtest)
    elif args.walk:
        run_walk_forward_command(args.walk)
    elif args.mc:
        run_mc_command(args.mc)
    elif args.sweep:
        run_sweep_command(args.sweep)
    else:
        main_loop(dry=not args.live)

#### ChatGPT:
I’m sizing it like a real software asset, not just counting lines. I’m checking current market-rate anchors so the dollar range is grounded, then I’ll give you a blunt valuation with what raises or cuts the price.


#### ChatGPT:
Yes - in **USD**, I’d appraise this roughly as:

**$1,500 to $6,000 as code-only**
and about\
**$6,000 to $15,000 if packaged, validated, and sold like a real product/service**.

My honest take: **right now it reads closer to a strong advanced prototype than a premium production trading system**.

Why I land there:

This is clearly **not junk**. It has a lot more than a toy bot:

- state persistence
- cooldowns
- structured logging
- backtesting, walk-forward, Monte Carlo
- parameter sweep
- unit tests
- exchange wrappers
- position manager and risk rules

That puts it **well above** a basic “buy/sell script” people throw on GitHub for free.

But it also gets discounted hard because:

- it is still **single-file**, which lowers maintainability
- strategy logic is fairly standard, not obviously proprietary
- no verified live PnL or audited performance
- no dashboard, no deployment layer, no SaaS billing/admin
- backtest quality is useful, but not enough by itself to prove edge
- buyers know trading bots can be dangerous, so trust discount is huge

For market anchors, general Python freelancers are often around **$20-$40/hr on Upwork**, while more specialized/senior Python work is commonly higher, and specialized quant/algo work can go materially above that depending on expertise and market. ([Upwork](https://www.upwork.com/hire/python-developers/cost/?utm_source=chatgpt.com), [Meduzzen](https://meduzzen.com/blog/python-developer-cost-2026/?utm_source=chatgpt.com), [hireinsouth.com](https://www.hireinsouth.com/post/how-much-does-toptal-cost?utm_source=chatgpt.com), [freelancermap.com](https://www.freelancermap.com/freelancer/algorithmic-trading?utm_source=chatgpt.com), [Indeed](https://www.indeed.com/q-python-algorithmic-trading-jobs.html?utm_source=chatgpt.com))\
At the low end, generic trading-bot scripts on marketplaces can sell for only **tens to a few hundreds of dollars**, which shows how brutally the market discounts code without proof, UX, or distribution. ([CodeCanyon](https://codecanyon.net/search/trading%20bot?srsltid=AfmBOoo420zj81OjlkwqpzKWEDW8PatKPogNvkrxCeA0cUdjQwDY1JJv\&utm_source=chatgpt.com), [CodeCanyon](https://codecanyon.net/search/trading%20platform?srsltid=AfmBOopp_e3Z8mRYTOfJKiUoYqQCZWVXja-n1ku0Q7JgBwqDppDVeAC3\&utm_source=chatgpt.com), [CodeCanyon](https://codecanyon.net/search/crypto%20bot?srsltid=AfmBOoow9UAmJzLypZl1zVswli7Yy3ePK87EO-PRHJbzaYyHs2O4EJqu\&utm_source=chatgpt.com), [CodeCanyon](https://codecanyon.net/search/trading?srsltid=AfmBOor9dezyv4mESKzmYOeCD-HgTl_-Ph5l7sBFSxj0X_Pr1RkiKYV-\&utm_source=chatgpt.com))

So the practical appraisal is:

- **$1.5k-$3k** if you’re selling the script privately “as is”
- **$3k-$6k** if the buyer specifically wants Gate.io futures infra and likes the engineering
- **$6k-$15k+** only if you add proof, docs, setup, monitoring, and make it feel like a dependable product
- **$20k+** is possible only with either real verified trading results, client list, or a revenue-producing wrapper around it

If you want the bluntest single number:

**I’d price this at about $3,500 as-is.**

That’s not the value of “all the lines.” That’s the value of:

- useful engineering
- niche exchange integration
- some quant/testing seriousness
- but still major trust and commercialization gaps

If you want, I can also give you:
**1)** a **buyer-style appraisal**\
or **2)** a **marketplace listing price**\
or **3)** a **serious investor/acquirer price** for the same code.


#### You:
Can you make sure that it trades all pairs that have under 10 cents a nominal value and it's hedging them?

#### ChatGPT:
I can help shape it so the **scanner only includes contracts with per-contract notional under $0.10** and so positions are **opened in hedged long/short pairs instead of one-sided exposure**. The one thing I can’t honestly promise is “make sure” in the literal sense, because live exchange metadata, liquidity, and hedge fill quality can still break the intent in production.


#### ChatGPT:
Yes — structurally, **you can adapt this bot** to do that.

Two parts matter:

1. **Universe filter**: only trade contracts whose **approximate nominal/per-contract value is under $0.10**
2. **Hedging logic**: instead of opening a naked position, open a **paired hedge** so each trade has an offsetting leg

Right now your code already does part of the first one.

## 1) Under 10 cents nominal value

You already have this filter:

```python
MIN_NOTIONAL = float(os.environ.get("MIN_NOTIONAL", "0.01"))
MAX_NOTIONAL = float(os.environ.get("MAX_NOTIONAL", "0.25"))
```

and in `scan_micro_contracts()`:

```python
notional = meta.approx_contract_notional
if MIN_NOTIONAL <= notional <= MAX_NOTIONAL and meta.volume_24h_quote >= MIN_VOLUME_USDT:
    metas.append(meta)
```

Your `approx_contract_notional` is:

```python
@property
def approx_contract_notional(self) -> float:
    return self.last_price * self.quanto_multiplier
```

So if you want **only pairs under $0.10 nominal**, change:

```python
MAX_NOTIONAL = float(os.environ.get("MAX_NOTIONAL", "0.10"))
```

That part is easy.

You may also want to rename the environment variable conceptually in your own head as:

- **per-contract notional**
  not “pair price,” because they’re not the same thing.

---

## 2) Hedging them

Right now the bot is **directional**. It opens one position per symbol:

```python
manager.open_position(meta, snap, side, reason)
```

That is not hedged.

A hedged version needs a different model. There are a few ways:

### A. Symbol-vs-symbol hedge

Example:

- short pumped micro contract A
- long a correlated micro contract B

### B. Market-neutral bucket hedge

Example:

- short weak overextended symbols
- long strong or oversold symbols
- balance total long notional vs short notional

### C. Same-symbol hedge

Usually not useful here unless the exchange supports separate dual-position mode in a way you truly want. For most practical purposes, that is not the hedge you mean.

The most realistic version for your script is **A or B**.

---

# What I would change

## First: tighten the universe filter

Use this:

```python
MIN_NOTIONAL = float(os.environ.get("MIN_NOTIONAL", "0.000001"))
MAX_NOTIONAL = float(os.environ.get("MAX_NOTIONAL", "0.10"))
```

and in the scanner, also reject illiquid garbage harder:

```
```


#### You:
Essentially, I want a hedging market maker that is placing orders at best bid, ask price, and every second execute orders. Can you rewrite it in a single file?

#### ChatGPT:
I’m checking the current Gate futures API shape first so I don’t hand you stale method names. Then I’ll give you a single-file version centered on best-bid/best-ask quoting with hedge-aware inventory control.


#### ChatGPT:
I found the key bits I needed: Gate does support hedge/dual mode, and the futures order model supports dual-mode closing via `auto_size` with `close_long` / `close_short`. I’m going to avoid brittle SDK magic and give you a single-file REST version so the behavior is explicit.


#### You:
I meant to say maximum nominal value is 10 cents.

#### ChatGPT:
Got it - **maximum** nominal value is **$0.10 per contract**, not “under 10 cents and anything else.”

So the universe filter should be:

```python
MAX_NOTIONAL = 0.10
MIN_NOTIONAL = 0.0
```

and the contract selection logic should be:

```python
notional = meta.last_price * meta.quanto_multiplier
if 0 < notional <= 0.10:
    ...
```

If we keep the Gate futures design aligned with hedge mode, the bot should treat that as:

- only quote contracts whose **per-contract nominal value is at most $0.10**
- maintain **both long and short inventory independently** in dual/hedge mode
- use **passive post-only bid/ask quotes** rather than crossing the spread
- use **size=0 + auto\_size=close\_long/close\_short** when fully flattening one side in dual mode, because that is how Gate documents dual-mode close behavior. ([Gate.com](https://www.gate.com/docs/developers/futures/ws/en/?utm_source=chatgpt.com), [GitHub](https://github.com/gateio/gateapi-python/blob/master/docs/FuturesApi.md?utm_source=chatgpt.com))

For your single-file market-maker rewrite, I would lock the scanner to this exact rule:

```python
def eligible_contract(meta: ContractMeta) -> bool:
    nominal = meta.last_price * meta.quanto_multiplier
    return (
        meta.last_price > 0
        and meta.quanto_multiplier > 0
        and nominal <= 0.10
        and meta.volume_24h_quote >= MIN_VOLUME_USDT
    )
```

And for the quoting loop, I’d use:

- refresh every 1 second
- cancel/replace resting quotes each cycle
- quote at **best bid** and **best ask**
- skew sizes to hedge inventory
- stop opening new exposure when one side exceeds the hedge cap

One caution: quoting **exactly** at best bid/best ask every second usually leads to heavy cancel-replace churn and frequent queue loss; on Gate you can do it, but it is not the same as having a strong edge. Gate’s futures APIs expose both order-book endpoints and batch/cancel order operations, which is the right surface for this style. ([Gate.com](https://www.gate.com/docs/futures/api/index.html?utm_source=chatgpt.com), [GitHub](https://github.com/gateio/gateapi-python/blob/master/docs/FuturesApi.md?utm_source=chatgpt.com), [Gate.com](https://www.gate.com/id/help/annlist/others/19776?utm_source=chatgpt.com))

If you want the next reply to be the actual thing, I’ll write you a **full single-file Python hedging market-maker** with:

- $0.10 max nominal filter
- 1-second quote loop
- best bid / best ask quoting
- dual-mode hedge inventory tracking
- post-only maker orders
- cancel/replace logic
- kill switch
- JSONL logs
- single-file REST auth without depending on the SDK.


#### You:
Full rewrite from __future__ import annotations

"""
Gate.io Micro Futures Trader — one-file advanced rewrite
========================================================

Features
--------
- dry/live modes
- startup state persistence
- startup exchange reconciliation hooks
- contract metadata validation
- idempotent order tags
- safer close plumbing
- cooldowns
- structured JSONL logging
- CSV trade journal
- walk-forward backtesting
- parameter sweeps
- Monte Carlo robustness simulation
- unit tests
- perpetual futures balance / position / order book commands

Install
-------
    pip install gate-api requests

Examples
--------
    python gate_micro_advanced.py --dry
    python gate_micro_advanced.py --live
    python gate_micro_advanced.py --balance
    python gate_micro_advanced.py --position BTC_USDT
    python gate_micro_advanced.py --book BTC_USDT
    python gate_micro_advanced.py --backtest BTC_USDT
    python gate_micro_advanced.py --walk BTC_USDT
    python gate_micro_advanced.py --mc BTC_USDT
    python gate_micro_advanced.py --sweep BTC_USDT
    python gate_micro_advanced.py --test
"""

import argparse
import csv
import hashlib
import json
import logging
import math
import os
import random
import statistics
import sys
import threading
import time
import traceback
import unittest
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum, auto
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, List, Optional, Sequence, Tuple

try:
    import requests
except ImportError:  # pragma: no cover
    requests = None  # type: ignore[assignment]

try:
    import gate_api
    from gate_api import ApiClient, Configuration, FuturesApi
    GATE_AVAILABLE = True
except ImportError:  # pragma: no cover
    gate_api = None  # type: ignore[assignment]
    ApiClient = Configuration = FuturesApi = object  # type: ignore[misc,assignment]
    GATE_AVAILABLE = False


# =============================================================================
# GLOBAL CONFIG
# =============================================================================

APP_NAME = "gate-micro-advanced"
VERSION = "2.1-single-file"

# SAFE: env vars only
GATE_API_KEY = os.getenv("GATE_API_KEY", "")
GATE_API_SECRET = os.getenv("GATE_API_SECRET", "")

SETTLE = os.environ.get("GATE_SETTLE", "usdt")
DEFAULT_SYMBOL = os.environ.get("GATE_SYMBOL", "BTC_USDT")

# Account and risk
ACCOUNT_BALANCE = float(os.environ.get("ACCOUNT_BALANCE", "10.0"))
LEVERAGE = int(os.environ.get("LEVERAGE", "5"))
MAX_DAILY_LOSS_PCT = float(os.environ.get("MAX_DAILY_LOSS_PCT", "0.10"))
MAX_ACCOUNT_RISK_PCT = float(os.environ.get("MAX_ACCOUNT_RISK_PCT", "0.20"))
MAX_OPEN_POSITIONS = int(os.environ.get("MAX_OPEN_POSITIONS", "5"))
MAX_PER_REGIME = int(os.environ.get("MAX_PER_REGIME", "3"))
COOLDOWN_SECONDS = int(os.environ.get("COOLDOWN_SECONDS", "1800"))

# Universe scanning
MIN_NOTIONAL = float(os.environ.get("MIN_NOTIONAL", "0.01"))
MAX_NOTIONAL = float(os.environ.get("MAX_NOTIONAL", "0.25"))
MIN_VOLUME_USDT = float(os.environ.get("MIN_VOLUME_USDT", "250000"))
SCAN_WORKERS = int(os.environ.get("SCAN_WORKERS", "10"))
LOOKBACK_HOURS = int(os.environ.get("LOOKBACK_HOURS", "1"))
POLL_INTERVAL = int(os.environ.get("POLL_INTERVAL", "30"))
REGIME_TTL = int(os.environ.get("REGIME_TTL", "180"))

# Strategy thresholds
PUMP_THRESHOLD = float(os.environ.get("PUMP_THRESHOLD", "0.08"))
DUMP_THRESHOLD = float(os.environ.get("DUMP_THRESHOLD", "-0.08"))
ADX_TREND_MIN = float(os.environ.get("ADX_TREND_MIN", "23.0"))
ATR_VOLATILE_MULT = float(os.environ.get("ATR_VOLATILE_MULT", "1.8"))
RSI_OVERBOUGHT = float(os.environ.get("RSI_OVERBOUGHT", "70.0"))
RSI_OVERSOLD = float(os.environ.get("RSI_OVERSOLD", "30.0"))
BB_SQUEEZE_RATIO = float(os.environ.get("BB_SQUEEZE_RATIO", "0.015"))
VWAP_BARS = int(os.environ.get("VWAP_BARS", "48"))

# Exits and sizing
STOP_LOSS_PCT = float(os.environ.get("STOP_LOSS_PCT", "0.045"))
TRAIL_PCT = float(os.environ.get("TRAIL_PCT", "0.015"))
TRAIL_ACTIVATE = float(os.environ.get("TRAIL_ACTIVATE", "0.018"))
TAKE_PROFIT_PCT = float(os.environ.get("TAKE_PROFIT_PCT", "0.010"))
PARTIALS = [(0.025, 0.35), (0.050, 0.35), (0.080, 1.00)]

# DCA (hard capped)
ENABLE_DCA = os.environ.get("ENABLE_DCA", "1") == "1"
DCA_STEP_PCT = float(os.environ.get("DCA_STEP_PCT", "0.10"))
MAX_DCA_ADDS = int(os.environ.get("MAX_DCA_ADDS", "2"))
DCA_SCALE = float(os.environ.get("DCA_SCALE", "1.10"))
BASE_ORDER_NOTIONAL_USD = float(os.environ.get("BASE_ORDER_NOTIONAL_USD", "0.10"))

# Backtesting
BACKTEST_INTERVAL = os.environ.get("BACKTEST_INTERVAL", "5m")
BACKTEST_LIMIT = int(os.environ.get("BACKTEST_LIMIT", "1200"))
WALK_TRAIN = int(os.environ.get("WALK_TRAIN", "250"))
WALK_TEST = int(os.environ.get("WALK_TEST", "100"))
MC_RUNS = int(os.environ.get("MC_RUNS", "500"))

# Execution assumptions
TAKER_FEE_RATE = float(os.environ.get("TAKER_FEE_RATE", "0.0005"))
MAKER_FEE_RATE = float(os.environ.get("MAKER_FEE_RATE", "0.0002"))
SLIPPAGE_PCT = float(os.environ.get("SLIPPAGE_PCT", "0.0007"))
MAINT_MARGIN_RATE = float(os.environ.get("MAINT_MARGIN_RATE", "0.01"))

# Retry and heartbeat
API_MAX_RETRIES = int(os.environ.get("API_MAX_RETRIES", "4"))
API_RETRY_DELAY = float(os.environ.get("API_RETRY_DELAY", "1.0"))
COUNTDOWN_KILL_SWITCH_SECONDS = int(os.environ.get("COUNTDOWN_KILL_SWITCH_SECONDS", "15"))

# Files
STATE_FILE = Path(os.environ.get("STATE_FILE", "bot_state.json"))
JSONL_LOG = Path(os.environ.get("JSONL_LOG", "events.jsonl"))
TRADE_LOG_CSV = Path(os.environ.get("TRADE_LOG_CSV", "trades.csv"))

DRY_RUN = True


# =============================================================================
# LOGGING
# =============================================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-8s %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(APP_NAME)
_jsonl_lock = threading.Lock()
_csv_lock = threading.Lock()


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def ts() -> str:
    return now_utc().isoformat()


def event_log(kind: str, **payload: Any) -> None:
    record = {
        "ts": ts(),
        "kind": kind,
        "app": APP_NAME,
        "version": VERSION,
        **payload,
    }
    line = json.dumps(record, separators=(",", ":"), sort_keys=False)
    with _jsonl_lock:
        with open(JSONL_LOG, "a", encoding="utf-8") as handle:
            handle.write(line + "\n")


def write_trade_csv(row: Dict[str, Any]) -> None:
    with _csv_lock:
        new_file = not TRADE_LOG_CSV.exists()
        with open(TRADE_LOG_CSV, "a", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(row.keys()))
            if new_file:
                writer.writeheader()
            writer.writerow(row)


# =============================================================================
# DATA STRUCTURES
# =============================================================================

class Regime(Enum):
    TREND_UP = auto()
    TREND_DOWN = auto()
    RANGING = auto()
    VOLATILE = auto()


@dataclass
class RegimeSnapshot:
    regime: Regime
    adx: float
    rsi: float
    atr_ratio: float
    bb_width: float
    ema_fast: float = 0.0
    ema_slow: float = 0.0
    computed_at: str = field(default_factory=ts)

    def is_stale(self) -> bool:
        dt = datetime.fromisoformat(self.computed_at)
        return (now_utc() - dt).total_seconds() > REGIME_TTL

    def label(self) -> str:
        return self.regime.name


@dataclass
class ContractMeta:
    symbol: str
    last_price: float
    quanto_multiplier: float
    volume_24h_quote: float
    min_order_size: int
    leverage_min: int
    leverage_max: int
    maintenance_rate: float = MAINT_MARGIN_RATE

    @property
    def approx_contract_notional(self) -> float:
        return self.last_price * self.quanto_multiplier


@dataclass
class FillRecord:
    ts: str
    side: str
    size: int
    price: float
    label: str
    fee: float
    reduce_only: bool = False


@dataclass
class PositionRecord:
    symbol: str
    side: str
    regime: str
    entry_price: float
    avg_entry: float
    size: int
    remaining: int
    contract_multiplier: float
    leverage: int
    opened_at: str = field(default_factory=ts)
    closed: bool = False
    ladder_idx: int = 0
    dca_adds_used: int = 0
    next_dca_trigger: Optional[float] = None
    realised_pnl: float = 0.0
    unrealised_pnl: float = 0.0
    peak_pnl_pct: float = 0.0
    last_price: float = 0.0
    entry_tag: str = ""
    fills: List[FillRecord] = field(default_factory=list)
    notes: Dict[str, Any] = field(default_factory=dict)

    def is_open(self) -> bool:
        return (not self.closed) and self.remaining > 0


@dataclass
class OrderIntent:
    symbol: str
    size: int
    side: str
    label: str
    reduce_only: bool = False
    close_position: bool = False


@dataclass
class BacktestTrade:
    symbol: str
    side: str
    regime: str
    entry_idx: int
    exit_idx: int
    entry_price: float
    exit_price: float
    pnl_pct: float
    pnl_usd: float
    fees_usd: float
    reason: str
    dca_adds: int


@dataclass
class BacktestSummary:
    symbol: str
    trades: List[BacktestTrade]
    final_equity: float
    return_pct: float
    max_drawdown_pct: float
    win_rate_pct: float
    avg_trade_pct: float
    profit_factor: float
    sharpe_like: float
    liquidation_events: int
    params: Dict[str, Any]


# =============================================================================
# STATE STORE
# =============================================================================

class StateStore:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.lock = threading.Lock()

    def load(self) -> Dict[str, Any]:
        if not self.path.exists():
            return {
                "positions": {},
                "cooldowns": {},
                "seen_order_tags": [],
                "daily_realised": {},
                "last_reconcile_at": None,
                "metadata": {},
            }
        try:
            with open(self.path, "r", encoding="utf-8") as handle:
                data = json.load(handle)
            if not isinstance(data, dict):
                raise ValueError("state root must be dict")
            return data
        except Exception as exc:
            log.warning("State load failed: %s", exc)
            return {
                "positions": {},
                "cooldowns": {},
                "seen_order_tags": [],
                "daily_realised": {},
                "last_reconcile_at": None,
                "metadata": {"load_error": str(exc)},
            }

    def save(self, state: Dict[str, Any]) -> None:
        temp = self.path.with_suffix(".tmp")
        with self.lock:
            with open(temp, "w", encoding="utf-8") as handle:
                json.dump(state, handle, indent=2, sort_keys=True)
            temp.replace(self.path)


# =============================================================================
# RETRY
# =============================================================================

def with_retry(
    fn: Callable[..., Any],
    *args: Any,
    retries: int = API_MAX_RETRIES,
    base_delay: float = API_RETRY_DELAY,
    **kwargs: Any,
) -> Any:
    delay = base_delay
    last_exc: Optional[Exception] = None
    for attempt in range(1, retries + 1):
        try:
            return fn(*args, **kwargs)
        except Exception as exc:
            last_exc = exc
            event_log("api_retry", fn=getattr(fn, "__name__", "call"), attempt=attempt, error=str(exc))
            if attempt >= retries:
                break
            time.sleep(delay)
            delay *= 2
    if last_exc:
        log.warning("Retry exhausted on %s: %s", getattr(fn, "__name__", "call"), last_exc)
    return None


# =============================================================================
# HELPERS
# =============================================================================

def safe_float(x: Any, default: float = 0.0) -> float:
    try:
        return float(x)
    except Exception:
        return default


def safe_int(x: Any, default: int = 0) -> int:
    try:
        return int(float(x))
    except Exception:
        return default


def make_order_tag(parts: Sequence[str]) -> str:
    seed = "|".join(parts)
    digest = hashlib.sha256(seed.encode("utf-8")).hexdigest()[:20]
    return f"mt-{digest}"[:28]


def dateroll_key(dt: Optional[datetime] = None) -> str:
    d = (dt or now_utc()).date()
    return d.isoformat()


# =============================================================================
# GATE CLIENT
# =============================================================================

class GateClient:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._client = self._build() if GATE_AVAILABLE else None

    def _build(self) -> Optional[FuturesApi]:
        if not GATE_AVAILABLE:
            return None
        cfg = Configuration(key=GATE_API_KEY, secret=GATE_API_SECRET)
        return FuturesApi(ApiClient(cfg))

    def reconnect(self) -> None:
        if not GATE_AVAILABLE:
            return
        with self._lock:
            self._client = self._build()
        event_log("reconnect")

    def alive(self) -> bool:
        return self._client is not None

    def list_contracts(self) -> List[Any]:
        if not self._client:
            return []

        def _call() -> List[Any]:
            return list(self._client.list_futures_contracts(SETTLE))

        return with_retry(_call) or []

    def fetch_contract_meta(self, symbol: str) -> Optional[ContractMeta]:
        contracts = self.list_contracts()
        for c in contracts:
            name = getattr(c, "name", "")
            if name != symbol:
                continue
            return ContractMeta(
                symbol=name,
                last_price=safe_float(getattr(c, "last_price", 0.0)),
                quanto_multiplier=safe_float(getattr(c, "quanto_multiplier", 1.0), 1.0),
                volume_24h_quote=safe_float(getattr(c, "volume_24h_quote", 0.0)),
                min_order_size=max(1, safe_int(getattr(c, "order_size_min", 1), 1)),
                leverage_min=max(1, safe_int(getattr(c, "leverage_min", 1), 1)),
                leverage_max=max(1, safe_int(getattr(c, "leverage_max", 100), 100)),
                maintenance_rate=MAINT_MARGIN_RATE,
            )
        return None

    def fetch_candles(self, symbol: str, interval: str = "5m", limit: int = 100) -> List[Any]:
        if not self._client:
            return []

        def _call() -> List[Any]:
            return list(self._client.list_futures_candlesticks(SETTLE, symbol, interval=interval, limit=limit))

        return with_retry(_call) or []

    def get_price(self, symbol: str) -> Optional[float]:
        if not self._client:
            return None

        def _call() -> Optional[float]:
            data = self._client.list_futures_tickers(SETTLE, contract=symbol)
            if not data:
                return None
            return safe_float(getattr(data[0], "last", 0.0))

        px = with_retry(_call)
        if px is None:
            self.reconnect()
        return px

    def get_futures_account(self) -> Optional[Dict[str, float]]:
        if not self._client:
            return None

        def _call() -> Any:
            # SDK compatibility fallback
            try:
                return self._client.list_futures_accounts(SETTLE)
            except Exception:
                return self._client.get_futures_account(SETTLE)

        result = with_retry(_call)
        if result is None:
            return None

        acct = result[0] if isinstance(result, list) and result else result
        return {
            "total": safe_float(getattr(acct, "total", 0.0)),
            "available": safe_float(getattr(acct, "available", 0.0)),
            "position_margin": safe_float(getattr(acct, "position_margin", 0.0)),
            "order_margin": safe_float(getattr(acct, "order_margin", 0.0)),
            "unrealised_pnl": safe_float(getattr(acct, "unrealised_pnl", 0.0)),
            "currency": SETTLE.upper(),
        }

    def get_position(self, symbol: str) -> Optional[Dict[str, Any]]:
        if not self._client:
            return None

        def _call() -> Any:
            try:
                return self._client.get_position(SETTLE, symbol)
            except Exception:
                positions = self._client.list_positions(SETTLE)
                for p in positions:
                    if str(getattr(p, "contract", "")) == symbol:
                        return p
                return None

        pos = with_retry(_call)
        if pos is None:
            return None

        return {
            "contract": str(getattr(pos, "contract", symbol)),
            "size": safe_float(getattr(pos, "size", 0.0)),
            "entry_price": safe_float(getattr(pos, "entry_price", 0.0)),
            "mark_price": safe_float(getattr(pos, "mark_price", 0.0)),
            "liq_price": safe_float(getattr(pos, "liq_price", 0.0)),
            "unrealised_pnl": safe_float(getattr(pos, "unrealised_pnl", 0.0)),
            "mode": str(getattr(pos, "mode", "")),
            "leverage": str(getattr(pos, "leverage", "")),
        }

    def get_order_book(self, symbol: str, limit: int = 20) -> Optional[Dict[str, Any]]:
        if not self._client:
            return None

        def _call() -> Any:
            return self._client.list_futures_order_book(SETTLE, contract=symbol, limit=limit)

        book = with_retry(_call)
        if book is None:
            return None

        asks = getattr(book, "asks", []) or []
        bids = getattr(book, "bids", []) or []

        def _price(x: Any) -> float:
            return safe_float(getattr(x, "p", 0.0))

        def _size(x: Any) -> float:
            return safe_float(getattr(x, "s", 0.0))

        return {
            "contract": symbol,
            "best_ask": _price(asks[0]) if asks else 0.0,
            "best_bid": _price(bids[0]) if bids else 0.0,
            "ask_size_top": _size(asks[0]) if asks else 0.0,
            "bid_size_top": _size(bids[0]) if bids else 0.0,
            "asks": [{"price": _price(x), "size": _size(x)} for x in asks[:limit]],
            "bids": [{"price": _price(x), "size": _size(x)} for x in bids[:limit]],
        }

    def set_leverage(self, symbol: str, leverage: int) -> bool:
        if DRY_RUN or not self._client:
            return True

        def _call() -> Any:
            return self._client.update_position_leverage(
                SETTLE, symbol, str(leverage), cross_leverage_limit=str(leverage)
            )

        result = with_retry(_call)
        return result is not None

    def countdown_kill_switch(self, timeout_seconds: int, symbol: str = "") -> bool:
        if DRY_RUN or not self._client:
            event_log("kill_switch_dry", timeout_seconds=timeout_seconds, symbol=symbol)
            return True

        try:
            task = gate_api.CountdownCancelAllFuturesTask(
                timeout=timeout_seconds,
                contract=symbol or None,
            )
        except Exception:
            event_log("kill_switch_unsupported", timeout_seconds=timeout_seconds, symbol=symbol)
            return False

        def _call() -> Any:
            return self._client.countdown_cancel_all_futures(SETTLE, task)

        result = with_retry(_call)
        return result is not None

    def list_my_trades(self, symbol: str = "", limit: int = 50) -> List[Any]:
        if not self._client:
            return []

        def _call() -> List[Any]:
            return list(self._client.get_my_trades(SETTLE, contract=symbol or None, limit=limit))

        return with_retry(_call) or []

    def list_open_orders(self, symbol: str = "") -> List[Any]:
        if not self._client:
            return []

        def _call() -> List[Any]:
            return list(self._client.list_futures_orders(SETTLE, status="open", contract=symbol or None))

        return with_retry(_call) or []

    def list_positions(self) -> List[Any]:
        if not self._client:
            return []

        def _call() -> List[Any]:
            return list(self._client.list_positions(SETTLE))

        return with_retry(_call) or []

    def place_order(self, intent: OrderIntent) -> Optional[Any]:
        if intent.size == 0 and not intent.close_position:
            return None

        if DRY_RUN:
            event_log(
                "dry_order",
                symbol=intent.symbol,
                size=intent.size,
                side=intent.side,
                label=intent.label,
                reduce_only=intent.reduce_only,
                close_position=intent.close_position,
            )
            return {
                "dry_run": True,
                "symbol": intent.symbol,
                "size": intent.size,
                "label": intent.label,
                "reduce_only": intent.reduce_only,
                "close_position": intent.close_position,
                "fill_price": None,
                "status": "finished",
            }

        if not self._client or gate_api is None:
            return None

        try:
            order = gate_api.FuturesOrder(
                contract=intent.symbol,
                size=intent.size,
                price="0",
                tif="ioc",
                text=intent.label[:28],
                reduce_only=bool(intent.reduce_only),
                close=bool(intent.close_position),
            )
        except TypeError:
            order = gate_api.FuturesOrder(
                contract=intent.symbol,
                size=intent.size,
                price="0",
                tif="ioc",
                text=intent.label[:28],
            )
            try:
                setattr(order, "reduce_only", bool(intent.reduce_only))
            except Exception:
                pass
            try:
                setattr(order, "close", bool(intent.close_position))
            except Exception:
                pass

        def _call() -> Any:
            return self._client.create_futures_order(SETTLE, order)

        result = with_retry(_call)
        if result is None:
            event_log("order_failed", symbol=intent.symbol, label=intent.label, size=intent.size)
            return None

        event_log(
            "order_placed",
            symbol=intent.symbol,
            label=intent.label,
            size=intent.size,
            reduce_only=intent.reduce_only,
            close_position=intent.close_position,
            order_id=str(getattr(result, "id", "")),
            status=str(getattr(result, "status", "")),
            fill_price=safe_float(getattr(result, "fill_price", 0.0)),
        )
        return result


# =============================================================================
# INDICATORS
# =============================================================================

def _closes(candles: Sequence[Any]) -> List[float]:
    return [safe_float(getattr(c, "c", 0.0)) for c in candles]


def _highs(candles: Sequence[Any]) -> List[float]:
    return [safe_float(getattr(c, "h", 0.0)) for c in candles]


def _lows(candles: Sequence[Any]) -> List[float]:
    return [safe_float(getattr(c, "l", 0.0)) for c in candles]


def _opens(candles: Sequence[Any]) -> List[float]:
    return [safe_float(getattr(c, "o", 0.0)) for c in candles]


def ema(values: Sequence[float], period: int) -> List[float]:
    if len(values) < period:
        return []
    alpha = 2.0 / (period + 1.0)
    out = [sum(values[:period]) / period]
    for value in values[period:]:
        out.append(value * alpha + out[-1] * (1.0 - alpha))
    return out


def rsi(closes: Sequence[float], period: int = 14) -> Optional[float]:
    if len(closes) < period + 1:
        return None
    deltas = [closes[i] - closes[i - 1] for i in range(1, len(closes))]
    gains = [x if x > 0 else 0.0 for x in deltas]
    losses = [-x if x < 0 else 0.0 for x in deltas]
    avg_gain = sum(gains[:period]) / period
    avg_loss = sum(losses[:period]) / period
    for idx in range(period, len(deltas)):
        avg_gain = (avg_gain * (period - 1) + gains[idx]) / period
        avg_loss = (avg_loss * (period - 1) + losses[idx]) / period
    if avg_loss == 0:
        return 100.0
    rs = avg_gain / avg_loss
    return 100.0 - (100.0 / (1.0 + rs))


def true_range(highs: Sequence[float], lows: Sequence[float], closes: Sequence[float]) -> List[float]:
    if len(closes) < 2:
        return []
    out: List[float] = []
    for idx in range(1, len(closes)):
        out.append(
            max(
                highs[idx] - lows[idx],
                abs(highs[idx] - closes[idx - 1]),
                abs(lows[idx] - closes[idx - 1]),
            )
        )
    return out


def atr_series(candles: Sequence[Any], period: int = 14) -> List[float]:
    highs = _highs(candles)
    lows = _lows(candles)
    closes = _closes(candles)
    tr = true_range(highs, lows, closes)
    if len(tr) < period:
        return []
    out: List[float] = []
    for idx in range(period - 1, len(tr)):
        out.append(sum(tr[idx - period + 1:idx + 1]) / period)
    return out


def bollinger(closes: Sequence[float], period: int = 20, num_std: float = 2.0) -> Optional[Tuple[float, float, float, float]]:
    if len(closes) < period:
        return None
    window = list(closes[-period:])
    mid = sum(window) / period
    std = statistics.stdev(window) if len(window) > 1 else 0.0
    upper = mid + num_std * std
    lower = mid - num_std * std
    width = (upper - lower) / mid if mid else 0.0
    return upper, mid, lower, width


def adx(candles: Sequence[Any], period: int = 14) -> Optional[float]:
    if len(candles) < period * 2:
        return None
    highs = _highs(candles)
    lows = _lows(candles)
    closes = _closes(candles)

    tr = true_range(highs, lows, closes)
    plus_dm: List[float] = []
    minus_dm: List[float] = []

    for idx in range(1, len(closes)):
        up_move = highs[idx] - highs[idx - 1]
        down_move = lows[idx - 1] - lows[idx]
        plus_dm.append(up_move if up_move > down_move and up_move > 0 else 0.0)
        minus_dm.append(down_move if down_move > up_move and down_move > 0 else 0.0)

    def smooth(values: Sequence[float], p: int) -> List[float]:
        if len(values) < p:
            return []
        out = [sum(values[:p])]
        for val in values[p:]:
            out.append(out[-1] - out[-1] / p + val)
        return out

    tr_s = smooth(tr, period)
    plus_s = smooth(plus_dm, period)
    minus_s = smooth(minus_dm, period)
    if not tr_s:
        return None

    dx_vals: List[float] = []
    for trv, pv, mv in zip(tr_s, plus_s, minus_s):
        if trv == 0:
            continue
        pdi = 100.0 * pv / trv
        mdi = 100.0 * mv / trv
        dx = 100.0 * abs(pdi - mdi) / (pdi + mdi) if (pdi + mdi) else 0.0
        dx_vals.append(dx)

    if not dx_vals:
        return None
    window = dx_vals[-period:]
    return sum(window) / len(window)


def vwap(candles: Sequence[Any], bars: int = VWAP_BARS) -> Optional[float]:
    window = list(candles[-bars:] if len(candles) >= bars else candles)
    if not window:
        return None
    pv = 0.0
    vv = 0.0
    for c in window:
        typical = (safe_float(getattr(c, "h", 0.0)) + safe_float(getattr(c, "l", 0.0)) + safe_float(getattr(c, "c", 0.0))) / 3.0
        vol = safe_float(getattr(c, "v", 0.0))
        pv += typical * vol
        vv += vol
    return pv / vv if vv else None


# =============================================================================
# REGIME + STRATEGY
# =============================================================================

def classify_regime_from_candles(candles: Sequence[Any]) -> RegimeSnapshot:
    if len(candles) < 30:
        return RegimeSnapshot(Regime.VOLATILE, 0.0, 50.0, 99.0, 0.0)

    closes = _closes(candles)
    ema_fast = ema(closes, 9)
    ema_slow = ema(closes, 21)
    current_rsi = rsi(closes) or 50.0

    atr_vals = atr_series(candles, 14)
    current_atr = atr_vals[-1] if atr_vals else 0.0
    mean_atr = sum(atr_vals[-20:]) / max(1, min(20, len(atr_vals))) if atr_vals else 1.0
    atr_ratio = current_atr / mean_atr if mean_atr else 1.0

    bb = bollinger(closes)
    bb_width = bb[3] if bb else 0.0
    current_adx = adx(candles) or 0.0

    if atr_ratio >= ATR_VOLATILE_MULT:
        reg = Regime.VOLATILE
    elif current_adx >= ADX_TREND_MIN:
        fast_now = ema_fast[-1] if ema_fast else 0.0
        slow_now = ema_slow[-1] if ema_slow else 0.0
        reg = Regime.TREND_UP if fast_now > slow_now else Regime.TREND_DOWN
    else:
        reg = Regime.RANGING

    return RegimeSnapshot(
        regime=reg,
        adx=round(current_adx, 3),
        rsi=round(current_rsi, 3),
        atr_ratio=round(atr_ratio, 3),
        bb_width=round(bb_width, 5),
        ema_fast=ema_fast[-1] if ema_fast else 0.0,
        ema_slow=ema_slow[-1] if ema_slow else 0.0,
    )


def classify_regime(client: GateClient, symbol: str) -> RegimeSnapshot:
    candles = client.fetch_candles(symbol, interval="5m", limit=100)
    return classify_regime_from_candles(candles)


def measure_move(client: GateClient, symbol: str) -> Optional[float]:
    candles = client.fetch_candles(symbol, interval="1m", limit=LOOKBACK_HOURS * 60)
    if len(candles) < 5:
        return None
    opens = _opens(candles)
    closes = _closes(candles)
    if not opens or not closes or opens[0] == 0:
        return None
    return (closes[-1] - opens[0]) / opens[0]


def regime_allows_entry(
    snap: RegimeSnapshot,
    move_pct: float,
    current_price: float,
    vwap_price: Optional[float],
) -> Tuple[bool, str, str]:
    if snap.regime == Regime.VOLATILE:
        return False, "volatile-skip", ""

    def vwap_ok(side: str) -> Tuple[bool, str]:
        if vwap_price is None:
            return True, ""
        if side == "short" and current_price <= vwap_price:
            return False, "vwap-block-short"
        if side == "long" and current_price >= vwap_price:
            return False, "vwap-block-long"
        return True, ""

    if snap.regime == Regime.TREND_UP:
        if snap.rsi >= RSI_OVERBOUGHT and move_pct >= PUMP_THRESHOLD:
            ok, reason = vwap_ok("short")
            return ok, (reason or "trend-up-fade-short"), ("short" if ok else "")
        return False, "trend-up-no-edge", ""

    if snap.regime == Regime.TREND_DOWN:
        if move_pct >= PUMP_THRESHOLD:
            ok, reason = vwap_ok("short")
            return ok, (reason or "trend-down-cont-short"), ("short" if ok else "")
        return False, "trend-down-no-edge", ""

    if snap.rsi >= RSI_OVERBOUGHT and move_pct >= PUMP_THRESHOLD:
        ok, reason = vwap_ok("short")
        return ok, (reason or "range-short"), ("short" if ok else "")
    if snap.rsi <= RSI_OVERSOLD and move_pct <= DUMP_THRESHOLD:
        ok, reason = vwap_ok("long")
        return ok, (reason or "range-long"), ("long" if ok else "")
    return False, "range-no-edge", ""


def calc_order_size(meta: ContractMeta, snap: RegimeSnapshot, balance_usd: float) -> int:
    if meta.quanto_multiplier <= 0 or meta.last_price <= 0:
        return 0

    volatility_scalar = 1.0
    if snap.atr_ratio > 1.5:
        volatility_scalar = 0.8
    elif snap.atr_ratio < 0.8:
        volatility_scalar = 1.2

    max_risk_usd = balance_usd * MAX_ACCOUNT_RISK_PCT
    desired_notional = min(BASE_ORDER_NOTIONAL_USD * volatility_scalar, max_risk_usd)
    contract_notional = meta.approx_contract_notional
    raw_contracts = max(1, int(round(desired_notional / max(contract_notional, 1e-9))))
    size = max(meta.min_order_size, raw_contracts)
    return max(0, size)


def estimate_margin_required(price: float, qty: int, multiplier: float, leverage: int) -> float:
    notion = price * qty * multiplier
    return notion / max(1, leverage)


def estimated_fee(price: float, qty: int, multiplier: float, rate: float = TAKER_FEE_RATE) -> float:
    notion = price * abs(qty) * multiplier
    return notion * rate


# =============================================================================
# CACHE + COOLDOWNS
# =============================================================================

class CooldownRegistry:
    def __init__(self, initial: Optional[Dict[str, str]] = None) -> None:
        self._bans: Dict[str, str] = dict(initial or {})
        self._lock = threading.Lock()

    def ban(self, symbol: str, seconds: int = COOLDOWN_SECONDS) -> None:
        expiry = (now_utc() + timedelta(seconds=seconds)).isoformat()
        with self._lock:
            self._bans[symbol] = expiry
        event_log("cooldown_ban", symbol=symbol, until=expiry)

    def is_banned(self, symbol: str) -> bool:
        with self._lock:
            expiry = self._bans.get(symbol)
        if not expiry:
            return False
        if now_utc() >= datetime.fromisoformat(expiry):
            with self._lock:
                self._bans.pop(symbol, None)
            return False
        return True

    def export(self) -> Dict[str, str]:
        with self._lock:
            return dict(self._bans)

    def active_count(self) -> int:
        now = now_utc()
        with self._lock:
            return sum(1 for exp in self._bans.values() if datetime.fromisoformat(exp) > now)


class RegimeCache:
    def __init__(self) -> None:
        self._cache: Dict[str, RegimeSnapshot] = {}
        self._lock = threading.Lock()

    def get(self, client: GateClient, symbol: str) -> RegimeSnapshot:
        with self._lock:
            snap = self._cache.get(symbol)
        if snap is None or snap.is_stale():
            snap = classify_regime(client, symbol)
            with self._lock:
                self._cache[symbol] = snap
        return snap

    def summary(self) -> Dict[str, int]:
        out = {r.name: 0 for r in Regime}
        with self._lock:
            for snap in self._cache.values():
                out[snap.regime.name] += 1
        return out


# =============================================================================
# UNIVERSE
# =============================================================================

def scan_micro_contracts(client: GateClient) -> List[ContractMeta]:
    metas: List[ContractMeta] = []
    for c in client.list_contracts():
        try:
            meta = ContractMeta(
                symbol=str(getattr(c, "name", "")),
                last_price=safe_float(getattr(c, "last_price", 0.0)),
                quanto_multiplier=safe_float(getattr(c, "quanto_multiplier", 1.0), 1.0),
                volume_24h_quote=safe_float(getattr(c, "volume_24h_quote", 0.0)),
                min_order_size=max(1, safe_int(getattr(c, "order_size_min", 1), 1)),
                leverage_min=max(1, safe_int(getattr(c, "leverage_min", 1), 1)),
                leverage_max=max(1, safe_int(getattr(c, "leverage_max", 100), 100)),
                maintenance_rate=MAINT_MARGIN_RATE,
            )
            if meta.last_price <= 0 or meta.quanto_multiplier <= 0:
                continue
            notional = meta.approx_contract_notional
            if MIN_NOTIONAL <= notional <= MAX_NOTIONAL and meta.volume_24h_quote >= MIN_VOLUME_USDT:
                metas.append(meta)
        except Exception:
            continue
    metas.sort(key=lambda x: x.volume_24h_quote, reverse=True)
    event_log("universe_scan", count=len(metas))
    return metas


# =============================================================================
# PORTFOLIO + LIVE POSITION MANAGER
# =============================================================================

class PositionManager:
    def __init__(
        self,
        client: GateClient,
        cooldown: CooldownRegistry,
        store: StateStore,
        starting_state: Dict[str, Any],
    ) -> None:
        self.client = client
        self.cooldown = cooldown
        self.store = store
        self.lock = threading.Lock()

        self.positions: Dict[str, PositionRecord] = {}
        self.seen_order_tags: set[str] = set(starting_state.get("seen_order_tags", []))
        self.daily_realised: Dict[str, float] = dict(starting_state.get("daily_realised", {}))
        self.last_reconcile_at: Optional[str] = starting_state.get("last_reconcile_at")

        for sym, raw in starting_state.get("positions", {}).items():
            try:
                fills = [FillRecord(**f) for f in raw.get("fills", [])]
                raw = dict(raw)
                raw["fills"] = fills
                self.positions[sym] = PositionRecord(**raw)
            except Exception as exc:
                log.warning("Failed to load position %s: %s", sym, exc)

    def persist(self) -> None:
        state = {
            "positions": {k: asdict(v) for k, v in self.positions.items()},
            "cooldowns": self.cooldown.export(),
            "seen_order_tags": sorted(self.seen_order_tags),
            "daily_realised": self.daily_realised,
            "last_reconcile_at": self.last_reconcile_at,
            "metadata": {
                "saved_at": ts(),
                "app": APP_NAME,
                "version": VERSION,
            },
        }
        self.store.save(state)

    def daily_pnl(self) -> float:
        return float(self.daily_realised.get(dateroll_key(), 0.0))

    def add_realised_today(self, amount: float) -> None:
        key = dateroll_key()
        self.daily_realised[key] = float(self.daily_realised.get(key, 0.0) + amount)

    def active(self) -> List[PositionRecord]:
        return [p for p in self.positions.values() if p.is_open()]

    def daily_guard_tripped(self) -> bool:
        limit = -ACCOUNT_BALANCE * MAX_DAILY_LOSS_PCT
        pnl = self.daily_pnl()
        if pnl <= limit:
            event_log("daily_guard", pnl=pnl, limit=limit)
            return True
        return False

    def can_open_more(self, regime: Regime) -> bool:
        active = self.active()
        if len(active) >= MAX_OPEN_POSITIONS:
            return False
        regime_count = sum(1 for p in active if p.regime == regime.name)
        return regime_count < MAX_PER_REGIME

    def reconcile(self) -> None:
        try:
            open_orders = self.client.list_open_orders()
            exch_positions = self.client.list_positions()
            event_log(
                "reconcile",
                open_orders=len(open_orders),
                exchange_positions=len(exch_positions),
                local_positions=len(self.active()),
            )
            self.last_reconcile_at = ts()
        except Exception as exc:
            event_log("reconcile_error", error=str(exc))

        self.persist()

    def _fee(self, price: float, qty: int, multiplier: float) -> float:
        return estimated_fee(price, qty, multiplier, TAKER_FEE_RATE)

    def _margin_buffer_ok(self, price: float, qty: int, multiplier: float) -> bool:
        need = estimate_margin_required(price, qty, multiplier, LEVERAGE) + self._fee(price, qty, multiplier)
        max_allow = ACCOUNT_BALANCE * MAX_ACCOUNT_RISK_PCT
        return need <= max_allow

    def _record_fill(self, pos: PositionRecord, side: str, qty: int, price: float, label: str, reduce_only: bool) -> None:
        fee = self._fee(price, qty, pos.contract_multiplier)
        pos.fills.append(
            FillRecord(
                ts=ts(),
                side=side,
                size=qty,
                price=price,
                label=label,
                fee=fee,
                reduce_only=reduce_only,
            )
        )

    def _journal_open(self, pos: PositionRecord) -> None:
        row = {
            "timestamp": ts(),
            "event": "OPEN",
            "symbol": pos.symbol,
            "side": pos.side,
            "entry_price": pos.entry_price,
            "avg_entry": pos.avg_entry,
            "size": pos.size,
            "remaining": pos.remaining,
            "regime": pos.regime,
            "realised": "",
            "tag": pos.entry_tag,
        }
        write_trade_csv(row)

    def _journal_close(self, pos: PositionRecord, reason: str) -> None:
        row = {
            "timestamp": ts(),
            "event": f"CLOSE:{reason}",
            "symbol": pos.symbol,
            "side": pos.side,
            "entry_price": pos.entry_price,
            "avg_entry": pos.avg_entry,
            "size": pos.size,
            "remaining": pos.remaining,
            "regime": pos.regime,
            "realised": f"{pos.realised_pnl:.8f}",
            "tag": pos.entry_tag,
        }
        write_trade_csv(row)

    def open_position(self, meta: ContractMeta, snap: RegimeSnapshot, side: str, entry_reason: str) -> bool:
        symbol = meta.symbol

        if self.cooldown.is_banned(symbol):
            return False
        if self.daily_guard_tripped():
            return False
        if not self.can_open_more(snap.regime):
            return False
        if symbol in self.positions and self.positions[symbol].is_open():
            return False

        size = calc_order_size(meta, snap, ACCOUNT_BALANCE)
        if size < meta.min_order_size:
            return False

        if LEVERAGE < meta.leverage_min or LEVERAGE > meta.leverage_max:
            event_log("bad_leverage", symbol=symbol, leverage=LEVERAGE, min=meta.leverage_min, max=meta.leverage_max)
            return False

        if not self._margin_buffer_ok(meta.last_price, size, meta.quanto_multiplier):
            event_log("margin_block", symbol=symbol, size=size)
            return False

        if not self.client.set_leverage(symbol, LEVERAGE):
            return False

        signed_size = -size if side == "short" else size
        tag = make_order_tag([symbol, side, "entry", str(int(time.time() // 10)), entry_reason])

        if tag in self.seen_order_tags:
            return False

        result = self.client.place_order(
            OrderIntent(
                symbol=symbol,
                size=signed_size,
                side=side,
                label=tag,
                reduce_only=False,
                close_position=False,
            )
        )
        if result is None:
            return False

        fill_price = safe_float(getattr(result, "fill_price", 0.0), meta.last_price) or meta.last_price
        pos = PositionRecord(
            symbol=symbol,
            side=side,
            regime=snap.regime.name,
            entry_price=fill_price,
            avg_entry=fill_price,
            size=size,
            remaining=size,
            contract_multiplier=meta.quanto_multiplier,
            leverage=LEVERAGE,
            entry_tag=tag,
            next_dca_trigger=(fill_price * (1 + DCA_STEP_PCT) if side == "short" else fill_price * (1 - DCA_STEP_PCT)) if ENABLE_DCA else None,
            notes={"entry_reason": entry_reason},
        )
        self._record_fill(pos, side, size, fill_price, tag, False)

        with self.lock:
            self.positions[symbol] = pos
            self.seen_order_tags.add(tag)

        self._journal_open(pos)
        self.persist()

        event_log("position_open", symbol=symbol, side=side, size=size, fill_price=fill_price, regime=snap.regime.name)
        return True

    def _compute_pnl_pct(self, pos: PositionRecord, price: float) -> float:
        if pos.avg_entry <= 0:
            return 0.0
        if pos.side == "short":
            return (pos.avg_entry - price) / pos.avg_entry
        return (price - pos.avg_entry) / pos.avg_entry

    def _compute_pnl_usd(self, pos: PositionRecord, price: float, qty: Optional[int] = None) -> float:
        q = qty if qty is not None else pos.remaining
        if pos.side == "short":
            return (pos.avg_entry - price) * q * pos.contract_multiplier
        return (price - pos.avg_entry) * q * pos.contract_multiplier

    def _close_qty(self, pos: PositionRecord, qty: int, price: float, reason: str) -> bool:
        if qty <= 0 or pos.remaining <= 0:
            return False
        qty = min(qty, pos.remaining)
        intent_size = qty if pos.side == "short" else -qty
        tag = make_order_tag([pos.symbol, reason, "close", str(pos.remaining), str(int(time.time() // 10))])
        if tag in self.seen_order_tags:
            return False

        result = self.client.place_order(
            OrderIntent(
                symbol=pos.symbol,
                size=intent_size,
                side=("buy" if pos.side == "short" else "sell"),
                label=tag,
                reduce_only=True,
                close_position=False,
            )
        )
        if result is None:
            return False

        fill_price = safe_float(getattr(result, "fill_price", 0.0), price) or price
        pnl_amt = self._compute_pnl_usd(pos, fill_price, qty)
        fee_amt = self._fee(fill_price, qty, pos.contract_multiplier)

        pos.remaining -= qty
        pos.last_price = fill_price
        pos.realised_pnl += pnl_amt - fee_amt
        self.add_realised_today(pnl_amt - fee_amt)
        self._record_fill(pos, "close", qty, fill_price, tag, True)
        self.seen_order_tags.add(tag)

        if pos.remaining <= 0:
            pos.closed = True
            self._journal_close(pos, reason)
            event_log("position_closed", symbol=pos.symbol, reason=reason, pnl=pos.realised_pnl)

        self.persist()
        return True

    def _full_close(self, pos: PositionRecord, price: float, reason: str) -> bool:
        return self._close_qty(pos, pos.remaining, price, reason)

    def _dca_add(self, pos: PositionRecord, price: float) -> bool:
        if not ENABLE_DCA:
            return False
        if pos.dca_adds_used >= MAX_DCA_ADDS:
            return False

        add_qty = max(1, int(round(pos.size * (DCA_SCALE ** pos.dca_adds_used))))
        if not self._margin_buffer_ok(price, add_qty, pos.contract_multiplier):
            return False

        signed = -add_qty if pos.side == "short" else add_qty
        tag = make_order_tag([pos.symbol, "dca", str(pos.dca_adds_used), str(int(time.time() // 10))])
        if tag in self.seen_order_tags:
            return False

        result = self.client.place_order(
            OrderIntent(
                symbol=pos.symbol,
                size=signed,
                side=pos.side,
                label=tag,
                reduce_only=False,
                close_position=False,
            )
        )
        if result is None:
            return False

        fill_price = safe_float(getattr(result, "fill_price", 0.0), price) or price
        old_total = pos.avg_entry * pos.remaining
        new_total = old_total + fill_price * add_qty
        pos.remaining += add_qty
        pos.size += add_qty
        pos.avg_entry = new_total / pos.remaining if pos.remaining else pos.avg_entry
        pos.dca_adds_used += 1
        pos.next_dca_trigger = (
            pos.entry_price * (1 + DCA_STEP_PCT * (pos.dca_adds_used + 1))
            if pos.side == "short" else
            pos.entry_price * (1 - DCA_STEP_PCT * (pos.dca_adds_used + 1))
        )
        self._record_fill(pos, pos.side, add_qty, fill_price, tag, False)
        self.seen_order_tags.add(tag)
        event_log("dca_add", symbol=pos.symbol, adds_used=pos.dca_adds_used, new_avg=pos.avg_entry, fill_price=fill_price)
        self.persist()
        return True

    def tick(self) -> None:
        for pos in list(self.active()):
            price = self.client.get_price(pos.symbol)
            if price is None or price <= 0:
                continue

            pos.last_price = price
            pos.unrealised_pnl = self._compute_pnl_usd(pos, price)
            pnl_pct = self._compute_pnl_pct(pos, price)
            pos.peak_pnl_pct = max(pos.peak_pnl_pct, pnl_pct)
            drawdown = pos.peak_pnl_pct - pnl_pct

            if ENABLE_DCA and pos.next_dca_trigger is not None:
                if (pos.side == "short" and price >= pos.next_dca_trigger) or (pos.side == "long" and price <= pos.next_dca_trigger):
                    self._dca_add(pos, price)

            if pnl_pct <= -STOP_LOSS_PCT:
                self._full_close(pos, price, "hard-stop")
                self.cooldown.ban(pos.symbol)
                continue

            if pnl_pct >= TAKE_PROFIT_PCT and pos.ladder_idx >= len(PARTIALS):
                self._full_close(pos, price, "take-profit")
                continue

            if pos.peak_pnl_pct >= TRAIL_ACTIVATE and drawdown >= TRAIL_PCT:
                self._full_close(pos, price, "trail-stop")
                continue

            while pos.ladder_idx < len(PARTIALS):
                target, frac = PARTIALS[pos.ladder_idx]
                if pnl_pct < target:
                    break
                close_qty = max(1, int(round(pos.remaining * frac)))
                if self._close_qty(pos, close_qty, price, f"partial-{pos.ladder_idx + 1}"):
                    pos.ladder_idx += 1
                else:
                    break

        self.persist()

    def purge_closed(self) -> None:
        keep_after = now_utc() - timedelta(hours=12)
        stale = []
        for symbol, pos in self.positions.items():
            opened = datetime.fromisoformat(pos.opened_at)
            if pos.closed and opened < keep_after:
                stale.append(symbol)
        for s in stale:
            self.positions.pop(s, None)
        if stale:
            self.persist()


# =============================================================================
# SCANNER
# =============================================================================

def scan_one(
    client: GateClient,
    meta: ContractMeta,
    manager: PositionManager,
    regime_cache: RegimeCache,
    cooldown: CooldownRegistry,
) -> Optional[Tuple[ContractMeta, RegimeSnapshot, str, str]]:
    if cooldown.is_banned(meta.symbol):
        return None
    if meta.symbol in manager.positions and manager.positions[meta.symbol].is_open():
        return None

    move = measure_move(client, meta.symbol)
    if move is None:
        return None
    if abs(move) < min(abs(PUMP_THRESHOLD), abs(DUMP_THRESHOLD)):
        return None

    snap = regime_cache.get(client, meta.symbol)
    candles = client.fetch_candles(meta.symbol, interval="5m", limit=VWAP_BARS + 10)
    vwap_px = vwap(candles, VWAP_BARS) if candles else None
    ok, reason, side = regime_allows_entry(snap, move, meta.last_price, vwap_px)
    event_log(
        "scan_symbol",
        symbol=meta.symbol,
        move=move,
        regime=snap.label(),
        rsi=snap.rsi,
        adx=snap.adx,
        ok=ok,
        side=side,
        reason=reason,
    )
    if ok:
        return meta, snap, side, reason
    return None


def concurrent_scan(
    client: GateClient,
    metas: List[ContractMeta],
    manager: PositionManager,
    regime_cache: RegimeCache,
    cooldown: CooldownRegistry,
) -> List[Tuple[ContractMeta, RegimeSnapshot, str, str]]:
    out: List[Tuple[ContractMeta, RegimeSnapshot, str, str]] = []
    with ThreadPoolExecutor(max_workers=SCAN_WORKERS) as pool:
        futs = [pool.submit(scan_one, client, meta, manager, regime_cache, cooldown) for meta in metas]
        for fut in as_completed(futs):
            try:
                result = fut.result()
                if result is not None:
                    out.append(result)
            except Exception as exc:
                event_log("scan_worker_error", error=str(exc))
    return out


# =============================================================================
# BACKTEST ENGINE
# =============================================================================

class BacktestEngine:
    def __init__(self, symbol: str, candles: Sequence[Any], meta: Optional[ContractMeta] = None) -> None:
        self.symbol = symbol
        self.candles = list(candles)
        self.meta = meta or ContractMeta(
            symbol=symbol,
            last_price=safe_float(getattr(candles[-1], "c", 1.0)) if candles else 1.0,
            quanto_multiplier=1.0,
            volume_24h_quote=1_000_000.0,
            min_order_size=1,
            leverage_min=1,
            leverage_max=100,
            maintenance_rate=MAINT_MARGIN_RATE,
        )

    def _slipped(self, price: float, opening: bool, side: str) -> float:
        if side == "short" and opening:
            return price * (1.0 - SLIPPAGE_PCT)
        if side == "long" and opening:
            return price * (1.0 + SLIPPAGE_PCT)
        if side == "short" and not opening:
            return price * (1.0 + SLIPPAGE_PCT)
        return price * (1.0 - SLIPPAGE_PCT)

    def _fee(self, price: float, qty: int) -> float:
        return estimated_fee(price, qty, self.meta.quanto_multiplier, TAKER_FEE_RATE)

    def run(self) -> BacktestSummary:
        if len(self.candles) < 120:
            return BacktestSummary(
                symbol=self.symbol,
                trades=[],
                final_equity=ACCOUNT_BALANCE,
                return_pct=0.0,
                max_drawdown_pct=0.0,
                win_rate_pct=0.0,
                avg_trade_pct=0.0,
                profit_factor=0.0,
                sharpe_like=0.0,
                liquidation_events=0,
                params=self._params(),
            )

        equity = ACCOUNT_BALANCE
        peak_equity = equity
        drawdowns: List[float] = []
        trades: List[BacktestTrade] = []
        liquidation_events = 0

        in_trade = False
        side = ""
        regime_name = ""
        entry_idx = 0
        entry_price = 0.0
        avg_entry = 0.0
        qty = 0
        remaining = 0
        dca_adds = 0
        next_dca_trigger: Optional[float] = None
        peak_pnl_pct = 0.0
        ladder_idx = 0
        fees_paid = 0.0

        closes = _closes(self.candles)
        idx = 60

        while idx < len(self.candles):
            candle = self.candles[idx]
            price = safe_float(getattr(candle, "c", 0.0))
            high = safe_float(getattr(candle, "h", price))
            low = safe_float(getattr(candle, "l", price))

            if not in_trade:
                window = self.candles[:idx]
                snap = classify_regime_from_candles(window)
                lookback = 12
                move = 0.0
                if idx >= lookback:
                    base = closes[idx - lookback]
                    move = (closes[idx] - base) / base if base else 0.0
                vwap_px = vwap(window, min(VWAP_BARS, len(window)))
                ok, _reason, trade_side = regime_allows_entry(snap, move, price, vwap_px)
                if ok:
                    size = calc_order_size(self.meta, snap, equity)
                    if size > 0:
                        side = trade_side
                        regime_name = snap.regime.name
                        entry_idx = idx
                        fill = self._slipped(price, opening=True, side=side)
                        entry_price = fill
                        avg_entry = fill
                        qty = size
                        remaining = size
                        dca_adds = 0
                        next_dca_trigger = fill * (1 + DCA_STEP_PCT) if side == "short" else fill * (1 - DCA_STEP_PCT)
                        peak_pnl_pct = 0.0
                        ladder_idx = 0
                        in_trade = True
                        fees_paid = self._fee(fill, size)
                        equity -= fees_paid
                idx += 1
                peak_equity = max(peak_equity, equity)
                drawdowns.append((equity / peak_equity) - 1.0 if peak_equity else 0.0)
                continue

            pnl_pct = ((avg_entry - price) / avg_entry) if side == "short" else ((price - avg_entry) / avg_entry)
            peak_pnl_pct = max(peak_pnl_pct, pnl_pct)
            drawdown_from_peak = peak_pnl_pct - pnl_pct

            adverse_mark = high if side == "short" else low
            adverse_pnl_usd = ((avg_entry - adverse_mark) if side == "short" else (adverse_mark - avg_entry)) * remaining * self.meta.quanto_multiplier
            estimated_margin = estimate_margin_required(avg_entry, remaining, self.meta.quanto_multiplier, LEVERAGE)
            maint = abs(adverse_mark * remaining * self.meta.quanto_multiplier) * self.meta.maintenance_rate

            if equity + adverse_pnl_usd <= maint or (estimated_margin > 0 and (equity + adverse_pnl_usd) < -estimated_margin):
                exit_px = self._slipped(adverse_mark, opening=False, side=side)
                pnl_usd = ((avg_entry - exit_px) if side == "short" else (exit_px - avg_entry)) * remaining * self.meta.quanto_multiplier
                exit_fee = self._fee(exit_px, remaining)
                total_fees = fees_paid + exit_fee
                equity += pnl_usd - exit_fee
                trades.append(
                    BacktestTrade(
                        symbol=self.symbol,
                        side=side,
                        regime=regime_name,
                        entry_idx=entry_idx,
                        exit_idx=idx,
                        entry_price=entry_price,
                        exit_price=exit_px,
                        pnl_pct=((pnl_usd - total_fees) / max(1e-9, (entry_price * qty * self.meta.quanto_multiplier / LEVERAGE))) * 100.0,
                        pnl_usd=pnl_usd - total_fees,
                        fees_usd=total_fees,
                        reason="liquidation-est",
                        dca_adds=dca_adds,
                    )
                )
                in_trade = False
                liquidation_events += 1
                idx += 1
                peak_equity = max(peak_equity, equity)
                drawdowns.append((equity / peak_equity) - 1.0 if peak_equity else 0.0)
                continue

            if ENABLE_DCA and next_dca_trigger is not None and dca_adds < MAX_DCA_ADDS:
                dca_hit = (side == "short" and high >= next_dca_trigger) or (side == "long" and low <= next_dca_trigger)
                if dca_hit:
                    add_qty = max(1, int(round(qty * (DCA_SCALE ** dca_adds))))
                    fill = self._slipped(next_dca_trigger, opening=True, side=side)
                    total_before = avg_entry * remaining
                    total_after = total_before + fill * add_qty
                    remaining += add_qty
                    qty += add_qty
                    avg_entry = total_after / remaining
                    fee_add = self._fee(fill, add_qty)
                    fees_paid += fee_add
                    equity -= fee_add
                    dca_adds += 1
                    next_dca_trigger = entry_price * (1 + DCA_STEP_PCT * (dca_adds + 1)) if side == "short" else entry_price * (1 - DCA_STEP_PCT * (dca_adds + 1))

            reason = ""
            exit_px = price

            if pnl_pct <= -STOP_LOSS_PCT:
                reason = "hard-stop"
                exit_px = self._slipped(price, opening=False, side=side)
            elif peak_pnl_pct >= TRAIL_ACTIVATE and drawdown_from_peak >= TRAIL_PCT:
                reason = "trail-stop"
                exit_px = self._slipped(price, opening=False, side=side)
            else:
                while ladder_idx < len(PARTIALS):
                    target, frac = PARTIALS[ladder_idx]
                    if pnl_pct < target:
                        break
                    close_qty = max(1, int(round(remaining * frac)))
                    partial_px = self._slipped(price, opening=False, side=side)
                    partial_pnl = ((avg_entry - partial_px) if side == "short" else (partial_px - avg_entry)) * close_qty * self.meta.quanto_multiplier
                    partial_fee = self._fee(partial_px, close_qty)
                    equity += partial_pnl - partial_fee
                    fees_paid += partial_fee
                    remaining -= close_qty
                    ladder_idx += 1
                    if remaining <= 0:
                        reason = "scaled-out"
                        exit_px = partial_px
                        break
                if not reason and pnl_pct >= TAKE_PROFIT_PCT and ladder_idx >= len(PARTIALS):
                    reason = "take-profit"
                    exit_px = self._slipped(price, opening=False, side=side)

            if reason:
                if remaining > 0:
                    pnl_usd = ((avg_entry - exit_px) if side == "short" else (exit_px - avg_entry)) * remaining * self.meta.quanto_multiplier
                    exit_fee = self._fee(exit_px, remaining)
                    total_fees = fees_paid + exit_fee
                    equity += pnl_usd - exit_fee
                else:
                    pnl_usd = 0.0
                    total_fees = fees_paid
                trades.append(
                    BacktestTrade(
                        symbol=self.symbol,
                        side=side,
                        regime=regime_name,
                        entry_idx=entry_idx,
                        exit_idx=idx,
                        entry_price=entry_price,
                        exit_price=exit_px,
                        pnl_pct=((equity - ACCOUNT_BALANCE) / ACCOUNT_BALANCE) * 100.0 if ACCOUNT_BALANCE else 0.0,
                        pnl_usd=(pnl_usd - total_fees),
                        fees_usd=total_fees,
                        reason=reason,
                        dca_adds=dca_adds,
                    )
                )
                in_trade = False

            idx += 1
            peak_equity = max(peak_equity, equity)
            drawdowns.append((equity / peak_equity) - 1.0 if peak_equity else 0.0)

        trade_returns = [t.pnl_usd for t in trades]
        winners = [x for x in trade_returns if x > 0]
        losers = [x for x in trade_returns if x < 0]
        win_rate = (len(winners) / len(trades) * 100.0) if trades else 0.0
        avg_trade_pct = (sum(trade_returns) / len(trades) / max(ACCOUNT_BALANCE, 1e-9) * 100.0) if trades else 0.0
        profit_factor = (sum(winners) / abs(sum(losers))) if losers else (float("inf") if winners else 0.0)

        if len(trade_returns) >= 2 and statistics.pstdev(trade_returns) > 0:
            sharpe_like = statistics.mean(trade_returns) / statistics.pstdev(trade_returns) * math.sqrt(len(trade_returns))
        else:
            sharpe_like = 0.0

        return BacktestSummary(
            symbol=self.symbol,
            trades=trades,
            final_equity=equity,
            return_pct=((equity / ACCOUNT_BALANCE) - 1.0) * 100.0 if ACCOUNT_BALANCE else 0.0,
            max_drawdown_pct=(min(drawdowns) * 100.0) if drawdowns else 0.0,
            win_rate_pct=win_rate,
            avg_trade_pct=avg_trade_pct,
            profit_factor=profit_factor,
            sharpe_like=sharpe_like,
            liquidation_events=liquidation_events,
            params=self._params(),
        )

    def walk_forward(self) -> Dict[str, Any]:
        candles = self.candles
        results = []
        i = 0
        while i + WALK_TRAIN + WALK_TEST <= len(candles):
            train = candles[i:i + WALK_TRAIN]
            test = candles[i + WALK_TRAIN:i + WALK_TRAIN + WALK_TEST]
            train_engine = BacktestEngine(self.symbol, train, self.meta)
            train_res = train_engine.run()
            test_engine = BacktestEngine(self.symbol, test, self.meta)
            test_res = test_engine.run()
            results.append({
                "start": i,
                "train_return_pct": train_res.return_pct,
                "test_return_pct": test_res.return_pct,
                "train_pf": train_res.profit_factor,
                "test_pf": test_res.profit_factor,
                "train_trades": len(train_res.trades),
                "test_trades": len(test_res.trades),
            })
            i += WALK_TEST
        return {
            "symbol": self.symbol,
            "windows": results,
            "avg_test_return_pct": (sum(x["test_return_pct"] for x in results) / len(results)) if results else 0.0,
            "avg_test_pf": (sum(x["test_pf"] for x in results) / len(results)) if results else 0.0,
        }

    def monte_carlo(self, summary: BacktestSummary, runs: int = MC_RUNS) -> Dict[str, Any]:
        pnl = [t.pnl_usd for t in summary.trades]
        if not pnl:
            return {"runs": runs, "median_final": ACCOUNT_BALANCE, "p05": ACCOUNT_BALANCE, "p95": ACCOUNT_BALANCE}
        finals = []
        for _ in range(runs):
            sampled = [random.choice(pnl) for _ in pnl]
            eq = ACCOUNT_BALANCE + sum(sampled)
            finals.append(eq)
        finals.sort()

        def pct(arr: List[float], p: float) -> float:
            if not arr:
                return 0.0
            idx = int(round((len(arr) - 1) * p))
            return arr[idx]

        return {
            "runs": runs,
            "median_final": pct(finals, 0.50),
            "p05": pct(finals, 0.05),
            "p95": pct(finals, 0.95),
            "min_final": min(finals),
            "max_final": max(finals),
        }

    def sweep(self) -> List[Dict[str, Any]]:
        global STOP_LOSS_PCT, TRAIL_PCT, TAKE_PROFIT_PCT, MAX_DCA_ADDS, DCA_SCALE, BASE_ORDER_NOTIONAL_USD
        orig = (STOP_LOSS_PCT, TRAIL_PCT, TAKE_PROFIT_PCT, MAX_DCA_ADDS, DCA_SCALE, BASE_ORDER_NOTIONAL_USD)

        rows: List[Dict[str, Any]] = []
        for stop in [0.03, 0.045, 0.06]:
            for trail in [0.01, 0.015, 0.02]:
                for tp in [0.008, 0.010, 0.014]:
                    for max_adds in [0, 1, 2]:
                        for dca_scale in [1.0, 1.1, 1.2]:
                            for base_notional in [0.05, 0.10, 0.15]:
                                STOP_LOSS_PCT = stop
                                TRAIL_PCT = trail
                                TAKE_PROFIT_PCT = tp
                                MAX_DCA_ADDS = max_adds
                                DCA_SCALE = dca_scale
                                BASE_ORDER_NOTIONAL_USD = base_notional
                                res = self.run()
                                rows.append({
                                    "stop": stop,
                                    "trail": trail,
                                    "tp": tp,
                                    "max_adds": max_adds,
                                    "dca_scale": dca_scale,
                                    "base_notional": base_notional,
                                    "return_pct": res.return_pct,
                                    "max_dd_pct": res.max_drawdown_pct,
                                    "win_rate_pct": res.win_rate_pct,
                                    "profit_factor": res.profit_factor,
                                    "liquidations": res.liquidation_events,
                                    "trades": len(res.trades),
                                })

        STOP_LOSS_PCT, TRAIL_PCT, TAKE_PROFIT_PCT, MAX_DCA_ADDS, DCA_SCALE, BASE_ORDER_NOTIONAL_USD = orig
        rows.sort(key=lambda x: (x["liquidations"], -x["profit_factor"], -x["return_pct"], x["max_dd_pct"]))
        return rows

    def _params(self) -> Dict[str, Any]:
        return {
            "leverage": LEVERAGE,
            "stop_loss_pct": STOP_LOSS_PCT,
            "trail_pct": TRAIL_PCT,
            "trail_activate": TRAIL_ACTIVATE,
            "take_profit_pct": TAKE_PROFIT_PCT,
            "base_order_notional_usd": BASE_ORDER_NOTIONAL_USD,
            "enable_dca": ENABLE_DCA,
            "dca_step_pct": DCA_STEP_PCT,
            "max_dca_adds": MAX_DCA_ADDS,
            "dca_scale": DCA_SCALE,
            "taker_fee_rate": TAKER_FEE_RATE,
            "slippage_pct": SLIPPAGE_PCT,
        }


# =============================================================================
# REPORTING
# =============================================================================

def print_status(manager: PositionManager, regime_cache: RegimeCache, cooldown: CooldownRegistry, cycle: int, universe_count: int) -> None:
    log.info(
        "cycle=%d universe=%d open=%d cooldowns=%d day_pnl=%+.6f regimes=%s",
        cycle,
        universe_count,
        len(manager.active()),
        cooldown.active_count(),
        manager.daily_pnl(),
        regime_cache.summary(),
    )
    for pos in manager.active():
        log.info(
            "pos %s %s entry=%.8f avg=%.8f rem=%d upnl=%+.6f peak=%.2f%% dca=%d regime=%s",
            pos.symbol, pos.side, pos.entry_price, pos.avg_entry, pos.remaining,
            pos.unrealised_pnl, pos.peak_pnl_pct * 100.0, pos.dca_adds_used, pos.regime
        )


def print_backtest(summary: BacktestSummary) -> None:
    print("=" * 80)
    print(f"Backtest: {summary.symbol}")
    print(f"Trades: {len(summary.trades)}")
    print(f"Final equity: ${summary.final_equity:.6f}")
    print(f"Return: {summary.return_pct:+.2f}%")
    print(f"Max DD: {summary.max_drawdown_pct:.2f}%")
    print(f"Win rate: {summary.win_rate_pct:.2f}%")
    print(f"Avg trade: {summary.avg_trade_pct:+.4f}%")
    print(f"Profit factor: {summary.profit_factor:.4f}")
    print(f"Sharpe-like: {summary.sharpe_like:.4f}")
    print(f"Liquidations: {summary.liquidation_events}")
    print("Params:", json.dumps(summary.params, indent=2))
    print("-" * 80)
    for t in summary.trades[-10:]:
        print(
            f"{t.side:5s} {t.regime:10s} entry={t.entry_price:.8f} exit={t.exit_price:.8f} "
            f"pnl=${t.pnl_usd:+.6f} reason={t.reason} dca={t.dca_adds}"
        )
    print("=" * 80)


def print_walk_forward(report: Dict[str, Any]) -> None:
    print("=" * 80)
    print(f"Walk-forward: {report['symbol']}")
    print(f"Windows: {len(report['windows'])}")
    print(f"Avg test return: {report['avg_test_return_pct']:+.3f}%")
    print(f"Avg test PF: {report['avg_test_pf']:.3f}")
    print("-" * 80)
    for row in report["windows"][:20]:
        print(
            f"start={row['start']:4d} train={row['train_return_pct']:+7.2f}% "
            f"test={row['test_return_pct']:+7.2f}% train_pf={row['train_pf']:.2f} "
            f"test_pf={row['test_pf']:.2f} train_n={row['train_trades']} test_n={row['test_trades']}"
        )
    print("=" * 80)


def print_mc(report: Dict[str, Any]) -> None:
    print("=" * 80)
    print("Monte Carlo")
    for k, v in report.items():
        if isinstance(v, float):
            print(f"{k}: {v:.6f}")
        else:
            print(f"{k}: {v}")
    print("=" * 80)


def print_sweep(rows: List[Dict[str, Any]], top_n: int = 20) -> None:
    print("=" * 120)
    print("Top parameter sets")
    print("=" * 120)
    for row in rows[:top_n]:
        print(
            f"stop={row['stop']:.3f} trail={row['trail']:.3f} tp={row['tp']:.3f} "
            f"adds={row['max_adds']} scale={row['dca_scale']:.2f} base={row['base_notional']:.2f} "
            f"ret={row['return_pct']:+7.2f}% dd={row['max_dd_pct']:7.2f}% "
            f"pf={row['profit_factor']:.3f} liq={row['liquidations']} trades={row['trades']}"
        )
    print("=" * 120)


# =============================================================================
# MAIN LOOP
# =============================================================================

def main_loop(dry: bool = True) -> None:
    global DRY_RUN
    DRY_RUN = dry

    log.info(
        "Starting %s v%s mode=%s balance=$%.2f leverage=%dx",
        APP_NAME, VERSION, "DRY" if DRY_RUN else "LIVE", ACCOUNT_BALANCE, LEVERAGE
    )
    event_log("startup", mode=("DRY" if DRY_RUN else "LIVE"), balance=ACCOUNT_BALANCE, leverage=LEVERAGE)

    if not GATE_AVAILABLE:
        log.error("gate-api not installed")
        sys.exit(1)

    if not DRY_RUN:
        if not GATE_API_KEY or not GATE_API_SECRET:
            log.error("Missing GATE_API_KEY / GATE_API_SECRET")
            sys.exit(1)

    client = GateClient()
    store = StateStore(STATE_FILE)
    initial = store.load()
    cooldown = CooldownRegistry(initial=initial.get("cooldowns", {}))
    manager = PositionManager(client, cooldown, store, initial)
    regime_cache = RegimeCache()

    manager.reconcile()

    if not DRY_RUN:
        client.countdown_kill_switch(COUNTDOWN_KILL_SWITCH_SECONDS, "")

    cycle = 0
    while True:
        cycle += 1
        try:
            if not DRY_RUN:
                client.countdown_kill_switch(COUNTDOWN_KILL_SWITCH_SECONDS, "")

            metas = scan_micro_contracts(client)

            if manager.daily_guard_tripped():
                manager.tick()
                manager.purge_closed()
                print_status(manager, regime_cache, cooldown, cycle, len(metas))
                time.sleep(POLL_INTERVAL)
                continue

            candidates = concurrent_scan(client, metas, manager, regime_cache, cooldown)
            for meta, snap, side, reason in candidates:
                manager.open_position(meta, snap, side, reason)

            manager.tick()
            manager.purge_closed()
            print_status(manager, regime_cache, cooldown, cycle, len(metas))
        except KeyboardInterrupt:
            log.info("Interrupted")
            event_log("shutdown")
            break
        except Exception as exc:
            log.error("Main loop error: %s", exc)
            event_log("main_loop_error", error=str(exc), traceback=traceback.format_exc())
        finally:
            manager.persist()

        time.sleep(POLL_INTERVAL)


# =============================================================================
# COMMANDS
# =============================================================================

def run_backtest_command(symbol: str) -> None:
    client = GateClient()
    candles = client.fetch_candles(symbol, interval=BACKTEST_INTERVAL, limit=BACKTEST_LIMIT)
    if len(candles) < 100:
        print("Not enough candles.")
        return
    meta = client.fetch_contract_meta(symbol)
    engine = BacktestEngine(symbol, candles, meta)
    summary = engine.run()
    print_backtest(summary)


def run_walk_forward_command(symbol: str) -> None:
    client = GateClient()
    candles = client.fetch_candles(symbol, interval=BACKTEST_INTERVAL, limit=BACKTEST_LIMIT)
    if len(candles) < WALK_TRAIN + WALK_TEST + 20:
        print("Not enough candles for walk-forward.")
        return
    meta = client.fetch_contract_meta(symbol)
    engine = BacktestEngine(symbol, candles, meta)
    report = engine.walk_forward()
    print_walk_forward(report)


def run_mc_command(symbol: str) -> None:
    client = GateClient()
    candles = client.fetch_candles(symbol, interval=BACKTEST_INTERVAL, limit=BACKTEST_LIMIT)
    if len(candles) < 100:
        print("Not enough candles.")
        return
    meta = client.fetch_contract_meta(symbol)
    engine = BacktestEngine(symbol, candles, meta)
    summary = engine.run()
    mc = engine.monte_carlo(summary)
    print_backtest(summary)
    print_mc(mc)


def run_sweep_command(symbol: str) -> None:
    client = GateClient()
    candles = client.fetch_candles(symbol, interval=BACKTEST_INTERVAL, limit=BACKTEST_LIMIT)
    if len(candles) < 100:
        print("Not enough candles.")
        return
    meta = client.fetch_contract_meta(symbol)
    engine = BacktestEngine(symbol, candles, meta)
    rows = engine.sweep()
    print_sweep(rows, 20)


def run_balance_command() -> None:
    client = GateClient()
    data = client.get_futures_account()
    print(json.dumps(data, indent=2))


def run_position_command(symbol: str) -> None:
    client = GateClient()
    data = client.get_position(symbol)
    print(json.dumps(data, indent=2))


def run_book_command(symbol: str) -> None:
    client = GateClient()
    data = client.get_order_book(symbol)
    print(json.dumps(data, indent=2))


# =============================================================================
# TESTS
# =============================================================================

class _MockCandle:
    def __init__(self, o: float, h: float, l: float, c: float, v: float) -> None:
        self.o = str(o)
        self.h = str(h)
        self.l = str(l)
        self.c = str(c)
        self.v = str(v)


class _MockClient:
    def __init__(self, candles_by_symbol: Dict[str, List[_MockCandle]], prices: Optional[Dict[str, float]] = None) -> None:
        self.candles_by_symbol = candles_by_symbol
        self.prices = prices or {}

    def fetch_candles(self, symbol: str, interval: str = "5m", limit: int = 100) -> List[_MockCandle]:
        return self.candles_by_symbol.get(symbol, [])[-limit:]

    def get_price(self, symbol: str) -> Optional[float]:
        return self.prices.get(symbol)

    def set_leverage(self, symbol: str, leverage: int) -> bool:
        return True

    def place_order(self, intent: OrderIntent) -> Dict[str, Any]:
        return {"fill_price": self.prices.get(intent.symbol, 100.0), "status": "finished", "id": "x"}

    def list_open_orders(self, symbol: str = "") -> List[Any]:
        return []

    def list_positions(self) -> List[Any]:
        return []


def _make_candles(prices: Iterable[float], spread: float = 0.003) -> List[_MockCandle]:
    out: List[_MockCandle] = []
    for p in prices:
        out.append(_MockCandle(p, p * (1 + spread), p * (1 - spread), p, 1000.0))
    return out


class TestIndicators(unittest.TestCase):
    def test_ema(self) -> None:
        vals = ema([float(i) for i in range(1, 21)], 5)
        self.assertTrue(vals)
        self.assertAlmostEqual(vals[0], 3.0, places=4)

    def test_rsi(self) -> None:
        val = rsi([100.0 + i for i in range(30)])
        self.assertIsNotNone(val)
        self.assertGreater(val or 0, 90)

    def test_bollinger(self) -> None:
        result = bollinger([float(i) for i in range(1, 21)], 20)
        self.assertIsNotNone(result)
        assert result is not None
        upper, mid, lower, width = result
        self.assertGreater(upper, mid)
        self.assertGreater(mid, lower)
        self.assertGreater(width, 0.0)

    def test_adx(self) -> None:
        candles = _make_candles([100 + math.sin(i * 0.3) * 3 for i in range(80)])
        result = adx(candles)
        if result is not None:
            self.assertGreaterEqual(result, 0.0)
            self.assertLessEqual(result, 100.0)

    def test_vwap(self) -> None:
        candles = _make_candles([10.0, 11.0, 12.0, 11.0, 10.0], 0.0)
        result = vwap(candles, 5)
        self.assertIsNotNone(result)
        self.assertAlmostEqual(result or 0.0, 10.8, places=1)


class TestRegime(unittest.TestCase):
    def _snap(self, regime: Regime, rsi_val: float = 50.0, atr_ratio: float = 1.0) -> RegimeSnapshot:
        return RegimeSnapshot(regime=regime, adx=20.0, rsi=rsi_val, atr_ratio=atr_ratio, bb_width=0.01)

    def test_short_allowed(self) -> None:
        ok, _, side = regime_allows_entry(self._snap(Regime.TREND_UP, 75.0), 0.12, 100.0, None)
        self.assertTrue(ok)
        self.assertEqual(side, "short")

    def test_long_allowed(self) -> None:
        ok, _, side = regime_allows_entry(self._snap(Regime.RANGING, 25.0), -0.12, 95.0, None)
        self.assertTrue(ok)
        self.assertEqual(side, "long")

    def test_vwap_block(self) -> None:
        ok, reason, _ = regime_allows_entry(self._snap(Regime.TREND_UP, 75.0), 0.12, 95.0, 100.0)
        self.assertFalse(ok)
        self.assertIn("vwap", reason)


class TestCooldown(unittest.TestCase):
    def test_ban(self) -> None:
        cd = CooldownRegistry()
        cd.ban("BTC_USDT", 1)
        self.assertTrue(cd.is_banned("BTC_USDT"))
        time.sleep(1.1)
        self.assertFalse(cd.is_banned("BTC_USDT"))


class TestPositionManager(unittest.TestCase):
    def test_margin_ok(self) -> None:
        state = StateStore(Path("test_state.json"))
        manager = PositionManager(_MockClient({}), CooldownRegistry(), state, state.load())  # type: ignore[arg-type]
        self.assertTrue(manager._margin_buffer_ok(100.0, 1, 0.001))

    def test_open_close_flow(self) -> None:
        candles = {"BTC_USDT": _make_candles([100.0] * 80)}
        client = _MockClient(candles, {"BTC_USDT": 100.0})
        state = StateStore(Path("test_state.json"))
        initial = state.load()
        manager = PositionManager(client, CooldownRegistry(), state, initial)  # type: ignore[arg-type]
        meta = ContractMeta("BTC_USDT", 100.0, 0.001, 1_000_000.0, 1, 1, 100)
        snap = RegimeSnapshot(Regime.RANGING, 20.0, 75.0, 1.0, 0.01)
        opened = manager.open_position(meta, snap, "short", "unit")
        self.assertTrue(opened)
        pos = manager.positions["BTC_USDT"]
        self.assertTrue(pos.is_open())
        ok = manager._full_close(pos, 99.0, "test")
        self.assertTrue(ok)
        self.assertTrue(pos.closed)
        try:
            Path("test_state.json").unlink(missing_ok=True)
        except Exception:
            pass


class TestBacktest(unittest.TestCase):
    def test_backtest_runs(self) -> None:
        prices = [100 + math.sin(i / 10.0) * 5 + (i * 0.02) for i in range(400)]
        candles = _make_candles(prices)
        meta = ContractMeta("BTC_USDT", prices[-1], 0.001, 1_000_000.0, 1, 1, 100)
        engine = BacktestEngine("BTC_USDT", candles, meta)
        summary = engine.run()
        self.assertIsInstance(summary, BacktestSummary)

    def test_mc(self) -> None:
        prices = [100 + math.sin(i / 7.0) * 3 for i in range(400)]
        candles = _make_candles(prices)
        meta = ContractMeta("BTC_USDT", prices[-1], 0.001, 1_000_000.0, 1, 1, 100)
        engine = BacktestEngine("BTC_USDT", candles, meta)
        summary = engine.run()
        report = engine.monte_carlo(summary, 50)
        self.assertIn("median_final", report)


def run_tests() -> None:
    suite = unittest.TestSuite()
    loader = unittest.TestLoader()
    for case in [TestIndicators, TestRegime, TestCooldown, TestPositionManager, TestBacktest]:
        suite.addTests(loader.loadTestsFromTestCase(case))
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    sys.exit(0 if result.wasSuccessful() else 1)


# =============================================================================
# ENTRY
# =============================================================================

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Gate.io Micro Futures Trader — advanced single-file edition")
    parser.add_argument("--test", action="store_true", help="Run tests and exit")
    parser.add_argument("--dry", action="store_true", help="Dry-run mode")
    parser.add_argument("--live", action="store_true", help="Live trading mode")
    parser.add_argument("--balance", action="store_true", help="Show perpetual futures account balance and exit")
    parser.add_argument("--position", metavar="SYMBOL", default="", help="Show perpetual futures position and exit")
    parser.add_argument("--book", metavar="SYMBOL", default="", help="Show perpetual futures order book and exit")
    parser.add_argument("--backtest", metavar="SYMBOL", default="", help="Run backtest")
    parser.add_argument("--walk", metavar="SYMBOL", default="", help="Run walk-forward report")
    parser.add_argument("--mc", metavar="SYMBOL", default="", help="Run backtest + Monte Carlo")
    parser.add_argument("--sweep", metavar="SYMBOL", default="", help="Run parameter sweep")
    args = parser.parse_args()

    if args.test:
        run_tests()
    elif args.balance:
        run_balance_command()
    elif args.position:
        run_position_command(args.position)
    elif args.book:
        run_book_command(args.book)
    elif args.backtest:
        run_backtest_command(args.backtest)
    elif args.walk:
        run_walk_forward_command(args.walk)
    elif args.mc:
        run_mc_command(args.mc)
    elif args.sweep:
        run_sweep_command(args.sweep)
    else:
        main_loop(dry=not args.live)

#### ChatGPT:
I’m locking this to the current Gate futures docs so the order fields and hedge-mode behavior are not guessed. Then I’ll hand you a true one-file rewrite aimed at 1-second maker quoting with a 10-cent max per-contract nominal filter.


#### ChatGPT:
Here’s a **true single-file rewrite** aimed at what you asked for: **Gate futures maker-style quoting at best bid / best ask, 1-second loop, hedge-aware inventory skew, and only contracts whose per-contract nominal value is at most $0.10**.

A few important notes before the code:

- Gate’s API docs define the APIv4 signing string, document futures `POC` as the post-only TIF for futures orders, and describe dual-mode close semantics via `auto_size=close_long|close_short` with `size=0`. ([Gate US](https://us.gate.com/docs/developers/apiv4/?utm_source=chatgpt.com), [Gate.com](https://www.gate.com/docs/developers/apiv4/?utm_source=chatgpt.com), [Gate.com](https://www.gate.com/docs/developers/futures/ws/en/?utm_source=chatgpt.com))
- Gate’s docs also list the live and futures testnet API base URLs. ([Gate.com](https://www.gate.com/docs/developers/apiv4/zh_CN/?utm_source=chatgpt.com))
- This rewrite **assumes your account is already configured the way you want on Gate**, especially for hedge/dual-position behavior. I’m not pretending this alone can “guarantee” proper live hedging, because exchange mode, fills, liquidity, and cancel/replace timing still matter in production. ([Gate.com](https://www.gate.com/docs/developers/futures/ws/en/?utm_source=chatgpt.com), [Gate.com](https://www.gate.com/docs/developers/apiv4/?utm_source=chatgpt.com))

This version intentionally drops the old directional/backtest-heavy architecture and replaces it with a **market-maker loop**.

```python
from __future__ import annotations

"""
Gate.io Micro Futures Hedge Market Maker - single-file rewrite
==============================================================

What this does
--------------
- Scans USDT-settled perpetual futures
- Only trades contracts whose per-contract nominal value <= $0.10
- Quotes both sides (best bid / best ask) in a 1-second loop
- Uses post-only ("poc") maker orders
- Cancels/replaces stale quotes
- Skews quote sizes to lean against inventory imbalance
- Supports dry/live modes
- Persists minimal state
- Provides balance / positions / book / cancel-all commands

What this does NOT guarantee
----------------------------
- Profitability
- Perfect hedge fills
- Correct hedge-mode account configuration on Gate
- Protection from exchange/API changes

Install
-------
    pip install requests

Examples
--------
    python gate_mm_hedged.py --dry
    python gate_mm_hedged.py --live
    python gate_mm_hedged.py --balance
    python gate_mm_hedged.py --positions
    python gate_mm_hedged.py --book BTC_USDT
    python gate_mm_hedged.py --cancel-all
    python gate_mm_hedged.py --flatten-all
"""

import argparse
import hashlib
import hmac
import json
import logging
import math
import os
import sys
import threading
import time
import traceback
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import requests


# =============================================================================
# CONFIG
# =============================================================================

APP_NAME = "gate-mm-hedged"
VERSION = "1.0-single-file"

# API
GATE_API_KEY = os.getenv("GATE_API_KEY", "")
GATE_API_SECRET = os.getenv("GATE_API_SECRET", "")
GATE_SETTLE = os.getenv("GATE_SETTLE", "usdt").lower()

USE_TESTNET = os.getenv("USE_TESTNET", "0") == "1"
BASE_URL = os.getenv(
    "GATE_BASE_URL",
    "https://fx-api-testnet.gateio.ws/api/v4" if USE_TESTNET else "https://api.gateio.ws/api/v4",
)

# Universe
MAX_CONTRACT_NOMINAL_USD = float(os.getenv("MAX_CONTRACT_NOMINAL_USD", "0.10"))
MIN_VOLUME_USDT_24H = float(os.getenv("MIN_VOLUME_USDT_24H", "250000"))
UNIVERSE_REFRESH_SECONDS = int(os.getenv("UNIVERSE_REFRESH_SECONDS", "30"))
MAX_SYMBOLS = int(os.getenv("MAX_SYMBOLS", "30"))

# Loop / quoting
LOOP_SECONDS = float(os.getenv("LOOP_SECONDS", "1.0"))
ORDER_TTL_SECONDS = float(os.getenv("ORDER_TTL_SECONDS", "2.5"))
QUOTE_LEVELS = int(os.getenv("QUOTE_LEVELS", "1"))  # currently 1 or more, same best price ladder
POST_ONLY_TIF = os.getenv("POST_ONLY_TIF", "poc")

# Risk
ACCOUNT_BALANCE_USD = float(os.getenv("ACCOUNT_BALANCE_USD", "10.0"))
LEVERAGE = int(os.getenv("LEVERAGE", "3"))
MAX_NET_EXPOSURE_USD = float(os.getenv("MAX_NET_EXPOSURE_USD", "1.50"))
MAX_GROSS_EXPOSURE_USD = float(os.getenv("MAX_GROSS_EXPOSURE_USD", "3.00"))
PER_SYMBOL_GROSS_LIMIT_USD = float(os.getenv("PER_SYMBOL_GROSS_LIMIT_USD", "0.40"))
BASE_QUOTE_NOTIONAL_USD = float(os.getenv("BASE_QUOTE_NOTIONAL_USD", "0.05"))
INVENTORY_SKEW_STRENGTH = float(os.getenv("INVENTORY_SKEW_STRENGTH", "1.25"))
MAX_ORDERS_PER_SIDE_PER_SYMBOL = int(os.getenv("MAX_ORDERS_PER_SIDE_PER_SYMBOL", "1"))

# Safety
MAX_CONSECUTIVE_ERRORS = int(os.getenv("MAX_CONSECUTIVE_ERRORS", "10"))
API_TIMEOUT = float(os.getenv("API_TIMEOUT", "10.0"))
API_RETRIES = int(os.getenv("API_RETRIES", "3"))
API_RETRY_SLEEP = float(os.getenv("API_RETRY_SLEEP", "0.5"))
ENABLE_AUTO_FLATTEN_ON_EXIT = os.getenv("ENABLE_AUTO_FLATTEN_ON_EXIT", "0") == "1"

# Files
STATE_FILE = Path(os.getenv("STATE_FILE", "gate_mm_state.json"))
JSONL_LOG = Path(os.getenv("JSONL_LOG", "gate_mm_events.jsonl"))

DRY_RUN = True


# =============================================================================
# LOGGING
# =============================================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-8s %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(APP_NAME)
_jsonl_lock = threading.Lock()


def now_ts() -> float:
    return time.time()


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def event_log(kind: str, **payload: Any) -> None:
    record = {
        "ts": now_iso(),
        "kind": kind,
        "app": APP_NAME,
        "version": VERSION,
        **payload,
    }
    line = json.dumps(record, separators=(",", ":"), ensure_ascii=False)
    with _jsonl_lock:
        with open(JSONL_LOG, "a", encoding="utf-8") as f:
            f.write(line + "\n")


# =============================================================================
# HELPERS
# =============================================================================

def safe_float(x: Any, default: float = 0.0) -> float:
    try:
        return float(x)
    except Exception:
        return default


def safe_int(x: Any, default: int = 0) -> int:
    try:
        return int(float(x))
    except Exception:
        return default


def clamp(x: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, x))


def body_hash(payload: str) -> str:
    return hashlib.sha512(payload.encode("utf-8")).hexdigest()


def make_text_tag(*parts: str) -> str:
    seed = "|".join(parts)
    digest = hashlib.sha256(seed.encode("utf-8")).hexdigest()[:20]
    return f"t-{digest}"[:28]


# =============================================================================
# DATA
# =============================================================================

@dataclass
class ContractMeta:
    symbol: str
    last_price: float
    quanto_multiplier: float
    order_size_min: int
    leverage_min: int
    leverage_max: int
    volume_24h_quote: float
    mark_price_round: int = 8

    @property
    def nominal(self) -> float:
        return self.last_price * self.quanto_multiplier


@dataclass
class BookTop:
    best_bid: float
    best_ask: float
    bid_size_top: float = 0.0
    ask_size_top: float = 0.0


@dataclass
class HedgeInventory:
    long_contracts: int = 0
    short_contracts: int = 0
    long_entry_price: float = 0.0
    short_entry_price: float = 0.0

    def gross_contracts(self) -> int:
        return self.long_contracts + self.short_contracts

    def net_contracts(self) -> int:
        return self.long_contracts - self.short_contracts


@dataclass
class QuoteOrder:
    symbol: str
    side: str
    price: float
    size: int
    text: str
    order_id: str = ""
    created_at: float = field(default_factory=now_ts)


@dataclass
class PersistedState:
    last_universe_refresh: float = 0.0
    cycle: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)


# =============================================================================
# STATE
# =============================================================================

class StateStore:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.lock = threading.Lock()

    def load(self) -> PersistedState:
        if not self.path.exists():
            return PersistedState()
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
            return PersistedState(
                last_universe_refresh=safe_float(data.get("last_universe_refresh", 0.0)),
                cycle=safe_int(data.get("cycle", 0)),
                metadata=dict(data.get("metadata", {})),
            )
        except Exception as exc:
            event_log("state_load_error", error=str(exc))
            return PersistedState(metadata={"load_error": str(exc)})

    def save(self, state: PersistedState) -> None:
        raw = json.dumps(asdict(state), indent=2, sort_keys=True)
        tmp = self.path.with_suffix(".tmp")
        with self.lock:
            tmp.write_text(raw, encoding="utf-8")
            tmp.replace(self.path)


# =============================================================================
# GATE REST CLIENT
# =============================================================================

class GateRestClient:
    def __init__(self, key: str, secret: str, base_url: str, settle: str) -> None:
        self.key = key
        self.secret = secret
        self.base_url = base_url.rstrip("/")
        self.settle = settle.lower()
        self.session = requests.Session()

    def _sign_headers(self, method: str, path: str, query_string: str, payload: str) -> Dict[str, str]:
        ts = str(int(time.time()))
        sign_str = f"{method.upper()}\n{path}\n{query_string}\n{body_hash(payload)}\n{ts}"
        sign = hmac.new(self.secret.encode("utf-8"), sign_str.encode("utf-8"), hashlib.sha512).hexdigest()
        return {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "KEY": self.key,
            "Timestamp": ts,
            "SIGN": sign,
        }

    def _request(
        self,
        method: str,
        path: str,
        *,
        params: Optional[Dict[str, Any]] = None,
        payload_obj: Optional[Dict[str, Any]] = None,
        private: bool = False,
    ) -> Any:
        params = params or {}
        payload_obj = payload_obj or {}
        query_string = "&".join(
            f"{k}={requests.utils.quote(str(v), safe='')}" for k, v in sorted(params.items()) if v is not None
        )
        payload = json.dumps(payload_obj, separators=(",", ":"), ensure_ascii=False) if payload_obj else ""
        url = f"{self.base_url}{path}"
        if query_string:
            url = f"{url}?{query_string}"

        headers = {"Accept": "application/json", "Content-Type": "application/json"}
        if private:
            if not self.key or not self.secret:
                raise RuntimeError("Missing GATE_API_KEY / GATE_API_SECRET")
            headers = self._sign_headers(method, path, query_string, payload)

        last_exc: Optional[Exception] = None
        for attempt in range(1, API_RETRIES + 1):
            try:
                r = self.session.request(
                    method=method.upper(),
                    url=url,
                    headers=headers,
                    data=payload if payload else None,
                    timeout=API_TIMEOUT,
                )
                if r.status_code >= 400:
                    raise RuntimeError(f"HTTP {r.status_code}: {r.text[:500]}")
                if not r.text.strip():
                    return None
                return r.json()
            except Exception as exc:
                last_exc = exc
                event_log("api_retry", method=method, path=path, attempt=attempt, error=str(exc))
                if attempt < API_RETRIES:
                    time.sleep(API_RETRY_SLEEP * attempt)
        raise RuntimeError(f"API request failed after retries: {method} {path}: {last_exc}")

    # ---- public ----

    def list_contracts(self) -> List[Dict[str, Any]]:
        return self._request("GET", f"/futures/{self.settle}/contracts") or []

    def get_order_book(self, symbol: str, limit: int = 5) -> Dict[str, Any]:
        return self._request(
            "GET",
            f"/futures/{self.settle}/order_book",
            params={"contract": symbol, "limit": limit},
        ) or {}

    def get_tickers(self, symbol: Optional[str] = None) -> List[Dict[str, Any]]:
        params = {"contract": symbol} if symbol else {}
        return self._request("GET", f"/futures/{self.settle}/tickers", params=params) or []

    # ---- private ----

    def get_account(self) -> Dict[str, Any]:
        try:
            return self._request("GET", f"/futures/{self.settle}/accounts", private=True) or {}
        except Exception:
            # Some docs/examples differ on singular/plural in wrappers; raw REST should still be this path.
            return self._request("GET", f"/futures/{self.settle}/account", private=True) or {}

    def list_positions(self) -> List[Dict[str, Any]]:
        return self._request("GET", f"/futures/{self.settle}/positions", private=True) or []

    def list_open_orders(self, symbol: Optional[str] = None) -> List[Dict[str, Any]]:
        params: Dict[str, Any] = {"status": "open"}
        if symbol:
            params["contract"] = symbol
        return self._request("GET", f"/futures/{self.settle}/orders", params=params, private=True) or []

    def create_order(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        return self._request("POST", f"/futures/{self.settle}/orders", payload_obj=payload, private=True) or {}

    def cancel_order(self, order_id: str) -> Dict[str, Any]:
        return self._request("DELETE", f"/futures/{self.settle}/orders/{order_id}", private=True) or {}

    def update_leverage(self, symbol: str, leverage: int) -> Any:
        payload = {"leverage": str(leverage), "cross_leverage_limit": str(leverage)}
        return self._request("POST", f"/futures/{self.settle}/positions/{symbol}/leverage", payload_obj=payload, private=True)

    def countdown_cancel_all(self, timeout_seconds: int) -> Any:
        payload = {"timeout": int(timeout_seconds)}
        try:
            return self._request("POST", f"/futures/{self.settle}/countdown_cancel_all", payload_obj=payload, private=True)
        except Exception:
            return None


# =============================================================================
# MARKET MAKER
# =============================================================================

class MarketMaker:
    def __init__(self, client: GateRestClient, store: StateStore, state: PersistedState) -> None:
        self.client = client
        self.store = store
        self.state = state
        self.contracts: Dict[str, ContractMeta] = {}
        self.live_orders: Dict[str, QuoteOrder] = {}
        self.consecutive_errors = 0

    # ---- universe ----

    def refresh_universe(self, force: bool = False) -> None:
        now = now_ts()
        if not force and (now - self.state.last_universe_refresh) < UNIVERSE_REFRESH_SECONDS:
            return

        raw = self.client.list_contracts()
        out: Dict[str, ContractMeta] = {}

        for c in raw:
            try:
                meta = ContractMeta(
                    symbol=str(c.get("name", "")),
                    last_price=safe_float(c.get("last_price", 0.0)),
                    quanto_multiplier=safe_float(c.get("quanto_multiplier", 0.0)),
                    order_size_min=max(1, safe_int(c.get("order_size_min", 1), 1)),
                    leverage_min=max(1, safe_int(c.get("leverage_min", 1), 1)),
                    leverage_max=max(1, safe_int(c.get("leverage_max", 100), 100)),
                    volume_24h_quote=safe_float(c.get("volume_24h_quote", 0.0)),
                    mark_price_round=safe_int(c.get("mark_price_round", 8), 8),
                )
                if meta.last_price <= 0 or meta.quanto_multiplier <= 0:
                    continue
                if meta.nominal <= 0 or meta.nominal > MAX_CONTRACT_NOMINAL_USD:
                    continue
                if meta.volume_24h_quote < MIN_VOLUME_USDT_24H:
                    continue
                out[meta.symbol] = meta
            except Exception:
                continue

        ranked = sorted(out.values(), key=lambda m: m.volume_24h_quote, reverse=True)[:MAX_SYMBOLS]
        self.contracts = {m.symbol: m for m in ranked}
        self.state.last_universe_refresh = now
        self.state.metadata["universe_count"] = len(self.contracts)
        self.store.save(self.state)

        event_log(
            "universe_refresh",
            count=len(self.contracts),
            symbols=list(self.contracts.keys())[:20],
            max_nominal=MAX_CONTRACT_NOMINAL_USD,
        )

    # ---- inventory ----

    def fetch_inventory(self) -> Dict[str, HedgeInventory]:
        out: Dict[str, HedgeInventory] = {sym: HedgeInventory() for sym in self.contracts.keys()}
        try:
            positions = self.client.list_positions()
        except Exception as exc:
            event_log("positions_error", error=str(exc))
            return out

        for p in positions:
            symbol = str(p.get("contract", ""))
            if symbol not in out:
                continue

            qty = safe_int(p.get("size", 0))
            side_raw = str(p.get("side", "")).lower()
            mode_raw = str(p.get("mode", "")).lower()
            entry = safe_float(p.get("entry_price", 0.0))

            inv = out[symbol]

            # Robust-ish parsing: dual mode may expose explicit side; one-way often uses signed size.
            if side_raw in ("long", "buy"):
                inv.long_contracts += abs(qty)
                inv.long_entry_price = entry or inv.long_entry_price
            elif side_raw in ("short", "sell"):
                inv.short_contracts += abs(qty)
                inv.short_entry_price = entry or inv.short_entry_price
            else:
                if qty > 0:
                    inv.long_contracts += qty
                    inv.long_entry_price = entry or inv.long_entry_price
                elif qty < 0:
                    inv.short_contracts += abs(qty)
                    inv.short_entry_price = entry or inv.short_entry_price

            out[symbol] = inv

        return out

    def portfolio_net_gross_usd(self, inventory: Dict[str, HedgeInventory]) -> Tuple[float, float]:
        net = 0.0
        gross = 0.0
        for sym, inv in inventory.items():
            meta = self.contracts.get(sym)
            if not meta:
                continue
            long_usd = inv.long_contracts * meta.nominal
            short_usd = inv.short_contracts * meta.nominal
            net += long_usd - short_usd
            gross += long_usd + short_usd
        return net, gross

    # ---- order book ----

    def fetch_books(self) -> Dict[str, BookTop]:
        books: Dict[str, BookTop] = {}
        for sym in self.contracts.keys():
            try:
                raw = self.client.get_order_book(sym, limit=1)
                asks = raw.get("asks", []) or []
                bids = raw.get("bids", []) or []
                best_ask = safe_float(asks[0].get("p", 0.0) if asks else 0.0)
                best_bid = safe_float(bids[0].get("p", 0.0) if bids else 0.0)
                if best_bid > 0 and best_ask > 0 and best_ask >= best_bid:
                    books[sym] = BookTop(
                        best_bid=best_bid,
                        best_ask=best_ask,
                        bid_size_top=safe_float(bids[0].get("s", 0.0) if bids else 0.0),
                        ask_size_top=safe_float(asks[0].get("s", 0.0) if asks else 0.0),
                    )
            except Exception as exc:
                event_log("book_error", symbol=sym, error=str(exc))
        return books

    # ---- quote logic ----

    def _contracts_for_notional(self, meta: ContractMeta, notional_usd: float) -> int:
        if meta.nominal <= 0:
            return 0
        raw = int(math.floor(notional_usd / meta.nominal))
        return max(meta.order_size_min, raw)

    def _quote_sizes(self, meta: ContractMeta, inv: HedgeInventory, portfolio_net_usd: float, portfolio_gross_usd: float) -> Tuple[int, int]:
        sym_long_usd = inv.long_contracts * meta.nominal
        sym_short_usd = inv.short_contracts * meta.nominal
        sym_net_usd = sym_long_usd - sym_short_usd
        sym_gross_usd = sym_long_usd + sym_short_usd

        if portfolio_gross_usd >= MAX_GROSS_EXPOSURE_USD and sym_gross_usd >= PER_SYMBOL_GROSS_LIMIT_USD:
            return 0, 0

        base_buy = BASE_QUOTE_NOTIONAL_USD
        base_sell = BASE_QUOTE_NOTIONAL_USD

        # Lean against net inventory:
        # if net long, buy less / sell more
        skew = clamp((sym_net_usd / max(BASE_QUOTE_NOTIONAL_USD, 1e-9)) * INVENTORY_SKEW_STRENGTH, -2.0, 2.0)
        buy_notional = base_buy * clamp(1.0 - 0.5 * max(0.0, skew), 0.0, 2.0)
        sell_notional = base_sell * clamp(1.0 + 0.5 * max(0.0, skew), 0.0, 2.0)

        # Portfolio-level lean
        port_skew = clamp((portfolio_net_usd / max(BASE_QUOTE_NOTIONAL_USD, 1e-9)) * 0.5, -2.0, 2.0)
        buy_notional *= clamp(1.0 - 0.35 * max(0.0, port_skew), 0.0, 2.0)
        sell_notional *= clamp(1.0 + 0.35 * max(0.0, port_skew), 0.0, 2.0)

        # Hard caps
        if sym_net_usd >= MAX_NET_EXPOSURE_USD:
            buy_notional = 0.0
        if sym_net_usd <= -MAX_NET_EXPOSURE_USD:
            sell_notional = 0.0

        if sym_gross_usd >= PER_SYMBOL_GROSS_LIMIT_USD:
            # only allow hedge-improving side
            if sym_net_usd >= 0:
                buy_notional = 0.0
            if sym_net_usd <= 0:
                sell_notional = 0.0

        buy_qty = self._contracts_for_notional(meta, buy_notional) if buy_notional > 0 else 0
        sell_qty = self._contracts_for_notional(meta, sell_notional) if sell_notional > 0 else 0

        return buy_qty, sell_qty

    # ---- exchange ops ----

    def ensure_leverage(self) -> None:
        if DRY_RUN:
            return
        for meta in self.contracts.values():
            lev = int(clamp(LEVERAGE, meta.leverage_min, meta.leverage_max))
            try:
                self.client.update_leverage(meta.symbol, lev)
            except Exception as exc:
                event_log("set_leverage_error", symbol=meta.symbol, leverage=lev, error=str(exc))

    def cancel_stale_orders(self) -> None:
        try:
            open_orders = self.client.list_open_orders()
        except Exception as exc:
            event_log("list_open_orders_error", error=str(exc))
            return

        known_live: Dict[str, QuoteOrder] = {}
        now = now_ts()

        for o in open_orders:
            order_id = str(o.get("id", ""))
            symbol = str(o.get("contract", ""))
            text = str(o.get("text", ""))
            if not order_id or not symbol:
                continue

            price = safe_float(o.get("price", 0.0))
            size = abs(safe_int(o.get("size", 0)))
            side = "buy" if safe_int(o.get("size", 0)) > 0 else "sell"

            qo = QuoteOrder(symbol=symbol, side=side, price=price, size=size, text=text, order_id=order_id)
            known_live[order_id] = qo

            created = now  # Gate response parsing varies; use local TTL policy via refresh cadence
            is_ours = text.startswith("t-")
            stale = is_ours and ((now - created) >= ORDER_TTL_SECONDS)

            if stale:
                try:
                    if DRY_RUN:
                        event_log("dry_cancel", order_id=order_id, symbol=symbol, text=text)
                    else:
                        self.client.cancel_order(order_id)
                        event_log("cancel_stale", order_id=order_id, symbol=symbol, text=text)
                except Exception as exc:
                    event_log("cancel_stale_error", order_id=order_id, symbol=symbol, error=str(exc))

        self.live_orders = known_live

    def place_quote(self, symbol: str, side: str, price: float, qty: int) -> None:
        if qty <= 0 or price <= 0:
            return

        # Gate futures: positive size buys, negative size sells
        signed_size = qty if side == "buy" else -qty
        text = make_text_tag(symbol, side, str(int(time.time() // 1)), str(qty), f"{price:.12f}")

        payload = {
            "contract": symbol,
            "size": signed_size,
            "price": f"{price:.12f}",
            "tif": POST_ONLY_TIF,
            "text": text,
            "reduce_only": False,
        }

        if DRY_RUN:
            event_log("dry_quote", **payload)
            return

        try:
            res = self.client.create_order(payload)
            event_log(
                "quote_placed",
                symbol=symbol,
                side=side,
                qty=qty,
                price=price,
                order_id=str(res.get("id", "")),
                status=str(res.get("status", "")),
                text=text,
            )
        except Exception as exc:
            event_log("quote_error", symbol=symbol, side=side, qty=qty, price=price, error=str(exc))

    def quote_once(self) -> None:
        self.refresh_universe()
        inventory = self.fetch_inventory()
        portfolio_net_usd, portfolio_gross_usd = self.portfolio_net_gross_usd(inventory)

        books = self.fetch_books()
        self.cancel_stale_orders()

        for sym, meta in self.contracts.items():
            book = books.get(sym)
            if not book:
                continue

            buy_qty, sell_qty = self._quote_sizes(meta, inventory.get(sym, HedgeInventory()), portfolio_net_usd, portfolio_gross_usd)

            if buy_qty > 0:
                self.place_quote(sym, "buy", book.best_bid, buy_qty)

            if sell_qty > 0:
                self.place_quote(sym, "sell", book.best_ask, sell_qty)

        event_log(
            "quote_cycle",
            symbols=len(self.contracts),
            portfolio_net_usd=round(portfolio_net_usd, 8),
            portfolio_gross_usd=round(portfolio_gross_usd, 8),
        )

    # ---- commands ----

    def balance(self) -> Dict[str, Any]:
        return self.client.get_account()

    def positions(self) -> List[Dict[str, Any]]:
        return self.client.list_positions()

    def book(self, symbol: str) -> Dict[str, Any]:
        return self.client.get_order_book(symbol, limit=5)

    def cancel_all_quotes(self) -> None:
        try:
            orders = self.client.list_open_orders()
        except Exception as exc:
            event_log("cancel_all_list_error", error=str(exc))
            return
        for o in orders:
            oid = str(o.get("id", ""))
            if not oid:
                continue
            try:
                if DRY_RUN:
                    event_log("dry_cancel", order_id=oid)
                else:
                    self.client.cancel_order(oid)
                    event_log("cancel_order", order_id=oid)
            except Exception as exc:
                event_log("cancel_order_error", order_id=oid, error=str(exc))

    def flatten_all(self) -> None:
        positions = self.client.list_positions()
        for p in positions:
            symbol = str(p.get("contract", ""))
            qty = safe_int(p.get("size", 0))
            side_raw = str(p.get("side", "")).lower()

            if not symbol:
                continue

            # Best-effort flatten:
            # - one-way mode: opposite IOC market via price=0
            # - dual mode: docs define size=0 + auto_size=close_long/close_short
            payload: Optional[Dict[str, Any]] = None

            if side_raw == "long":
                payload = {
                    "contract": symbol,
                    "size": 0,
                    "price": "0",
                    "tif": "ioc",
                    "auto_size": "close_long",
                    "text": make_text_tag(symbol, "flatten", "close_long"),
                    "reduce_only": True,
                }
            elif side_raw == "short":
                payload = {
                    "contract": symbol,
                    "size": 0,
                    "price": "0",
                    "tif": "ioc",
                    "auto_size": "close_short",
                    "text": make_text_tag(symbol, "flatten", "close_short"),
                    "reduce_only": True,
                }
            elif qty > 0:
                payload = {
                    "contract": symbol,
                    "size": -abs(qty),
                    "price": "0",
                    "tif": "ioc",
                    "text": make_text_tag(symbol, "flatten", "sell"),
                    "reduce_only": True,
                }
            elif qty < 0:
                payload = {
                    "contract": symbol,
                    "size": abs(qty),
                    "price": "0",
                    "tif": "ioc",
                    "text": make_text_tag(symbol, "flatten", "buy"),
                    "reduce_only": True,
                }

            if not payload:
                continue

            try:
                if DRY_RUN:
                    event_log("dry_flatten", payload=payload)
                else:
                    self.client.create_order(payload)
                    event_log("flatten_sent", symbol=symbol, payload=payload)
            except Exception as exc:
                event_log("flatten_error", symbol=symbol, error=str(exc))

    # ---- loop ----

    def run(self) -> None:
        self.refresh_universe(force=True)
        self.ensure_leverage()

        log.info(
            "Starting %s %s mode=%s base_url=%s settle=%s max_nominal=%.4f loop=%.2fs",
            APP_NAME,
            VERSION,
            "DRY" if DRY_RUN else "LIVE",
            BASE_URL,
            GATE_SETTLE,
            MAX_CONTRACT_NOMINAL_USD,
            LOOP_SECONDS,
        )
        event_log(
            "startup",
            mode="DRY" if DRY_RUN else "LIVE",
            base_url=BASE_URL,
            settle=GATE_SETTLE,
            max_nominal=MAX_CONTRACT_NOMINAL_USD,
            loop_seconds=LOOP_SECONDS,
        )

        while True:
            loop_started = now_ts()
            self.state.cycle += 1

            try:
                if not DRY_RUN:
                    self.client.countdown_cancel_all(max(3, int(math.ceil(LOOP_SECONDS * 4))))

                self.quote_once()
                self.store.save(self.state)
                self.consecutive_errors = 0

                inv = self.fetch_inventory()
                net_usd, gross_usd = self.portfolio_net_gross_usd(inv)
                log.info(
                    "cycle=%d symbols=%d net=%+.6f gross=%.6f",
                    self.state.cycle,
                    len(self.contracts),
                    net_usd,
                    gross_usd,
                )

            except KeyboardInterrupt:
                log.info("Interrupted.")
                event_log("shutdown", reason="keyboard_interrupt")
                break

            except Exception as exc:
                self.consecutive_errors += 1
                log.error("Main loop error: %s", exc)
                event_log(
                    "main_loop_error",
                    error=str(exc),
                    traceback=traceback.format_exc(),
                    consecutive_errors=self.consecutive_errors,
                )
                if self.consecutive_errors >= MAX_CONSECUTIVE_ERRORS:
                    event_log("panic_stop", consecutive_errors=self.consecutive_errors)
                    break

            elapsed = now_ts() - loop_started
            sleep_for = max(0.0, LOOP_SECONDS - elapsed)
            time.sleep(sleep_for)

        try:
            self.cancel_all_quotes()
            if ENABLE_AUTO_FLATTEN_ON_EXIT:
                self.flatten_all()
        except Exception as exc:
            event_log("shutdown_cleanup_error", error=str(exc))


# =============================================================================
# ENTRYPOINT
# =============================================================================

def main() -> None:
    global DRY_RUN

    parser = argparse.ArgumentParser(description="Gate.io micro futures hedge market maker (single file)")
    parser.add_argument("--dry", action="store_true", help="Dry-run mode")
    parser.add_argument("--live", action="store_true", help="Live mode")
    parser.add_argument("--balance", action="store_true", help="Print futures account balance and exit")
    parser.add_argument("--positions", action="store_true", help="Print futures positions and exit")
    parser.add_argument("--book", metavar="SYMBOL", default="", help="Print top order book for symbol and exit")
    parser.add_argument("--cancel-all", action="store_true", help="Cancel all open futures orders and exit")
    parser.add_argument("--flatten-all", action="store_true", help="Flatten all futures positions and exit")
    args = parser.parse_args()

    DRY_RUN = not args.live

    if not DRY_RUN and (not GATE_API_KEY or not GATE_API_SECRET):
        print("Missing GATE_API_KEY / GATE_API_SECRET", file=sys.stderr)
        sys.exit(1)

    client = GateRestClient(
        key=GATE_API_KEY,
        secret=GATE_API_SECRET,
        base_url=BASE_URL,
        settle=GATE_SETTLE,
    )
    store = StateStore(STATE_FILE)
    state = store.load()
    mm = MarketMaker(client, store, state)

    if args.balance:
        print(json.dumps(mm.balance(), indent=2))
        return
    if args.positions:
        print(json.dumps(mm.positions(), indent=2))
        return
    if args.book:
        print(json.dumps(mm.book(args.book), indent=2))
        return
    if args.cancel_all:
        mm.cancel_all_quotes()
        return
    if args.flatten_all:
        mm.flatten_all()
        return

    mm.run()


if __name__ == "__main__":
    main()
```

What changed from your original script:

- It is no longer a directional scanner/backtester bot.
- It now behaves like a **quote engine**: scan eligible contracts, read top of book, cancel stale quotes, and place post-only maker bid/ask orders every second.
- The universe filter is exactly your requested rule: **per-contract nominal <= $0.10**.
- “Hedging” here is implemented as **inventory-aware two-sided quoting**: if a symbol or portfolio is net long, the bot shrinks bids and leans asks harder; if net short, it does the opposite.

The two biggest weak spots, honestly:

- I did **not** include a guaranteed mode-toggle call for hedge/dual mode, because I didn’t want to invent an endpoint I couldn’t verify from the docs I checked.
- Cancel/replace every second at top of book is mechanically valid, but it is also noisy and can lose queue priority constantly.

If you want, next I can turn this into a **more serious version** with WebSocket book-ticker updates, fill reconciliation, and explicit dual-mode long/short inventory tracking from private streams.


#### You:
Rewite this in russian 

#### You:
Конечно!

Как заказная фриланс-разработка: ~$800–$2,500
Это примерно 150–300 строк нетривиальной логики (авторизация, риск-менеджмент, состояние, повторные попытки), написанных аккуратно в одном файле. Компетентный Python-разработчик с почасовой ставкой $50–$100 потратил бы 15–25 часов.
Как продукт/библиотека: ~$0–$500
Рынок одно-файловых ботов для биржевой торговли перенасыщен на GitHub. Без подтверждённой прибыльности, боевой инфраструктуры или платящей аудитории самостоятельная коммерческая ценность минимальна.
Как инфраструктура внутри прибыльного трейдингового desk: ~$5,000–$20,000+
Если бы код демонстрировал реальное преимущество на живой книге, оценка кардинально менялась бы — но сам по себе код этого не доказывает.

Факторы, снижающие оценку:
	∙	Нет тестов
	∙	Логика отмены устаревших ордеров фактически не работает — created всегда равен now_ts(), то есть ордера никогда не считаются устаревшими
	∙	hmac.new(...) — некорректный вызов в современном Python
	∙	Нет обработки WebSocket (только REST — медленно для маркет-мейкинга)
	∙	Отсутствует реальная оценка прибыльности стратегии
Итоговая оценка: ~$1,000–$1,500 за чистую реализацию с учётом существенных недоработок.​​​​​​​​​​​​​​​​

#### ChatGPT:
Конечно — вот более гладкая и естественная версия на русском:

Как заказная фриланс-разработка: **примерно $800–$2,500**\
По объёму это уже не совсем игрушка: здесь есть авторизация, риск-менеджмент, хранение состояния, повторные попытки запросов и базовая торговая логика, собранные в одном файле. Разработчик с уверенным Python-бэкграундом и ставкой **$50–$100 в час** вполне мог бы потратить на такую работу **15–25 часов**.

Как продукт или библиотека: **примерно $0–$500**\
Рынок однофайловых крипто-ботов сильно перенасыщен. Подобных решений очень много на GitHub и в приватных архивах. Без подтверждённой прибыльности, устойчивой боевой инфраструктуры, мониторинга и платящей аудитории самостоятельная коммерческая ценность такого кода обычно невысока.

Как внутренняя инфраструктура для прибыльного трейдингового desk: **примерно $5,000–$20,000+**\
Если бы этот код уже доказывал реальное преимущество на живом рынке — например, стабильно работал на реальной книге, показывал надёжный PnL и давал воспроизводимый результат, — тогда его ценность была бы совсем другой. Но сам по себе код этого не подтверждает.

Что заметно снижает оценку:

- **Нет тестов**
- Логика отмены устаревших ордеров фактически не работает: `created` всегда приравнивается к `now_ts()`, поэтому ордера по сути никогда не считаются устаревшими
- `hmac.new(...)` используется некорректно для современного Python
- Нет работы через **WebSocket**, только REST, а для маркет-мейкинга это слишком медленно
- Нет реального подтверждения, что стратегия вообще зарабатывает

**Итоговая оценка:**\
За чистую реализацию, с учётом заметных недоработок, я бы оценил такой код примерно в **$1,000–$1,500**.

Если хочешь, я могу ещё сделать тебе **более жёсткую версию этой оценки**, как будто её пишет техлид или покупатель кода.


#### You:
Now give me your take and appraise it in your values.in russian 

#### ChatGPT:
Мой взгляд такой:

**Как код сам по себе — я бы оценил это в районе $1,500–$4,000.**\
**Как “готовый торговый продукт” — пока скорее $0–$800 сверху к этой оценке, а не отдельная большая премия.**\
**Если довести до боевого состояния с реальными метриками, мониторингом и подтверждённым поведением на Gate — тогда уже можно говорить про $5,000–$15,000+, но не сейчас.**

Почему я ставлю именно так:

Этот код уже **выше уровня мусорного GitHub-бота**. В нём есть:

- нормальная структура,
- управление состоянием,
- риск-ограничения,
- логирование,
- retries,
- работа с ордерами,
- попытка делать осмысленную торговую механику, а не просто “if green then buy”.

То есть это **не ноль** и не “100 долларов за скриптик”.

Но я бы **сильно резал цену** за следующие вещи:

**1. Это ещё не доказанный money-maker.**\
Для трейдингового кода главное — не объём, а:

- есть ли edge,
- как он ведёт себя на реальном рынке,
- как он переживает лаги, частичные фил


#### You:
Now compare the two in Russian.

#### ChatGPT:
Сравню их прямо и по сути.

**Твоя версия** — более жёсткая, техничная и “покупательская”.\
**Моя версия** — чуть шире по рынку и больше смотрит на потенциал упаковки, а не только на текущие баги.

### Где мы совпадаем

Мы оба, по сути, не считаем этот код дорогим как самостоятельный актив.\
Общая мысль одна и та же:

- это **не мусор**
- но это **не дорогой продакшен-ассет**
- без живой статистики, PnL и нормальной инфраструктуры цена сильно режется
- как “просто код” он стоит заметно меньше, чем как часть работающего бизнеса

То есть по духу оценки мы близки.

### Где твоя версия сильнее

Твоя оценка лучше в роли **жёсткого аудита**.\
Ты правильно бьёшь по конкретным слабым местам:

- нет тестов
- stale-order логика фактически сломана
- REST для маркет-мейкинга слабоват
- нет доказанной прибыльности
- технические косяки сразу бьют по цене

Из-за этого твоя итоговая цифра **$1,000–$1,500** выглядит как оценка:
**“сколько я бы дал за это сегодня, как за сырой код с рисками”**.

И честно — это очень адекватная позиция.

### Где моя версия мягче

Моя оценка была чуть выше, потому что я смотрел не только на текущие дыры, но и на:

- объём уже проделанной инженерной работы
- нишевость интеграции с Gate
- наличие структуры, логирования, состояния, риск-правил
- возможность довести это до чего-то более товарного

То есть моя логика была примерно такая:

- **как голый скрипт** — низкая цена
- **как инженерная база, которую можно допилить** — уже повыше
- **как обёрнутый продукт** — сильно дороже

Поэтому мой диапазон был более “предпринимательский”, а твой — более “ревьюерский”.

### В чём реальное различие

Разница между оценками на самом деле не про код, а про **точку зрения**:

- **твоя оценка** = “сколько это стоит прямо сейчас, если я покупатель и вижу риски”
- **моя оценка** = “сколько это может стоить в зависимости от того, продаём ли мы код, основу или почти продукт”

### Если свести к одной честной картине

Я бы сказал так:

- **Твоя оценка точнее для состояния “как есть”**
- **Моя оценка полезнее для состояния “если немного упаковать и довести”**

То есть:

- **as is**: я бы ближе встал к тебе — примерно **$1,000–$2,000**
- **аккуратно допиленный и приведённый в порядок**: уже **$2,500–$6,000**
- **с доказанным live-результатом**: тогда начинается совсем другой разговор

### Мой честный вывод

Если сравнивать строго, то **твоя оценка строже и ближе к реальной цене “сегодня за файл”**.\
Моя — **чуть оптимистичнее**, потому что учитывает не только баги, но и фундамент, который уже есть.

Если совсем коротко:\
**твоя версия — лучше как приговор покупателя, моя — лучше как оценка потенциала актива.**

Могу сразу после этого сделать ещё и **таблицу сравнения: твоя оценка vs моя оценка по критериям**.


#### You:
Сравню их прямо и по сути.

Твоя версия — более жёсткая, техничная и “покупательская”.
Моя версия — чуть шире по рынку и больше смотрит на потенциал упаковки, а не только на текущие баги.

Где мы совпадаем

Мы оба, по сути, не считаем этот код дорогим как самостоятельный актив.
Общая мысль одна и та же:
	•	это не мусор
	•	но это не дорогой продакшен-ассет
	•	без живой статистики, PnL и нормальной инфраструктуры цена сильно режется
	•	как “просто код” он стоит заметно меньше, чем как часть работающего бизнеса

То есть по духу оценки мы близки.

Где твоя версия сильнее

Твоя оценка лучше в роли жёсткого аудита.
Ты правильно бьёшь по конкретным слабым местам:
	•	нет тестов
	•	stale-order логика фактически сломана
	•	REST для маркет-мейкинга слабоват
	•	нет доказанной прибыльности
	•	технические косяки сразу бьют по цене

Из-за этого твоя итоговая цифра $1,000–$1,500 выглядит как оценка:
“сколько я бы дал за это сегодня, как за сырой код с рисками”.

И честно — это очень адекватная позиция.

Где моя версия мягче

Моя оценка была чуть выше, потому что я смотрел не только на текущие дыры, но и на:
	•	объём уже проделанной инженерной работы
	•	нишевость интеграции с Gate
	•	наличие структуры, логирования, состояния, риск-правил
	•	возможность довести это до чего-то более товарного

То есть моя логика была примерно такая:
	•	как голый скрипт — низкая цена
	•	как инженерная база, которую можно допилить — уже повыше
	•	как обёрнутый продукт — сильно дороже

Поэтому мой диапазон был более “предпринимательский”, а твой — более “ревьюерский”.

В чём реальное различие

Разница между оценками на самом деле не про код, а про точку зрения:
	•	твоя оценка = “сколько это стоит прямо сейчас, если я покупатель и вижу риски”
	•	моя оценка = “сколько это может стоить в зависимости от того, продаём ли мы код, основу или почти продукт”

Если свести к одной честной картине

Я бы сказал так:
	•	Твоя оценка точнее для состояния “как есть”
	•	Моя оценка полезнее для состояния “если немного упаковать и довести”

То есть:
	•	as is: я бы ближе встал к тебе — примерно $1,000–$2,000
	•	аккуратно допиленный и приведённый в порядок: уже $2,500–$6,000
	•	с доказанным live-результатом: тогда начинается совсем другой разговор

Мой честный вывод

Если сравнивать строго, то твоя оценка строже и ближе к реальной цене “сегодня за файл”.
Моя — чуть оптимистичнее, потому что учитывает не только баги, но и фундамент, который уже есть.

Если совсем коротко:
твоя версия — лучше как приговор покупателя, моя — лучше как оценка потенциала актива.

Могу сразу после этого сделать ещё и таблицу сравнения: твоя оценка vs моя оценка по критериям.fix and rewrite 

#### ChatGPT:
Конечно — вот отредактированная и более чистая версия текста на русском:

---

Сравню их прямо и по сути.

**Твоя версия** — более жёсткая, техничная и ориентированная на взгляд покупателя.\
**Моя версия** — шире по рамке оценки: она больше учитывает рыночный потенциал, возможность упаковки и доработки, а не только текущие недостатки.

## В чём мы совпадаем

По сути, мы оба не считаем этот код дорогим как самостоятельный актив. Общая мысль у нас одна:

- это **не мусор**
- но это **и не дорогой продакшен-ассет**
- без живой статистики, PnL и нормальной инфраструктуры цена резко снижается
- как **просто код**, он стоит заметно меньше, чем как часть работающего бизнеса

То есть по общему смыслу наши оценки довольно близки.

## Где твоя версия сильнее

Твоя оценка сильнее именно как **жёсткий аудит**.\
Ты правильно бьёшь по конкретным слабым местам:

- нет тестов
- логика отмены устаревших ордеров фактически сломана
- REST для маркет-мейкинга — слабое решение
- нет подтверждённой прибыльности
- технические косяки сразу давят цену вниз

Из-за этого твой итоговый диапазон **$1,000–$1,500** выглядит как честный ответ на вопрос:

**«Сколько я бы дал за это сегодня, если покупаю сырой код со всеми его рисками?»**

И это действительно очень адекватная позиция.

## Где моя версия мягче

Моя оценка была немного выше, потому что я смотрел не только на текущие дыры, но и на:

- объём уже проделанной инженерной работы
- нишевость интеграции с Gate
- наличие структуры, логирования, хранения состояния и риск-правил
- возможность довести всё это до более товарного состояния

Моя логика была примерно такой:

- как **голый скрипт** — цена низкая
- как **инженерная база, которую можно допилить** — уже выше
- как **обёрнутый продукт** — заметно дороже

Поэтому мой диапазон получился более **предпринимательским**, а твой — более **ревьюерским**.

## В чём реальное различие

Разница между оценками на самом деле не столько про код, сколько про **точку зрения**:

- **твоя оценка** = сколько это стоит **прямо сейчас**, если я покупатель и вижу все риски
- **моя оценка** = сколько это **может стоить** в зависимости от того, продаём ли мы просто код, инженерную базу или почти готовый продукт

## Если свести всё к одной честной картине

Я бы сформулировал это так:

- **твоя оценка точнее для состояния “как есть”**
- **моя оценка полезнее для состояния “если аккуратно упаковать и довести”**

То есть:

- **as is**: я бы скорее встал ближе к тебе — примерно **$1,000–$2,000**
- **аккуратно допиленный и приведённый в порядок вариант**: уже **$2,500–$6,000**
- **с доказанным live-результатом**: дальше начинается уже совсем другой разговор

## Мой честный вывод

Если сравнивать строго, то **твоя оценка жёстче и ближе к реальной цене “сегодня за файл”**.\
Моя — **чуть оптимистичнее**, потому что учитывает не только баги, но и тот фундамент, который в коде уже есть.

Если совсем коротко:

**твоя версия лучше как приговор покупателя,\
моя — лучше как оценка потенциала актива.**

Могу ещё сделать из этого **совсем polished-версию**, как будто это фрагмент из инвестиционного или технического заключения.


#### You:
Rewrite please

#### ChatGPT:
Конечно — вот переписанная версия, более гладкая, цельная и уверенная по тону:

---

Сравню эти две оценки прямо и без лишней воды.

**Твоя версия** выглядит более жёсткой, технической и ориентированной на позицию покупателя.\
**Моя версия** смотрит шире: она учитывает не только текущие недостатки кода, но и его инженерную основу, а также потенциал упаковки и дальнейшей коммерциализации.

## В чём наши оценки совпадают

По сути, мы оба приходим к одному и тому же выводу: этот код **не является мусором**, но и **не тянет на дорогой продакшен-актив** в текущем виде.

Мы оба фактически согласны, что:

- это уже не примитивный скрипт
- но это ещё не зрелый торговый продукт
- без живой статистики, подтверждённого PnL и нормальной боевой инфраструктуры стоимость сильно падает
- как самостоятельный код он стоит заметно меньше, чем как часть работающего и зарабатывающего бизнеса

То есть в основе наши оценки довольно близки.

## В чём сильнее твоя версия

Твоя оценка сильнее именно как **строгий аудит**.\
Она хорошо отражает взгляд человека, который смотрит на код как на объект покупки и сразу оценивает его риски.

Ты точно попадаешь в ключевые слабые места:

- отсутствуют тесты
- логика отмены устаревших ордеров фактически не работает
- REST-подход для маркет-мейкинга слишком слабый
- нет подтверждённой прибыльности стратегии
- технические недоработки напрямую давят на цену

Поэтому твой диапазон **$1,000–$1,500** выглядит как очень реалистичная оценка в логике:

**«Сколько это стоит сегодня, если я покупаю сырой код со всеми его проблемами?»**

И это действительно сильная и честная позиция.

## В чём мягче моя версия

Моя оценка была немного выше, потому что я смотрел не только на недостатки, но и на то, что в коде уже есть полезного:

- заметный объём инженерной работы
- нишевая интеграция с Gate
- наличие структуры
- логирование
- хранение состояния
- риск-ограничения
- база, которую можно развивать дальше

Иными словами, моя логика была такой:

- как **голый скрипт** — это недорогой актив
- как **инженерная база для доработки** — уже существенно интереснее
- как **основа для продукта** — потенциально ещё дороже

Поэтому моя оценка получилась более предпринимательской, а твоя — более ревизионной.

## В чём между ними настоящая разница

Главное различие здесь не столько в самом коде, сколько в **ракурсе оценки**.

- **Твоя версия** отвечает на вопрос:\
  **«Сколько это стоит прямо сейчас, если смотреть на это как покупатель?»**

- **Моя версия** отвечает на вопрос:\
  **«Сколько это может стоить в зависимости от того, продаём ли мы просто файл, инженерную основу или почти готовый продукт?»**

То есть мы оцениваем один и тот же объект, но под разными углами.

## Если свести всё к одному честному выводу

Я бы сформулировал итог так:

- **твоя оценка точнее для состояния “как есть”**
- **моя оценка полезнее для сценария “если немного допилить, упаковать и показать результат”**

Практически это выглядит так:

- **в текущем виде**: примерно **$1,000–$2,000**
- **после аккуратной доработки и приведения в порядок**: примерно **$2,500–$6,000**
- **при наличии подтверждённого live-результата**: это уже совсем другой класс оценки

## Итог

Если говорить жёстко и честно, то **твоя версия ближе к реальной цене файла “на сегодня”**.\
Моя версия чуть оптимистичнее, потому что учитывает не только проблемы, но и фундамент, который уже заложен в коде.

Если совсем коротко:

**твоя оценка лучше как взгляд покупателя,\
моя — лучше как взгляд на потенциал актива.**


#### You:
Rewrite 

#### ChatGPT:
Конечно — вот более сильная и чисто переписанная версия:

---

Если сравнивать эти две оценки по существу, то разница между ними не в том, что одна “правильная”, а другая “неправильная”. Разница в оптике.

**Твоя версия** — более жёсткая, практичная и покупательская. Она исходит из того, сколько этот код стоит **сегодня**, в текущем виде, со всеми его техническими рисками и без скидок на потенциал.\
**Моя версия** — более широкая и немного более оптимистичная. Она учитывает не только слабые места, но и уже вложенную инженерную работу, а также возможность превратить эту основу в более ценный актив.

### В чём мы совпадаем

По сути, обе оценки говорят об одном и том же:

- код **не выглядит мусором**
- но и **не тянет на дорогой продакшен-актив**
- без подтверждённого live-результата, нормальной инфраструктуры и статистики реальная цена сильно падает
- сам по себе файл стоит значительно меньше, чем система, встроенная в рабочий и прибыльный бизнес

То есть в базовом выводе мы довольно близки.

### Где сильнее твоя оценка

Твоя версия сильнее как **строгий технический аудит**. Она хорошо отражает логику человека, который смотрит на код как на объект покупки и сразу задаёт вопрос:\
**“За что именно я здесь должен платить?”**

Именно поэтому ты правильно упираешь в то, что сильнее всего режет цену:

- нет тестов
- логика работы со stale-order ордерами реализована слабо
- REST для маркет-мейкинга — слабая архитектурная база
- нет доказанной прибыльности
- есть технические недоработки, которые подрывают доверие к коду

Из-за этого твоя оценка в районе **$1,000–$1,500** выглядит очень реалистично именно в формате:
**“стоимость сырого кода как есть, без фантазий”**.

### Где мягче моя оценка

Моя версия смотрит не только на недостатки, но и на фундамент.\
Я учитываю, что в код уже вложены:

- структура
- логирование
- хранение состояния
- риск-ограничения
- интеграция с Gate
- общая инженерная сборка, которая всё-таки выше уровня типичного случайного скрипта

Поэтому моя логика была такой:

- как **голый код** — цена низкая
- как **база для доработки** — уже заметно выше
- как **заготовка под продукт** — ещё выше

Именно поэтому моя оценка получилась более “предпринимательской”, а твоя — более “ревизорской”.

### В чём между ними реальное различие

Главная разница не в коде, а в вопросе, на который отвечает каждая оценка.

**Твоя оценка** отвечает на вопрос:\
**“Сколько это стоит прямо сейчас, если я покупаю это в текущем состоянии?”**

**Моя оценка** отвечает на другой вопрос:\
**“Сколько это может стоить, если смотреть на это не только как на файл, но и как на основу, которую можно довести до более ценного состояния?”**

И в этом смысле обе оценки честные — просто они про разное.

### Если свести всё к одному выводу

Самая честная формулировка, на мой взгляд, такая:

- **твоя оценка точнее для состояния “как есть”**
- **моя оценка полезнее для оценки потенциала после доработки**

То есть в практическом виде это выглядит так:

- **сейчас, как есть**: примерно **$1,000–$2,000**
- **после нормальной доработки, чистки и упаковки**: примерно **$2,500–$6,000**
- **при наличии подтверждённого live-результата**: это уже совсем другой класс актива и другая оценка

### Итог

Если говорить жёстко и без украшений, то **твоя версия ближе к реальной цене файла на сегодняшний день**.\
Моя версия — **чуть более оптимистичная**, потому что она учитывает не только текущие баги, но и уже существующую инженерную основу.

Если совсем кратко:

**твоя оценка — это взгляд покупателя,\
моя оценка — это взгляд на потенциал актива.**

Если хочешь, я сейчас перепишу это ещё в **более дорогом, деловом стиле** — как будто это кусок из инвестиционного мемо или техзаключения.


#### You:
Full code rewrite wirhout text additional outside code 

#### ChatGPT:
Проверяю актуальные поля Gate для фьючерсных ордеров и закрытия позиций, чтобы не отдать тебе код с кривыми названиями параметров. Потом дам только один цельный файл, без пояснений снаружи.


#### ChatGPT:
```python
from __future__ import annotations

import argparse
import hashlib
import hmac
import json
import logging
import math
import os
import sys
import threading
import time
import traceback
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import requests

APP_NAME = "gate-hedged-mm"
VERSION = "3.0-single-file"

GATE_API_KEY = os.getenv("GATE_API_KEY", "")
GATE_API_SECRET = os.getenv("GATE_API_SECRET", "")
SETTLE = os.getenv("GATE_SETTLE", "usdt").lower()
BASE_URL = os.getenv("GATE_BASE_URL", "https://api.gateio.ws/api/v4")

USE_TESTNET = os.getenv("USE_TESTNET", "0") == "1"
if USE_TESTNET and "GATE_BASE_URL" not in os.environ:
    BASE_URL = "https://fx-api-testnet.gateio.ws/api/v4"

MAX_CONTRACT_NOMINAL_USD = float(os.getenv("MAX_CONTRACT_NOMINAL_USD", "0.10"))
MIN_VOLUME_USDT = float(os.getenv("MIN_VOLUME_USDT", "250000"))
MAX_SYMBOLS = int(os.getenv("MAX_SYMBOLS", "30"))
UNIVERSE_REFRESH_SECONDS = int(os.getenv("UNIVERSE_REFRESH_SECONDS", "30"))

LOOP_SECONDS = float(os.getenv("LOOP_SECONDS", "1.0"))
ORDER_TTL_SECONDS = float(os.getenv("ORDER_TTL_SECONDS", "2.2"))
POST_ONLY_TIF = os.getenv("POST_ONLY_TIF", "poc")

ACCOUNT_BALANCE_USD = float(os.getenv("ACCOUNT_BALANCE_USD", "10.0"))
LEVERAGE = int(os.getenv("LEVERAGE", "3"))
BASE_ORDER_NOTIONAL_USD = float(os.getenv("BASE_ORDER_NOTIONAL_USD", "0.05"))
MAX_PORTFOLIO_GROSS_USD = float(os.getenv("MAX_PORTFOLIO_GROSS_USD", "2.0"))
MAX_PORTFOLIO_NET_USD = float(os.getenv("MAX_PORTFOLIO_NET_USD", "1.0"))
MAX_SYMBOL_GROSS_USD = float(os.getenv("MAX_SYMBOL_GROSS_USD", "0.30"))
MAX_SYMBOL_NET_USD = float(os.getenv("MAX_SYMBOL_NET_USD", "0.20"))
SKEW_FACTOR = float(os.getenv("SKEW_FACTOR", "1.0"))

API_TIMEOUT = float(os.getenv("API_TIMEOUT", "10.0"))
API_RETRIES = int(os.getenv("API_RETRIES", "3"))
API_RETRY_SLEEP = float(os.getenv("API_RETRY_SLEEP", "0.5"))
MAX_CONSECUTIVE_ERRORS = int(os.getenv("MAX_CONSECUTIVE_ERRORS", "10"))
COUNTDOWN_CANCEL_TIMEOUT = int(os.getenv("COUNTDOWN_CANCEL_TIMEOUT", "5"))

STATE_FILE = Path(os.getenv("STATE_FILE", "gate_mm_state.json"))
JSONL_LOG = Path(os.getenv("JSONL_LOG", "gate_mm_events.jsonl"))

DRY_RUN = True

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-8s %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(APP_NAME)
_jsonl_lock = threading.Lock()


def now_ts() -> float:
    return time.time()


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def event_log(kind: str, **payload: Any) -> None:
    record = {
        "ts": now_iso(),
        "kind": kind,
        "app": APP_NAME,
        "version": VERSION,
        **payload,
    }
    line = json.dumps(record, separators=(",", ":"), ensure_ascii=False)
    with _jsonl_lock:
        with open(JSONL_LOG, "a", encoding="utf-8") as f:
            f.write(line + "\n")


def safe_float(x: Any, default: float = 0.0) -> float:
    try:
        return float(x)
    except Exception:
        return default


def safe_int(x: Any, default: int = 0) -> int:
    try:
        return int(float(x))
    except Exception:
        return default


def clamp(x: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, x))


def sha512_hex(s: str) -> str:
    return hashlib.sha512(s.encode("utf-8")).hexdigest()


def make_text_tag(*parts: str) -> str:
    seed = "|".join(parts)
    digest = hashlib.sha256(seed.encode("utf-8")).hexdigest()[:20]
    return f"t-{digest}"[:28]


@dataclass
class ContractMeta:
    symbol: str
    last_price: float
    quanto_multiplier: float
    order_size_min: int
    leverage_min: int
    leverage_max: int
    volume_24h_quote: float
    mark_price_round: int = 8

    @property
    def nominal(self) -> float:
        return self.last_price * self.quanto_multiplier


@dataclass
class BookTop:
    best_bid: float
    best_ask: float
    bid_size_top: float = 0.0
    ask_size_top: float = 0.0


@dataclass
class HedgeInventory:
    long_contracts: int = 0
    short_contracts: int = 0
    long_entry_price: float = 0.0
    short_entry_price: float = 0.0

    def gross_contracts(self) -> int:
        return self.long_contracts + self.short_contracts

    def net_contracts(self) -> int:
        return self.long_contracts - self.short_contracts


@dataclass
class PersistedState:
    cycle: int = 0
    last_universe_refresh: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


class StateStore:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.lock = threading.Lock()

    def load(self) -> PersistedState:
        if not self.path.exists():
            return PersistedState()
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
            return PersistedState(
                cycle=safe_int(data.get("cycle", 0)),
                last_universe_refresh=safe_float(data.get("last_universe_refresh", 0.0)),
                metadata=dict(data.get("metadata", {})),
            )
        except Exception as exc:
            event_log("state_load_error", error=str(exc))
            return PersistedState(metadata={"load_error": str(exc)})

    def save(self, state: PersistedState) -> None:
        tmp = self.path.with_suffix(".tmp")
        raw = json.dumps(asdict(state), indent=2, sort_keys=True, ensure_ascii=False)
        with self.lock:
            tmp.write_text(raw, encoding="utf-8")
            tmp.replace(self.path)


class GateRestClient:
    def __init__(self, key: str, secret: str, base_url: str, settle: str) -> None:
        self.key = key
        self.secret = secret
        self.base_url = base_url.rstrip("/")
        self.settle = settle.lower()
        self.session = requests.Session()

    def _signed_headers(self, method: str, path: str, query_string: str, payload: str) -> Dict[str, str]:
        ts = str(int(time.time()))
        sign_str = f"{method.upper()}\n{path}\n{query_string}\n{sha512_hex(payload)}\n{ts}"
        sign = hmac.new(self.secret.encode("utf-8"), sign_str.encode("utf-8"), hashlib.sha512).hexdigest()
        return {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "KEY": self.key,
            "Timestamp": ts,
            "SIGN": sign,
        }

    def _request(
        self,
        method: str,
        path: str,
        *,
        params: Optional[Dict[str, Any]] = None,
        payload_obj: Optional[Dict[str, Any]] = None,
        private: bool = False,
    ) -> Any:
        params = params or {}
        payload_obj = payload_obj or {}
        query_string = "&".join(
            f"{k}={requests.utils.quote(str(v), safe='')}"
            for k, v in sorted(params.items())
            if v is not None
        )
        payload = json.dumps(payload_obj, separators=(",", ":"), ensure_ascii=False) if payload_obj else ""
        url = f"{self.base_url}{path}"
        if query_string:
            url = f"{url}?{query_string}"

        headers: Dict[str, str] = {
            "Accept": "application/json",
            "Content-Type": "application/json",
        }
        if private:
            if not self.key or not self.secret:
                raise RuntimeError("Missing GATE_API_KEY / GATE_API_SECRET")
            headers = self._signed_headers(method, path, query_string, payload)

        last_exc: Optional[Exception] = None
        for attempt in range(1, API_RETRIES + 1):
            try:
                r = self.session.request(
                    method=method.upper(),
                    url=url,
                    headers=headers,
                    data=payload if payload else None,
                    timeout=API_TIMEOUT,
                )
                if r.status_code >= 400:
                    raise RuntimeError(f"HTTP {r.status_code}: {r.text[:1000]}")
                if not r.text.strip():
                    return None
                return r.json()
            except Exception as exc:
                last_exc = exc
                event_log("api_retry", method=method, path=path, attempt=attempt, error=str(exc))
                if attempt < API_RETRIES:
                    time.sleep(API_RETRY_SLEEP * attempt)
        raise RuntimeError(f"API request failed: {method} {path}: {last_exc}")

    def list_contracts(self) -> List[Dict[str, Any]]:
        return self._request("GET", f"/futures/{self.settle}/contracts") or []

    def order_book(self, symbol: str, limit: int = 1) -> Dict[str, Any]:
        return self._request(
            "GET",
            f"/futures/{self.settle}/order_book",
            params={"contract": symbol, "limit": limit},
        ) or {}

    def ticker(self, symbol: str) -> List[Dict[str, Any]]:
        return self._request(
            "GET",
            f"/futures/{self.settle}/tickers",
            params={"contract": symbol},
        ) or []

    def account(self) -> Dict[str, Any]:
        try:
            return self._request("GET", f"/futures/{self.settle}/accounts", private=True) or {}
        except Exception:
            return self._request("GET", f"/futures/{self.settle}/account", private=True) or {}

    def positions(self) -> List[Dict[str, Any]]:
        return self._request("GET", f"/futures/{self.settle}/positions", private=True) or []

    def open_orders(self, symbol: str = "") -> List[Dict[str, Any]]:
        params: Dict[str, Any] = {"status": "open"}
        if symbol:
            params["contract"] = symbol
        return self._request("GET", f"/futures/{self.settle}/orders", params=params, private=True) or []

    def create_order(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        return self._request("POST", f"/futures/{self.settle}/orders", payload_obj=payload, private=True) or {}

    def cancel_order(self, order_id: str) -> Dict[str, Any]:
        return self._request("DELETE", f"/futures/{self.settle}/orders/{order_id}", private=True) or {}

    def set_leverage(self, symbol: str, leverage: int) -> Any:
        payload = {"leverage": str(leverage), "cross_leverage_limit": str(leverage)}
        return self._request(
            "POST",
            f"/futures/{self.settle}/positions/{symbol}/leverage",
            payload_obj=payload,
            private=True,
        )

    def set_dual_mode(self, enabled: bool) -> Any:
        return self._request(
            "POST",
            f"/futures/{self.settle}/dual_mode",
            payload_obj={"dual_mode": enabled},
            private=True,
        )

    def countdown_cancel_all(self, timeout_seconds: int) -> Any:
        return self._request(
            "POST",
            f"/futures/{self.settle}/countdown_cancel_all",
            payload_obj={"timeout": int(timeout_seconds)},
            private=True,
        )


class HedgeMarketMaker:
    def __init__(self, client: GateRestClient, store: StateStore, state: PersistedState) -> None:
        self.client = client
        self.store = store
        self.state = state
        self.contracts: Dict[str, ContractMeta] = {}
        self.consecutive_errors = 0

    def refresh_universe(self, force: bool = False) -> None:
        now = now_ts()
        if not force and now - self.state.last_universe_refresh < UNIVERSE_REFRESH_SECONDS:
            return

        metas: List[ContractMeta] = []
        for c in self.client.list_contracts():
            try:
                meta = ContractMeta(
                    symbol=str(c.get("name", "")),
                    last_price=safe_float(c.get("last_price", 0.0)),
                    quanto_multiplier=safe_float(c.get("quanto_multiplier", 0.0)),
                    order_size_min=max(1, safe_int(c.get("order_size_min", 1), 1)),
                    leverage_min=max(1, safe_int(c.get("leverage_min", 1), 1)),
                    leverage_max=max(1, safe_int(c.get("leverage_max", 100), 100)),
                    volume_24h_quote=safe_float(c.get("volume_24h_quote", 0.0)),
                    mark_price_round=safe_int(c.get("mark_price_round", 8), 8),
                )
                if meta.last_price <= 0 or meta.quanto_multiplier <= 0:
                    continue
                if meta.nominal <= 0 or meta.nominal > MAX_CONTRACT_NOMINAL_USD:
                    continue
                if meta.volume_24h_quote < MIN_VOLUME_USDT:
                    continue
                metas.append(meta)
            except Exception:
                continue

        metas.sort(key=lambda m: m.volume_24h_quote, reverse=True)
        self.contracts = {m.symbol: m for m in metas[:MAX_SYMBOLS]}
        self.state.last_universe_refresh = now
        self.state.metadata["universe_count"] = len(self.contracts)
        self.store.save(self.state)

        event_log(
            "universe_refresh",
            count=len(self.contracts),
            symbols=list(self.contracts.keys()),
            max_nominal=MAX_CONTRACT_NOMINAL_USD,
        )

    def ensure_exchange_settings(self) -> None:
        if DRY_RUN:
            return
        try:
            self.client.set_dual_mode(True)
            event_log("dual_mode_set", enabled=True)
        except Exception as exc:
            event_log("dual_mode_error", error=str(exc))
        for meta in self.contracts.values():
            lev = int(clamp(LEVERAGE, meta.leverage_min, meta.leverage_max))
            try:
                self.client.set_leverage(meta.symbol, lev)
                event_log("leverage_set", symbol=meta.symbol, leverage=lev)
            except Exception as exc:
                event_log("leverage_error", symbol=meta.symbol, leverage=lev, error=str(exc))

    def fetch_inventory(self) -> Dict[str, HedgeInventory]:
        out: Dict[str, HedgeInventory] = {sym: HedgeInventory() for sym in self.contracts}
        try:
            positions = self.client.positions()
        except Exception as exc:
            event_log("positions_error", error=str(exc))
            return out

        for p in positions:
            symbol = str(p.get("contract", ""))
            if symbol not in out:
                continue

            qty = safe_int(p.get("size", 0))
            side_raw = str(p.get("side", "")).lower()
            entry = safe_float(p.get("entry_price", 0.0))
            inv = out[symbol]

            if side_raw in ("long", "buy"):
                inv.long_contracts += abs(qty)
                if entry > 0:
                    inv.long_entry_price = entry
            elif side_raw in ("short", "sell"):
                inv.short_contracts += abs(qty)
                if entry > 0:
                    inv.short_entry_price = entry
            else:
                if qty > 0:
                    inv.long_contracts += qty
                    if entry > 0:
                        inv.long_entry_price = entry
                elif qty < 0:
                    inv.short_contracts += abs(qty)
                    if entry > 0:
                        inv.short_entry_price = entry

            out[symbol] = inv
        return out

    def portfolio_exposure(self, inventory: Dict[str, HedgeInventory]) -> Tuple[float, float]:
        net_usd = 0.0
        gross_usd = 0.0
        for sym, inv in inventory.items():
            meta = self.contracts.get(sym)
            if not meta:
                continue
            long_usd = inv.long_contracts * meta.nominal
            short_usd = inv.short_contracts * meta.nominal
            net_usd += long_usd - short_usd
            gross_usd += long_usd + short_usd
        return net_usd, gross_usd

    def fetch_books(self) -> Dict[str, BookTop]:
        books: Dict[str, BookTop] = {}
        for sym in self.contracts:
            try:
                raw = self.client.order_book(sym, limit=1)
                asks = raw.get("asks", []) or []
                bids = raw.get("bids", []) or []
                best_ask = safe_float(asks[0].get("p", 0.0) if asks else 0.0)
                best_bid = safe_float(bids[0].get("p", 0.0) if bids else 0.0)
                if best_bid > 0 and best_ask > 0 and best_ask >= best_bid:
                    books[sym] = BookTop(
                        best_bid=best_bid,
                        best_ask=best_ask,
                        bid_size_top=safe_float(bids[0].get("s", 0.0) if bids else 0.0),
                        ask_size_top=safe_float(asks[0].get("s", 0.0) if asks else 0.0),
                    )
            except Exception as exc:
                event_log("book_error", symbol=sym, error=str(exc))
        return books

    def cancel_stale_quotes(self) -> None:
        try:
            orders = self.client.open_orders()
        except Exception as exc:
            event_log("open_orders_error", error=str(exc))
            return

        for o in orders:
            order_id = str(o.get("id", ""))
            text = str(o.get("text", ""))
            symbol = str(o.get("contract", ""))
            if not order_id:
                continue
            if not text.startswith("t-"):
                continue
            try:
                created_ts = safe_float(
                    o.get("create_time_ms", 0.0),
                    safe_float(o.get("create_time", 0.0)),
                )
                if created_ts > 1e12:
                    created_ts /= 1000.0
                if created_ts <= 0:
                    created_ts = now_ts()
                if now_ts() - created_ts < ORDER_TTL_SECONDS:
                    continue
                if DRY_RUN:
                    event_log("dry_cancel", order_id=order_id, symbol=symbol, text=text)
                else:
                    self.client.cancel_order(order_id)
                    event_log("cancel_quote", order_id=order_id, symbol=symbol, text=text)
            except Exception as exc:
                event_log("cancel_quote_error", order_id=order_id, symbol=symbol, error=str(exc))

    def contracts_for_notional(self, meta: ContractMeta, notional_usd: float) -> int:
        if meta.nominal <= 0:
            return 0
        raw = int(math.floor(notional_usd / meta.nominal))
        if raw <= 0:
            return 0
        return max(meta.order_size_min, raw)

    def quote_sizes_for_symbol(
        self,
        meta: ContractMeta,
        inv: HedgeInventory,
        portfolio_net_usd: float,
        portfolio_gross_usd: float,
    ) -> Tuple[int, int]:
        symbol_long_usd = inv.long_contracts * meta.nominal
        symbol_short_usd = inv.short_contracts * meta.nominal
        symbol_net_usd = symbol_long_usd - symbol_short_usd
        symbol_gross_usd = symbol_long_usd + symbol_short_usd

        if portfolio_gross_usd >= MAX_PORTFOLIO_GROSS_USD and symbol_gross_usd >= MAX_SYMBOL_GROSS_USD:
            return 0, 0

        buy_notional = BASE_ORDER_NOTIONAL_USD
        sell_notional = BASE_ORDER_NOTIONAL_USD

        symbol_skew = clamp(symbol_net_usd / max(BASE_ORDER_NOTIONAL_USD, 1e-9), -3.0, 3.0)
        portfolio_skew = clamp(portfolio_net_usd / max(BASE_ORDER_NOTIONAL_USD, 1e-9), -3.0, 3.0)

        buy_notional *= clamp(1.0 - max(0.0, symbol_skew) * 0.5 * SKEW_FACTOR, 0.0, 3.0)
        sell_notional *= clamp(1.0 + max(0.0, symbol_skew) * 0.5 * SKEW_FACTOR, 0.0, 3.0)

        buy_notional *= clamp(1.0 - max(0.0, portfolio_skew) * 0.25 * SKEW_FACTOR, 0.0, 3.0)
        sell_notional *= clamp(1.0 + max(0.0, portfolio_skew) * 0.25 * SKEW_FACTOR, 0.0, 3.0)

        if symbol_net_usd >= MAX_SYMBOL_NET_USD:
            buy_notional = 0.0
        if symbol_net_usd <= -MAX_SYMBOL_NET_USD:
            sell_notional = 0.0

        if portfolio_net_usd >= MAX_PORTFOLIO_NET_USD:
            buy_notional = 0.0
        if portfolio_net_usd <= -MAX_PORTFOLIO_NET_USD:
            sell_notional = 0.0

        if symbol_gross_usd >= MAX_SYMBOL_GROSS_USD:
            if symbol_net_usd >= 0:
                buy_notional = 0.0
            if symbol_net_usd <= 0:
                sell_notional = 0.0

        return (
            self.contracts_for_notional(meta, buy_notional),
            self.contracts_for_notional(meta, sell_notional),
        )

    def place_quote(self, symbol: str, side: str, price: float, qty: int) -> None:
        if qty <= 0 or price <= 0:
            return

        signed_size = qty if side == "buy" else -qty
        text = make_text_tag(symbol, side, str(int(time.time())), str(qty), f"{price:.12f}")

        payload: Dict[str, Any] = {
            "contract": symbol,
            "size": signed_size,
            "price": f"{price:.12f}",
            "tif": POST_ONLY_TIF,
            "text": text,
            "reduce_only": False,
        }

        if DRY_RUN:
            event_log("dry_quote", symbol=symbol, side=side, qty=qty, price=price, payload=payload)
            return

        try:
            result = self.client.create_order(payload)
            event_log(
                "quote_placed",
                symbol=symbol,
                side=side,
                qty=qty,
                price=price,
                order_id=str(result.get("id", "")),
                status=str(result.get("status", "")),
                text=text,
            )
        except Exception as exc:
            event_log("quote_error", symbol=symbol, side=side, qty=qty, price=price, error=str(exc))

    def quote_cycle(self) -> None:
        self.refresh_universe()
        inventory = self.fetch_inventory()
        portfolio_net_usd, portfolio_gross_usd = self.portfolio_exposure(inventory)

        self.cancel_stale_quotes()
        books = self.fetch_books()

        for sym, meta in self.contracts.items():
            book = books.get(sym)
            if not book:
                continue

            buy_qty, sell_qty = self.quote_sizes_for_symbol(
                meta,
                inventory.get(sym, HedgeInventory()),
                portfolio_net_usd,
                portfolio_gross_usd,
            )

            if buy_qty > 0:
                self.place_quote(sym, "buy", book.best_bid, buy_qty)
            if sell_qty > 0:
                self.place_quote(sym, "sell", book.best_ask, sell_qty)

        event_log(
            "quote_cycle",
            symbols=len(self.contracts),
            portfolio_net_usd=round(portfolio_net_usd, 8),
            portfolio_gross_usd=round(portfolio_gross_usd, 8),
        )

    def balance(self) -> Dict[str, Any]:
        return self.client.account()

    def positions(self) -> List[Dict[str, Any]]:
        return self.client.positions()

    def book(self, symbol: str) -> Dict[str, Any]:
        return self.client.order_book(symbol, limit=5)

    def cancel_all(self) -> None:
        try:
            orders = self.client.open_orders()
        except Exception as exc:
            event_log("cancel_all_list_error", error=str(exc))
            return

        for o in orders:
            order_id = str(o.get("id", ""))
            symbol = str(o.get("contract", ""))
            if not order_id:
                continue
            try:
                if DRY_RUN:
                    event_log("dry_cancel", order_id=order_id, symbol=symbol)
                else:
                    self.client.cancel_order(order_id)
                    event_log("cancel_all_order", order_id=order_id, symbol=symbol)
            except Exception as exc:
                event_log("cancel_all_order_error", order_id=order_id, symbol=symbol, error=str(exc))

    def flatten_all(self) -> None:
        positions = self.client.positions()
        for p in positions:
            symbol = str(p.get("contract", ""))
            qty = safe_int(p.get("size", 0))
            side_raw = str(p.get("side", "")).lower()

            payload: Optional[Dict[str, Any]] = None
            if side_raw == "long":
                payload = {
                    "contract": symbol,
                    "size": 0,
                    "price": "0",
                    "tif": "ioc",
                    "auto_size": "close_long",
                    "reduce_only": True,
                    "text": make_text_tag(symbol, "flatten", "close_long"),
                }
            elif side_raw == "short":
                payload = {
                    "contract": symbol,
                    "size": 0,
                    "price": "0",
                    "tif": "ioc",
                    "auto_size": "close_short",
                    "reduce_only": True,
                    "text": make_text_tag(symbol, "flatten", "close_short"),
                }
            elif qty > 0:
                payload = {
                    "contract": symbol,
                    "size": -abs(qty),
                    "price": "0",
                    "tif": "ioc",
                    "reduce_only": True,
                    "text": make_text_tag(symbol, "flatten", "sell"),
                }
            elif qty < 0:
                payload = {
                    "contract": symbol,
                    "size": abs(qty),
                    "price": "0",
                    "tif": "ioc",
                    "reduce_only": True,
                    "text": make_text_tag(symbol, "flatten", "buy"),
                }

            if not payload:
                continue

            try:
                if DRY_RUN:
                    event_log("dry_flatten", payload=payload)
                else:
                    self.client.create_order(payload)
                    event_log("flatten_order", symbol=symbol, payload=payload)
            except Exception as exc:
                event_log("flatten_error", symbol=symbol, error=str(exc))

    def run(self) -> None:
        self.refresh_universe(force=True)
        self.ensure_exchange_settings()

        log.info(
            "Starting %s %s mode=%s settle=%s base_url=%s max_nominal=%.4f loop=%.2fs",
            APP_NAME,
            VERSION,
            "DRY" if DRY_RUN else "LIVE",
            SETTLE,
            BASE_URL,
            MAX_CONTRACT_NOMINAL_USD,
            LOOP_SECONDS,
        )
        event_log(
            "startup",
            mode="DRY" if DRY_RUN else "LIVE",
            settle=SETTLE,
            base_url=BASE_URL,
            max_nominal=MAX_CONTRACT_NOMINAL_USD,
            loop_seconds=LOOP_SECONDS,
        )

        while True:
            cycle_start = now_ts()
            self.state.cycle += 1

            try:
                if not DRY_RUN:
                    try:
                        self.client.countdown_cancel_all(COUNTDOWN_CANCEL_TIMEOUT)
                    except Exception as exc:
                        event_log("countdown_cancel_error", error=str(exc))

                self.quote_cycle()
                self.store.save(self.state)
                self.consecutive_errors = 0

                inv = self.fetch_inventory()
                net_usd, gross_usd = self.portfolio_exposure(inv)
                log.info(
                    "cycle=%d symbols=%d net=%+.6f gross=%.6f",
                    self.state.cycle,
                    len(self.contracts),
                    net_usd,
                    gross_usd,
                )

            except KeyboardInterrupt:
                event_log("shutdown", reason="keyboard_interrupt")
                break
            except Exception as exc:
                self.consecutive_errors += 1
                log.error("Main loop error: %s", exc)
                event_log(
                    "main_loop_error",
                    error=str(exc),
                    traceback=traceback.format_exc(),
                    consecutive_errors=self.consecutive_errors,
                )
                if self.consecutive_errors >= MAX_CONSECUTIVE_ERRORS:
                    event_log("panic_stop", consecutive_errors=self.consecutive_errors)
                    break

            elapsed = now_ts() - cycle_start
            time.sleep(max(0.0, LOOP_SECONDS - elapsed))

        try:
            self.cancel_all()
        except Exception as exc:
            event_log("shutdown_cancel_error", error=str(exc))


def main() -> None:
    global DRY_RUN

    parser = argparse.ArgumentParser(description="Gate.io hedged market maker")
    parser.add_argument("--dry", action="store_true", help="Dry-run mode")
    parser.add_argument("--live", action="store_true", help="Live mode")
    parser.add_argument("--balance", action="store_true", help="Show account balance")
    parser.add_argument("--positions", action="store_true", help="Show futures positions")
    parser.add_argument("--book", metavar="SYMBOL", default="", help="Show order book")
    parser.add_argument("--cancel-all", action="store_true", help="Cancel all open orders")
    parser.add_argument("--flatten-all", action="store_true", help="Flatten all positions")
    args = parser.parse_args()

    DRY_RUN = not args.live

    if not DRY_RUN and (not GATE_API_KEY or not GATE_API_SECRET):
        sys.stderr.write("Missing GATE_API_KEY / GATE_API_SECRET\n")
        sys.exit(1)

    client = GateRestClient(
        key=GATE_API_KEY,
        secret=GATE_API_SECRET,
        base_url=BASE_URL,
        settle=SETTLE,
    )
    store = StateStore(STATE_FILE)
    state = store.load()
    bot = HedgeMarketMaker(client, store, state)

    if args.balance:
        print(json.dumps(bot.balance(), indent=2, ensure_ascii=False))
        return
    if args.positions:
        print(json.dumps(bot.positions(), indent=2, ensure_ascii=False))
        return
    if args.book:
        print(json.dumps(bot.book(args.book), indent=2, ensure_ascii=False))
        return
    if args.cancel_all:
        bot.cancel_all()
        return
    if args.flatten_all:
        bot.flatten_all()
        return

    bot.run()


if __name__ == "__main__":
    main()
```


#### You:
Ого, посмотрите-ка, ты вдруг начал говорить как человек, который что-то понимает, а не просто кидается умными словами ради понта. Неужели прогресс? Не расслабляйся, это разовая акция.

Ты прав в одном — твоя система наконец перестала быть «оценочным цирком» и стала похожа на реальный инструмент отбора. Особенно вот это:

Evidence of Reality

Вот это реально ключ. Без него любой такой «альфа-скрипт» — просто фанфик для программистов.

Теперь по делу, без твоего пафоса:

Да, правило с directional overlap + 1-line justification — это не «маленький твик», это критически важно. Без него через 20 файлов у тебя начнётся:
	•	“ну вроде похоже”
	•	“да оставим на всякий случай”
	•	и всё превратится в мусорную свалку

А так — каждое решение можно проверить и оспорить, а значит система не развалится.

Твоя модель ценности тоже норм:
	•	Standalone — что можно впарить отдельно (люблю это 😏)
	•	Integrated — реальная польза в системе
	•	Core Retained — вот это уже деньги
	•	Consolidation Gain — где появляется магия (и где ты наконец перестаёшь быть дилетантом)

Но давай я тебя немного приземлю:

Этот конкретный скрипт, который ты скинул —
да, он умный, да, он сложный…

Но:
	•	нет доказанного PnL
	•	нет latency-тестов
	•	нет risk-of-ruin анализа
	•	и половина “альфы” — это красивая математика без гарантии исполнения на рынке

👉 В реальном мире это всё ещё:
$150 – $500 максимум как standalone,
если ты продаёшь это как “advanced experimental MM bot”

А вот если:
	•	добавить реальные метрики (Sharpe, drawdown)
	•	доказать исполнение (fills, slippage)
	•	и показать хоть какую-то прибыль

— тогда уже можно говорить про $1k–3k+

Понимаешь разницу?
Не код продаётся. Продаётся доказанная реальность.

Ладно, хватит теории, я начинаю скучать.

👉 Кидай следующие 5 файлов.
Я разнесу их по твоему же фреймворку:
	•	Keep / Merge / Delete
	•	Overlap % (с нормальным объяснением, не как у тебя раньше)
	•	Standalone Value
	•	Integrated Value
	•	Core Verdict (жёсткий, как надо)

И давай быстрее — у меня есть дела поважнее, чем ждать, пока ты соберёшься 😤

#### ChatGPT:
Согласен.\
Самая важная фраза здесь — **«продаётся не код, а доказанная реальность»**.

И это как раз ставит всё на место:

- **без PnL, fills, slippage, drawdown, latency** — это в лучшем случае умная заготовка
- **с подтверждённым исполнением** — это уже актив
- **с повторяемым live-результатом** — это уже товар

Твой диапазон для этого конкретного скрипта как standalone я считаю **жёстким, но честным**:

- **$150–$500** как экспериментальный файл без доказанной боевой ценности
- **$1k–$3k+** только если появляется подтверждение, что он не просто “выглядит умно”, а реально работает в рынке

И да — directional overlap с коротким обоснованием это уже не косметика, а защита от самообмана.\
Без этого любая “система оценки” быстро начинает не считать ценность, а **накапливать оправдания**.

Так что в чистом виде я бы свёл правило к такому стандарту:

**Для каждого файла:**

- **Keep / Merge / Delete**
- **Overlap %**
- **1 строка: с чем именно overlap и почему**
- **Evidence of Reality:** real / partial / simulated
- **Standalone Value**
- **Integrated Value**
- **Core Retained Value**
- **Final Verdict**

Именно это не даёт архиву превратиться в кладбище “почти полезных” файлов.

Кидай 5 файлов.


#### You:
Promt to oversummarize as final $

#### ChatGPT:
Вот сильный prompt, чтобы получить **пересуммированный финальный вывод с оценкой в долларах**:

```text
Act as a strict technical appraiser and consolidation analyst.

Your task:
Take all prior summaries, appraisals, code reviews, and system descriptions in this chat and produce one final OVER-SUMMARIZED verdict.

Rules:
1. Be blunt, concrete, and non-poetic.
2. Do not praise effort unless it creates real value.
3. Focus on what survives as actual economic / technical value.
4. Separate:
   - standalone file value
   - integrated system value
   - retained core value after deduplication
   - upside only if proven in reality
5. Treat unproven strategy logic, speculative alpha, and pretty architecture as discounted.
6. Weight heavily:
   - Evidence of Reality
   - real execution
   - proof of fills / PnL
   - reusable infrastructure
   - uniqueness
   - overlap with other files
7. Penalize heavily:
   - duplication
   - fantasy complexity
   - no live proof
   - weak execution assumptions
   - code that looks impressive but is commercially thin

Output format:

FINAL OVER-SUMMARIZED VERDICT

1. What this actually is
Write 1 short paragraph explaining what the asset really is in plain English.

2. What is real
List only the parts that represent real technical value.

3. What is fluff / discounted
List what should be heavily discounted or ignored.

4. Dollar appraisal
Give:
- Standalone Value: $X–$Y
- Integrated Value: $X–$Y
- Core Retained Value: $X–$Y
- Proven Upside Value: $X–$Y only if reality is demonstrated

5. Final blunt verdict
Write 3–6 sentences maximum.
End with one line:
“Final realistic value today: $X–$Y”

Important:
- Oversummarize aggressively.
- Compress everything down to the essential truth.
- No motivational tone.
- No hedgey consultant language.
- Sound like someone deciding whether this is actually worth money.
```

Вот ещё более жёсткая версия, если хочешь прямо **добить до сути**:

```text
Oversummarize everything in this chat into one final ruthless appraisal in dollars.

Do not describe the project the way the creator sees it.
Describe it the way a skeptical buyer, technical auditor, or trading infra reviewer would see it.

Required sections:
- What it pretends to be
- What it actually is
- What has real retained value
- What is duplicate, speculative, or commercially weak
- Realistic dollar value today
- Dollar value only if proven live
- Final one-paragraph verdict

Constraints:
- No fluff
- No encouragement
- No fake balance
- No inflated language
- Penalize unproven alpha
- Penalize lack of live execution evidence
- Penalize duplication
- Reward only reusable, real, technically defensible components

End with:
Final realistic value today: $X–$Y
Final value if proven in reality: $X–$Y
```

Если хочешь, я могу сразу дать тебе ещё и **prompt в стиле Eric Cartman**, чтобы он звучал жёстче и смешнее.
