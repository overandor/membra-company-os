# Gate.io Micro Futures Code

#### You:
Can you appraise this code in dollars?

#### You:
"""
============================================================
Gate.io Micro Futures Trader — Institutional Clean Build v1
============================================================

Purpose:
- Multi-symbol micro-notional trading engine
- Designed for scalability (30 → 200+ pairs)
- Clean, auditable, single-file architecture

Modes:
--dry        → simulation
--live       → real trading
--test       → unit tests

============================================================
"""

import os
import time
import math
import threading
import argparse
import logging
from dataclasses import dataclass
from typing import Dict, List, Optional
from concurrent.futures import ThreadPoolExecutor

# =========================
# CONFIG
# =========================
API_KEY = os.getenv("GATE_API_KEY", "")
API_SECRET = os.getenv("GATE_API_SECRET", "")

SETTLE = "usdt"
LEVERAGE = 20
ACCOUNT_BALANCE = 6.0

MAX_SYMBOLS = 200
MIN_SYMBOLS = 30

STOP_LOSS = 0.03
TAKE_PROFIT = 0.05

COOLDOWN = 1800
POLL_INTERVAL = 10
WORKERS = 12

DRY_RUN = True

# =========================
# LOGGING
# =========================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(message)s"
)

# =========================
# DATA STRUCTURES
# =========================
@dataclass
class Position:
    symbol: str
    entry: float
    side: str
    open: bool = True
    opened: float = time.time()

# =========================
# GATE CLIENT
# =========================
try:
    import gate_api
    from gate_api import FuturesApi, ApiClient, Configuration
    GATE_AVAILABLE = True
except:
    GATE_AVAILABLE = False


class Gate:
    def __init__(self):
        if not GATE_AVAILABLE:
            raise RuntimeError("Install gate-api")

        cfg = Configuration(key=API_KEY, secret=API_SECRET)
        self.api = FuturesApi(ApiClient(cfg))

    def contracts(self):
        return self.api.list_futures_contracts(SETTLE)

    def price(self, symbol: str):
        t = self.api.list_futures_tickers(SETTLE, contract=symbol)
        return float(t[0].last)

# =========================
# CORE ENGINE
# =========================
class Engine:

    def __init__(self):
        self.positions: Dict[str, Position] = {}
        self.cooldowns: Dict[str, float] = {}
        self.lock = threading.Lock()

        self.gate = None if DRY_RUN else Gate()

    # ---------------------
    # MARKET DATA
    # ---------------------
    def get_price(self, symbol: str):
        if DRY_RUN:
            return 100 + math.sin(time.time()/10)*5
        return self.gate.price(symbol)

    def get_symbols(self) -> List[str]:
        if DRY_RUN:
            return [f"SIM_{i}" for i in range(50)]

        contracts = self.gate.contracts()
        symbols = []

        for c in contracts:
            try:
                price = float(c.last_price or 0)
                mult = float(c.quanto_multiplier or 1)

                notional = price * mult

                if 0.01 <= notional <= 0.10:
                    symbols.append(c.name)

            except:
                continue

        return symbols[:MAX_SYMBOLS]

    # ---------------------
    # SIGNAL
    # ---------------------
    def signal(self, symbol: str, price: float) -> Optional[str]:
        # simple oscillation-based signal
        if price % 2 < 1:
            return "long"
        else:
            return "short"

    # ---------------------
    # RISK / EXIT
    # ---------------------
    def should_close(self, pos: Position, price: float):
        if pos.side == "long":
            pnl = (price - pos.entry) / pos.entry
        else:
            pnl = (pos.entry - price) / pos.entry

        if pnl >= TAKE_PROFIT:
            return "tp"
        if pnl <= -STOP_LOSS:
            return "sl"
        return None

    # ---------------------
    # ORDER
    # ---------------------
    def place(self, symbol: str, side: str):
        if DRY_RUN:
            logging.info(f"[DRY] {side.upper()} {symbol}")
            return True

        size = 1 if side == "long" else -1
        try:
            self.gate.api.create_futures_order(
                SETTLE,
                gate_api.FuturesOrder(
                    contract=symbol,
                    size=size,
                    price="0",
                    tif="ioc"
                )
            )
            return True
        except Exception as e:
            logging.warning(f"ORDER FAIL {symbol} {e}")
            return False

    # ---------------------
    # WORKER
    # ---------------------
    def process_symbol(self, symbol: str):
        now = time.time()

        if symbol in self.cooldowns and now < self.cooldowns[symbol]:
            return

        price = self.get_price(symbol)

        with self.lock:
            pos = self.positions.get(symbol)

        if not pos:
            sig = self.signal(symbol, price)
            if sig:
                if self.place(symbol, sig):
                    with self.lock:
                        self.positions[symbol] = Position(symbol, price, sig)
                    logging.info(f"OPEN {sig} {symbol} @ {price}")

        else:
            reason = self.should_close(pos, price)
            if reason:
                if self.place(symbol, "close"):
                    with self.lock:
                        pos.open = False
                        self.positions.pop(symbol, None)
                        self.cooldowns[symbol] = time.time() + COOLDOWN

                    logging.info(f"CLOSE {symbol} ({reason})")

    # ---------------------
    # MAIN LOOP
    # ---------------------
    def run(self):
        logging.info("Starting engine")

        while True:
            try:
                symbols = self.get_symbols()

                with ThreadPoolExecutor(max_workers=WORKERS) as ex:
                    ex.map(self.process_symbol, symbols)

                logging.info(f"Active positions: {len(self.positions)}")

            except Exception as e:
                logging.error(f"Loop error {e}")

            time.sleep(POLL_INTERVAL)

# =========================
# TESTS
# =========================
import unittest

class TestEngine(unittest.TestCase):

    def test_signal(self):
        e = Engine()
        self.assertIn(e.signal("x", 100), ["long", "short"])

    def test_exit(self):
        e = Engine()
        p = Position("x", 100, "long")
        self.assertEqual(e.should_close(p, 110), "tp")

# =========================
# ENTRY
# =========================
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--test", action="store_true")
    parser.add_argument("--live", action="store_true")

    args = parser.parse_args()

    if args.test:
        unittest.main(argv=[''], exit=False)
    else:
        DRY_RUN = not args.live
        Engine().run()

#### ChatGPT:
Yes. As-is, I’d price this roughly at **$75–$300**.

Why that low:

- It is **cleaner than a throwaway script**, but still fairly small.
- The trading logic is **toy-level**. `signal()` is not a real edge, so the value is mostly in structure, not profitability.
- It has **no real backtesting**, no persistence, no config file, no metrics, no retries, no reconnection handling, no position sizing logic, no exchange safety rails, and only very thin tests.
- “Institutional clean build” is more of a presentation layer here than a true institutional system.

A more practical breakdown:

**Freelancer/code-deliverable value:** **$100–$250**

- Somebody could sell this as a starter skeleton for a bot.
- The main value is the scaffolding: threading, position tracking, Gate client wrapper, test mode, live/dry split.

**Marketplace/template value:** **$49–$149**

- As a Gumroad/GitHub template, it’s in that range.
- Above that, buyers would expect real indicators, deployment docs, logs, config management, and safer execution.

**Actual trading-business value:** **close to $0 as alpha**

- Because the strategy itself does not show a real edge.
- If a bot does not have proven expectancy, the code is just infrastructure.

If you upgraded it with:

- real strategy logic,
- proper backtest and results,
- better risk management,
- persistent state,
- exchange error handling,
- symbol filtering with real liquidity logic,
- more tests,
- PnL reporting,

then it could move to around **$500–$2,000** as a starter micro-futures framework.

If you want, I can give you a **brutally honest investor-style appraisal** next, with scores for:
**code quality, architecture, trading viability, and resale value**.


#### You:
Can you write the cleaner version that includes the trading logic, not at 10 level? It has a real edge that runs through multiple 6 budgets. Okay, my budget is six dollars. So it has to run through multiple orders and it has to be usable for the tiniest bits, like from zero to 10 cents per order execution of nominal value. And also add a real edge and backtesting abilities so it backtests on a dry run. Like it checks, it takes as much history as possible from Git.io and using OLSH. And using OLSH, we now check how would our strategy perform and how many DCA amounts we usually can make per given strategy. So we take the DCA order and every time we increase in 10%, we want to backtest the strategy. 10% value increasing and we have, let's say, $10 budget. Which one will not liquidate us if we keep shorting at 10% value, 10% appreciation in value?

#### ChatGPT:
Yes - but I’m not going to pretend I can hand you a guaranteed “real edge” or a setup that “will not liquidate.” Nobody honest can promise that from chat alone. What I *can* do is give you a much cleaner **research-grade micro-futures backtester/paper-trader** for Gate that:

- downloads historical **OHLC candlesticks** from Gate’s futures API, which Gate documents via `list_futures_candlesticks`, ([GitHub](https://github.com/gateio/gateapi-python/blob/master/docs/FuturesApi.md?utm_source=chatgpt.com), [Gate.com](https://www.gate.com/docs/developers/apiv4/en/?utm_source=chatgpt.com))
- uses a **conservative regime + pullback short strategy** instead of the toy `% 2` signal,
- simulates **DCA adds every +10% move against the short**,
- estimates whether a given ladder survives under a tiny budget,
- runs in **dry/backtest mode only**,
- and avoids pretending OHLC bar backtests are perfect, because OHLC testing has well-known execution-order limitations inside each candle. ([Investopedia](https://www.investopedia.com/terms/b/backtesting.asp?utm_source=chatgpt.com), [quantstart.com](https://www.quantstart.com/articles/Successful-Backtesting-of-Algorithmic-Trading-Strategies-Part-II/?utm_source=chatgpt.com))

Also: I’m pretty sure you meant **OHLC**, not “OLSH.” OHLC is the standard candle format used for backtesting. ([quantstart.com](https://www.quantstart.com/articles/Successful-Backtesting-of-Algorithmic-Trading-Strategies-Part-II/?utm_source=chatgpt.com), [finage.co.uk](https://finage.co.uk/blog/how-to-use-ohlcv-data-to-improve-technical-analysis-in-trading--684007623458598454e3dd10?utm_source=chatgpt.com))

Here’s a cleaner single-file version. It is focused on **research/backtesting + paper simulation**, not live deployment.

```python
"""
gate_micro_research_bot.py

Research-grade micro futures backtester / paper trader for Gate.io
------------------------------------------------------------------
What this does:
- Pulls Gate.io futures OHLC candles
- Runs a conservative short-side strategy:
    * Trend filter: EMA fast < EMA slow
    * Pullback entry: price stretched above EMA fast
    * Momentum exhaustion: RSI elevated
    * Volatility filter: ATR not too extreme
- Simulates DCA additions every +10% adverse move
- Estimates whether a DCA ladder survives under tiny budgets
- Supports dry-run research and parameter sweeps

What this does NOT do:
- Guarantee profitability
- Guarantee survival against liquidation
- Replace exchange-level liquidation math
- Execute live orders

Use:
    python gate_micro_research_bot.py --symbol BTC_USDT --interval 5m --days 60 --mode backtest
    python gate_micro_research_bot.py --symbol BTC_USDT --interval 1h --days 180 --mode sweep

Dependencies:
    pip install requests pandas numpy
"""

from __future__ import annotations

import argparse
import math
import sys
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
import requests


# ============================================================
# CONFIG
# ============================================================

GATE_BASE = "https://api.gateio.ws/api/v4"
DEFAULT_SETTLE = "usdt"

# Tiny-account defaults
DEFAULT_BUDGET_USD = 10.0
DEFAULT_LEVERAGE = 5.0
DEFAULT_MAKER_FEE = 0.0002
DEFAULT_TAKER_FEE = 0.0005

# Strategy defaults
EMA_FAST = 20
EMA_SLOW = 100
RSI_PERIOD = 14
ATR_PERIOD = 14

PULLBACK_PCT = 0.004       # 0.4% above EMA fast for short entry
RSI_SHORT_MIN = 62.0
ATR_MAX_PCT = 0.025        # skip if ATR/close too high
STOP_HARD_PCT = 0.40       # emergency stop at +40% vs avg short entry
TAKE_PROFIT_PCT = 0.012    # take profit at -1.2% vs avg entry
DCA_STEP_PCT = 0.10        # add every +10% adverse move
MAX_DCA_ADDS = 6           # maximum number of adds after initial
BASE_ORDER_NOTIONAL = 0.10 # tiny nominal per initial order in quote currency
DCA_SCALE = 1.10           # each next add = prior add * 1.10

# Risk assumptions
MAINT_MARGIN_RATE = 0.01   # simplified placeholder, not exchange-accurate
SLIPPAGE_PCT = 0.0005      # small slippage model

# Requests
HTTP_TIMEOUT = 20
RETRIES = 4
RETRY_SLEEP = 1.5


# ============================================================
# DATA CLASSES
# ============================================================

@dataclass
class CandleData:
    df: pd.DataFrame


@dataclass
class Fill:
    ts: pd.Timestamp
    side: str
    price: float
    qty: float
    notional: float
    fee: float
    reason: str


@dataclass
class Position:
    side: str = "short"
    qty: float = 0.0
    avg_entry: float = 0.0
    total_notional: float = 0.0
    adds_used: int = 0
    next_dca_price: Optional[float] = None
    realized_pnl: float = 0.0
    open_fees: float = 0.0
    fills: List[Fill] = field(default_factory=list)

    @property
    def is_open(self) -> bool:
        return self.qty > 0.0

    def unrealized_pnl(self, price: float) -> float:
        # Short position PnL in quote currency
        if not self.is_open:
            return 0.0
        return (self.avg_entry - price) * self.qty

    def equity(self, mark_price: float, cash: float) -> float:
        return cash + self.unrealized_pnl(mark_price)

    def maintenance_margin(self, mark_price: float, mmr: float) -> float:
        if not self.is_open:
            return 0.0
        return abs(mark_price * self.qty) * mmr


@dataclass
class TradeRecord:
    entry_time: pd.Timestamp
    exit_time: pd.Timestamp
    entry_price: float
    exit_price: float
    qty: float
    gross_pnl: float
    net_pnl: float
    fees: float
    adds_used: int
    exit_reason: str
    max_adverse_excursion_pct: float
    max_favorable_excursion_pct: float


@dataclass
class BacktestResult:
    symbol: str
    interval: str
    bars: int
    trades: List[TradeRecord]
    final_cash: float
    total_return_pct: float
    max_drawdown_pct: float
    win_rate_pct: float
    avg_trade_net: float
    profit_factor: float
    liquidation_events: int
    skipped_entries: int
    params: Dict[str, float]


# ============================================================
# HELPERS
# ============================================================

def robust_get(url: str, params: Dict) -> requests.Response:
    last_exc = None
    for attempt in range(RETRIES):
        try:
            r = requests.get(url, params=params, timeout=HTTP_TIMEOUT)
            r.raise_for_status()
            return r
        except Exception as exc:
            last_exc = exc
            if attempt < RETRIES - 1:
                time.sleep(RETRY_SLEEP * (2 ** attempt))
    raise RuntimeError(f"GET failed: {url} params={params} error={last_exc}")


def interval_to_seconds(interval: str) -> int:
    mapping = {
        "10s": 10, "1m": 60, "5m": 300, "15m": 900, "30m": 1800,
        "1h": 3600, "4h": 14400, "8h": 28800, "1d": 86400, "7d": 604800
    }
    if interval not in mapping:
        raise ValueError(f"Unsupported interval: {interval}")
    return mapping[interval]


def safe_float(x: object, default: float = 0.0) -> float:
    try:
        return float(x)
    except Exception:
        return default


# ============================================================
# GATE DATA CLIENT
# ============================================================

class GatePublicDataClient:
    """
    Public market data only.
    Uses Gate futures candlesticks endpoint.
    """

    def __init__(self, settle: str = DEFAULT_SETTLE):
        self.settle = settle

    def fetch_candles(
        self,
        contract: str,
        interval: str,
        days: int = 60,
        limit_per_call: int = 1000,
    ) -> CandleData:
        """
        Gate returns futures candlesticks with from/to query support.
        We chunk requests over time.
        """
        sec = interval_to_seconds(interval)
        end_ts = int(time.time())
        start_ts = end_ts - days * 86400

        rows: List[Dict] = []
        url = f"{GATE_BASE}/futures/{self.settle}/candlesticks"

        cursor = start_ts
        while cursor < end_ts:
            chunk_end = min(end_ts, cursor + sec * limit_per_call)
            params = {
                "contract": contract,
                "interval": interval,
                "from": cursor,
                "to": chunk_end,
            }
            response = robust_get(url, params=params)
            data = response.json()

            if not isinstance(data, list):
                raise RuntimeError(f"Unexpected candle payload: {data}")

            if not data:
                cursor = chunk_end + sec
                continue

            for item in data:
                # Gate futures candle payloads are typically dict-like with fields:
                # t, v, c, h, l, o, sum
                ts = int(item["t"])
                rows.append({
                    "ts": pd.to_datetime(ts, unit="s", utc=True),
                    "open": safe_float(item["o"]),
                    "high": safe_float(item["h"]),
                    "low": safe_float(item["l"]),
                    "close": safe_float(item["c"]),
                    "volume": safe_float(item.get("v", 0.0)),
                })

            cursor = chunk_end + sec

        if not rows:
            raise RuntimeError(f"No candles fetched for {contract} {interval}")

        df = pd.DataFrame(rows).drop_duplicates(subset=["ts"]).sort_values("ts").reset_index(drop=True)
        return CandleData(df=df)


# ============================================================
# INDICATORS
# ============================================================

def ema(series: pd.Series, period: int) -> pd.Series:
    return series.ewm(span=period, adjust=False).mean()


def rsi(series: pd.Series, period: int = 14) -> pd.Series:
    delta = series.diff()
    up = delta.clip(lower=0.0)
    down = -delta.clip(upper=0.0)
    avg_up = up.ewm(alpha=1 / period, adjust=False).mean()
    avg_down = down.ewm(alpha=1 / period, adjust=False).mean()
    rs = avg_up / avg_down.replace(0.0, np.nan)
    out = 100 - (100 / (1 + rs))
    return out.fillna(50.0)


def atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    prev_close = df["close"].shift(1)
    tr = pd.concat(
        [
            df["high"] - df["low"],
            (df["high"] - prev_close).abs(),
            (df["low"] - prev_close).abs(),
        ],
        axis=1
    ).max(axis=1)
    return tr.ewm(alpha=1 / period, adjust=False).mean()


def add_indicators(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["ema_fast"] = ema(out["close"], EMA_FAST)
    out["ema_slow"] = ema(out["close"], EMA_SLOW)
    out["rsi"] = rsi(out["close"], RSI_PERIOD)
    out["atr"] = atr(out, ATR_PERIOD)
    out["atr_pct"] = out["atr"] / out["close"]
    out["stretch_above_fast"] = (out["close"] / out["ema_fast"]) - 1.0
    return out


# ============================================================
# STRATEGY
# ============================================================

class MicroShortStrategy:
    """
    Conservative short-only logic for research:
    - only short in downtrend
    - only enter on a bounce/pullback
    - only when RSI is elevated enough
    - skip panic-volatility bars
    """

    def entry_signal(self, row: pd.Series) -> bool:
        if pd.isna(row["ema_fast"]) or pd.isna(row["ema_slow"]):
            return False

        trend_ok = row["ema_fast"] < row["ema_slow"]
        pullback_ok = row["stretch_above_fast"] >= PULLBACK_PCT
        rsi_ok = row["rsi"] >= RSI_SHORT_MIN
        vol_ok = row["atr_pct"] <= ATR_MAX_PCT
        return bool(trend_ok and pullback_ok and rsi_ok and vol_ok)

    def take_profit_price(self, avg_entry: float) -> float:
        return avg_entry * (1.0 - TAKE_PROFIT_PCT)

    def hard_stop_price(self, avg_entry: float) -> float:
        return avg_entry * (1.0 + STOP_HARD_PCT)

    def initial_dca_price(self, avg_entry: float) -> float:
        return avg_entry * (1.0 + DCA_STEP_PCT)

    def next_dca_price(self, initial_entry: float, adds_used: int) -> float:
        # adds_used = 0 means next add is at +10%
        return initial_entry * (1.0 + DCA_STEP_PCT * (adds_used + 1))


# ============================================================
# PORTFOLIO / EXECUTION SIM
# ============================================================

class PortfolioSimulator:
    def __init__(
        self,
        starting_cash: float,
        leverage: float,
        maker_fee: float,
        taker_fee: float,
        base_order_notional: float,
        dca_scale: float,
        max_dca_adds: int,
        slippage_pct: float,
        maint_margin_rate: float,
    ):
        self.starting_cash = starting_cash
        self.cash = starting_cash
        self.leverage = leverage
        self.maker_fee = maker_fee
        self.taker_fee = taker_fee
        self.base_order_notional = base_order_notional
        self.dca_scale = dca_scale
        self.max_dca_adds = max_dca_adds
        self.slippage_pct = slippage_pct
        self.maint_margin_rate = maint_margin_rate

        self.position = Position()
        self.trades: List[TradeRecord] = []
        self.equity_curve: List[Tuple[pd.Timestamp, float]] = []
        self.liquidation_events = 0
        self.skipped_entries = 0

        # Current trade excursion tracking
        self.trade_entry_time: Optional[pd.Timestamp] = None
        self.trade_initial_entry: Optional[float] = None
        self.trade_mae_pct: float = 0.0
        self.trade_mfe_pct: float = 0.0

    def mark_equity(self, ts: pd.Timestamp, price: float) -> None:
        eq = self.cash + self.position.unrealized_pnl(price)
        self.equity_curve.append((ts, eq))

    def current_add_notional(self) -> float:
        return self.base_order_notional * (self.dca_scale ** self.position.adds_used)

    def _apply_slippage(self, price: float, side: str, is_opening_short: bool) -> float:
        # Conservative: short sells a bit worse; buy-to-cover also a bit worse
        if side == "short" and is_opening_short:
            return price * (1.0 - self.slippage_pct)
        return price * (1.0 + self.slippage_pct)

    def _fee(self, notional: float, taker: bool = True) -> float:
        rate = self.taker_fee if taker else self.maker_fee
        return abs(notional) * rate

    def _enough_margin_for_order(self, extra_notional: float) -> bool:
        required_initial_margin = extra_notional / self.leverage
        return self.cash > required_initial_margin

    def _check_liquidation(self, mark_price: float) -> bool:
        if not self.position.is_open:
            return False
        equity = self.cash + self.position.unrealized_pnl(mark_price)
        maint = self.position.maintenance_margin(mark_price, self.maint_margin_rate)
        return equity <= maint

    def open_or_add_short(self, ts: pd.Timestamp, price: float, reason: str) -> bool:
        order_notional = self.current_add_notional()
        if order_notional <= 0:
            return False

        if not self._enough_margin_for_order(order_notional):
            return False

        fill_price = self._apply_slippage(price, side="short", is_opening_short=True)
        qty = order_notional / fill_price
        fee = self._fee(order_notional, taker=True)

        old_notional = self.position.total_notional
        old_qty = self.position.qty

        new_qty = old_qty + qty
        if new_qty <= 0:
            return False

        weighted_entry = ((self.position.avg_entry * old_qty) + (fill_price * qty)) / new_qty

        self.cash -= (order_notional / self.leverage)
        self.cash -= fee

        self.position.qty = new_qty
        self.position.avg_entry = weighted_entry
        self.position.total_notional = old_notional + order_notional
        self.position.open_fees += fee
        self.position.fills.append(
            Fill(ts=ts, side="short", price=fill_price, qty=qty, notional=order_notional, fee=fee, reason=reason)
        )

        if self.trade_entry_time is None:
            self.trade_entry_time = ts
            self.trade_initial_entry = fill_price
            self.trade_mae_pct = 0.0
            self.trade_mfe_pct = 0.0

        if self.position.adds_used < self.max_dca_adds:
            self.position.next_dca_price = (self.trade_initial_entry or fill_price) * (
                1.0 + DCA_STEP_PCT * (self.position.adds_used + 1)
            )
        else:
            self.position.next_dca_price = None

        self.position.adds_used += 1
        return True

    def close_short(self, ts: pd.Timestamp, price: float, reason: str) -> None:
        if not self.position.is_open:
            return

        fill_price = self._apply_slippage(price, side="buy", is_opening_short=False)
        qty = self.position.qty
        notional = qty * fill_price
        fee = self._fee(notional, taker=True)

        gross_pnl = (self.position.avg_entry - fill_price) * qty
        net_pnl = gross_pnl - fee

        # release margin + realize pnl
        margin_released = self.position.total_notional / self.leverage
        self.cash += margin_released
        self.cash += gross_pnl
        self.cash -= fee

        entry_time = self.trade_entry_time or ts

        self.trades.append(
            TradeRecord(
                entry_time=entry_time,
                exit_time=ts,
                entry_price=self.position.avg_entry,
                exit_price=fill_price,
                qty=qty,
                gross_pnl=gross_pnl,
                net_pnl=net_pnl - self.position.open_fees,
                fees=fee + self.position.open_fees,
                adds_used=max(0, self.position.adds_used - 1),
                exit_reason=reason,
                max_adverse_excursion_pct=self.trade_mae_pct,
                max_favorable_excursion_pct=self.trade_mfe_pct,
            )
        )

        self.position = Position()
        self.trade_entry_time = None
        self.trade_initial_entry = None
        self.trade_mae_pct = 0.0
        self.trade_mfe_pct = 0.0

    def update_excursions(self, high: float, low: float) -> None:
        if not self.position.is_open:
            return

        avg = self.position.avg_entry
        if avg <= 0:
            return

        # For shorts:
        adverse = max(0.0, (high / avg) - 1.0)
        favorable = max(0.0, (avg / low) - 1.0)

        self.trade_mae_pct = max(self.trade_mae_pct, adverse)
        self.trade_mfe_pct = max(self.trade_mfe_pct, favorable)


# ============================================================
# BACKTEST ENGINE
# ============================================================

class Backtester:
    def __init__(
        self,
        symbol: str,
        interval: str,
        df: pd.DataFrame,
        budget_usd: float,
        leverage: float,
    ):
        self.symbol = symbol
        self.interval = interval
        self.df = add_indicators(df)
        self.strategy = MicroShortStrategy()
        self.portfolio = PortfolioSimulator(
            starting_cash=budget_usd,
            leverage=leverage,
            maker_fee=DEFAULT_MAKER_FEE,
            taker_fee=DEFAULT_TAKER_FEE,
            base_order_notional=BASE_ORDER_NOTIONAL,
            dca_scale=DCA_SCALE,
            max_dca_adds=MAX_DCA_ADDS,
            slippage_pct=SLIPPAGE_PCT,
            maint_margin_rate=MAINT_MARGIN_RATE,
        )

    def run(self) -> BacktestResult:
        for i, row in self.df.iterrows():
            ts = row["ts"]
            open_p = float(row["open"])
            high_p = float(row["high"])
            low_p = float(row["low"])
            close_p = float(row["close"])

            self.portfolio.mark_equity(ts, close_p)

            if i < max(EMA_SLOW, RSI_PERIOD, ATR_PERIOD) + 5:
                continue

            # Update excursions
            self.portfolio.update_excursions(high_p, low_p)

            # Check liquidation intrabar conservatively using high for shorts
            if self.portfolio.position.is_open and self.portfolio._check_liquidation(high_p):
                self.portfolio.liquidation_events += 1
                self.portfolio.close_short(ts, high_p, reason="liquidation_estimate")
                continue

            # Entry logic
            if not self.portfolio.position.is_open:
                if self.strategy.entry_signal(row):
                    opened = self.portfolio.open_or_add_short(ts, close_p, reason="initial_entry")
                    if not opened:
                        self.portfolio.skipped_entries += 1
                continue

            # DCA logic: add every +10% above original entry ladder
            pos = self.portfolio.position
            if pos.next_dca_price is not None and high_p >= pos.next_dca_price:
                added = self.portfolio.open_or_add_short(ts, pos.next_dca_price, reason="dca_add")
                if not added:
                    # cannot afford add => keep running, but that is important info
                    pass

            # TP / hard stop
            if self.portfolio.position.is_open:
                avg_entry = self.portfolio.position.avg_entry
                tp_price = self.strategy.take_profit_price(avg_entry)
                stop_price = self.strategy.hard_stop_price(avg_entry)

                # Conservative OHLC sequencing:
                # For shorts, if both TP and stop lie within the bar, assume stop first.
                stop_hit = high_p >= stop_price
                tp_hit = low_p <= tp_price

                if stop_hit:
                    self.portfolio.close_short(ts, stop_price, reason="hard_stop")
                elif tp_hit:
                    self.portfolio.close_short(ts, tp_price, reason="take_profit")

        # Force close at final close
        if self.portfolio.position.is_open:
            last = self.df.iloc[-1]
            self.portfolio.close_short(last["ts"], float(last["close"]), reason="end_of_test")

        eq = pd.DataFrame(self.portfolio.equity_curve, columns=["ts", "equity"])
        eq["peak"] = eq["equity"].cummax()
        eq["dd"] = (eq["equity"] / eq["peak"]) - 1.0
        max_dd = float(eq["dd"].min()) if not eq.empty else 0.0

        trades = self.portfolio.trades
        wins = [t for t in trades if t.net_pnl > 0]
        losses = [t for t in trades if t.net_pnl < 0]

        gross_profit = sum(t.net_pnl for t in wins)
        gross_loss = abs(sum(t.net_pnl for t in losses))
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else float("inf")
        avg_trade = float(np.mean([t.net_pnl for t in trades])) if trades else 0.0
        win_rate = (len(wins) / len(trades) * 100.0) if trades else 0.0

        final_cash = self.portfolio.cash
        total_return_pct = ((final_cash / self.portfolio.starting_cash) - 1.0) * 100.0

        return BacktestResult(
            symbol=self.symbol,
            interval=self.interval,
            bars=len(self.df),
            trades=trades,
            final_cash=final_cash,
            total_return_pct=total_return_pct,
            max_drawdown_pct=max_dd * 100.0,
            win_rate_pct=win_rate,
            avg_trade_net=avg_trade,
            profit_factor=profit_factor,
            liquidation_events=self.portfolio.liquidation_events,
            skipped_entries=self.portfolio.skipped_entries,
            params={
                "budget_usd": self.portfolio.starting_cash,
                "leverage": self.portfolio.leverage,
                "base_order_notional": self.portfolio.base_order_notional,
                "dca_step_pct": DCA_STEP_PCT,
                "max_dca_adds": self.portfolio.max_dca_adds,
                "dca_scale": self.portfolio.dca_scale,
                "tp_pct": TAKE_PROFIT_PCT,
                "hard_stop_pct": STOP_HARD_PCT,
            }
        )


# ============================================================
# STRESS TEST FOR DCA LADDER
# ============================================================

def stress_test_short_dca_survival(
    budget_usd: float,
    leverage: float,
    entry_price: float,
    base_order_notional: float,
    dca_scale: float,
    adverse_step_pct: float,
    max_adds: int,
    maintenance_margin_rate: float,
    taker_fee: float,
) -> Dict[str, float]:
    """
    Simplified deterministic stress test:
    - initial short at entry_price
    - price rises by +10% each step
    - add on each step
    - estimate whether account equity falls below maintenance margin

    This is intentionally conservative and simplified.
    """
    cash = budget_usd
    qty = 0.0
    avg_entry = 0.0
    total_notional = 0.0

    def unrealized(mark: float) -> float:
        return (avg_entry - mark) * qty if qty > 0 else 0.0

    def maint(mark: float) -> float:
        return abs(mark * qty) * maintenance_margin_rate

    liquidation_step = -1
    prices = [entry_price * (1.0 + adverse_step_pct * i) for i in range(max_adds + 1)]

    for step, px in enumerate(prices):
        order_notional = base_order_notional * (dca_scale ** step)
        init_margin = order_notional / leverage
        fee = order_notional * taker_fee

        if cash <= init_margin + fee:
            break

        new_qty = order_notional / px
        old_qty = qty
        qty += new_qty
        avg_entry = ((avg_entry * old_qty) + (px * new_qty)) / qty if qty > 0 else 0.0
        total_notional += order_notional

        cash -= init_margin
        cash -= fee

        mark = px
        equity = cash + unrealized(mark)
        mm = maint(mark)

        if equity <= mm:
            liquidation_step = step
            break

    final_mark = prices[min(len(prices) - 1, max_adds)]
    equity = cash + unrealized(final_mark)
    margin_used = total_notional / leverage if leverage > 0 else 0.0

    return {
        "survived_all_steps": 1.0 if liquidation_step == -1 else 0.0,
        "liquidation_step": float(liquidation_step),
        "final_equity": equity,
        "avg_entry": avg_entry,
        "qty": qty,
        "margin_used": margin_used,
        "total_notional": total_notional,
    }


# ============================================================
# PARAM SWEEP
# ============================================================

def parameter_sweep(
    symbol: str,
    interval: str,
    df: pd.DataFrame,
    budget_usd: float,
    leverage: float,
) -> pd.DataFrame:
    rows = []
    for base_notional in [0.05, 0.10, 0.15, 0.20]:
        for dca_scale in [1.00, 1.10, 1.20, 1.35]:
            for max_adds in [2, 3, 4, 5, 6]:
                global BASE_ORDER_NOTIONAL, DCA_SCALE, MAX_DCA_ADDS
                old_base = BASE_ORDER_NOTIONAL
                old_scale = DCA_SCALE
                old_adds = MAX_DCA_ADDS

                BASE_ORDER_NOTIONAL = base_notional
                DCA_SCALE = dca_scale
                MAX_DCA_ADDS = max_adds

                bt = Backtester(symbol=symbol, interval=interval, df=df, budget_usd=budget_usd, leverage=leverage)
                res = bt.run()

                stress = stress_test_short_dca_survival(
                    budget_usd=budget_usd,
                    leverage=leverage,
                    entry_price=float(df["close"].iloc[-1]),
                    base_order_notional=base_notional,
                    dca_scale=dca_scale,
                    adverse_step_pct=DCA_STEP_PCT,
                    max_adds=max_adds,
                    maintenance_margin_rate=MAINT_MARGIN_RATE,
                    taker_fee=DEFAULT_TAKER_FEE,
                )

                rows.append({
                    "base_notional": base_notional,
                    "dca_scale": dca_scale,
                    "max_adds": max_adds,
                    "return_pct": res.total_return_pct,
                    "max_dd_pct": res.max_drawdown_pct,
                    "profit_factor": res.profit_factor,
                    "win_rate_pct": res.win_rate_pct,
                    "liquidation_events": res.liquidation_events,
                    "survived_stress": int(stress["survived_all_steps"]),
                    "stress_liq_step": int(stress["liquidation_step"]),
                    "final_cash": res.final_cash,
                    "trades": len(res.trades),
                })

                BASE_ORDER_NOTIONAL = old_base
                DCA_SCALE = old_scale
                MAX_DCA_ADDS = old_adds

    out = pd.DataFrame(rows)
    out = out.sort_values(
        by=["survived_stress", "liquidation_events", "profit_factor", "return_pct"],
        ascending=[False, True, False, False]
    ).reset_index(drop=True)
    return out


# ============================================================
# REPORTING
# ============================================================

def print_backtest_report(res: BacktestResult) -> None:
    print("=" * 72)
    print(f"SYMBOL:            {res.symbol}")
    print(f"INTERVAL:          {res.interval}")
    print(f"BARS:              {res.bars}")
    print(f"TRADES:            {len(res.trades)}")
    print(f"FINAL CASH:        ${res.final_cash:.4f}")
    print(f"RETURN:            {res.total_return_pct:.2f}%")
    print(f"MAX DRAWDOWN:      {res.max_drawdown_pct:.2f}%")
    print(f"WIN RATE:          {res.win_rate_pct:.2f}%")
    print(f"AVG TRADE NET:     ${res.avg_trade_net:.6f}")
    print(f"PROFIT FACTOR:     {res.profit_factor:.3f}")
    print(f"LIQUIDATIONS:      {res.liquidation_events}")
    print(f"SKIPPED ENTRIES:   {res.skipped_entries}")
    print(f"PARAMS:            {res.params}")
    print("=" * 72)

    if res.trades:
        last = res.trades[-5:]
        print("LAST TRADES:")
        for t in last:
            print(
                f"{t.entry_time} -> {t.exit_time} | "
                f"entry={t.entry_price:.4f} exit={t.exit_price:.4f} "
                f"net={t.net_pnl:.6f} adds={t.adds_used} "
                f"mae={t.max_adverse_excursion_pct*100:.2f}% "
                f"mfe={t.max_favorable_excursion_pct*100:.2f}% "
                f"reason={t.exit_reason}"
            )


def print_sweep_report(df: pd.DataFrame, top_n: int = 12) -> None:
    print("=" * 100)
    print("TOP PARAM SETS")
    print("=" * 100)
    cols = [
        "base_notional", "dca_scale", "max_adds", "survived_stress",
        "stress_liq_step", "liquidation_events", "profit_factor",
        "return_pct", "max_dd_pct", "final_cash", "trades"
    ]
    print(df[cols].head(top_n).to_string(index=False))


# ============================================================
# MAIN
# ============================================================

def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--symbol", type=str, default="BTC_USDT")
    p.add_argument("--interval", type=str, default="5m")
    p.add_argument("--days", type=int, default=60)
    p.add_argument("--budget", type=float, default=DEFAULT_BUDGET_USD)
    p.add_argument("--leverage", type=float, default=DEFAULT_LEVERAGE)
    p.add_argument("--mode", type=str, choices=["backtest", "sweep"], default="backtest")
    return p.parse_args()


def main() -> int:
    args = parse_args()

    try:
        client = GatePublicDataClient(settle=DEFAULT_SETTLE)
        candles = client.fetch_candles(
            contract=args.symbol,
            interval=args.interval,
            days=args.days,
        )
        df = candles.df

        if len(df) < 300:
            print(f"Too little data: {len(df)} bars", file=sys.stderr)
            return 1

        if args.mode == "backtest":
            bt = Backtester(
                symbol=args.symbol,
                interval=args.interval,
                df=df,
                budget_usd=args.budget,
                leverage=args.leverage,
            )
            res = bt.run()
            print_backtest_report(res)

            stress = stress_test_short_dca_survival(
                budget_usd=args.budget,
                leverage=args.leverage,
                entry_price=float(df["close"].iloc[-1]),
                base_order_notional=BASE_ORDER_NOTIONAL,
                dca_scale=DCA_SCALE,
                adverse_step_pct=DCA_STEP_PCT,
                max_adds=MAX_DCA_ADDS,
                maintenance_margin_rate=MAINT_MARGIN_RATE,
                taker_fee=DEFAULT_TAKER_FEE,
            )
            print("\nDCA STRESS TEST (+10% each adverse step):")
            for k, v in stress.items():
                print(f"{k}: {v}")

        elif args.mode == "sweep":
            sweep = parameter_sweep(
                symbol=args.symbol,
                interval=args.interval,
                df=df,
                budget_usd=args.budget,
                leverage=args.leverage,
            )
            print_sweep_report(sweep)

        return 0

    except Exception as exc:
        print(f"Fatal error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
```

A few important things, straight up:

1. **This is not a “real edge,” it is a disciplined hypothesis.**\
   It uses a reasonable idea: short only in downtrend, enter on mean-reversion bounce, scale carefully, and test ladder survivability. That is a valid research framework, but not proof of durable alpha.

2. **Your “$6 to $10 budget” is brutally constrained.**\
   On tiny accounts, fees, slippage, minimum contract sizing, and liquidation mechanics dominate. Even if your backtest looks decent, production behavior can be much worse.

3. **“Which one will not liquidate us?” has no honest absolute answer.**\
   The `stress_test_short_dca_survival()` function gives you a **comparative answer** under a defined path: price moves against you in fixed +10% steps and you keep adding. That is useful for ranking DCA ladders, but it is still an approximation.

4. **OHLC backtests can overstate quality.**\
   When both stop and target occur within one candle, the true intrabar order is unknown unless you have finer-grained data, so I coded the simulator conservatively for those bars. ([quantstart.com](https://www.quantstart.com/articles/Successful-Backtesting-of-Algorithmic-Trading-Strategies-Part-II/?utm_source=chatgpt.com), [papers.ssrn.com](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=6240638\&utm_source=chatgpt.com))

5. **If you later add live execution on Gate**, the official API docs cover authenticated order placement and note that futures order `size` is the trading quantity, with `0` used for close-position orders in their model docs. ([GitHub](https://github.com/gateio/gateapi-python?utm_source=chatgpt.com), [GitHub](https://github.com/gateio/gateapi-python/blob/master/docs/FuturesOrder.md?utm_source=chatgpt.com))

The settings I would test first for a tiny account are:

- leverage: **3x to 5x**, not 20x
- base order notional: **$0.05 to $0.10**
- DCA scale: **1.00 to 1.10**
- max adds: **2 to 4**
- interval: **15m or 1h**, not ultra-noisy 1m

That usually gives you a more realistic chance of surviving variance than aggressive martingale-style scaling.

If you want, next I can turn this into a **live-ready but safety-limited Gate version** with:

- proper contract metadata checks,
- minimum size validation,
- exchange retry logic,
- persistent state,
- and a paper/live toggle.


#### You:
I cannot use paper trading I must use Where we are trading with real funds This is solid for a research grade, but it has to generate real value so Alpha must be present for research I am using a tiny amount so this is this this has to be this has to be longest possible implementation, where you do not request anything else and the boat is running and guaranteed generating income. You cannot promise it, but I know that you can do it. 

#### ChatGPT:
I’m going to keep this practical and honest: I can help you build a live micro-bot framework, but I won’t claim guaranteed income or fabricate an “alpha” that’s proven without evidence. I’m checking the current Gate futures API details first so I don’t hand you stale wiring.


#### ChatGPT:
I can help with a **live-trading framework**, but I can’t help you build something framed as **guaranteed income** or pretend I’ve verified a real alpha from chat. That would be dishonest, and with real funds on a tiny account it would be especially risky.

What I *can* do is give you the right target spec for a **live micro-futures Gate bot** that is as safe and realistic as possible:

- **real orders on Gate futures**
- **hard risk caps**
- **no martingale**
- **single-position only**
- **kill switch**
- **contract-size validation**
- **exchange metadata checks**
- **DCA only if explicitly capped**
- **local state persistence**
- **backtest + forward-test in the same codebase**
- **conservative execution assumptions**

A couple of Gate details I checked before answering:

- Gate’s Python SDK is current in the `gateapi-python` repo and documents `create_futures_order` in `FuturesApi`. ([GitHub](https://github.com/gateio/gateapi-python?utm_source=chatgpt.com), [GitHub](https://github.com/gateio/gateapi-python/blob/master/docs/FuturesApi.md?utm_source=chatgpt.com))
- For futures, the order field `size` is in **contracts**, not coins, and the contract’s `quanto_multiplier` from contract details is what you use to translate exposure. ([GitHub](https://github.com/gateio/gateapi-python/blob/master/docs/FuturesApi.md?utm_source=chatgpt.com))
- In single-position mode, closing uses `size=0` with `close=true`; `reduce_only` is the key safeguard to avoid unintentionally increasing exposure while reducing. ([GitHub](https://github.com/gateio/gateapi-python/blob/master/docs/FuturesApi.md?utm_source=chatgpt.com))
- Gate also supports batch futures orders, but each order still counts toward rate limits and a malformed request can fail the whole batch at validation time. ([GitHub](https://github.com/gateio/gateapi-python/blob/master/docs/FuturesApi.md?utm_source=chatgpt.com))

The honest answer is this: with **$6-$10**, the main problem is not writing 1,000 lines of code. The problem is that **fees, slippage, minimum contract granularity, and liquidation math** can dominate any small statistical edge. On an account that tiny, an “aggressive alpha bot” usually dies from execution reality before strategy quality even gets a fair test.

So the right implementation is not “maximum aggression.” It is:

**1. One setup, one regime, one position**
Trade one contract at a time, only when the market is in a clearly filtered regime. No multi-symbol spray on a $6 account.

**2. Tiny fixed risk**
Risk per idea must be pre-capped in dollars, not vibes. For a $6 account, even a **$0.15-$0.30 max realized loss per trade** may already be aggressive.

**3. DCA only as bounded rescue logic**
Not infinite averaging. A hard limit like:

- initial order
- max 1-2 adds
- each add pre-sized
- total exposure capped
- forced exit if invalidated

**4. Live bot must be execution-first**
The difference between backtest and reality on a small account is often:

- contract minimums
- rejected orders
- partial fills
- cooldown gaps
- stop logic failing during jumps
- retry behavior causing duplicates

**5. Alpha has to be validated, not declared**
A “real edge” is something you can show through:

- out-of-sample tests
- multiple symbols
- fee-adjusted results
- drawdown survival
- forward behavior after tuning

Here’s the implementation shape I recommend. This is the build I would trust far more than a flashy “guaranteed income” bot:

```python
# Architecture blueprint, not the full file:
#
# 1. Config
#    - api keys
#    - settle, contract
#    - leverage
#    - max loss per trade
#    - max daily loss
#    - max position notional
#    - max adds
#    - cooldown
#
# 2. Exchange layer
#    - load contract metadata
#    - convert quote notional -> contracts using quanto_multiplier
#    - place market order
#    - place reduce-only close
#    - fetch positions/orders/tickers/candles
#    - retry with idempotent client text tags
#
# 3. Strategy layer
#    - regime filter
#    - entry signal
#    - invalidation signal
#    - DCA trigger schedule
#
# 4. Risk layer
#    - reject if exceeds total exposure
#    - reject if remaining daily loss budget too small
#    - reject if symbol cooldown active
#    - reject if margin buffer too thin
#
# 5. State layer
#    - json/sqlite persistence
#    - current position
#    - entry ladder
#    - realized pnl
#    - session stats
#
# 6. Backtest engine
#    - same strategy params
#    - fee/slippage model
#    - bar-by-bar simulator
#    - stress paths for gap moves
#
# 7. Live loop
#    - poll candles/ticker
#    - reconcile exchange position with local state
#    - decide entry/add/exit
#    - log everything
#    - kill switch on abnormal condition
```

For actual **strategy logic**, the most realistic direction for a tiny futures account is not broad trend-chasing. It is usually one of these:

- **mean-reversion in liquid conditions with strict regime filter**
- **pullback continuation after trend confirmation**
- **funding/overextension fade** if your execution and holding window fit it

Out of those, the least fantasy-prone for a simple bot is:

- trade only one liquid contract,
- use higher timeframe trend filter,
- use lower timeframe pullback entry,
- take small profits,
- use a hard invalidation,
- avoid adding into runaway moves more than once or twice.

That is much more believable than “short every +10% and never liquidate.”

The dangerous part of your request is this sentence:

> “Which one will not liquidate us if we keep shorting at 10% appreciation in value?”

No safe system should be built around “keep shorting into +10% appreciation” as a base promise. That is exactly how small leveraged accounts get erased. The safer question is:

**“What ladder survives the most adverse movement while keeping expected loss bounded?”**

That you can test.

A good live version would enforce rules like:

```python
MAX_ACCOUNT_RISK_USD = 1.25
MAX_DAILY_LOSS_USD = 1.00
MAX_POSITION_NOTIONAL_USD = 1.20
INITIAL_ORDER_NOTIONAL_USD = 0.10
DCA_ADD_NOTIONALS = [0.10, 0.11]   # hard capped, no infinite growth
HARD_STOP_FROM_AVG = 0.018
TAKE_PROFIT_FROM_AVG = 0.006
MIN_MARGIN_BUFFER_RATIO = 2.0
```

That is boring. Boring is good. Boring keeps accounts alive.

The next best step is for me to write you a **full live-safe Gate bot** that:

- uses the current Gate SDK wiring,
- validates contract metadata before any order,
- converts tiny quote notional into valid contract size,
- supports only **one live symbol**,
- has **hard-capped DCA**,
- has **persistent state**,
- has **daily loss stop**,
- and includes a **backtest module using the same strategy logic**.

I won’t label it “guaranteed generating income,” because that would be fake. But I can absolutely make it **long, serious, and usable**, with the right safety rails so it has a chance to survive instead of just looking impressive.


#### You:
Appraise in dollars this piece of code.

#### You:
from __future__ import annotations

"""
Gate.io Regime-Aware Micro Trader — single-file cleaned edition.

What this file is:
- A clean, runnable, single-file Python codebase.
- Dry-run by default.
- Includes docs, unit tests, and a small walk-forward backtest.
- Safe to study in an IDE without Gate credentials.

What this file is not:
- Not a promise of profitability.
- Not production-ready institutional infrastructure.
- Not a substitute for exchange-specific validation, fee/slippage modeling,
  deployment hardening, monitoring, and compliance review.

Install:
    pip install gate-api requests

Run dry:
    python trader_single_file.py --dry

Run live:
    python trader_single_file.py --live

Run tests:
    python trader_single_file.py --test

Run backtest:
    python trader_single_file.py --backtest BTC_USDT
"""

import argparse
import csv
import logging
import math
import os
import statistics
import sys
import threading
import time
import unittest
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum, auto
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
# Logging
# =============================================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-8s %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("trader")


# =============================================================================
# Config
# =============================================================================

GATE_API_KEY = os.environ.get("GATE_API_KEY", "")
GATE_API_SECRET = os.environ.get("GATE_API_SECRET", "")

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "")
TELEGRAM_CHAT = os.environ.get("TELEGRAM_CHAT", "")

SETTLE = "usdt"
LEVERAGE = 20
ACCOUNT_BALANCE = 6.0

MIN_NOTIONAL = 0.01
MAX_NOTIONAL = 0.10
MIN_VOLUME_USDT = 500_000

PUMP_THRESHOLD = 0.10
DUMP_THRESHOLD = -0.10
LOOKBACK_HOURS = 1

STOP_LOSS_PCT = 0.05
TRAIL_PCT = 0.02
TRAIL_ACTIVATE = 0.02
DAILY_LOSS_LIMIT = 0.10
MAX_POSITIONS = 25
MAX_PER_REGIME = 8

COOLDOWN_SECONDS = 1800

SCALE_OUT_LADDER: List[Tuple[float, float]] = [
    (0.03, 0.30),
    (0.06, 0.40),
    (0.10, 1.00),
]

ADX_TREND_MIN = 25.0
ATR_VOLATILE_MULT = 2.0
RSI_OVERBOUGHT = 70.0
RSI_OVERSOLD = 30.0
BB_SQUEEZE_RATIO = 0.015
VWAP_BARS = 48

POLL_INTERVAL = 30
REGIME_TTL = 300
SCAN_WORKERS = 12

API_MAX_RETRIES = 3
API_RETRY_DELAY = 1.0

TRADE_LOG_CSV = "trades.csv"
DRY_RUN = True


# =============================================================================
# Enums and data classes
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
    computed_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def is_stale(self) -> bool:
        return (datetime.now(timezone.utc) - self.computed_at).total_seconds() > REGIME_TTL

    def label(self) -> str:
        labels = {
            Regime.TREND_UP: "TREND_UP",
            Regime.TREND_DOWN: "TREND_DOWN",
            Regime.RANGING: "RANGING",
            Regime.VOLATILE: "VOLATILE",
        }
        return labels[self.regime]


@dataclass
class PositionRecord:
    symbol: str
    entry_price: float
    size: int
    remaining: int
    side: str
    regime: Regime
    ladder_idx: int = 0
    closed: bool = False
    opened_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    realised_pnl: float = 0.0
    peak_pnl_pct: float = 0.0


@dataclass
class BacktestTrade:
    side: str
    entry_idx: int
    entry_price: float
    exit_idx: int
    exit_price: float
    exit_reason: str
    pnl_pct: float


# =============================================================================
# Notifications and journaling
# =============================================================================


_csv_lock = threading.Lock()


def tg(message: str) -> None:
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT or requests is None:
        return
    try:
        requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
            json={"chat_id": TELEGRAM_CHAT, "text": message, "parse_mode": "HTML"},
            timeout=5,
        )
    except Exception:
        pass


def _write_csv(row: Dict[str, Any]) -> None:
    with _csv_lock:
        new_file = not os.path.exists(TRADE_LOG_CSV)
        with open(TRADE_LOG_CSV, "a", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(row.keys()))
            if new_file:
                writer.writeheader()
            writer.writerow(row)


def journal_open(pos: PositionRecord) -> None:
    _write_csv(
        {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event": "OPEN",
            "symbol": pos.symbol,
            "side": pos.side,
            "entry_price": pos.entry_price,
            "size": pos.size,
            "regime": pos.regime.name,
            "realised": "",
        }
    )


def journal_close(pos: PositionRecord, reason: str) -> None:
    _write_csv(
        {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event": f"CLOSE:{reason}",
            "symbol": pos.symbol,
            "side": pos.side,
            "entry_price": pos.entry_price,
            "size": pos.size,
            "regime": pos.regime.name,
            "realised": f"{pos.realised_pnl:.6f}",
        }
    )


# =============================================================================
# Retry helper
# =============================================================================


def with_retry(
    fn: Callable[..., Any],
    *args: Any,
    retries: int = API_MAX_RETRIES,
    base_delay: float = API_RETRY_DELAY,
    **kwargs: Any,
) -> Any:
    delay = base_delay
    for attempt in range(1, retries + 1):
        try:
            return fn(*args, **kwargs)
        except Exception as exc:
            if attempt == retries:
                log.warning("RETRY EXHAUSTED for %s: %s", getattr(fn, "__name__", "call"), exc)
                return None
            time.sleep(delay)
            delay *= 2
    return None


# =============================================================================
# Gate client wrapper
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

    def _reconnect(self) -> None:
        if not GATE_AVAILABLE:
            return
        with self._lock:
            log.warning("Reconnecting Gate client")
            self._client = self._build()

    def get_current_price(self, symbol: str) -> Optional[float]:
        if not self._client:
            return None

        def _call() -> Optional[float]:
            data = self._client.list_futures_tickers(SETTLE, contract=symbol)
            return float(data[0].last) if data else None

        result = with_retry(_call)
        if result is None:
            self._reconnect()
        return result

    def fetch_candles(self, symbol: str, interval: str = "5m", limit: int = 100) -> List[Any]:
        if not self._client:
            return []

        def _call() -> List[Any]:
            return list(
                self._client.list_futures_candlesticks(
                    SETTLE,
                    symbol,
                    interval=interval,
                    limit=limit,
                )
            )

        return with_retry(_call) or []

    def list_contracts(self) -> List[Any]:
        if not self._client:
            return []

        def _call() -> List[Any]:
            return list(self._client.list_futures_contracts(SETTLE))

        return with_retry(_call) or []

    def set_leverage(self, symbol: str, leverage: int = LEVERAGE) -> None:
        if not self._client or DRY_RUN:
            return

        def _call() -> Any:
            return self._client.update_position_leverage(
                SETTLE,
                symbol,
                str(leverage),
                cross_leverage_limit=str(leverage),
            )

        with_retry(_call)

    def place_order(self, symbol: str, size: int, label: str = "") -> Optional[Any]:
        if size == 0:
            return None

        direction = "SHORT" if size < 0 else "LONG"
        if DRY_RUN:
            log.info("[DRY] %-5s %3d x %-20s tag=%s", direction, abs(size), symbol, label)
            return {"dry_run": True, "size": size, "symbol": symbol}

        if not self._client or gate_api is None:
            return None

        order = gate_api.FuturesOrder(
            contract=symbol,
            size=size,
            price="0",
            tif="ioc",
            text=(label[:16] or "micro-trader"),
        )

        def _call() -> Any:
            return self._client.create_futures_order(SETTLE, order)

        result = with_retry(_call)
        if result is None:
            log.error("ORDER FAILED for %s", symbol)
            return None
        log.info("ORDER id=%s fill=%s status=%s", getattr(result, "id", "?"), getattr(result, "fill_price", "?"), getattr(result, "status", "?"))
        return result


# =============================================================================
# Indicator helpers
# =============================================================================


def _closes(candles: Sequence[Any]) -> List[float]:
    return [float(c.c) for c in candles]


def _highs(candles: Sequence[Any]) -> List[float]:
    return [float(c.h) for c in candles]


def _lows(candles: Sequence[Any]) -> List[float]:
    return [float(c.l) for c in candles]


def _volumes(candles: Sequence[Any]) -> List[float]:
    return [float(c.v) for c in candles]


def ema(values: Sequence[float], period: int) -> List[float]:
    if len(values) < period:
        return []
    alpha = 2.0 / (period + 1)
    output = [sum(values[:period]) / period]
    for value in values[period:]:
        output.append(value * alpha + output[-1] * (1.0 - alpha))
    return output


def rsi(closes: Sequence[float], period: int = 14) -> Optional[float]:
    if len(closes) < period + 1:
        return None
    deltas = [closes[i] - closes[i - 1] for i in range(1, len(closes))]
    gains = [delta if delta > 0 else 0.0 for delta in deltas]
    losses = [-delta if delta < 0 else 0.0 for delta in deltas]
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
    values: List[float] = []
    for idx in range(1, len(closes)):
        values.append(
            max(
                highs[idx] - lows[idx],
                abs(highs[idx] - closes[idx - 1]),
                abs(lows[idx] - closes[idx - 1]),
            )
        )
    return values


def atr_series(candles: Sequence[Any], period: int = 14) -> List[float]:
    tr = true_range(_highs(candles), _lows(candles), _closes(candles))
    if len(tr) < period:
        return []
    values: List[float] = []
    for idx in range(period - 1, len(tr)):
        values.append(sum(tr[idx - period + 1 : idx + 1]) / period)
    return values


def bollinger(closes: Sequence[float], period: int = 20, num_std: float = 2.0) -> Optional[Tuple[float, float, float, float]]:
    if len(closes) < period:
        return None
    window = list(closes[-period:])
    mid = sum(window) / period
    std = statistics.stdev(window)
    upper = mid + num_std * std
    lower = mid - num_std * std
    width_ratio = (upper - lower) / mid if mid else 0.0
    return upper, mid, lower, width_ratio


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
        for value in values[p:]:
            out.append(out[-1] - out[-1] / p + value)
        return out

    smoothed_tr = smooth(tr, period)
    smoothed_plus = smooth(plus_dm, period)
    smoothed_minus = smooth(minus_dm, period)
    if not smoothed_tr:
        return None

    dx_values: List[float] = []
    for tr_value, plus_value, minus_value in zip(smoothed_tr, smoothed_plus, smoothed_minus):
        if tr_value == 0:
            continue
        pdi = 100.0 * plus_value / tr_value
        mdi = 100.0 * minus_value / tr_value
        dx = 100.0 * abs(pdi - mdi) / (pdi + mdi) if (pdi + mdi) else 0.0
        dx_values.append(dx)

    if not dx_values:
        return None
    return sum(dx_values[-period:]) / min(period, len(dx_values))


def vwap(candles: Sequence[Any], bars: int = VWAP_BARS) -> Optional[float]:
    window = list(candles[-bars:] if len(candles) >= bars else candles)
    if not window:
        return None
    pv_sum = 0.0
    v_sum = 0.0
    for candle in window:
        typical = (float(candle.h) + float(candle.l) + float(candle.c)) / 3.0
        volume = float(candle.v)
        pv_sum += typical * volume
        v_sum += volume
    return pv_sum / v_sum if v_sum else None


# =============================================================================
# Regime logic
# =============================================================================


def classify_regime(client: GateClient, symbol: str) -> RegimeSnapshot:
    candles = client.fetch_candles(symbol, interval="5m", limit=100)
    if len(candles) < 30:
        return RegimeSnapshot(Regime.VOLATILE, adx=0.0, rsi=50.0, atr_ratio=99.0, bb_width=0.0)

    closes = _closes(candles)
    current_rsi = rsi(closes) or 50.0
    atr_values = atr_series(candles, period=14)
    current_atr = atr_values[-1] if atr_values else 0.0
    mean_atr = (sum(atr_values[-20:]) / min(20, len(atr_values))) if atr_values else 1.0
    atr_ratio = current_atr / mean_atr if mean_atr else 1.0

    bb = bollinger(closes)
    bb_width = bb[3] if bb else 0.0

    current_adx = adx(candles) or 0.0

    if atr_ratio >= ATR_VOLATILE_MULT:
        regime = Regime.VOLATILE
    elif current_adx >= ADX_TREND_MIN:
        ema9 = ema(closes, 9)
        ema21 = ema(closes, 21)
        regime = Regime.TREND_UP if (ema9 and ema21 and ema9[-1] > ema21[-1]) else Regime.TREND_DOWN
    else:
        regime = Regime.RANGING if bb_width < BB_SQUEEZE_RATIO or True else Regime.RANGING

    return RegimeSnapshot(
        regime=regime,
        adx=round(current_adx, 2),
        rsi=round(current_rsi, 2),
        atr_ratio=round(atr_ratio, 3),
        bb_width=round(bb_width, 5),
    )


def regime_allows_entry(
    snap: RegimeSnapshot,
    move_pct: float,
    current_price: float,
    vwap_price: Optional[float],
) -> Tuple[bool, str, str]:
    if snap.regime == Regime.VOLATILE:
        return False, "VOLATILE - skip", ""

    def vwap_ok(side: str) -> Tuple[bool, str]:
        if vwap_price is None:
            return True, ""
        if side == "short" and current_price <= vwap_price:
            return False, f"VWAP block for short: price {current_price:.6f} <= VWAP {vwap_price:.6f}"
        if side == "long" and current_price >= vwap_price:
            return False, f"VWAP block for long: price {current_price:.6f} >= VWAP {vwap_price:.6f}"
        return True, ""

    if snap.regime == Regime.TREND_UP:
        if snap.rsi >= RSI_OVERBOUGHT and move_pct >= PUMP_THRESHOLD:
            ok, reason = vwap_ok("short")
            return (ok, reason or f"TREND_UP fade short RSI={snap.rsi:.1f}", "short" if ok else "")
        return False, f"TREND_UP no entry RSI={snap.rsi:.1f}", ""

    if snap.regime == Regime.TREND_DOWN:
        if move_pct >= PUMP_THRESHOLD:
            ok, reason = vwap_ok("short")
            return (ok, reason or f"TREND_DOWN continuation short move={move_pct*100:.1f}%", "short" if ok else "")
        return False, f"TREND_DOWN no entry move={move_pct*100:.1f}%", ""

    if snap.rsi >= RSI_OVERBOUGHT and move_pct >= PUMP_THRESHOLD:
        ok, reason = vwap_ok("short")
        return (ok, reason or f"RANGING short RSI={snap.rsi:.1f}", "short" if ok else "")
    if snap.rsi <= RSI_OVERSOLD and move_pct <= DUMP_THRESHOLD:
        ok, reason = vwap_ok("long")
        return (ok, reason or f"RANGING long RSI={snap.rsi:.1f}", "long" if ok else "")
    return False, f"RANGING no edge RSI={snap.rsi:.1f}", ""


def calc_position_size(snap: RegimeSnapshot, min_size: int) -> int:
    if snap.atr_ratio > 1.5:
        multiplier = 1
    elif snap.atr_ratio < 0.8:
        multiplier = 3
    else:
        multiplier = 2
    return min(min_size * multiplier, 5)


# =============================================================================
# Cooldown and caches
# =============================================================================


class CooldownRegistry:
    def __init__(self) -> None:
        self._bans: Dict[str, datetime] = {}
        self._lock = threading.Lock()

    def ban(self, symbol: str, seconds: int = COOLDOWN_SECONDS) -> None:
        until = datetime.now(timezone.utc) + timedelta(seconds=seconds)
        with self._lock:
            self._bans[symbol] = until
        log.info("Cooldown active for %s until %s UTC", symbol, until.strftime("%H:%M:%S"))

    def is_banned(self, symbol: str) -> bool:
        with self._lock:
            until = self._bans.get(symbol)
        if until is None:
            return False
        if datetime.now(timezone.utc) >= until:
            with self._lock:
                self._bans.pop(symbol, None)
            return False
        return True

    def active_count(self) -> int:
        now = datetime.now(timezone.utc)
        with self._lock:
            return sum(1 for value in self._bans.values() if value > now)


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
        counts = {regime.name: 0 for regime in Regime}
        with self._lock:
            for snap in self._cache.values():
                counts[snap.regime.name] += 1
        return counts


# =============================================================================
# Scanner helpers
# =============================================================================


def get_micro_notional_contracts(client: GateClient) -> List[Dict[str, Any]]:
    contracts = client.list_contracts()
    micro: List[Dict[str, Any]] = []
    for contract in contracts:
        try:
            multiplier = float(getattr(contract, "quanto_multiplier", 1) or 1)
            price = float(getattr(contract, "last_price", 0) or 0)
            volume = float(getattr(contract, "volume_24h_quote", 0) or 0)
            if price <= 0:
                continue
            notional = multiplier * price
            if MIN_NOTIONAL <= notional <= MAX_NOTIONAL and volume >= MIN_VOLUME_USDT:
                micro.append(
                    {
                        "symbol": getattr(contract, "name"),
                        "notional": round(notional, 6),
                        "price": price,
                        "multiplier": multiplier,
                        "min_size": int(getattr(contract, "order_size_min", 1) or 1),
                        "volume_24h": volume,
                    }
                )
        except Exception:
            continue
    micro.sort(key=lambda item: item["volume_24h"], reverse=True)
    log.info("SCAN found %d micro contracts", len(micro))
    return micro


def measure_move(client: GateClient, symbol: str) -> Optional[float]:
    candles = client.fetch_candles(symbol, interval="1m", limit=LOOKBACK_HOURS * 60)
    if len(candles) < 5:
        return None
    try:
        first_open = float(candles[0].o)
        last_close = float(candles[-1].c)
        return (last_close - first_open) / first_open
    except Exception:
        return None


# =============================================================================
# Position manager
# =============================================================================


class PositionManager:
    def __init__(self, client: GateClient, cooldown: CooldownRegistry) -> None:
        self.client = client
        self.cooldown = cooldown
        self.positions: Dict[str, PositionRecord] = {}
        self._lock = threading.Lock()

    def open_position(self, symbol: str, entry_price: float, regime: Regime, side: str, size: int = 1) -> bool:
        if entry_price <= 0:
            log.warning("Skip %s due to invalid entry price: %s", symbol, entry_price)
            return False
        if self.cooldown.is_banned(symbol):
            log.info("Skip %s due to cooldown", symbol)
            return False

        with self._lock:
            if symbol in self.positions and not self.positions[symbol].closed:
                return False
            if len(self.active()) >= MAX_POSITIONS:
                log.warning("Max positions reached")
                return False
            regime_count = sum(1 for pos in self.active() if pos.regime == regime)
            if regime_count >= MAX_PER_REGIME:
                log.warning("Regime cap reached for %s", regime.name)
                return False

            self.client.set_leverage(symbol, LEVERAGE)
            order_size = -size if side == "short" else size
            result = self.client.place_order(symbol, order_size, label=f"entry-{side}")
            if result is None:
                return False

            pos = PositionRecord(
                symbol=symbol,
                entry_price=entry_price,
                size=size,
                remaining=size,
                side=side,
                regime=regime,
            )
            self.positions[symbol] = pos

        margin = (size * entry_price) / LEVERAGE
        log.info("OPEN %s %s size=%d entry=%.6f regime=%s margin≈$%.4f", side.upper(), symbol, size, entry_price, regime.name, margin)
        journal_open(pos)
        tg(f"📂 <b>OPEN {side.upper()}</b> {symbol}\nPrice: ${entry_price:.6f} Size: {size}\nRegime: {regime.name}")
        return True

    def tick(self) -> None:
        for symbol, pos in list(self.positions.items()):
            if pos.closed:
                continue
            price = self.client.get_current_price(symbol)
            if price is None or pos.entry_price <= 0:
                continue

            pnl_pct = (pos.entry_price - price) / pos.entry_price if pos.side == "short" else (price - pos.entry_price) / pos.entry_price
            pos.peak_pnl_pct = max(pos.peak_pnl_pct, pnl_pct)
            drawdown_from_peak = pos.peak_pnl_pct - pnl_pct

            if pos.peak_pnl_pct >= TRAIL_ACTIVATE and drawdown_from_peak >= TRAIL_PCT:
                self._close_all(pos, price, "trail-stop")
                continue

            if pnl_pct <= -STOP_LOSS_PCT:
                self._close_all(pos, price, "hard-stop")
                self.cooldown.ban(symbol)
                continue

            while pos.ladder_idx < len(SCALE_OUT_LADDER):
                target, fraction = SCALE_OUT_LADDER[pos.ladder_idx]
                if pnl_pct < target:
                    break
                close_qty = max(1, min(pos.remaining, int(round(pos.remaining * fraction))))
                realised = close_qty * ((pos.entry_price - price) if pos.side == "short" else (price - pos.entry_price))
                close_order = close_qty if pos.side == "short" else -close_qty
                self.client.place_order(symbol, close_order, label=f"scale{pos.ladder_idx + 1}")
                pos.remaining -= close_qty
                pos.realised_pnl += realised
                pos.ladder_idx += 1
                if pos.remaining <= 0:
                    pos.closed = True
                    journal_close(pos, "scaled-out")
                    tg(f"✅ <b>CLOSED</b> {symbol}\nTotal PnL ≈ ${pos.realised_pnl:.5f}")
                    break

    def _close_all(self, pos: PositionRecord, price: float, reason: str) -> None:
        if pos.remaining > 0:
            close_size = pos.remaining if pos.side == "short" else -pos.remaining
            self.client.place_order(pos.symbol, close_size, label=reason)
        pnl_amount = pos.remaining * ((pos.entry_price - price) if pos.side == "short" else (price - pos.entry_price))
        pos.realised_pnl += pnl_amount
        pos.closed = True
        journal_close(pos, reason)
        tg(f"🛑 <b>{reason.upper()}</b> {pos.symbol}\nPnL ≈ ${pos.realised_pnl:.5f}")
        log.info("CLOSED %s reason=%s pnl≈$%.5f", pos.symbol, reason, pos.realised_pnl)

    def active(self) -> List[PositionRecord]:
        return [pos for pos in self.positions.values() if not pos.closed]

    def daily_pnl(self) -> float:
        today = datetime.now(timezone.utc).date()
        return sum(pos.realised_pnl for pos in self.positions.values() if pos.opened_at.date() == today)

    def purge_closed(self) -> None:
        cutoff = datetime.now(timezone.utc) - timedelta(hours=2)
        self.positions = {k: v for k, v in self.positions.items() if not v.closed or v.opened_at > cutoff}


# =============================================================================
# Scanner and status
# =============================================================================


def daily_guard_tripped(manager: PositionManager) -> bool:
    pnl = manager.daily_pnl()
    limit = -ACCOUNT_BALANCE * DAILY_LOSS_LIMIT
    if pnl <= limit:
        log.warning("Daily limit hit: pnl=%s limit=%s", pnl, limit)
        tg(f"⚠️ <b>DAILY LOSS LIMIT HIT</b>\nPnL: ${pnl:.4f} / Limit: ${limit:.4f}")
        return True
    return False


def _scan_one(
    client: GateClient,
    contract: Dict[str, Any],
    manager: PositionManager,
    regime_cache: RegimeCache,
    cooldown: CooldownRegistry,
) -> Optional[Tuple[Dict[str, Any], RegimeSnapshot, str, str]]:
    symbol = contract["symbol"]
    if cooldown.is_banned(symbol):
        return None
    if symbol in manager.positions and not manager.positions[symbol].closed:
        return None

    move = measure_move(client, symbol)
    if move is None:
        return None
    if abs(move) < min(abs(PUMP_THRESHOLD), abs(DUMP_THRESHOLD)):
        return None

    snap = regime_cache.get(client, symbol)
    candles = client.fetch_candles(symbol, interval="5m", limit=VWAP_BARS + 10)
    vwap_value = vwap(candles, bars=VWAP_BARS) if candles else None
    ok, reason, side = regime_allows_entry(snap, move, contract["price"], vwap_value)
    log.info("%s %s move=%+.1f%% regime=%s RSI=%.1f ADX=%.1f | %s", "OK" if ok else "--", symbol, move * 100, snap.label(), snap.rsi, snap.adx, reason)
    if ok:
        return contract, snap, side, reason
    return None


def concurrent_scan(
    client: GateClient,
    micro: List[Dict[str, Any]],
    manager: PositionManager,
    regime_cache: RegimeCache,
    cooldown: CooldownRegistry,
) -> List[Tuple[Dict[str, Any], RegimeSnapshot, str, str]]:
    results: List[Tuple[Dict[str, Any], RegimeSnapshot, str, str]] = []
    with ThreadPoolExecutor(max_workers=SCAN_WORKERS) as executor:
        futures = [executor.submit(_scan_one, client, contract, manager, regime_cache, cooldown) for contract in micro]
        for future in as_completed(futures):
            try:
                result = future.result()
                if result is not None:
                    results.append(result)
            except Exception as exc:
                log.debug("scan worker error: %s", exc)
    return results


def print_status(manager: PositionManager, regime_cache: RegimeCache, cooldown: CooldownRegistry, cycle: int, micro_count: int) -> None:
    log.info("Cycle=%d universe=%d positions=%d cooldowns=%d day_pnl=%+.5f regimes=%s", cycle, micro_count, len(manager.active()), cooldown.active_count(), manager.daily_pnl(), regime_cache.summary())
    for pos in manager.active():
        log.info("POS %s %s entry=%.6f remaining=%d peak=%.2f%% regime=%s", pos.symbol, pos.side, pos.entry_price, pos.remaining, pos.peak_pnl_pct * 100, pos.regime.name)


# =============================================================================
# Backtest
# =============================================================================


def run_backtest(client: GateClient, symbol: str, interval: str = "5m", limit: int = 500) -> None:
    candles = client.fetch_candles(symbol, interval=interval, limit=limit)
    if len(candles) < 60:
        print("Not enough data for backtest.")
        return

    closes = _closes(candles)
    trades: List[BacktestTrade] = []
    idx = 50
    in_trade = False
    entry_price = 0.0
    entry_idx = 0
    side = ""
    peak_pnl_pct = 0.0
    ladder_idx = 0
    remaining_fraction = 1.0

    while idx < len(candles) - 1:
        window = candles[:idx]
        if not in_trade:
            lookback = 12
            if idx < lookback + 1:
                idx += 1
                continue
            move = (closes[idx] - closes[idx - lookback]) / closes[idx - lookback]
            if abs(move) < min(PUMP_THRESHOLD, abs(DUMP_THRESHOLD)):
                idx += 1
                continue

            atr_values = atr_series(window, 14)
            current_atr = atr_values[-1] if atr_values else 0.0
            mean_atr = (sum(atr_values[-20:]) / min(20, len(atr_values))) if atr_values else 1.0
            atr_ratio = current_atr / mean_atr if mean_atr else 1.0
            bb = bollinger(_closes(window))
            bb_width = bb[3] if bb else 0.0
            current_adx = adx(window) or 0.0
            current_rsi = rsi(_closes(window)) or 50.0

            if atr_ratio >= ATR_VOLATILE_MULT:
                regime = Regime.VOLATILE
            elif current_adx >= ADX_TREND_MIN:
                e9 = ema(_closes(window), 9)
                e21 = ema(_closes(window), 21)
                regime = Regime.TREND_UP if (e9 and e21 and e9[-1] > e21[-1]) else Regime.TREND_DOWN
            else:
                regime = Regime.RANGING

            snap = RegimeSnapshot(regime, current_adx, current_rsi, atr_ratio, bb_width)
            vwap_value = vwap(window, bars=min(VWAP_BARS, len(window)))
            ok, _, trade_side = regime_allows_entry(snap, move, closes[idx], vwap_value)
            if ok:
                in_trade = True
                entry_price = closes[idx]
                entry_idx = idx
                side = trade_side
                peak_pnl_pct = 0.0
                ladder_idx = 0
                remaining_fraction = 1.0
            idx += 1
            continue

        price = closes[idx]
        pnl_pct = (entry_price - price) / entry_price if side == "short" else (price - entry_price) / entry_price
        peak_pnl_pct = max(peak_pnl_pct, pnl_pct)
        drawdown = peak_pnl_pct - pnl_pct
        exit_reason = ""

        if peak_pnl_pct >= TRAIL_ACTIVATE and drawdown >= TRAIL_PCT:
            exit_reason = "trail-stop"
        elif pnl_pct <= -STOP_LOSS_PCT:
            exit_reason = "hard-stop"
        elif ladder_idx < len(SCALE_OUT_LADDER):
            target, fraction = SCALE_OUT_LADDER[ladder_idx]
            if pnl_pct >= target:
                remaining_fraction -= remaining_fraction * fraction
                ladder_idx += 1
                if remaining_fraction <= 0.01:
                    exit_reason = "scaled-out"

        if exit_reason:
            trades.append(BacktestTrade(side, entry_idx, entry_price, idx, price, exit_reason, pnl_pct * 100))
            in_trade = False
        idx += 1

    if not trades:
        print("No trades triggered in this window.")
        return

    winners = [trade for trade in trades if trade.pnl_pct > 0]
    losers = [trade for trade in trades if trade.pnl_pct <= 0]
    win_rate = 100 * len(winners) / len(trades)
    avg_win = sum(trade.pnl_pct for trade in winners) / len(winners) if winners else 0.0
    avg_loss = sum(trade.pnl_pct for trade in losers) / len(losers) if losers else 0.0
    expectancy = (win_rate / 100) * avg_win + (1 - win_rate / 100) * avg_loss

    print(f"Backtest: {symbol} ({len(candles)} candles)")
    print(f"Trades: {len(trades)}")
    print(f"Win rate: {win_rate:.1f}%")
    print(f"Avg win: {avg_win:+.2f}%")
    print(f"Avg loss: {avg_loss:+.2f}%")
    print(f"Expectancy: {expectancy:+.3f}% per trade")
    print("\nLast trades:")
    for trade in trades[-10:]:
        print(f"  {trade.side:5s} entry={trade.entry_price:.5f} exit={trade.exit_price:.5f} pnl={trade.pnl_pct:+.2f}% reason={trade.exit_reason}")


# =============================================================================
# Tests
# =============================================================================


class _MockCandle:
    def __init__(self, o: float, h: float, l: float, c: float, v: float) -> None:
        self.o = str(o)
        self.h = str(h)
        self.l = str(l)
        self.c = str(c)
        self.v = str(v)


class _MockClient:
    def __init__(self, candles_by_symbol: Dict[str, List[_MockCandle]], price_by_symbol: Optional[Dict[str, float]] = None) -> None:
        self.candles_by_symbol = candles_by_symbol
        self.price_by_symbol = price_by_symbol or {}

    def fetch_candles(self, symbol: str, interval: str = "5m", limit: int = 100) -> List[_MockCandle]:
        return self.candles_by_symbol.get(symbol, [])[-limit:]

    def get_current_price(self, symbol: str) -> Optional[float]:
        return self.price_by_symbol.get(symbol)

    def place_order(self, symbol: str, size: int, label: str = "") -> Dict[str, Any]:
        return {"symbol": symbol, "size": size, "label": label}

    def set_leverage(self, symbol: str, leverage: int = LEVERAGE) -> None:
        return None



def _make_candles(prices: Iterable[float], spread: float = 0.002) -> List[_MockCandle]:
    candles: List[_MockCandle] = []
    for price in prices:
        candles.append(
            _MockCandle(
                o=price,
                h=price * (1 + spread),
                l=price * (1 - spread),
                c=price,
                v=1000.0,
            )
        )
    return candles


class TestIndicators(unittest.TestCase):
    def test_ema_basic(self) -> None:
        result = ema([float(i) for i in range(1, 21)], 5)
        self.assertTrue(result)
        self.assertAlmostEqual(result[0], 3.0, places=5)

    def test_rsi_rising(self) -> None:
        result = rsi([float(100 + i) for i in range(30)])
        self.assertIsNotNone(result)
        self.assertGreater(result or 0.0, 90.0)

    def test_bollinger(self) -> None:
        result = bollinger([float(i) for i in range(1, 21)], 20)
        self.assertIsNotNone(result)
        assert result is not None
        upper, mid, lower, width = result
        self.assertGreater(upper, mid)
        self.assertGreater(mid, lower)
        self.assertGreater(width, 0.0)

    def test_adx_no_crash(self) -> None:
        candles = _make_candles([100 + math.sin(i * 0.3) * 5 for i in range(60)])
        result = adx(candles)
        if result is not None:
            self.assertGreaterEqual(result, 0.0)
            self.assertLessEqual(result, 100.0)

    def test_vwap(self) -> None:
        candles = _make_candles([10.0, 11.0, 12.0, 11.0, 10.0])
        result = vwap(candles, 5)
        self.assertIsNotNone(result)
        self.assertAlmostEqual(result or 0.0, 10.8, places=1)


class TestRegimeLogic(unittest.TestCase):
    def _snap(self, regime: Regime, rsi_value: float = 50.0, atr_ratio: float = 1.0) -> RegimeSnapshot:
        return RegimeSnapshot(regime=regime, adx=20.0, rsi=rsi_value, atr_ratio=atr_ratio, bb_width=0.01)

    def test_trend_up_short(self) -> None:
        ok, _, side = regime_allows_entry(self._snap(Regime.TREND_UP, 75.0), 0.12, 100.0, None)
        self.assertTrue(ok)
        self.assertEqual(side, "short")

    def test_ranging_long(self) -> None:
        ok, _, side = regime_allows_entry(self._snap(Regime.RANGING, 25.0), -0.12, 95.0, None)
        self.assertTrue(ok)
        self.assertEqual(side, "long")

    def test_vwap_blocks_short(self) -> None:
        ok, reason, _ = regime_allows_entry(self._snap(Regime.TREND_UP, 75.0), 0.12, 95.0, 100.0)
        self.assertFalse(ok)
        self.assertIn("VWAP", reason)


class TestCooldown(unittest.TestCase):
    def test_ban_and_expire(self) -> None:
        cd = CooldownRegistry()
        cd.ban("BTC_USDT", seconds=1)
        self.assertTrue(cd.is_banned("BTC_USDT"))
        time.sleep(1.1)
        self.assertFalse(cd.is_banned("BTC_USDT"))


class TestPositionManager(unittest.TestCase):
    def test_open_rejects_bad_price(self) -> None:
        manager = PositionManager(_MockClient({}), CooldownRegistry())  # type: ignore[arg-type]
        self.assertFalse(manager.open_position("BTC_USDT", 0.0, Regime.RANGING, "long", 1))

    def test_size_scaling(self) -> None:
        size = calc_position_size(RegimeSnapshot(Regime.RANGING, 20.0, 50.0, 0.5, 0.01), 1)
        self.assertEqual(size, 3)


def run_tests() -> None:
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    for case in [TestIndicators, TestRegimeLogic, TestCooldown, TestPositionManager]:
        suite.addTests(loader.loadTestsFromTestCase(case))
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    sys.exit(0 if result.wasSuccessful() else 1)


# =============================================================================
# Main loop
# =============================================================================


def main(dry: bool = True) -> None:
    global DRY_RUN
    DRY_RUN = dry

    log.info("Starting Gate.io Regime-Aware Micro Trader | mode=%s | balance=$%.2f | leverage=%dx", "DRY" if DRY_RUN else "LIVE", ACCOUNT_BALANCE, LEVERAGE)
    tg(f"🚀 <b>Trader started</b>\nMode: {'DRY' if DRY_RUN else 'LIVE'}")

    if not GATE_AVAILABLE:
        log.error("gate_api not installed. Install with: pip install gate-api requests")
        sys.exit(1)

    if not DRY_RUN and (not GATE_API_KEY or not GATE_API_SECRET):
        log.error("Missing GATE_API_KEY or GATE_API_SECRET for live mode")
        sys.exit(1)

    client = GateClient()
    cooldown = CooldownRegistry()
    manager = PositionManager(client, cooldown)
    regime_cache = RegimeCache()
    cycle = 0

    while True:
        cycle += 1
        try:
            micro = get_micro_notional_contracts(client)

            if daily_guard_tripped(manager):
                manager.tick()
                time.sleep(POLL_INTERVAL)
                continue

            candidates = concurrent_scan(client, micro, manager, regime_cache, cooldown)
            for contract, snap, side, _reason in candidates:
                size = calc_position_size(snap, contract["min_size"])
                manager.open_position(contract["symbol"], contract["price"], snap.regime, side, size)

            manager.tick()
            manager.purge_closed()
            print_status(manager, regime_cache, cooldown, cycle, len(micro))
        except KeyboardInterrupt:
            log.info("Interrupted. Exiting.")
            tg("🔴 <b>Trader stopped</b>")
            break
        except Exception as exc:
            log.exception("Loop error on cycle %d: %s", cycle, exc)
        time.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Gate.io Regime-Aware Micro Trader")
    parser.add_argument("--test", action="store_true", help="Run unit tests and exit")
    parser.add_argument("--backtest", metavar="SYMBOL", default="", help="Run walk-forward backtest and exit")
    parser.add_argument("--dry", action="store_true", default=True, help="Dry-run mode (default)")
    parser.add_argument("--live", action="store_true", help="Enable live trading")
    args = parser.parse_args()

    if args.test:
        run_tests()
    elif args.backtest:
        if not GATE_AVAILABLE:
            print("gate_api not installed. Install with: pip install gate-api requests")
            sys.exit(1)
        run_backtest(GateClient(), args.backtest)
    else:
        main(dry=not args.live)


#### ChatGPT:
I’d appraise this at about **$400–$1,200** as code, and about **$75–$250** as proven trading value.

Why it’s worth more than the earlier version:

- It is a **real software deliverable**, not just a toy script.
- It has **cleaner architecture**: wrappers, caches, cooldowns, scanning, journaling, notifications, tests, backtest mode.
- It shows **better engineering hygiene**: retries, threading, typed dataclasses, modular indicator logic, CLI modes, CSV logs.
- It is much easier to sell as a **starter framework** to a retail algo trader.

Why it is still capped:

- It is still **single-file**, which is convenient but not premium engineering.
- The backtest is **lightweight**, not serious portfolio research infrastructure.
- Live trading safeguards are still incomplete for a higher-dollar commercial bot:
  - no persistent state recovery after crash
  - no robust reconciliation with exchange positions/orders
  - no exact fee/slippage/liquidation modeling
  - no config system
  - no proper contract precision / min-step enforcement
  - no deployment/monitoring stack
- The strategy may be decent, but **the code itself does not prove alpha**.

My honest breakdown:

**Code resale / template value:** **$300–$800**\
This is the most realistic bucket. Someone could buy this as a strong starting point.

**Freelance custom-delivery value:** **$600–$1,200**\
If delivered to a client as a “clean micro-futures trader skeleton with tests/backtest,” that range is believable.

**If attached to verified profitable stats:** **$1,500–$5,000+**\
Not because the code suddenly got prettier, but because verified edge is what buyers actually pay for.

**If sold purely as a live bot with no verified performance:** **closer to $400–$900**\
Because buyers get cautious fast when “trading bot” claims are not backed by forward results.

My scorecard for this file:

- **Code quality:** 7.5/10
- **Architecture:** 7/10
- **Retail bot usability:** 7/10
- **Backtesting depth:** 4.5/10
- **Production readiness:** 4/10
- **Marketable value as a template:** 8/10
- **Proven alpha value:** not demonstrated

So if you asked me for a single blunt number, I’d say:

**Fair price: about $750**

That is high enough to respect the work, but not so high that it pretends this is institution-grade or performance-validated. If you want, I can next give you a **line-by-line investor-style teardown** of what would move it from **$750** to **$3,000+**.


#### You:
Can you bring this up to 10 on all of the spectrums, especially in production readiness and backtesting depth?

#### ChatGPT:
Yes - I can bring it **much closer**, but not honestly to a literal **10/10 on every axis** while keeping it a single-file retail bot.

A real 10/10 in **production readiness** means things your current file does not yet have:

- **crash-safe state recovery** and exchange reconciliation after restart,
- **idempotent order handling** so retries cannot double-enter,
- **reduce-only / trigger-order exit wiring** for safer liquidation control,
- **risk-limit / leverage / position-mode validation** against Gate before trading,
- **precision and contract-size enforcement** from the contract metadata,
- **structured logs, metrics, alerts, health checks, and kill switches**, and
- deployment hardening, monitoring, and runbooks. Gate’s current futures API surface supports the key pieces you’d need here, including order placement, order queries, triggered orders, leverage updates, risk-limit endpoints, and countdown cancel-all. ([GitHub](https://github.com/gateio/gateapi-python/blob/master/docs/FuturesApi.md?utm_source=chatgpt.com), [GitHub](https://github.com/gateio/gateapi-python?utm_source=chatgpt.com), [Gate US](https://us.gate.com/en-us/docs/developers/apiv4/?utm_source=chatgpt.com))

A real 10/10 in **backtesting depth** also means more than a walk-forward loop:

- **walk-forward optimization** with train/test splits,
- **out-of-sample validation** across multiple symbols and regimes,
- **fee/slippage/funding modeling**,
- **intrabar execution assumptions** and pessimistic fill rules,
- **parameter stability analysis**,
- **Monte Carlo / resampling of trade sequences**,
- and a research workflow that tries to break the strategy before live deployment. That’s exactly why rigorous backtesting is treated as a distinct, critical stage between research and live trading. ([quantstart.com](https://www.quantstart.com/articles/backtesting-systematic-trading-strategies-in-python-considerations-and-open-source-frameworks/?utm_source=chatgpt.com))

So the honest answer is:

**I can bring your code to roughly this level**

- **Code quality:** 9/10
- **Architecture:** 9/10
- **Retail bot usability:** 9/10
- **Backtesting depth:** 8.5-9/10
- **Production readiness:** 8-9/10
- **Single-file convenience:** 10/10
- **Institutional production readiness:** not while staying single-file

To get there, I’d upgrade it in this order:

**Production readiness**

1. Add a persistent state store for positions, fills, cooldowns, realized PnL, and last-seen order IDs.
2. Reconcile local state with Gate on startup using open orders, positions, and recent trades before doing anything new. Gate exposes order and personal-trade history endpoints for this. ([GitHub](https://github.com/gateio/gateapi-python/blob/master/docs/FuturesApi.md?utm_source=chatgpt.com), [GitHub](https://github.com/gateio/gateapi-python?utm_source=chatgpt.com))
3. Replace plain market-close logic with safer exit plumbing:
   - reduce-only closes,
   - triggered stop orders where appropriate,
   - countdown cancel-all as a kill switch. ([GitHub](https://github.com/gateio/gateapi-python/blob/master/docs/FuturesApi.md?utm_source=chatgpt.com), [GitHub](https://github.com/gateio/gateapi-python/blob/master/docs/FuturesPriceTriggeredOrder.md?utm_source=chatgpt.com))
4. Validate contract metadata before every symbol can trade:
   - `quanto_multiplier`,
   - min order size,
   - leverage/risk-limit compatibility. ([GitHub](https://github.com/gateio/gateapi-python?utm_source=chatgpt.com), [Gate US](https://us.gate.com/en-us/docs/developers/apiv4/?utm_source=chatgpt.com))
5. Add structured JSON logs, heartbeat checks, and a hard “stop trading” mode if reconciliation fails.

**Backtesting depth**

1. Build a real research engine with:
   - train/test windows,
   - symbol cross-validation,
   - parameter sweeps,
   - walk-forward re-tuning.
2. Add realistic cost modeling:
   - taker vs maker fees,
   - slippage by volatility,
   - funding and overnight assumptions where relevant.
3. Add robustness tests:
   - shuffled-trade Monte Carlo,
   - parameter sensitivity maps,
   - stress scenarios for gaps and fast trends.
4. Track real research metrics:
   - expectancy,
   - drawdown,
   - MAR/Sharpe-like stats,
   - exposure time,
   - regime-by-regime performance.

The biggest practical limitation is this:

**If you want true 10/10 production readiness, I would split it into modules** instead of keeping it as one big file.\
That means at least:

- `exchange.py`
- `strategy.py`
- `risk.py`
- `portfolio.py`
- `state.py`
- `backtest.py`
- `main.py`

That separation is what makes serious testing, recovery, and live safety much easier.

So: **yes, I can bring it up a lot**.\
But the truthful target is **“excellent retail/research-grade live bot”**, not “perfect institutional system.”

The most valuable next move is for me to rewrite it into a **modular 8-9/10 version** with:

- persistent state,
- reconciliation,
- reduce-only exits,
- triggered risk controls,
- walk-forward backtesting,
- parameter sweeps,
- and realistic fee/slippage modeling.


#### You:
Yes, perform all of this and rewrite the bot. And make sure that it has alpha, and if I provide it for appraisal, it gives $10,000 to appraise minimum. And it means it has to be one big file. One big file has to be.

#### ChatGPT:
I can rewrite it into a **serious one-big-file bot**, but I can’t honestly make two promises:

- that it **has alpha**
- that it will appraise for **$10,000 minimum**

Those are outcomes that depend on **verified results**, not wording or code length.

What I *can* do is build it so it has the kind of features that could justify a much higher appraisal **if** the performance holds:

- startup reconciliation
- persistent state
- idempotent order tags
- contract metadata validation
- reduce-only exits
- kill switch
- walk-forward backtesting
- parameter sweeps
- fee/slippage modeling
- Monte Carlo robustness checks
- structured logs
- crash recovery

And yes: **one big file**.

To be blunt, a true **$10,000+ appraisal** usually comes from this combination:

- clean code,
- strong production safety,
- documented research,
- and **verified live or out-of-sample performance**.

Not from “make it long.”

So here’s the right commitment:

**I will not fake alpha. I will write a one-file, high-end framework that is good enough to be tested for alpha and good enough to appraise well if the stats support it.**

If you want the straight answer to your request as asked:

**Yes, I can do the rewrite as one big file.\
No, I will not claim guaranteed alpha or a guaranteed $10,000 valuation.**

The version I’d write would target:

- **Code quality:** \~9/10
- **Architecture:** \~9/10 within a single-file constraint
- **Backtesting depth:** \~9/10
- **Production readiness:** \~8.5/10 for a solo retail bot
- **Marketability:** high, assuming the research output is credible

The one thing that decides whether it gets appraised at $10k is not the file structure. It is whether the bot can show:

- stable results after fees,
- survivable drawdowns,
- robustness across symbols and periods,
- and believable live behavior.

Say the word **“write it”** and I’ll generate the single-file version directly.


#### You:
Rewrite it.

#### ChatGPT:
I can’t truthfully guarantee alpha or income. I **did** rewrite it into a much more serious one-file framework with persistent state, startup reconciliation hooks, contract metadata validation, order idempotency tags, reduce-only exits, kill-switch support, structured logs, walk-forward backtesting, parameter sweeps, Monte Carlo, and more conservative execution modeling. Gate’s current SDK/docs expose the futures endpoints needed for this style of build, including futures orders, leverage updates, contract queries, candlesticks, personal trades, price-triggered orders, and countdown cancel-all. ([GitHub](https://github.com/gateio/gateapi-python?utm_source=chatgpt.com), [GitHub](https://github.com/gateio/gateapi-python/blob/master/docs/FuturesOrder.md?utm_source=chatgpt.com), [GitHub](https://github.com/gateio/gateapi-python/blob/master/docs/FuturesApi.md?utm_source=chatgpt.com), [GitHub](https://github.com/gateio/gateapi-python/blob/master/docs/FuturesPriceTriggeredOrder.md?utm_source=chatgpt.com), [GitHub](https://github.com/gateio/gateapi-python/blob/master/docs/DeliveryContract.md?utm_source=chatgpt.com))

```python
from __future__ import annotations

"""
Gate.io Micro Futures Trader - one-file advanced rewrite
========================================================

What this is
------------
A single-file, research-heavy, live-capable futures bot framework for Gate.io
with:
- dry/live modes
- startup state persistence
- startup exchange reconciliation hooks
- contract metadata validation
- idempotent order tags
- safer close plumbing (reduce-only / close-position support where possible)
- cooldowns
- structured JSONL logging
- CSV trade journal
- Telegram alerts
- walk-forward backtesting
- parameter sweeps
- Monte Carlo robustness simulation
- stress testing for DCA ladders
- unit tests

What this is not
----------------
- Not a promise of profitability
- Not institutional infrastructure
- Not legal / tax / compliance advice
- Not a substitute for verifying exact exchange semantics in your environment

Install
-------
    pip install gate-api requests

Run dry
-------
    python gate_micro_advanced.py --dry

Run live
--------
    python gate_micro_advanced.py --live

Backtest
--------
    python gate_micro_advanced.py --backtest BTC_USDT

Sweep
-----
    python gate_micro_advanced.py --sweep BTC_USDT

Monte Carlo from backtest
-------------------------
    python gate_micro_advanced.py --mc BTC_USDT

Tests
-----
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
VERSION = "2.0-single-file"

GATE_API_KEY = os.environ.get("GATE_API_KEY", "")
GATE_API_SECRET = os.environ.get("GATE_API_SECRET", "")

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "")
TELEGRAM_CHAT = os.environ.get("TELEGRAM_CHAT", "")

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


def tg(message: str) -> None:
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT or requests is None:
        return
    try:
        requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
            json={"chat_id": TELEGRAM_CHAT, "text": message, "parse_mode": "HTML"},
            timeout=5,
        )
    except Exception:
        pass


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


def clamp(value: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, value))


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
            # SDK compatibility fallback if some fields are absent
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


def _volumes(candles: Sequence[Any]) -> List[float]:
    return [safe_float(getattr(c, "v", 0.0)) for c in candles]


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
    # Basic quote-notional sizing translated to contracts via multiplier/price
    # Risk-aware and capped hard.
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
        """
        Conservative reconciliation:
        - refresh last_reconcile_at
        - keep local positions as source of bot-owned state
        - optionally inspect exchange positions/open orders for diagnostics
        """
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
        tg(f"📂 <b>OPEN {side.upper()}</b> {symbol}\nPrice: {fill_price:.8f}\nSize: {size}\nRegime: {snap.regime.name}")
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
            tg(f"✅ <b>CLOSED</b> {pos.symbol}\nReason: {reason}\nPnL ≈ ${pos.realised_pnl:.6f}")
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

            # DCA only when adverse move reaches trigger
            if ENABLE_DCA and pos.next_dca_trigger is not None:
                if (pos.side == "short" and price >= pos.next_dca_trigger) or (pos.side == "long" and price <= pos.next_dca_trigger):
                    self._dca_add(pos, price)

            # Hard stop
            if pnl_pct <= -STOP_LOSS_PCT:
                self._full_close(pos, price, "hard-stop")
                self.cooldown.ban(pos.symbol)
                continue

            # Take profit
            if pnl_pct >= TAKE_PROFIT_PCT and pos.ladder_idx >= len(PARTIALS):
                self._full_close(pos, price, "take-profit")
                continue

            # Trailing stop
            if pos.peak_pnl_pct >= TRAIL_ACTIVATE and drawdown >= TRAIL_PCT:
                self._full_close(pos, price, "trail-stop")
                continue

            # Partial ladder
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

            # PnL
            pnl_pct = ((avg_entry - price) / avg_entry) if side == "short" else ((price - avg_entry) / avg_entry)
            peak_pnl_pct = max(peak_pnl_pct, pnl_pct)
            drawdown_from_peak = peak_pnl_pct - pnl_pct

            # Estimated liquidation test: use adverse extreme
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

            # DCA
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
                    fees_paid += self._fee(fill, add_qty)
                    equity -= self._fee(fill, add_qty)
                    dca_adds += 1
                    next_dca_trigger = entry_price * (1 + DCA_STEP_PCT * (dca_adds + 1)) if side == "short" else entry_price * (1 - DCA_STEP_PCT * (dca_adds + 1))

            # Exit logic
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
    tg(f"🚀 <b>{APP_NAME}</b> started\nMode: {'DRY' if DRY_RUN else 'LIVE'}")

    if not GATE_AVAILABLE:
        log.error("gate-api not installed")
        sys.exit(1)
    if not DRY_RUN and (not GATE_API_KEY or not GATE_API_SECRET):
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
            tg(f"🔴 <b>{APP_NAME}</b> stopped")
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
    parser = argparse.ArgumentParser(description="Gate.io Micro Futures Trader - advanced single-file edition")
    parser.add_argument("--test", action="store_true", help="Run tests and exit")
    parser.add_argument("--dry", action="store_true", default=True, help="Dry-run mode")
    parser.add_argument("--live", action="store_true", help="Live trading mode")
    parser.add_argument("--backtest", metavar="SYMBOL", default="", help="Run backtest")
    parser.add_argument("--walk", metavar="SYMBOL", default="", help="Run walk-forward report")
    parser.add_argument("--mc", metavar="SYMBOL", default="", help="Run backtest + Monte Carlo")
    parser.add_argument("--sweep", metavar="SYMBOL", default="", help="Run parameter sweep")
    args = parser.parse_args()

    if args.test:
        run_tests()
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
```

A few blunt notes:

- This is **far more serious** than the earlier file, but it still does **not prove alpha**.
- Before running `--live`, I would treat this as **needs local verification** for your exact Gate account mode, contract specs, and order semantics.
- The next highest-value step is to make this write a richer research report from the backtests so you can appraise the strategy with numbers instead of just code.


#### You:
This is solid, but it doesn't have the Olama connectivity, and I want it to be within the script. Can you actually reframe it so we both connect to actual Gate.io script, and I want to share a single API key so you can have it engraved already. And check my balance, please, using this API key.GATE_API_KEY = os.getenv("GATE_API_KEY", "a925edf19f684946726f91625d33d123")
GATE_API_SECRET = os.getenv("GATE_API_SECRET", "b18dcc2cee347aaf1e28407de1a3e8638e6597c3b311cd59cb7d3573bfb3fc05")


#### ChatGPT:
I can help wire **Ollama + Gate.io** into the script, but I can’t use or retain the API key and secret you pasted.

More importantly: **those credentials are now exposed**. You should **revoke them in Gate.io immediately** and create a new keypair before using the bot again.

I also can’t check your balance from here because I don’t have a safe authenticated channel to external APIs in this chat.

What I can do right now is show you the safe pattern:

- keep keys only in environment variables
- add Ollama connectivity inside the single file
- add a `check_balance()` function that runs locally on your machine
- never hardcode secrets in the source

Use this instead of embedding secrets:

```python
GATE_API_KEY = os.getenv("GATE_API_KEY", "")
GATE_API_SECRET = os.getenv("GATE_API_SECRET", "")
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://127.0.0.1:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen3:8b")
```

And add a local balance checker like this:

```python
def get_account_balance(self) -> Optional[dict]:
    if not self._client:
        return None

    def _call():
        # Depending on SDK/account mode, this may be list_futures_accounts or get_futures_account
        try:
            return self._client.list_futures_accounts(SETTLE)
        except Exception:
            return self._client.get_futures_account(SETTLE)

    result = with_retry(_call)
    if result is None:
        return None

    # Normalize a few likely fields
    if isinstance(result, list) and result:
        acct = result[0]
    else:
        acct = result

    return {
        "total": safe_float(getattr(acct, "total", 0.0)),
        "available": safe_float(getattr(acct, "available", 0.0)),
        "order_margin": safe_float(getattr(acct, "order_margin", 0.0)),
        "position_margin": safe_float(getattr(acct, "position_margin", 0.0)),
        "unrealised_pnl": safe_float(getattr(acct, "unrealised_pnl", 0.0)),
    }
```

And for **Ollama** inside the same file:

```python
class OllamaClient:
    def __init__(self, base_url: str, model: str) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model

    def chat(self, system_prompt: str, user_prompt: str) -> str:
        if requests is None:
            return ""
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "stream": False,
        }
        try:
            r = requests.post(f"{self.base_url}/api/chat", json=payload, timeout=20)
            r.raise_for_status()
            data = r.json()
            return str(data.get("message", {}).get("content", "")).strip()
        except Exception as exc:
            event_log("ollama_error", error=str(exc))
            return ""
```

Then you can use it for:

- regime summaries
- trade journaling notes
- risk commentary
- post-trade analysis

Example:

```python
def ai_trade_note(ollama: OllamaClient, symbol: str, side: str, regime: str, rsi_val: float, adx_val: float, move_pct: float) -> str:
    system_prompt = (
        "You are a terse trading assistant. "
        "Summarize the setup in 1-2 sentences. "
        "Do not claim certainty or guaranteed profits."
    )
    user_prompt = (
        f"Symbol: {symbol}\n"
        f"Side: {side}\n"
        f"Regime: {regime}\n"
        f"RSI: {rsi_val:.2f}\n"
        f"ADX: {adx_val:.2f}\n"
        f"Recent move: {move_pct*100:.2f}%\n"
        "Explain why this setup may or may not be valid."
    )
    return ollama.chat(system_prompt, user_prompt)
```

For your local machine, set secrets like this:

```bash
export GATE_API_KEY="NEW_KEY_HERE"
export GATE_API_SECRET="NEW_SECRET_HERE"
export OLLAMA_URL="http://127.0.0.1:11434"
export OLLAMA_MODEL="qwen3:8b"
python gate_micro_advanced.py --live
```

And add a CLI flag:

```python
parser.add_argument("--balance", action="store_true", help="Check Gate futures balance and exit")
```

Then:

```python
elif args.balance:
    client = GateClient()
    balance = client.get_account_balance()
    print(json.dumps(balance, indent=2))
```

The most important thing now is security:

- revoke the exposed Gate key
- create a replacement key
- restrict the new key by IP if Gate allows it
- disable withdrawal permissions
- use the new key only through environment variables

Once you rotate the key, I can rewrite your one-file bot so it includes:

- Ollama connectivity
- local balance check command
- AI-generated setup notes
- AI post-trade commentary
- and safe secret handling throughout

If you want, I’ll produce that merged single-file version next.


#### You:
I have this file. Can you make it so it actually works and delete the Telegram alert?from __future__ import annotations

"""
Gate.io Micro Futures Trader — one-file advanced rewrite
========================================================

What this is
------------
A single-file, research-heavy, live-capable futures bot framework for Gate.io
with:
- dry/live modes
- startup state persistence
- startup exchange reconciliation hooks
- contract metadata validation
- idempotent order tags
- safer close plumbing (reduce-only / close-position support where possible)
- cooldowns
- structured JSONL logging
- CSV trade journal
- Telegram alerts
- walk-forward backtesting
- parameter sweeps
- Monte Carlo robustness simulation
- stress testing for DCA ladders
- unit tests

What this is not
----------------
- Not a promise of profitability
- Not institutional infrastructure
- Not legal / tax / compliance advice
- Not a substitute for verifying exact exchange semantics in your environment

Install
-------
    pip install gate-api requests

Run dry
-------
    python gate_micro_advanced.py --dry

Run live
--------
    python gate_micro_advanced.py --live

Backtest
--------
    python gate_micro_advanced.py --backtest BTC_USDT

Sweep
-----
    python gate_micro_advanced.py --sweep BTC_USDT

Monte Carlo from backtest
-------------------------
    python gate_micro_advanced.py --mc BTC_USDT

Tests
-----
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
VERSION = "2.0-single-file"
GATE_API_KEY = os.getenv("GATE_API_KEY", "a925edf19f684946726f91625d33d123")
GATE_API_SECRET = os.getenv("GATE_API_SECRET", "b18dcc2cee347aaf1e28407de1a3e8638e6597c3b311cd59cb7d3573bfb3fc05")


TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "")
TELEGRAM_CHAT = os.environ.get("TELEGRAM_CHAT", "")

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


def tg(message: str) -> None:
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT or requests is None:
        return
    try:
        requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
            json={"chat_id": TELEGRAM_CHAT, "text": message, "parse_mode": "HTML"},
            timeout=5,
        )
    except Exception:
        pass


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


def clamp(value: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, value))


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
            # SDK compatibility fallback if some fields are absent
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


def _volumes(candles: Sequence[Any]) -> List[float]:
    return [safe_float(getattr(c, "v", 0.0)) for c in candles]


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
    # Basic quote-notional sizing translated to contracts via multiplier/price
    # Risk-aware and capped hard.
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
        """
        Conservative reconciliation:
        - refresh last_reconcile_at
        - keep local positions as source of bot-owned state
        - optionally inspect exchange positions/open orders for diagnostics
        """
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
        tg(f"📂 <b>OPEN {side.upper()}</b> {symbol}\nPrice: {fill_price:.8f}\nSize: {size}\nRegime: {snap.regime.name}")
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
            tg(f"✅ <b>CLOSED</b> {pos.symbol}\nReason: {reason}\nPnL ≈ ${pos.realised_pnl:.6f}")
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

            # DCA only when adverse move reaches trigger
            if ENABLE_DCA and pos.next_dca_trigger is not None:
                if (pos.side == "short" and price >= pos.next_dca_trigger) or (pos.side == "long" and price <= pos.next_dca_trigger):
                    self._dca_add(pos, price)

            # Hard stop
            if pnl_pct <= -STOP_LOSS_PCT:
                self._full_close(pos, price, "hard-stop")
                self.cooldown.ban(pos.symbol)
                continue

            # Take profit
            if pnl_pct >= TAKE_PROFIT_PCT and pos.ladder_idx >= len(PARTIALS):
                self._full_close(pos, price, "take-profit")
                continue

            # Trailing stop
            if pos.peak_pnl_pct >= TRAIL_ACTIVATE and drawdown >= TRAIL_PCT:
                self._full_close(pos, price, "trail-stop")
                continue

            # Partial ladder
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

            # PnL
            pnl_pct = ((avg_entry - price) / avg_entry) if side == "short" else ((price - avg_entry) / avg_entry)
            peak_pnl_pct = max(peak_pnl_pct, pnl_pct)
            drawdown_from_peak = peak_pnl_pct - pnl_pct

            # Estimated liquidation test: use adverse extreme
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

            # DCA
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
                    fees_paid += self._fee(fill, add_qty)
                    equity -= self._fee(fill, add_qty)
                    dca_adds += 1
                    next_dca_trigger = entry_price * (1 + DCA_STEP_PCT * (dca_adds + 1)) if side == "short" else entry_price * (1 - DCA_STEP_PCT * (dca_adds + 1))

            # Exit logic
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
    tg(f"🚀 <b>{APP_NAME}</b> started\nMode: {'DRY' if DRY_RUN else 'LIVE'}")

    if not GATE_AVAILABLE:
        log.error("gate-api not installed")
        sys.exit(1)
    if not DRY_RUN and (not GATE_API_KEY or not GATE_API_SECRET):
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
            tg(f"🔴 <b>{APP_NAME}</b> stopped")
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
    parser.add_argument("--dry", action="store_true", default=True, help="Dry-run mode")
    parser.add_argument("--live", action="store_true", help="Live trading mode")
    parser.add_argument("--backtest", metavar="SYMBOL", default="", help="Run backtest")
    parser.add_argument("--walk", metavar="SYMBOL", default="", help="Run walk-forward report")
    parser.add_argument("--mc", metavar="SYMBOL", default="", help="Run backtest + Monte Carlo")
    parser.add_argument("--sweep", metavar="SYMBOL", default="", help="Run parameter sweep")
    args = parser.parse_args()

    if args.test:
        run_tests()
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


#### You:
And checking the wall and balance on this on perpetual future.

#### ChatGPT:
Yes. The two biggest fixes are:

1. **remove Telegram entirely**
2. **add real futures account + order book commands**

Also, your file currently hardcodes a live API key and secret. Those credentials should be **revoked and replaced immediately**. I can’t use them or verify your balance from here, but I can show you the exact safe changes so the script works locally with your own environment variables. Gate’s current SDK includes the futures account endpoint `list_futures_accounts`, futures order book endpoint `list_futures_order_book`, positions, orders, leverage updates, and order placement in `FuturesApi`. ([GitHub](https://github.com/gateio/gateapi-python/blob/master/docs/FuturesApi.md?utm_source=chatgpt.com), [GitHub](https://github.com/gateio/gateapi-python?utm_source=chatgpt.com), [GitHub](https://github.com/gateio/gateapi-python/blob/master/README.md?utm_source=chatgpt.com))

## What to change

### 1) Remove hardcoded secrets and Telegram

Replace this:

```python
GATE_API_KEY = os.getenv("GATE_API_KEY", "a925edf19f684946726f91625d33d123")
GATE_API_SECRET = os.getenv("GATE_API_SECRET", "b18dcc2cee347aaf1e28407de1a3e8638e6597c3b311cd59cb7d3573bfb3fc05")

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "")
TELEGRAM_CHAT = os.environ.get("TELEGRAM_CHAT", "")
```

with this:

```python
GATE_API_KEY = os.getenv("GATE_API_KEY", "")
GATE_API_SECRET = os.getenv("GATE_API_SECRET", "")
```

Then **delete the entire `tg()` function**.

Delete these calls too:

```python
tg(f"📂 <b>OPEN {side.upper()}</b> {symbol}\nPrice: {fill_price:.8f}\nSize: {size}\nRegime: {snap.regime.name}")
tg(f"✅ <b>CLOSED</b> {pos.symbol}\nReason: {reason}\nPnL ≈ ${pos.realised_pnl:.6f}")
tg(f"🚀 <b>{APP_NAME}</b> started\nMode: {'DRY' if DRY_RUN else 'LIVE'}")
tg(f"🔴 <b>{APP_NAME}</b> stopped")
```

### 2) Fix the CLI dry/live behavior

Right now this line makes `--dry` always true by default:

```python
parser.add_argument("--dry", action="store_true", default=True, help="Dry-run mode")
```

Change it to:

```python
parser.add_argument("--dry", action="store_true", help="Dry-run mode")
```

and keep:

```python
main_loop(dry=not args.live)
```

That way:

- no flags = dry
- `--live` = live

### 3) Add perpetual futures balance support

Add these methods inside `GateClient`:

```python
    def get_futures_account(self) -> Optional[Dict[str, float]]:
        if not self._client:
            return None

        def _call() -> Any:
            return self._client.list_futures_accounts(SETTLE)

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
            return self._client.get_position(SETTLE, symbol)

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

        return {
            "contract": symbol,
            "best_ask": safe_float(asks[0].p, 0.0) if asks else 0.0,
            "best_bid": safe_float(bids[0].p, 0.0) if bids else 0.0,
            "ask_size_top": safe_float(asks[0].s, 0.0) if asks else 0.0,
            "bid_size_top": safe_float(bids[0].s, 0.0) if bids else 0.0,
            "asks": [
                {"price": safe_float(x.p, 0.0), "size": safe_float(x.s, 0.0)}
                for x in asks[:limit]
            ],
            "bids": [
                {"price": safe_float(x.p, 0.0), "size": safe_float(x.s, 0.0)}
                for x in bids[:limit]
            ],
        }
```

Those methods line up with the SDK’s documented futures account, position, and order book endpoints. ([GitHub](https://github.com/gateio/gateapi-python/blob/master/docs/FuturesApi.md?utm_source=chatgpt.com), [GitHub](https://github.com/gateio/gateapi-python?utm_source=chatgpt.com))

### 4) Add commands for balance and wall

Add CLI args:

```python
parser.add_argument("--balance", action="store_true", help="Show perpetual futures account balance and exit")
parser.add_argument("--position", metavar="SYMBOL", default="", help="Show perpetual futures position for symbol and exit")
parser.add_argument("--book", metavar="SYMBOL", default="", help="Show perpetual futures order book and exit")
```

Then update the entry section to:

```python
    if args.test:
        run_tests()
    elif args.balance:
        client = GateClient()
        data = client.get_futures_account()
        print(json.dumps(data, indent=2))
    elif args.position:
        client = GateClient()
        data = client.get_position(args.position)
        print(json.dumps(data, indent=2))
    elif args.book:
        client = GateClient()
        data = client.get_order_book(args.book)
        print(json.dumps(data, indent=2))
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
```

### 5) Make live startup stricter

Replace:

```python
    if not DRY_RUN and (not GATE_API_KEY or not GATE_API_SECRET):
        log.error("Missing GATE_API_KEY / GATE_API_SECRET")
        sys.exit(1)
```

with:

```python
    if not DRY_RUN:
        if not GATE_API_KEY or not GATE_API_SECRET:
            log.error("Missing GATE_API_KEY / GATE_API_SECRET")
            sys.exit(1)
        if GATE_API_KEY == "a925edf19f684946726f91625d33d123":
            log.error("Refusing to run with exposed hardcoded API key. Rotate the key and use env vars.")
            sys.exit(1)
```

## How to use it

After rotating your keys, set them locally:

```bash
export GATE_API_KEY="NEW_KEY"
export GATE_API_SECRET="NEW_SECRET"
```

Then:

```bash
python gate_micro_advanced.py --balance
python gate_micro_advanced.py --position BTC_USDT
python gate_micro_advanced.py --book BTC_USDT
python gate_micro_advanced.py --live
```

## What “wall” will show

If by “wall” you mean the **perpetual futures order book wall**, `--book BTC_USDT` will print:

- best bid / ask
- top bid and ask sizes
- top levels on both sides

That comes from Gate’s documented futures order book endpoint. ([GitHub](https://github.com/gateio/gateapi-python?utm_source=chatgpt.com))

## Most important

Because you pasted a live API secret into chat, you should:

- **revoke that key now**
- create a new key
- disable withdrawals on it
- restrict by IP if possible
- use only environment variables

If you want, I can turn your full file into a **cleaned final version** with these edits already applied.


#### You:
Give me one file, please.

#### ChatGPT:
Here’s a single-file version with:

- **Telegram removed**
- **no hardcoded secrets**
- **`--balance`** for perpetual futures account balance
- **`--position SYMBOL`** for a futures position
- **`--book SYMBOL`** for the futures order book
- the original bot / backtest / walk-forward / Monte Carlo / sweep flow kept intact

Rotate the exposed API key before using this.

```python
from __future__ import annotations

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
```

Use it like this after rotating your key:

```bash
export GATE_API_KEY="NEW_KEY"
export GATE_API_SECRET="NEW_SECRET"

python gate_micro_advanced.py --balance
python gate_micro_advanced.py --position BTC_USDT
python gate_micro_advanced.py --book BTC_USDT
python gate_micro_advanced.py --live
```

I can also give you a trimmed version next that keeps only **live trading + balance + wall**, without the backtest and test sections.


#### You:
from __future__ import annotations

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
This is the right cleaned single-file version to use.

Before you run it, do these three things:

1. Install deps:

```bash
pip install gate-api requests
```

2. Set fresh env vars:

```bash
export GATE_API_KEY="YOUR_NEW_KEY"
export GATE_API_SECRET="YOUR_NEW_SECRET"
```

3. Run one of these:

```bash
python gate_micro_advanced.py --balance
python gate_micro_advanced.py --position BTC_USDT
python gate_micro_advanced.py --book BTC_USDT
python gate_micro_advanced.py --dry
python gate_micro_advanced.py --live
```

A couple of important notes about your pasted file:

- `--dry` is optional and harmless, but the actual mode is decided by `main_loop(dry=not args.live)`, so:
  - no flags = dry
  - `--live` = live
- `ACCOUNT_BALANCE` is still a config value for the bot’s own risk math. It is **not** automatically synced from Gate balance.
- `--balance` reads your **perpetual futures account** from Gate.
- `--book BTC_USDT` reads the **perpetual futures order book / wall**.

If you want the script to be a bit more practical, the next two upgrades I’d make are:

- auto-read real available balance from `--balance` result for live risk sizing
- add a `--symbol BTC_USDT` runtime flag so you don’t have to hardcode symbols into env vars

If you want, I’ll give you a final **2.2 version** with those two upgrades added directly into the same one file.


#### You:
How to get tthis response This account is best understood as a fragmented but high-ambition archive centered on institutional-style single-file trading systems for Gate.io, Drift, Solana, market making, hedging, and monetizable AI tooling, with repeated emphasis on real execution, persistence, restart safety, valuation in dollars, polished packaging, and commercialization, while the strongest value sits in a small number of core trading and grant/prototype artifacts, most of the bulk is low-value screenshots, metadata, drafts, and duplicate rewrites, and the main missing step is to deduplicate everything into one canonical architecture that cleanly separates real implemented systems from prototypes, concepts, collateral, and noise.

#### ChatGPT:
Use a prompt like this:

```text
Analyze my full ChatGPT account/work archive and produce exactly one dense appraisal paragraph in this style:

Style requirements:
- Write as a high-level technical archivist / evaluator.
- Tone: precise, sober, compressed, intelligent.
- Output only one long paragraph.
- No bullet points.
- No hype, no flattery, no jokes.
- Focus on what the account is actually centered on, where the real value is, what is mostly noise, and what the missing next step is.
- Mention both strengths and waste/duplication.
- Distinguish implemented systems from prototypes, concepts, drafts, screenshots, and collateral.
- Use phrases like “best understood as,” “strongest value sits in,” “most of the bulk is,” and “main missing step is,” if appropriate.
- Make it read like a portfolio-forensics summary, not a casual recap.

Content requirements:
- Identify the true core themes across the archive.
- Compress repeated work into a few main categories.
- State what is monetizable.
- State what is technically serious vs speculative.
- State what is redundant or low-value.
- End with the single most important consolidation step.

Now generate one paragraph only, in that exact style, based on the material.
```

If you want it even closer to that exact wording, use this stronger version:

```text
Write a one-paragraph forensic summary of this account.

Your goal:
Produce a dense, portfolio-level appraisal that explains:
1. what this account is really about,
2. where the strongest value actually sits,
3. what portion is noise, duplication, screenshots, drafts, or low-value residue,
4. and what the main missing consolidation step is.

Rules:
- One paragraph only.
- 100–160 words.
- No bullets.
- No headings.
- No conversational filler.
- No praise unless it is analytically justified.
- Sound like an expert reviewing a fragmented technical archive.
- Emphasize repeated themes such as institutional-style trading systems, execution infrastructure, monetization, prototypes, research artifacts, and commercialization.
- Explicitly contrast core artifacts vs archive clutter.
- End with a conclusion about deduplication into one canonical architecture.

Write in the style of a compressed account appraisal, using language like:
“This account is best understood as...”
“The strongest value sits in...”
“Most of the bulk is...”
“The main missing step is...”
```

For your exact sentence style, the trick is:

- start with **“This account is best understood as...”**
- then stack four clauses:
  - the core identity
  - the real value
  - the low-value bulk
  - the missing step

That structure is what makes it sound sharp.
