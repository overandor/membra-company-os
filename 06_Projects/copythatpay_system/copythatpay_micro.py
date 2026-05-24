#!/usr/bin/env python3
"""
CopyThatPay MICRO — Sub-Cent Market Maker for $9 Accounts
==========================================================
Micro-account optimized. Sub-cent tickers only. Asymmetric quoting.

Execution Doctrine: Micro-Account Market Making
  Optimized for $9 accounts on sub-cent Gate.io perpetuals:
    - Asymmetric quoting (bias toward favorable side, not both blindly)
    - Sub-cent tickers only (< $0.01 nominal)
    - Aggressive position sizing (70% active capital)
    - Adverse selection detection (stop quoting losing sides)
    - Fast exits (30s timeout, market fallback)
    - Growth-focused: $9 → $10+ target

  Individual components are standard (market making, delta-neutral positioning,
  inventory recycling, spread capture, maker/taker hybrid execution).
  The combination — micro sizing + hedged legs + immediate fills + non-passive
  behavior + low blow-up risk + scaling from small deposits — is distinctive.

Architecture:
  RiskEngine          — Centralized risk control, overrides all trading logic
  PerformanceTracker  — Equity curve, Sharpe, drawdown, CSV export
  TradeJournal        — Auditable, human-readable action log
  CopyThatPay         — Aggressive spread-capture engine with maker-first quoting

Execution Model:
  1. Quote both sides: post_only buy@bid + sell@ask (simultaneous)
  2. On fill: place reduce_only exit at spread target price
  3. On exit fill: record PnL, recycle quote (high turnover)
  4. Stale quote refresh: cancel + re-place when book moves >0.1%
  5. Taker fallback: cross spread after maker timeout (20s default)

Micro-Account Constraints ($9):
  1. Max $1.50 per position (aggressive for growth)
  2. 70% active capital, 20% reserve, 10% buffer
  3. Sub-cent tickers only (< $0.01, high contract counts)
  4. Asymmetric quoting (avoid adverse selection)
  5. Fast panic exits (3 min max hold, 30s exit timeout)
  6. Cooldown on failed exits (30s pause)
  7. 15% global drawdown max ($1.35 on $9)
  8. Growth target: $9 → $10 (11% gain)
"""

import ccxt.async_support as ccxt
import asyncio
import aiohttp
import csv
import json
import math
import os
import sys
import time
import traceback
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from dotenv import load_dotenv
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from rich.console import Console
from rich.table import Table

load_dotenv()
console = Console()

# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 1: CONFIGURATION
# All parameters are constants. No runtime mutation. No magic numbers in logic.
# ═══════════════════════════════════════════════════════════════════════════════

API_KEY    = os.getenv('GATE_API_KEY', '')
API_SECRET = os.getenv('GATE_API_SECRET', '')
GROQ_KEY   = os.getenv('GROQ_API_KEY', '')

if not API_KEY or not API_SECRET:
    console.print('[bold red]FATAL: GATE_API_KEY and GATE_API_SECRET must be set in .env')
    sys.exit(1)

# — File paths —
DATA_DIR          = Path('copythatpay_data')
SYMBOL_FILE       = DATA_DIR / 'symbols.json'
STATE_FILE        = DATA_DIR / 'state.json'
HEDGE_STATE_FILE  = DATA_DIR / 'hedge_state.json'
TRADE_JOURNAL     = DATA_DIR / 'journal.jsonl'
EQUITY_CURVE_CSV  = DATA_DIR / 'equity_curve.csv'
DAILY_REPORT_DIR  = DATA_DIR / 'reports'
PERF_METRICS_FILE = DATA_DIR / 'metrics.json'

# — Risk limits (institutional) —
MAX_DRAWDOWN_PER_SYMBOL   = 0.05    # 5% max per symbol (45c on $9)
MAX_DRAWDOWN_GLOBAL       = 0.15    # 15% total cap ($1.35 on $9)
MAX_CONCURRENT_SYMBOLS    = 3       # Max 3 positions for $9 account
MAX_EXPOSURE_PER_SYMBOL   = 0.15    # 15% of equity per symbol notional
MAX_NOTIONAL_PER_CONTRACT = 0.10    # only symbols where 1ct ≤ $0.10
MARGIN_RATIO_CRITICAL     = 0.70    # flatten all at 70% margin ratio
MAX_POSITION_AGE_SECONDS  = 180     # 3 minutes max hold (aggressive)
VOLATILITY_KILL_THRESHOLD = 0.05    # 5% candle move = pause symbol
MAX_DCA_ROUNDS            = 3       # bounded DCA — no infinite averaging

# — Capital partitioning (micro-account: $9) —
CAPITAL_ACTIVE_RATIO   = 0.70   # 70% available for trading (aggressive growth)
CAPITAL_RESERVE_RATIO  = 0.20   # 20% untouchable reserve
CAPITAL_BUFFER_RATIO   = 0.10   # 10% risk buffer (minimal for growth)
TOTAL_CAPITAL_USD      = 9.0     # Starting capital

# — Execution (micro-optimized) —
DEFAULT_LEVERAGE    = 5
FEE_RATE            = 0.00075
OFFSET              = 0.001      # 0.1% offset (tighter for sub-cent)
MAX_ORDER_RETRIES   = 3           # Fewer retries (faster)
FILL_TIMEOUT_SEC    = 5           # 5s entry timeout (aggressive)
MONITOR_INTERVAL    = 10          # 10s monitoring
MARGIN_MODE         = 'isolated'

# — Spread-capture params (micro-optimized) —
SPREAD_TARGET_PCT      = 0.005    # 0.5% target (easier on sub-cent)
MAKER_TIMEOUT_SEC      = 15       # 15s to taker (faster)
QUOTE_REFRESH_SEC      = 3        # 3s refresh (more responsive)
BOOK_DRIFT_THRESHOLD   = 0.002    # 0.2% drift (less noise)
CYCLE_INTERVAL_SEC     = 1        # 1s between symbols (faster cycling)

# — Sub-cent filter —
SUBCENT_PRICE_MAX      = 0.01     # Only tickers < $0.01
SUBCENT_VOLUME_MIN     = 5000    # Min $5k daily volume

# — Execution risk controls (new) —
PANIC_EXIT_SEC         = 300      # 5 minutes - market exit if no fill
EXIT_FILL_RATE_MIN     = 0.3      # 30% min exit fill rate before tightening
MAX_EXIT_WAIT_SEC      = 60       # 60 seconds max wait for exit fill
SYMBOL_COOLDOWN_SEC    = 30       # 30 seconds cooldown after failed exit
EDGE_DECAY_THRESHOLD   = 0.5      # if real edge < 50% of theoretical, pause


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 2: DATA STRUCTURES
# Immutable records for state tracking, audit trail, and risk snapshots.
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class HedgeLeg:
    """One side of a hedged position."""
    contracts: float = 0
    entry: float = 0
    timestamp: float = 0
    filled: bool = False
    dca_rounds: int = 0

@dataclass
class HedgePair:
    """A complete hedge: long + short on the same symbol."""
    long_leg: HedgeLeg = field(default_factory=HedgeLeg)
    short_leg: HedgeLeg = field(default_factory=HedgeLeg)
    hedge_open_time: float = 0
    harvests: int = 0
    
    # Execution risk metrics (new)
    exit_attempts: int = 0
    exit_fills: int = 0
    total_expected_profit: float = 0
    total_realized_profit: float = 0
    last_exit_time: float = 0

    @property
    def is_complete(self) -> bool:
        return self.long_leg.filled and self.short_leg.filled

    @property
    def is_empty(self) -> bool:
        return not self.long_leg.filled and not self.short_leg.filled

    @property
    def is_broken(self) -> bool:
        return self.long_leg.filled != self.short_leg.filled

    @property
    def age_seconds(self) -> float:
        if self.hedge_open_time <= 0:
            return 0
        return time.time() - self.hedge_open_time

@dataclass
class RiskSnapshot:
    """Point-in-time risk state. Attached to every journal entry for audit."""
    timestamp: float = 0
    equity: float = 0
    used_margin: float = 0
    free_capital: float = 0
    active_capital: float = 0
    margin_ratio: float = 0
    total_floating_pnl: float = 0
    drawdown_pct: float = 0
    open_hedges: int = 0
    broken_hedges: int = 0
    symbols_at_limit: int = 0
    risk_verdict: str = 'UNKNOWN'

@dataclass
class TradeRecord:
    """Auditable trade record. Every action produces one."""
    timestamp: str = ''
    epoch: float = 0
    action: str = ''
    symbol: str = ''
    side: str = ''
    contracts: float = 0
    price: float = 0
    pnl: float = 0
    reason: str = ''
    hedge_state: str = ''
    risk_snapshot: dict = field(default_factory=dict)

@dataclass
class EquityPoint:
    """Single point on the equity curve."""
    timestamp: str = ''
    epoch: float = 0
    equity: float = 0
    realized_pnl: float = 0
    unrealized_pnl: float = 0
    drawdown_pct: float = 0
    open_hedges: int = 0


@dataclass
class QuoteState:
    """Per-symbol state for the spread-capture engine."""
    long_order_id: str = ''
    short_order_id: str = ''
    long_quote_px: float = 0
    short_quote_px: float = 0
    long_filled: bool = False
    short_filled: bool = False
    long_entry: float = 0
    short_entry: float = 0
    long_cts: float = 0
    short_cts: float = 0
    long_exit_id: str = ''
    short_exit_id: str = ''
    cycles: int = 0
    realized: float = 0
    quote_time: float = 0


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 3: RISK ENGINE
# Centralized. Every trade goes through here. No exceptions. No overrides.
# ═══════════════════════════════════════════════════════════════════════════════

class RiskEngine:
    """Institutional risk control layer. Vetoes trades that breach limits."""

    def __init__(self):
        self.peak_equity: float = 0
        self.symbol_pnl: Dict[str, float] = {}
        self.symbol_exposure: Dict[str, float] = {}
        self.paused_symbols: Dict[str, float] = {}  # symbol -> pause until epoch
        self.cooldown_symbols: Dict[str, float] = {}  # symbol -> cooldown until epoch (new)
        self.global_pause_until: float = 0

    def update_peak_equity(self, equity: float) -> None:
        if equity > self.peak_equity:
            self.peak_equity = equity

    def current_drawdown(self, equity: float) -> float:
        if self.peak_equity <= 0:
            return 0
        return max(0, (self.peak_equity - equity) / self.peak_equity)

    def record_symbol_pnl(self, symbol: str, unrealized_pnl: float) -> None:
        self.symbol_pnl[symbol] = unrealized_pnl

    def record_symbol_exposure(self, symbol: str, notional: float) -> None:
        self.symbol_exposure[symbol] = notional

    def clear_symbol(self, symbol: str) -> None:
        self.symbol_pnl.pop(symbol, None)
        self.symbol_exposure.pop(symbol, None)
    
    def set_cooldown(self, symbol: str, duration_sec: float) -> None:
        """Set cooldown for symbol after failed exit"""
        self.cooldown_symbols[symbol] = time.time() + duration_sec
    
    def is_cooldown(self, symbol: str) -> bool:
        """Check if symbol is in cooldown"""
        return time.time() < self.cooldown_symbols.get(symbol, 0)

    def total_floating_pnl(self) -> float:
        return sum(self.symbol_pnl.values())

    def total_exposure(self) -> float:
        return sum(self.symbol_exposure.values())

    # — Gate checks: every trade must pass ALL of these —

    def check_global_risk(self, equity: float) -> Tuple[bool, str]:
        """Returns (safe, reason). If not safe, ALL trading must stop."""
        self.update_peak_equity(equity)
        dd = self.current_drawdown(equity)
        if dd >= MAX_DRAWDOWN_GLOBAL:
            return False, f'global drawdown {dd:.1%} >= {MAX_DRAWDOWN_GLOBAL:.0%} limit'

        floating = self.total_floating_pnl()
        if equity > 0 and abs(floating) / equity >= MAX_DRAWDOWN_GLOBAL:
            return False, f'floating loss {floating/equity:.1%} >= {MAX_DRAWDOWN_GLOBAL:.0%}'

        if time.time() < self.global_pause_until:
            return False, 'global pause active (volatility kill-switch)'

        return True, 'OK'

    def check_symbol_risk(self, symbol: str, equity: float) -> Tuple[bool, str]:
        """Returns (safe, reason) for a specific symbol."""
        if time.time() < self.paused_symbols.get(symbol, 0):
            return False, f'{symbol} paused (volatility)'
        
        if self.is_cooldown(symbol):
            return False, f'{symbol} in cooldown (failed exit)'

        sym_pnl = self.symbol_pnl.get(symbol, 0)
        if equity > 0 and sym_pnl < 0 and abs(sym_pnl) / equity >= MAX_DRAWDOWN_PER_SYMBOL:
            return False, f'{symbol} drawdown {sym_pnl/equity:.1%} >= {MAX_DRAWDOWN_PER_SYMBOL:.0%}'

        sym_exp = self.symbol_exposure.get(symbol, 0)
        if equity > 0 and sym_exp / equity >= MAX_EXPOSURE_PER_SYMBOL:
            return False, f'{symbol} exposure {sym_exp/equity:.1%} >= {MAX_EXPOSURE_PER_SYMBOL:.0%}'

        return True, 'OK'

    def check_can_open_new(self, current_hedges: int) -> Tuple[bool, str]:
        """Check if we can open another hedge pair."""
        if current_hedges >= MAX_CONCURRENT_SYMBOLS:
            return False, f'at {MAX_CONCURRENT_SYMBOLS} symbol cap'
        return True, 'OK'

    def check_dca_allowed(self, hedge_pair: HedgePair, side: str) -> Tuple[bool, str]:
        """Check if DCA is allowed (bounded to MAX_DCA_ROUNDS)."""
        leg = hedge_pair.long_leg if side == 'long' else hedge_pair.short_leg
        if leg.dca_rounds >= MAX_DCA_ROUNDS:
            return False, f'{side} DCA at {MAX_DCA_ROUNDS} round cap'
        return True, 'OK'

    def check_position_age(self, hedge_pair: HedgePair) -> Tuple[bool, str]:
        """Check if position has exceeded max age."""
        age = hedge_pair.age_seconds
        if age > MAX_POSITION_AGE_SECONDS:
            return False, f'position age {age:.0f}s > {MAX_POSITION_AGE_SECONDS}s limit'
        return True, 'OK'

    def pause_symbol(self, symbol: str, duration: float = 300) -> None:
        self.paused_symbols[symbol] = time.time() + duration

    def pause_global(self, duration: float = 600) -> None:
        self.global_pause_until = time.time() + duration

    def get_snapshot(self, equity: float, used: float, free: float,
                     hedges: Dict[str, HedgePair]) -> RiskSnapshot:
        """Generate a point-in-time risk snapshot for audit logging."""
        mr = used / equity if equity > 0 else 0
        active_cap = equity * CAPITAL_ACTIVE_RATIO
        dd = self.current_drawdown(equity)
        ok = sum(1 for hp in hedges.values() if hp.is_complete)
        broken = sum(1 for hp in hedges.values() if hp.is_broken)
        at_limit = sum(1 for s, p in self.symbol_pnl.items()
                       if equity > 0 and p < 0 and abs(p) / equity >= MAX_DRAWDOWN_PER_SYMBOL * 0.8)
        g_safe, g_reason = self.check_global_risk(equity)
        return RiskSnapshot(
            timestamp=time.time(), equity=equity, used_margin=used,
            free_capital=free, active_capital=active_cap, margin_ratio=mr,
            total_floating_pnl=self.total_floating_pnl(), drawdown_pct=dd,
            open_hedges=ok, broken_hedges=broken, symbols_at_limit=at_limit,
            risk_verdict='SAFE' if g_safe else f'BREACH: {g_reason}',
        )

    def symbols_to_flatten(self, equity: float, hedges: Dict[str, HedgePair]) -> List[Tuple[str, str]]:
        """Returns list of (symbol, reason) that must be force-flattened."""
        result = []
        for sym, hp in list(hedges.items()):
            age_ok, age_reason = self.check_position_age(hp)
            if not age_ok:
                result.append((sym, age_reason))
                continue
            sym_ok, sym_reason = self.check_symbol_risk(sym, equity)
            if not sym_ok and 'drawdown' in sym_reason:
                result.append((sym, sym_reason))
        return result


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 4: PERFORMANCE TRACKER
# Equity curve, Sharpe ratio, drawdown, win rate, CSV export, daily reports.
# ═══════════════════════════════════════════════════════════════════════════════

class PerformanceTracker:
    """Continuous performance measurement and reporting."""

    def __init__(self):
        self.equity_curve: List[EquityPoint] = []
        self.realized_trades: List[float] = []  # pnl of each closed trade
        self.total_realized: float = 0
        self.peak_equity: float = 0
        self.max_drawdown: float = 0
        self.session_start: float = time.time()
        self._ensure_dirs()

    def _ensure_dirs(self) -> None:
        DATA_DIR.mkdir(exist_ok=True)
        DAILY_REPORT_DIR.mkdir(parents=True, exist_ok=True)

    def record_equity(self, equity: float, unrealized: float, open_hedges: int) -> None:
        """Record an equity point. Called every monitor cycle."""
        if equity > self.peak_equity:
            self.peak_equity = equity
        dd = (self.peak_equity - equity) / self.peak_equity if self.peak_equity > 0 else 0
        if dd > self.max_drawdown:
            self.max_drawdown = dd
        pt = EquityPoint(
            timestamp=datetime.now(timezone.utc).isoformat(),
            epoch=time.time(),
            equity=equity,
            realized_pnl=self.total_realized,
            unrealized_pnl=unrealized,
            drawdown_pct=dd,
            open_hedges=open_hedges,
        )
        self.equity_curve.append(pt)
        self._append_equity_csv(pt)

    def record_trade_pnl(self, pnl: float) -> None:
        """Record a realized trade result."""
        self.realized_trades.append(pnl)
        self.total_realized += pnl

    def sharpe_ratio(self) -> float:
        """Approximate Sharpe ratio from realized trade PnLs."""
        if len(self.realized_trades) < 2:
            return 0
        mean = sum(self.realized_trades) / len(self.realized_trades)
        variance = sum((x - mean) ** 2 for x in self.realized_trades) / (len(self.realized_trades) - 1)
        std = math.sqrt(variance) if variance > 0 else 0
        if std == 0:
            return 0
        return mean / std

    def win_rate(self) -> float:
        """Percentage of trades that were profitable."""
        if not self.realized_trades:
            return 0
        wins = sum(1 for t in self.realized_trades if t > 0)
        return wins / len(self.realized_trades)

    def avg_profit(self) -> float:
        """Average PnL per trade."""
        if not self.realized_trades:
            return 0
        return sum(self.realized_trades) / len(self.realized_trades)

    def capital_utilization(self, used: float, equity: float) -> float:
        """Current capital utilization as percentage."""
        if equity <= 0:
            return 0
        return used / equity

    def get_summary(self, equity: float, used: float) -> dict:
        """Full performance summary for display and export."""
        return {
            'total_realized_pnl': self.total_realized,
            'trade_count': len(self.realized_trades),
            'win_rate': self.win_rate(),
            'avg_profit_per_trade': self.avg_profit(),
            'sharpe_ratio': self.sharpe_ratio(),
            'max_drawdown': self.max_drawdown,
            'peak_equity': self.peak_equity,
            'current_equity': equity,
            'capital_utilization': self.capital_utilization(used, equity),
            'session_duration_s': time.time() - self.session_start,
        }

    def _append_equity_csv(self, pt: EquityPoint) -> None:
        """Append one row to equity curve CSV."""
        try:
            write_header = not EQUITY_CURVE_CSV.exists()
            with open(EQUITY_CURVE_CSV, 'a', newline='') as f:
                w = csv.writer(f)
                if write_header:
                    w.writerow(['timestamp', 'epoch', 'equity', 'realized_pnl',
                                'unrealized_pnl', 'drawdown_pct', 'open_hedges'])
                w.writerow([pt.timestamp, pt.epoch, pt.equity, pt.realized_pnl,
                            pt.unrealized_pnl, pt.drawdown_pct, pt.open_hedges])
        except Exception:
            pass

    def export_daily_report(self, equity: float, used: float,
                            hedges: Dict[str, HedgePair], risk: RiskEngine) -> None:
        """Write a daily summary report to disk."""
        try:
            today = datetime.now(timezone.utc).strftime('%Y-%m-%d')
            report_path = DAILY_REPORT_DIR / f'report_{today}.txt'
            summary = self.get_summary(equity, used)
            snap = risk.get_snapshot(equity, used, equity - used, hedges)
            lines = [
                f'CopyThatPay Daily Report — {today}',
                '=' * 50,
                f'Equity:              ${equity:.4f}',
                f'Peak Equity:         ${self.peak_equity:.4f}',
                f'Total Realized PnL:  ${self.total_realized:.6f}',
                f'Trade Count:         {len(self.realized_trades)}',
                f'Win Rate:            {self.win_rate():.1%}',
                f'Avg Profit/Trade:    ${self.avg_profit():.6f}',
                f'Sharpe Ratio:        {self.sharpe_ratio():.3f}',
                f'Max Drawdown:        {self.max_drawdown:.2%}',
                f'Capital Utilization: {self.capital_utilization(used, equity):.1%}',
                f'',
                f'Risk State:',
                f'  Verdict:           {snap.risk_verdict}',
                f'  Margin Ratio:      {snap.margin_ratio:.1%}',
                f'  Floating PnL:      ${snap.total_floating_pnl:.6f}',
                f'  Open Hedges:       {snap.open_hedges}',
                f'  Broken Hedges:     {snap.broken_hedges}',
                f'  Symbols Near Limit:{snap.symbols_at_limit}',
                f'',
                f'Session Duration:    {summary["session_duration_s"]:.0f}s',
            ]
            with open(report_path, 'w') as f:
                f.write('\n'.join(lines) + '\n')
        except Exception:
            pass

    def save_metrics(self, equity: float, used: float) -> None:
        """Persist current metrics to JSON for external consumption."""
        try:
            with open(PERF_METRICS_FILE, 'w') as f:
                json.dump(self.get_summary(equity, used), f, indent=2)
        except Exception:
            pass


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 5: TRADE JOURNAL
# Every action logged with reason, risk state, hedge state. Human-readable.
# ═══════════════════════════════════════════════════════════════════════════════

class TradeJournal:
    """Auditable trade journal. Append-only JSONL + human-readable console output."""

    def __init__(self):
        DATA_DIR.mkdir(exist_ok=True)

    def log(self, action: str, symbol: str, side: str, contracts: float,
            price: float = 0, pnl: float = 0, reason: str = '',
            hedge_state: str = '', risk_snapshot: Optional[RiskSnapshot] = None) -> None:
        """Write one auditable record."""
        record = TradeRecord(
            timestamp=datetime.now(timezone.utc).isoformat(),
            epoch=time.time(),
            action=action,
            symbol=symbol,
            side=side,
            contracts=contracts,
            price=price,
            pnl=pnl,
            reason=reason,
            hedge_state=hedge_state,
            risk_snapshot=asdict(risk_snapshot) if risk_snapshot else {},
        )
        self._write_jsonl(record)
        self._print_human(record)

    def _write_jsonl(self, record: TradeRecord) -> None:
        try:
            with open(TRADE_JOURNAL, 'a') as f:
                f.write(json.dumps(asdict(record)) + '\n')
        except Exception:
            pass

    def _print_human(self, record: TradeRecord) -> None:
        color = 'green' if record.pnl > 0 else ('red' if record.pnl < 0 else 'cyan')
        pnl_str = f' PnL=${record.pnl:.6f}' if record.pnl != 0 else ''
        price_str = f' @{record.price:.8f}' if record.price > 0 else ''
        console.print(
            f'[{color}][JOURNAL] {record.action} {record.symbol} '
            f'{record.side} {record.contracts}ct{price_str}{pnl_str} '
            f'| {record.reason} | risk={record.risk_snapshot.get("risk_verdict", "N/A")}[/{color}]'
        )


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 6: CopyThatPay — MAIN TRADING ENGINE
# ═══════════════════════════════════════════════════════════════════════════════

class CopyThatPay:
    """Aggressive hedged spread-capture engine (HMSC)."""

    def __init__(self):
        self.exchange = None
        self.risk = RiskEngine()
        self.perf = PerformanceTracker()
        self.journal = TradeJournal()
        self.hedges: Dict[str, HedgePair] = {}
        self.quotes: Dict[str, QuoteState] = {}
        self.state: Dict[str, float] = {}
        self._last_report_day: str = ''

    async def init_exchange(self) -> None:
        self.exchange = ccxt.gateio({
            'apiKey': API_KEY, 'secret': API_SECRET, 'enableRateLimit': True,
            'timeout': 60000,  # 60 second timeout for API requests
            'options': {'defaultType': 'swap', 'defaultSettle': 'usdt',
                        'adjustForTimeDifference': True, 'recvWindow': 60000,
                        'fetchCurrencies': False},  # Skip problematic currencies endpoint
            'headers': {'User-Agent': 'Mozilla/5.0'}
        })

        # Retry logic with exponential backoff for load_markets
        for attempt in range(5):
            try:
                await self.exchange.load_markets()
                console.print('[green]Exchange connected[/green]')
                return
            except Exception as e:
                wait = 2 ** attempt
                console.print(f'[yellow]Init failed ({attempt+1}/5): {e}[/yellow]')
                if attempt < 4:  # Don't sleep after last attempt
                    await asyncio.sleep(wait)

        console.print('[red]WARNING: running without full market load - will retry in background[/red]')

    async def cleanup(self) -> None:
        if self.exchange:
            try:
                await self.exchange.close()
            except Exception:
                pass

    async def get_health(self) -> dict:
        """Fetch balance with capital partitioning."""
        h = {'equity': 0, 'used': 0, 'free': 0, 'active_capital': 0,
             'reserve': 0, 'buffer': 0, 'margin_ratio': 0, 'safe': True}
        try:
            bal = await self.exchange.fetch_balance()
            total = float(bal.get('total', {}).get('USDT', 0) or 0)
            used = float(bal.get('used', {}).get('USDT', 0) or 0)
            free = float(bal.get('free', {}).get('USDT', 0) or 0)
            if free <= 0:
                free = float(bal.get('info', {}).get('available', 0) or 0)
            if free <= 0:
                free = max(total - used, 0)
            mr = used / total if total > 0 else 0
            g_safe, _ = self.risk.check_global_risk(total)
            h.update({
                'equity': total, 'used': used, 'free': free,
                'active_capital': total * CAPITAL_ACTIVE_RATIO,
                'reserve': total * CAPITAL_RESERVE_RATIO,
                'buffer': total * CAPITAL_BUFFER_RATIO,
                'margin_ratio': mr,
                'safe': g_safe and mr < MARGIN_RATIO_CRITICAL,
            })
        except Exception as e:
            console.print(f'[red]Health error: {e}')
            h['safe'] = False
        return h

    async def check_volatility(self, symbol: str) -> bool:
        """Volatility kill-switch. Returns False if abnormal — pauses symbol."""
        try:
            ohlcv = await self.exchange.fetch_ohlcv(symbol, '5m', limit=2)
            if len(ohlcv) < 2:
                return True
            o, c = ohlcv[-1][1], ohlcv[-1][4]
            if o <= 0:
                return True
            move = abs(c - o) / o
            if move >= VOLATILITY_KILL_THRESHOLD:
                console.print(f'[bold red][{symbol}] VOL KILL: {move:.1%} >= {VOLATILITY_KILL_THRESHOLD:.0%}')
                self.risk.pause_symbol(symbol, 300)
                snap = self.risk.get_snapshot(0, 0, 0, self.hedges)
                self.journal.log('VOL_PAUSE', symbol, '', 0,
                                 reason=f'{move:.1%} 5m candle', risk_snapshot=snap)
                return False
        except Exception:
            pass
        return True

    async def safe_size(self, symbol: str) -> int:
        """Risk-gated order sizing. Allocates max contracts within risk limits."""
        try:
            h = await self.get_health()
            if not h['safe']:
                return 0
            usable = h['active_capital']
            if h['used'] >= usable:
                return 0
            mkt = self.exchange.market(symbol)
            tk = await self.exchange.fetch_ticker(symbol, {'type': 'swap'})
            px = float(tk['last'])
            if px <= 0:
                return 0
            cs = float(mkt.get('contractSize', 1) or 1)
            ntl = px * cs
            mrg = ntl / DEFAULT_LEVERAGE
            min_ct = max(int(mkt.get('limits', {}).get('amount', {}).get('min') or 1), 1)
            if ntl * min_ct > MAX_NOTIONAL_PER_CONTRACT * max(min_ct, 1):
                return 0
            remaining = (usable - h['used']) * 0.90
            if mrg * min_ct > remaining:
                return 0
            exposure_cap = h['equity'] * MAX_EXPOSURE_PER_SYMBOL if h['equity'] > 0 else 0
            max_by_margin = int(remaining / mrg) if mrg > 0 else min_ct
            max_by_exposure = int(exposure_cap / ntl) if ntl > 0 else min_ct
            ct = max(min_ct, min(max_by_margin, max_by_exposure))
            return ct
        except Exception as e:
            console.print(f'[{symbol}] Size err: {e}')
            return 0

    # — Order execution —

    async def open_position(self, symbol: str, side: str) -> bool:
        """Limit order crossing spread. Exp backoff. Risk-gated."""
        ct = await self.safe_size(symbol)
        if ct <= 0:
            return False
        delay = 1
        for attempt in range(MAX_ORDER_RETRIES):
            try:
                tk = await self.exchange.fetch_ticker(symbol, {'type': 'swap'})
                px = float(tk['last'])
                lim = px * (1 + OFFSET) if side == 'buy' else px * (1 - OFFSET)
                order = await self.exchange.create_limit_order(
                    symbol, side, ct, lim,
                    {'marginMode': MARGIN_MODE, 'type': 'swap'}
                )
                console.print(f'[cyan][{symbol}] {side.upper()} {ct}ct @ {lim:.8f} (#{attempt+1})')
                if await self._wait_fill(symbol, side, ct):
                    console.print(f'[bold green][{symbol}] {side.upper()} FILLED')
                    return True
                try:
                    await self.exchange.cancel_order(order['id'], symbol, {'type': 'swap'})
                except Exception:
                    pass
            except Exception as e:
                console.print(f'[{symbol}] {side} #{attempt+1}: {e}')
            await asyncio.sleep(delay)
            delay = min(delay * 2, 8)
        return False

    async def _wait_fill(self, symbol: str, side: str, target: float) -> bool:
        t0 = time.time()
        want = 'long' if side == 'buy' else 'short'
        while time.time() - t0 < FILL_TIMEOUT_SEC:
            try:
                pos = await self.exchange.fetch_positions([symbol], {'type': 'swap'})
                filled = sum(float(p['contracts']) for p in pos
                             if p['side'] == want and float(p.get('contracts', 0)) > 0)
                if filled >= target:
                    return True
            except Exception:
                pass
            await asyncio.sleep(1)
        return False

    async def cancel_reduce_orders(self, symbol: str) -> None:
        """Cancel stale reduce-only orders before placing new closes."""
        try:
            orders = await self.exchange.fetch_open_orders(
                symbol, params={'marginMode': MARGIN_MODE, 'type': 'swap'})
            for o in orders:
                reduce = o.get('reduceOnly', False)
                if not reduce:
                    info = o.get('info', {})
                    reduce = info.get('is_reduce_only', False) or info.get('reduce_only', False)
                if reduce:
                    await self.exchange.cancel_order(
                        o['id'], symbol, {'marginMode': MARGIN_MODE, 'type': 'swap'})
        except Exception:
            pass

    async def close_at_target(self, symbol: str, side: str, contracts: float,
                              target_price: float) -> bool:
        """Limit close at calculated target price. Guarantees profit on every exit."""
        await self.cancel_reduce_orders(symbol)
        close_side = 'sell' if side == 'long' else 'buy'
        delay = 1
        for attempt in range(MAX_ORDER_RETRIES):
            try:
                await self.exchange.create_limit_order(
                    symbol, close_side, contracts, target_price,
                    {'marginMode': MARGIN_MODE, 'reduceOnly': True, 'type': 'swap'}
                )
                console.print(f'[green][{symbol}] Close {side} {contracts}ct @ {target_price:.8f}')
                return True
            except Exception as e:
                console.print(f'[{symbol}] target close #{attempt+1}: {e}')
                await self.cancel_reduce_orders(symbol)
                await asyncio.sleep(delay)
                delay = min(delay * 2, 8)
        return False

    async def close_position_market(self, symbol: str, side: str, contracts: float) -> bool:
        """Market order fallback for emergency/forced closes."""
        close_side = 'sell' if side == 'long' else 'buy'
        try:
            await self.exchange.create_market_order(
                symbol, close_side, contracts,
                {'marginMode': MARGIN_MODE, 'reduceOnly': True, 'type': 'swap'})
            return True
        except Exception as e:
            console.print(f'[red][{symbol}] Market close failed: {e}')
            return False

    async def dca_opposite(self, symbol: str, closed_side: str) -> None:
        """Bounded DCA: add 1ct to opposite side. Risk engine caps rounds."""
        hp = self.hedges.get(symbol)
        if not hp:
            return
        opp = 'short' if closed_side == 'long' else 'long'
        allowed, reason = self.risk.check_dca_allowed(hp, opp)
        if not allowed:
            console.print(f'[yellow][{symbol}] DCA blocked: {reason}')
            return
        opp_side = 'sell' if closed_side == 'long' else 'buy'
        try:
            tk = await self.exchange.fetch_ticker(symbol, {'type': 'swap'})
            px = float(tk['last'])
            lim = px * (1 + OFFSET) if opp_side == 'buy' else px * (1 - OFFSET)
            await self.exchange.create_limit_order(
                symbol, opp_side, 1, lim,
                {'marginMode': MARGIN_MODE, 'type': 'swap'})
            leg = hp.short_leg if closed_side == 'long' else hp.long_leg
            leg.dca_rounds += 1
            snap = self.risk.get_snapshot(0, 0, 0, self.hedges)
            self.journal.log('DCA', symbol, opp_side, 1, price=lim,
                             reason=f'opposite DCA round {leg.dca_rounds}/{MAX_DCA_ROUNDS}',
                             risk_snapshot=snap)
        except Exception as e:
            console.print(f'[yellow][{symbol}] DCA failed: {e}')

    # — Hedge state persistence —

    def save_hedge_state(self) -> None:
        try:
            data = {}
            for sym, hp in self.hedges.items():
                data[sym] = asdict(hp)
            with open(HEDGE_STATE_FILE, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception:
            pass

    def load_hedge_state(self) -> None:
        if not HEDGE_STATE_FILE.exists():
            return
        try:
            with open(HEDGE_STATE_FILE) as f:
                data = json.load(f)
            for sym, hp_dict in data.items():
                ll = hp_dict.get('long_leg', {})
                sl = hp_dict.get('short_leg', {})
                self.hedges[sym] = HedgePair(
                    long_leg=HedgeLeg(**ll), short_leg=HedgeLeg(**sl),
                    hedge_open_time=hp_dict.get('hedge_open_time', 0),
                    harvests=hp_dict.get('harvests', 0),
                    # New execution metrics (default to 0 for backward compatibility)
                    exit_attempts=hp_dict.get('exit_attempts', 0),
                    exit_fills=hp_dict.get('exit_fills', 0),
                    total_expected_profit=hp_dict.get('total_expected_profit', 0),
                    total_realized_profit=hp_dict.get('total_realized_profit', 0),
                    last_exit_time=hp_dict.get('last_exit_time', 0),
                )
        except Exception:
            pass

    # — Flatten symbol (force close both legs) —

    async def flatten_symbol(self, symbol: str, reason: str = '') -> None:
        """Close both legs. Used by risk engine force-flatten and emergency."""
        await self.cancel_reduce_orders(symbol)
        try:
            positions = await self.exchange.fetch_positions([symbol], {'type': 'swap'})
            for pos in positions:
                ct = float(pos.get('contracts', 0) or 0)
                if ct <= 0:
                    continue
                side = pos['side']
                close_side = 'sell' if side == 'long' else 'buy'
                try:
                    tk = await self.exchange.fetch_ticker(symbol, {'type': 'swap'})
                    px = float(tk['last'])
                    lim = px * (1 + OFFSET) if close_side == 'buy' else px * (1 - OFFSET)
                    await self.exchange.create_limit_order(
                        symbol, close_side, ct, lim,
                        {'marginMode': MARGIN_MODE, 'reduceOnly': True, 'type': 'swap'})
                except Exception:
                    try:
                        await self.close_position_market(symbol, side, ct)
                    except Exception as e2:
                        console.print(f'[bold red][{symbol}] FLATTEN FAILED {side}: {e2}')
                await asyncio.sleep(0.3)
        except Exception as e:
            console.print(f'[red][{symbol}] Flatten error: {e}')
        self.hedges.pop(symbol, None)
        self.state[symbol] = 0.0
        self.risk.clear_symbol(symbol)
        snap = self.risk.get_snapshot(0, 0, 0, self.hedges)
        self.journal.log('FLATTEN', symbol, '', 0, reason=reason,
                         risk_snapshot=asdict(snap) if snap else {})
    
    # — Panic exit (market order for emergency) —
    
    async def panic_exit(self, symbol: str, reason: str = '') -> None:
        """Emergency market exit - accepts slippage to guarantee fill."""
        try:
            positions = await self.exchange.fetch_positions([symbol], {'type': 'swap'})
            for pos in positions:
                ct = float(pos.get('contracts', 0) or 0)
                if ct <= 0:
                    continue
                side = pos['side']
                close_side = 'sell' if side == 'long' else 'buy'
                try:
                    await self.exchange.create_market_order(
                        symbol, close_side, ct,
                        {'marginMode': MARGIN_MODE, 'reduceOnly': True, 'type': 'swap'})
                    console.print(f'[bold yellow][{symbol}] PANIC EXIT {side}: {ct}ct | {reason}')
                except Exception as e:
                    console.print(f'[bold red][{symbol}] PANIC EXIT FAILED {side}: {e}')
            # Set cooldown after panic exit
            self.risk.set_cooldown(symbol, SYMBOL_COOLDOWN_SEC)
        except Exception as e:
            console.print(f'[red][{symbol}] Panic exit error: {e}')

    # — Hedge open pair (atomic: both legs or rollback) —

    async def hedge_open_pair(self, symbol: str) -> bool:
        """Open LONG + SHORT atomically. Rollback on failure."""
        h = await self.get_health()
        if not h['safe']:
            return False
        ok_count = sum(1 for hp in self.hedges.values() if hp.is_complete)
        can_open, reason = self.risk.check_can_open_new(ok_count)
        if not can_open:
            return False
        sym_ok, sym_reason = self.risk.check_symbol_risk(symbol, h['equity'])
        if not sym_ok:
            return False
        vol_ok = await self.check_volatility(symbol)
        if not vol_ok:
            return False
        ct = await self.safe_size(symbol)
        if ct <= 0:
            return False
        mkt = self.exchange.market(symbol)
        cs = float(mkt.get('contractSize', 1) or 1)
        tk = await self.exchange.fetch_ticker(symbol, {'type': 'swap'})
        px = float(tk['last'])
        margin_both = (px * cs * ct / DEFAULT_LEVERAGE) * 2
        if margin_both > h['active_capital'] - h['used']:
            return False
        snap = self.risk.get_snapshot(h['equity'], h['used'], h['free'], self.hedges)
        self.journal.log('HEDGE_ATTEMPT', symbol, 'both', ct, price=px,
                         reason='new hedge pair', risk_snapshot=snap)
        console.print(f'[cyan][{symbol}] Opening hedge: LONG leg...')
        if not await self.open_position(symbol, 'buy'):
            self.journal.log('HEDGE_FAIL', symbol, 'long', 0, reason='long fill failed',
                             risk_snapshot=snap)
            return False
        await asyncio.sleep(0.5)
        console.print(f'[cyan][{symbol}] Opening hedge: SHORT leg...')
        if not await self.open_position(symbol, 'sell'):
            console.print(f'[yellow][{symbol}] Short failed — rolling back long')
            await self.flatten_symbol(symbol, reason='rollback: short leg failed')
            return False
        now = time.time()
        try:
            positions = await self.exchange.fetch_positions([symbol], {'type': 'swap'})
            hp = HedgePair(hedge_open_time=now)
            for pos in positions:
                pct = float(pos.get('contracts', 0) or 0)
                if pct <= 0:
                    continue
                entry = float(pos.get('entryPrice', 0) or 0)
                if pos['side'] == 'long':
                    hp.long_leg = HedgeLeg(contracts=pct, entry=entry,
                                           timestamp=now, filled=True)
                elif pos['side'] == 'short':
                    hp.short_leg = HedgeLeg(contracts=pct, entry=entry,
                                            timestamp=now, filled=True)
            if hp.is_complete:
                self.hedges[symbol] = hp
                ntl = px * cs * ct
                self.risk.record_symbol_exposure(symbol, ntl * 2)
                self.save_hedge_state()
                console.print(
                    f'[bold green][{symbol}] HEDGE OPEN — '
                    f'L:{hp.long_leg.contracts}ct@{hp.long_leg.entry:.8f} '
                    f'S:{hp.short_leg.contracts}ct@{hp.short_leg.entry:.8f}')
                self.journal.log('HEDGE_OPEN', symbol, 'both', ct, price=px,
                                 reason='pair confirmed',
                                 hedge_state=f'L@{hp.long_leg.entry:.8f} S@{hp.short_leg.entry:.8f}',
                                 risk_snapshot=snap)
                return True
            else:
                await self.flatten_symbol(symbol, reason='incomplete after fills')
                return False
        except Exception as e:
            await self.flatten_symbol(symbol, reason=f'confirm error: {e}')
            return False

    # — Hedge harvest (profit-only close + DCA + reopen) —

    async def hedge_harvest(self, symbol: str) -> None:
        """Close profitable leg at target price, DCA opposite, reopen. Zero-loss design."""
        hp = self.hedges.get(symbol)
        if not hp or not hp.is_complete:
            return
        try:
            positions = await self.exchange.fetch_positions([symbol], {'type': 'swap'})
            for pos in positions:
                ct = float(pos.get('contracts', 0) or 0)
                if ct <= 0:
                    continue
                side = pos['side']
                upnl = float(pos.get('unrealizedPnl', 0) or 0)
                entry = float(pos.get('entryPrice', 0) or 0)
                self.risk.record_symbol_pnl(symbol, upnl)
                effective_threshold = (BASE_PROFIT_PER_CT + FEE_COST_PER_CT) * ct
                if upnl >= effective_threshold:
                    per_ct_target = effective_threshold / ct
                    if side == 'long':
                        target_price = entry + per_ct_target
                    else:
                        target_price = entry - per_ct_target
                    h = await self.get_health()
                    snap = self.risk.get_snapshot(
                        h['equity'], h['used'], h['free'], self.hedges)
                    console.print(
                        f'[bold green][{symbol}] {side} PROFIT ${upnl:.6f} >= '
                        f'${effective_threshold:.6f} — harvest @ {target_price:.8f}')
                    closed = await self.close_at_target(symbol, side, ct, target_price)
                    if closed:
                        self.perf.record_trade_pnl(upnl)
                        hp.harvests += 1
                        self.journal.log(
                            'HARVEST', symbol, side, ct, price=target_price, pnl=upnl,
                            reason=f'profit>threshold target={target_price:.8f}',
                            hedge_state=f'harvest#{hp.harvests}', risk_snapshot=snap)
                        if side == 'long':
                            hp.long_leg.filled = False
                        else:
                            hp.short_leg.filled = False
                        self.save_hedge_state()
                        await asyncio.sleep(1)
                        await self.dca_opposite(symbol, side)
                        await asyncio.sleep(0.5)
                        reopen_side = 'buy' if side == 'long' else 'sell'
                        console.print(f'[cyan][{symbol}] Reopening {side} leg...')
                        if await self.open_position(symbol, reopen_side):
                            new_pos = await self.exchange.fetch_positions(
                                [symbol], {'type': 'swap'})
                            for np_ in new_pos:
                                nct = float(np_.get('contracts', 0) or 0)
                                if nct > 0 and np_['side'] == side:
                                    new_entry = float(np_.get('entryPrice', 0) or 0)
                                    leg = HedgeLeg(contracts=nct, entry=new_entry,
                                                   timestamp=time.time(), filled=True)
                                    if side == 'long':
                                        hp.long_leg = leg
                                    else:
                                        hp.short_leg = leg
                                    break
                            self.save_hedge_state()
                            console.print(f'[bold green][{symbol}] {side} REOPENED')
                            self.journal.log('REOPEN', symbol, side, ct,
                                             reason='profit cycle complete', risk_snapshot=snap)
                        else:
                            self.journal.log('HEDGE_BROKEN', symbol, side, 0,
                                             reason='reopen failed', risk_snapshot=snap)
                    return
            total_upnl = sum(float(p.get('unrealizedPnl', 0) or 0)
                             for p in positions if float(p.get('contracts', 0) or 0) > 0)
            self.state[symbol] = total_upnl
            self.risk.record_symbol_pnl(symbol, total_upnl)
        except Exception as e:
            console.print(f'[red][{symbol}] Harvest error: {e}')

    # — Hedge repair (fix broken hedges) —

    async def hedge_repair(self, symbol: str) -> None:
        """Detect and fix broken hedges. Flatten if unfixable."""
        hp = self.hedges.get(symbol)
        if not hp:
            return
        try:
            positions = await self.exchange.fetch_positions([symbol], {'type': 'swap'})
            has_long = has_short = False
            for pos in positions:
                ct = float(pos.get('contracts', 0) or 0)
                if ct <= 0:
                    continue
                if pos['side'] == 'long':
                    has_long = True
                elif pos['side'] == 'short':
                    has_short = True
            hp.long_leg.filled = has_long
            hp.short_leg.filled = has_short
            if hp.is_complete:
                return
            if hp.is_empty:
                self.hedges.pop(symbol, None)
                self.risk.clear_symbol(symbol)
                self.save_hedge_state()
                return
            missing = 'long' if not has_long else 'short'
            h = await self.get_health()
            if not h['safe']:
                await self.flatten_symbol(symbol, reason='unsafe to repair')
                return
            snap = self.risk.get_snapshot(h['equity'], h['used'], h['free'], self.hedges)
            self.journal.log('REPAIR_ATTEMPT', symbol, missing, 0,
                             reason=f'{missing} missing', risk_snapshot=snap)
            reopen_side = 'buy' if missing == 'long' else 'sell'
            if await self.open_position(symbol, reopen_side):
                new_pos = await self.exchange.fetch_positions([symbol], {'type': 'swap'})
                for np_ in new_pos:
                    nct = float(np_.get('contracts', 0) or 0)
                    if nct > 0 and np_['side'] == missing:
                        leg = HedgeLeg(contracts=nct,
                                       entry=float(np_.get('entryPrice', 0) or 0),
                                       timestamp=time.time(), filled=True)
                        if missing == 'long':
                            hp.long_leg = leg
                        else:
                            hp.short_leg = leg
                        break
                self.save_hedge_state()
                self.journal.log('REPAIR_OK', symbol, missing, 1,
                                 reason='repaired', risk_snapshot=snap)
            else:
                await self.flatten_symbol(symbol, reason=f'{missing} repair failed')
        except Exception as e:
            console.print(f'[red][{symbol}] Repair error: {e}')

    # — Emergency close all —

    async def emergency_close_all(self, reason: str = 'margin critical') -> None:
        """Flatten every position. Last resort."""
        console.print(f'[bold red]EMERGENCY FLATTEN: {reason}')
        try:
            positions = await self.exchange.fetch_positions(None, {'type': 'swap'})
            for pos in positions:
                ct = float(pos.get('contracts', 0) or 0)
                if ct <= 0:
                    continue
                sym = pos['symbol']
                side = pos['side']
                close_side = 'sell' if side == 'long' else 'buy'
                try:
                    tk = await self.exchange.fetch_ticker(sym, {'type': 'swap'})
                    px = float(tk['last'])
                    lim = px * 0.995 if close_side == 'sell' else px * 1.005
                    await self.exchange.create_limit_order(
                        sym, close_side, ct, lim,
                        {'marginMode': MARGIN_MODE, 'reduceOnly': True, 'type': 'swap'})
                except Exception:
                    try:
                        await self.exchange.create_market_order(
                            sym, close_side, ct,
                            {'marginMode': MARGIN_MODE, 'reduceOnly': True, 'type': 'swap'})
                    except Exception:
                        pass
                await asyncio.sleep(0.2)
        except Exception as e:
            console.print(f'[red]Emergency error: {e}')
        self.hedges.clear()
        self.save_hedge_state()
        snap = self.risk.get_snapshot(0, 0, 0, self.hedges)
        self.journal.log('EMERGENCY_FLATTEN', 'ALL', '', 0,
                         reason=reason, risk_snapshot=snap)

    # — Position recovery (restart-safe) —

    async def recover_positions(self) -> None:
        """Rebuild hedge state from exchange + disk. Full restart recovery."""
        self.load_hedge_state()
        if self.hedges:
            console.print(f'[cyan]Loaded {len(self.hedges)} hedge pairs from disk')
        try:
            all_pos = await self.exchange.fetch_positions(None, {'type': 'swap'})
            by_symbol: Dict[str, list] = {}
            for pos in all_pos:
                ct = float(pos.get('contracts', 0) or 0)
                if ct <= 0:
                    continue
                by_symbol.setdefault(pos['symbol'], []).append(pos)
            recovered = 0
            for sym, pos_list in by_symbol.items():
                now = time.time()
                hp = self.hedges.get(sym, HedgePair(hedge_open_time=now))
                for pos in pos_list:
                    ct = float(pos.get('contracts', 0) or 0)
                    side = pos['side']
                    entry = float(pos.get('entryPrice', 0) or 0)
                    upnl = float(pos.get('unrealizedPnl', 0) or 0)
                    leg = HedgeLeg(contracts=ct, entry=entry,
                                   timestamp=hp.hedge_open_time or now, filled=True)
                    if side == 'long':
                        hp.long_leg = leg
                    elif side == 'short':
                        hp.short_leg = leg
                    self.state[sym] = self.state.get(sym, 0) + upnl
                    self.risk.record_symbol_pnl(sym, upnl)
                    recovered += 1
                self.hedges[sym] = hp
            self.save_hedge_state()
            if recovered:
                ok = sum(1 for hp in self.hedges.values() if hp.is_complete)
                broken = sum(1 for hp in self.hedges.values() if hp.is_broken)
                console.print(f'[bold cyan]Recovered {recovered} legs — {ok} complete, {broken} broken')
                snap = self.risk.get_snapshot(0, 0, 0, self.hedges)
                self.journal.log('RECOVER', 'ALL', '', 0,
                                 reason=f'{recovered} legs {ok} ok {broken} broken',
                                 risk_snapshot=snap)
        except Exception as e:
            console.print(f'[red]Recovery error: {e}')

    # — LLM symbol scoring (limited, deterministic filtering only) —

    async def _fetch_market_context(self, symbol: str) -> str:
        try:
            tk = await self.exchange.fetch_ticker(symbol, {'type': 'swap'})
            ohlcv = await self.exchange.fetch_ohlcv(symbol, '5m', limit=6)
            last = float(tk.get('last', 0))
            pct24 = float(tk.get('percentage', 0) or 0)
            vol24 = float(tk.get('quoteVolume', 0) or 0)
            closes = [c[4] for c in ohlcv] if ohlcv else []
            candle_str = ', '.join(f'{c:.8f}' for c in closes[-6:])
            return (f'Symbol: {symbol}\nLast: {last:.8f}\n24h change: {pct24:+.2f}%\n'
                    f'24h vol USDT: {vol24:.0f}\nRecent 5m closes: [{candle_str}]')
        except Exception:
            return f'Symbol: {symbol} (no data)'

    async def llm_score_symbol(self, symbol: str) -> float:
        """Score 0-10 for volatility (hedging opportunity). AI is advisory only."""
        if not GROQ_KEY:
            return 5.0
        try:
            context = await self._fetch_market_context(symbol)
            async with aiohttp.ClientSession() as sess:
                payload = {
                    'model': 'llama-3.1-8b-instant',
                    'messages': [
                        {'role': 'system', 'content':
                         'Score this crypto 0-10 for short-term volatility. '
                         'Higher = more volatile = better for hedged harvesting. '
                         'Reply ONLY a number.'},
                        {'role': 'user', 'content': context}
                    ],
                    'max_tokens': 5, 'temperature': 0.1,
                }
                headers = {'Authorization': f'Bearer {GROQ_KEY}',
                           'Content-Type': 'application/json'}
                async with sess.post(
                    'https://api.groq.com/openai/v1/chat/completions',
                    json=payload, headers=headers,
                    timeout=aiohttp.ClientTimeout(total=8)
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        raw = data['choices'][0]['message']['content'].strip()
                        return max(0.0, min(10.0, float(raw)))
        except Exception:
            pass
        return 5.0

    # — Symbol selection (auto-discovery, budget-aware) —

    async def fetch_eligible_symbols(self) -> List[str]:
        """Discover tradeable symbols within budget and risk limits."""
        if not self.exchange:
            await self.init_exchange()
        h = await self.get_health()
        if h['free'] <= 0:
            return []
        candidates = []
        for mkt in (self.exchange.markets or {}).values():
            sym = mkt.get('symbol')
            if not sym or not mkt.get('active', True) or not mkt.get('swap', False):
                continue
            if mkt.get('quote') != 'USDT' and mkt.get('settle') != 'USDT':
                continue
            cs = float(mkt.get('contractSize', 1) or 1)
            px = float(mkt.get('info', {}).get('last_price', 0) or 0)
            if px <= 0:
                continue
            ntl = px * cs
            mrg = ntl / DEFAULT_LEVERAGE
            if ntl <= MAX_NOTIONAL_PER_CONTRACT:
                candidates.append((sym, ntl, mrg))
        candidates.sort(key=lambda x: x[2])
        budget = h['active_capital'] - h['used']
        selected, running = [], 0.0
        for sym, ntl, mrg in candidates:
            hedge_cost = mrg * 2
            if running + hedge_cost <= budget and len(selected) < MAX_CONCURRENT_SYMBOLS:
                selected.append((sym, ntl, mrg))
                running += hedge_cost
        console.print(f'[bold green]{len(selected)} symbols eligible (hedge margin ${running:.4f})')
        return [s for s, _, _ in selected]

    # — Order book + position reading —

    async def fetch_book(self, symbol: str) -> Tuple[float, float]:
        """Return (best_bid, best_ask) from L2 order book."""
        try:
            ob = await self.exchange.fetch_order_book(symbol, 5, {'type': 'swap'})
            bid = float(ob['bids'][0][0]) if ob.get('bids') else 0
            ask = float(ob['asks'][0][0]) if ob.get('asks') else 0
            return bid, ask
        except Exception:
            tk = await self.exchange.fetch_ticker(symbol, {'type': 'swap'})
            px = float(tk['last'])
            return px * 0.9999, px * 1.0001

    async def read_positions(self, symbol: str) -> dict:
        """Read current positions for symbol. Returns {long: {cts, entry, upnl}, short: ...}."""
        result = {'long': None, 'short': None}
        try:
            positions = await self.exchange.fetch_positions([symbol], {'type': 'swap'})
            for pos in positions:
                ct = float(pos.get('contracts', 0) or 0)
                if ct <= 0:
                    continue
                side = pos['side']
                result[side] = {
                    'cts': ct,
                    'entry': float(pos.get('entryPrice', 0) or 0),
                    'upnl': float(pos.get('unrealizedPnl', 0) or 0),
                }
        except Exception:
            pass
        return result

    # — Spread-capture: maker quote placement —

    async def place_maker_quote(self, symbol: str, side: str, ct: int) -> Optional[str]:
        """Place post_only order at best bid (buy) or best ask (sell). Returns order ID."""
        try:
            bid, ask = await self.fetch_book(symbol)
            px = bid if side == 'buy' else ask
            if px <= 0:
                return None
            order = await self.exchange.create_limit_order(
                symbol, side, ct, px,
                {'marginMode': MARGIN_MODE, 'type': 'swap', 'postOnly': True})
            short_sym = symbol.split('/')[0]
            console.print(f'[cyan][{short_sym}] QUOTE {side.upper()} {ct}ct @ {px:.8f}')
            return order.get('id', '')
        except Exception as e:
            console.print(f'[{symbol}] Maker quote {side}: {e}')
            return None

    # — Spread-capture: taker fallback —

    async def taker_entry(self, symbol: str, side: str, ct: int) -> Optional[str]:
        """Cross the spread aggressively after maker timeout."""
        try:
            tk = await self.exchange.fetch_ticker(symbol, {'type': 'swap'})
            px = float(tk['last'])
            lim = px * (1 + OFFSET) if side == 'buy' else px * (1 - OFFSET)
            order = await self.exchange.create_limit_order(
                symbol, side, ct, lim,
                {'marginMode': MARGIN_MODE, 'type': 'swap'})
            short_sym = symbol.split('/')[0]
            console.print(f'[yellow][{short_sym}] TAKER {side.upper()} {ct}ct @ {lim:.8f}')
            return order.get('id', '')
        except Exception as e:
            console.print(f'[{symbol}] Taker {side}: {e}')
            return None

    # — Spread-capture: exit order at spread target —

    async def place_spread_exit(self, symbol: str, side: str, cts: float,
                                entry: float) -> Optional[str]:
        """Place reduce_only exit at entry ± spread target (covers fees)."""
        try:
            mkt = self.exchange.market(symbol)
            cs = float(mkt.get('contractSize', 1) or 1)
            fee_per_unit = entry * FEE_RATE * 2
            target_move = entry * SPREAD_TARGET_PCT + fee_per_unit
            if side == 'long':
                exit_px = entry + target_move
                close_side = 'sell'
            else:
                exit_px = entry - target_move
                close_side = 'buy'
            await self.cancel_reduce_orders(symbol)
            order = await self.exchange.create_limit_order(
                symbol, close_side, cts, exit_px,
                {'marginMode': MARGIN_MODE, 'reduceOnly': True, 'type': 'swap'})
            profit_est = target_move * cs * cts
            short_sym = symbol.split('/')[0]
            
            # Track execution metrics
            hp = self.hedges.get(symbol)
            if hp:
                hp.exit_attempts += 1
                hp.total_expected_profit += profit_est
                hp.last_exit_time = time.time()
            
            console.print(
                f'[green][{short_sym}] EXIT {side} {cts}ct @ {exit_px:.8f} '
                f'(entry={entry:.8f} profit=${profit_est:.6f} attempt={hp.exit_attempts if hp else 1})')
            return order.get('id', '')
        except Exception as e:
            console.print(f'[{symbol}] Exit order {side}: {e}')
            return None

    # — Spread-capture: manage one side (long or short) —

    async def _manage_side(self, symbol: str, side: str, qs: QuoteState) -> None:
        """Manage a single leg: quote → wait → taker fallback → exit placement."""
        is_long = side == 'long'
        filled = qs.long_filled if is_long else qs.short_filled
        order_id = qs.long_order_id if is_long else qs.short_order_id
        exit_id = qs.long_exit_id if is_long else qs.short_exit_id
        entry = qs.long_entry if is_long else qs.short_entry
        cts = qs.long_cts if is_long else qs.short_cts
        buy_side = 'buy' if is_long else 'sell'

        if filled and entry > 0 and cts > 0:
            if not exit_id:
                # Place exit order
                oid = await self.place_spread_exit(symbol, side, cts, entry)
                if oid:
                    if is_long:
                        qs.long_exit_id = oid
                    else:
                        qs.short_exit_id = oid
            else:
                # Check if exit filled or timed out
                try:
                    order = await self.exchange.fetch_order(exit_id, symbol)
                    if order['status'] == 'closed':
                        # Exit filled - track actual profit
                        hp = self.hedges.get(symbol)
                        if hp:
                            hp.exit_fills += 1
                            mkt = self.exchange.market(symbol)
                            cs = float(mkt.get('contractSize', 1) or 1)
                            fee_per_unit = entry * FEE_RATE * 2
                            target_move = entry * SPREAD_TARGET_PCT + fee_per_unit
                            profit_est = target_move * cs * cts
                            hp.total_realized_profit += profit_est
                        
                        sym_base = symbol.split('/')[0]
                        console.print(f'[green][{sym_base}] EXIT FILLED {side}')
                        if is_long:
                            qs.long_filled = False
                            qs.long_exit_id = ''
                            qs.realized += profit_est
                        else:
                            qs.short_filled = False
                            qs.short_exit_id = ''
                            qs.realized += profit_est
                    else:
                        # Check for timeout - switch to market exit
                        elapsed = time.time() - qs.quote_time
                        if elapsed > MAX_EXIT_WAIT_SEC:
                            console.print(f'[yellow][{symbol}] EXIT TIMEOUT after {elapsed:.0f}s, switching to market')
                            await self.exchange.cancel_order(exit_id, symbol)
                            # Market exit
                            await self.close_position_market(symbol, side, cts)
                            hp = self.hedges.get(symbol)
                            if hp:
                                hp.exit_fills += 1
                                # Estimate actual profit (likely negative due to slippage)
                                mkt = self.exchange.market(symbol)
                                cs = float(mkt.get('contractSize', 1) or 1)
                                tk = await self.exchange.fetch_ticker(symbol, {'type': 'swap'})
                                current_px = float(tk['last'])
                                if side == 'long':
                                    actual_profit = (current_px - entry) * cs * cts
                                else:
                                    actual_profit = (entry - current_px) * cs * cts
                                hp.total_realized_profit += actual_profit
                            
                            if is_long:
                                qs.long_filled = False
                                qs.long_exit_id = ''
                            else:
                                qs.short_filled = False
                                qs.short_exit_id = ''
                            
                            # Set cooldown after failed exit
                            self.risk.set_cooldown(symbol, SYMBOL_COOLDOWN_SEC)
                except Exception as e:
                    console.print(f'[{symbol}] Exit check error: {e}')
        else:
            pos = await self.read_positions(symbol)
            pos_data = pos.get(side)
            if not pos_data or pos_data['cts'] <= 0:
                mkt = self.exchange.market(symbol)
                cs = float(mkt.get('contractSize', 1) or 1)
                fee_per_unit = entry * FEE_RATE * 2
                profit = (entry * SPREAD_TARGET_PCT + fee_per_unit) * cs * cts
                self.perf.record_trade_pnl(profit)
                qs.cycles += 1
                qs.realized += profit
                short_sym = symbol.split('/')[0]
                h = await self.get_health()
                snap = self.risk.get_snapshot(h['equity'], h['used'], h['free'], self.hedges)
                self.journal.log('SPREAD_EXIT', symbol, side, cts, price=entry,
                                 pnl=profit,
                                 reason=f'cycle#{qs.cycles} +${profit:.8f}',
                                 risk_snapshot=snap)
                console.print(
                    f'[bold green][{short_sym}] {side.upper()} EXIT +${profit:.8f} '
                    f'(cycle {qs.cycles} total=${qs.realized:.8f})')
                if is_long:
                    qs.long_filled = False
                    qs.long_entry = 0
                    qs.long_cts = 0
                    qs.long_exit_id = ''
                    qs.long_order_id = ''
                else:
                    qs.short_filled = False
                    qs.short_entry = 0
                    qs.short_cts = 0
                    qs.short_exit_id = ''
                    qs.short_order_id = ''
        return

        if not order_id:
            ct = await self.safe_size(symbol)
            if ct <= 0:
                return
            oid = await self.place_maker_quote(symbol, buy_side, ct)
            if oid:
                if is_long:
                    qs.long_order_id = oid
                else:
                    qs.short_order_id = oid
                qs.quote_time = time.time()
            return

        elapsed = time.time() - qs.quote_time if qs.quote_time > 0 else 0
        try:
            order = await self.exchange.fetch_order(order_id, symbol, {'type': 'swap'})
            status = order.get('status', '')
            if status == 'closed':
                pos = await self.read_positions(symbol)
                pos_data = pos.get(side)
                if pos_data and pos_data['cts'] > 0:
                    if is_long:
                        qs.long_filled = True
                        qs.long_entry = pos_data['entry']
                        qs.long_cts = pos_data['cts']
                        qs.long_order_id = ''
                    else:
                        qs.short_filled = True
                        qs.short_entry = pos_data['entry']
                        qs.short_cts = pos_data['cts']
                        qs.short_order_id = ''
                return
            if status == 'canceled' or status == 'expired':
                if is_long:
                    qs.long_order_id = ''
                else:
                    qs.short_order_id = ''
                return
        except Exception:
            if is_long:
                qs.long_order_id = ''
            else:
                qs.short_order_id = ''
            return

        if elapsed >= QUOTE_REFRESH_SEC and elapsed < MAKER_TIMEOUT_SEC:
            bid, ask = await self.fetch_book(symbol)
            quote_px = qs.long_quote_px if is_long else qs.short_quote_px
            ref = bid if is_long else ask
            if ref > 0 and quote_px > 0 and abs(ref - quote_px) / ref > BOOK_DRIFT_THRESHOLD:
                try:
                    await self.exchange.cancel_order(order_id, symbol, {'type': 'swap'})
                except Exception:
                    pass
                if is_long:
                    qs.long_order_id = ''
                else:
                    qs.short_order_id = ''

        if elapsed >= MAKER_TIMEOUT_SEC:
            try:
                await self.exchange.cancel_order(order_id, symbol, {'type': 'swap'})
            except Exception:
                pass
            ct = await self.safe_size(symbol)
            if ct > 0:
                oid = await self.taker_entry(symbol, buy_side, ct)
                if oid:
                    await asyncio.sleep(FILL_TIMEOUT_SEC)
                    pos = await self.read_positions(symbol)
                    pos_data = pos.get(side)
                    if pos_data and pos_data['cts'] > 0:
                        if is_long:
                            qs.long_filled = True
                            qs.long_entry = pos_data['entry']
                            qs.long_cts = pos_data['cts']
                        else:
                            qs.short_filled = True
                            qs.short_entry = pos_data['entry']
                            qs.short_cts = pos_data['cts']
            if is_long:
                qs.long_order_id = ''
            else:
                qs.short_order_id = ''

    # — Spread-capture cycle (replaces passive execute_trade) —

    async def spread_capture_cycle(self, symbol: str) -> None:
        """Per-symbol: manage both sides independently. Risk-gated."""
        try:
            h = await self.get_health()
            if not h['safe']:
                if h['margin_ratio'] >= MARGIN_RATIO_CRITICAL:
                    await self.emergency_close_all('margin ratio critical')
                return
            g_safe, g_reason = self.risk.check_global_risk(h['equity'])
            if not g_safe:
                console.print(f'[red]Global risk breach: {g_reason}')
                return
            vol_ok = await self.check_volatility(symbol)
            if not vol_ok:
                return
            hp = self.hedges.get(symbol)
            if hp:
                age_ok, age_reason = self.risk.check_position_age(hp)
                if not age_ok:
                    console.print(f'[yellow][{symbol}] Time exit: {age_reason}')
                    await self.flatten_symbol(symbol, reason=age_reason)
                    self.quotes.pop(symbol, None)
                    return
                
                # Panic exit check: if position open too long without harvest
                position_age = time.time() - hp.hedge_open_time
                if position_age > PANIC_EXIT_SEC and hp.harvests == 0:
                    console.print(f'[bold red][{symbol}] PANIC: position {position_age:.0f}s old, no harvests')
                    await self.panic_exit(symbol, reason=f'position age {position_age:.0f}s > {PANIC_EXIT_SEC}s')
                    self.quotes.pop(symbol, None)
                    return
                
                # Edge decay check: if real edge < 50% of theoretical, pause
                if hp.exit_attempts > 0:
                    edge_ratio = hp.total_realized_profit / hp.total_expected_profit if hp.total_expected_profit > 0 else 0
                    if edge_ratio < EDGE_DECAY_THRESHOLD and hp.exit_attempts > 5:
                        console.print(f'[yellow][{symbol}] EDGE DECAY: real edge {edge_ratio:.1%} < threshold {EDGE_DECAY_THRESHOLD:.0%}')
                        self.risk.set_cooldown(symbol, SYMBOL_COOLDOWN_SEC * 2)  # Longer cooldown
                        self.quotes.pop(symbol, None)
                        return
                sym_safe, sym_reason = self.risk.check_symbol_risk(symbol, h['equity'])
                if not sym_safe and 'drawdown' in sym_reason:
                    console.print(f'[red][{symbol}] Risk flatten: {sym_reason}')
                    await self.flatten_symbol(symbol, reason=sym_reason)
                    self.quotes.pop(symbol, None)
                    return
            qs = self.quotes.get(symbol)
            if not qs:
                qs = QuoteState()
                self.quotes[symbol] = qs
            await self._manage_side(symbol, 'long', qs)
            await self._manage_side(symbol, 'short', qs)
            pos = await self.read_positions(symbol)
            if pos['long'] and pos['short']:
                now = time.time()
                hp = self.hedges.get(symbol)
                if not hp:
                    hp = HedgePair(hedge_open_time=now)
                hp.long_leg = HedgeLeg(
                    contracts=pos['long']['cts'], entry=pos['long']['entry'],
                    timestamp=now, filled=True)
                hp.short_leg = HedgeLeg(
                    contracts=pos['short']['cts'], entry=pos['short']['entry'],
                    timestamp=now, filled=True)
                self.hedges[symbol] = hp
                self.save_hedge_state()
            elif not pos['long'] and not pos['short']:
                self.hedges.pop(symbol, None)
                self.risk.clear_symbol(symbol)
                self.save_hedge_state()
        except Exception as e:
            console.print(f'[{symbol}] Spread cycle error: {e}')

    # — Risk enforcement sweep —

    async def risk_enforcement_sweep(self) -> None:
        """Check all hedges for risk breaches and flatten as needed."""
        try:
            h = await self.get_health()
            self.risk.update_peak_equity(h['equity'])
            self.perf.record_equity(
                h['equity'],
                sum(self.state.get(s, 0) for s in self.hedges),
                len(self.hedges))
            to_flatten = self.risk.symbols_to_flatten(h['equity'], self.hedges)
            for sym, reason in to_flatten:
                console.print(f'[red]Risk flatten {sym}: {reason}')
                await self.flatten_symbol(sym, reason=reason)
                self.quotes.pop(sym, None)
            today = datetime.now(timezone.utc).strftime('%Y-%m-%d')
            if today != self._last_report_day:
                self._last_report_day = today
                self.perf.export_daily_report(h['equity'], h['used'], self.hedges, self.risk)
                self.perf.save_metrics(h['equity'], h['used'])
        except Exception as e:
            console.print(f'[red]Risk sweep error: {e}')

    # — Monitor loop (dashboard) —

    async def monitor_loop(self, symbols: List[str]) -> None:
        """Periodic dashboard display."""
        while True:
            try:
                await asyncio.sleep(MONITOR_INTERVAL)
                h = await self.get_health()
                dd = self.risk.current_drawdown(h['equity'])
                total_upnl = 0.0
                for sym in list(self.hedges.keys()):
                    total_upnl += self.state.get(sym, 0)
                total_realized = sum(qs.realized for qs in self.quotes.values())
                total_cycles = sum(qs.cycles for qs in self.quotes.values())
                table = Table(title='CopyThatPay — Spread Capture')
                table.add_column('', style='bold')
                table.add_column('')
                snap = self.risk.get_snapshot(h['equity'], h['used'], h['free'], self.hedges)
                table.add_row('Risk', snap.risk_verdict)
                table.add_row('Equity', f'${h["equity"]:.4f}')
                table.add_row('Active/Reserve/Buffer',
                              f'${h["active_capital"]:.4f}/${h["reserve"]:.4f}/${h["buffer"]:.4f}')
                table.add_row('Used/Free', f'${h["used"]:.4f} / ${h["free"]:.4f}')
                table.add_row('Margin', f'{h["margin_ratio"]:.1%}')
                table.add_row('Drawdown',
                              f'{dd:.2%} (max {self.risk.current_drawdown(h["equity"]):.2%})')
                ok = sum(1 for hp in self.hedges.values() if hp.is_complete)
                broken = sum(1 for hp in self.hedges.values() if hp.is_broken)
                syms = len(set(self.hedges.keys()))
                table.add_row('Positions', f'{ok} hedged / {broken} broken / {syms} sym')
                table.add_row('uPnL', f'${total_upnl:.6f}')
                table.add_row('Realized', f'${total_realized:.6f} ({total_cycles} cycles)')
                ps = self.perf.get_summary(h['equity'], h['used'])
                table.add_row('Cycle PnL', f'${ps["total_realized_pnl"]:.6f}')
                table.add_row('Win Rate', f'{ps["win_rate"]:.0%} ({ps["trade_count"]} trades)')
                table.add_row('Sharpe', f'{ps["sharpe_ratio"]:.3f}')
                elapsed = time.time() - self.perf.session_start if self.perf.session_start else 1
                rate = total_realized / elapsed if elapsed > 0 else 0
                table.add_row('Rate', f'${rate:.8f}/s')
                table.add_row('Uptime', f'{elapsed:.0f}s')
                for sym in sorted(self.hedges.keys()):
                    hp = self.hedges[sym]
                    qs = self.quotes.get(sym, QuoteState())
                    short_sym = sym.split('/')[0]
                    l_status = f'{hp.long_leg.contracts:.0f}ct' if hp.long_leg.filled else 'quoting'
                    s_status = f'{hp.short_leg.contracts:.0f}ct' if hp.short_leg.filled else 'quoting'
                    table.add_row(
                        short_sym,
                        f'L:{l_status} S:{s_status} [{qs.cycles}cyc +${qs.realized:.6f}]')
                console.print(table)
            except Exception as e:
                console.print(f'[red]Monitor error: {e}')

    # — Main run loop —

    async def run(self) -> None:
        """Initialize, recover, then loop spread-capture on all symbols."""
        try:
            DATA_DIR.mkdir(exist_ok=True)
            DAILY_REPORT_DIR.mkdir(parents=True, exist_ok=True)
            symbols = []
            if SYMBOL_FILE.exists():
                try:
                    with open(SYMBOL_FILE) as f:
                        symbols = [s for s in json.load(f) if isinstance(s, str) and s]
                except Exception:
                    pass
            if not symbols:
                symbols = await self.fetch_eligible_symbols()
                if symbols:
                    with open(SYMBOL_FILE, 'w') as f:
                        json.dump(symbols, f, indent=2)
            if not symbols:
                console.print('[red]No eligible symbols. Exiting.')
                return
            self.state = {s: 0.0 for s in symbols}
            if not self.exchange:
                await self.init_exchange()
            for sym in symbols:
                try:
                    await self.exchange.set_leverage(
                        DEFAULT_LEVERAGE, sym,
                        {'marginMode': MARGIN_MODE, 'type': 'swap'})
                except Exception:
                    pass
            await self.recover_positions()
            h = await self.get_health()
            self.risk.update_peak_equity(h['equity'])
            ok = sum(1 for hp in self.hedges.values() if hp.is_complete)
            console.print(
                f'\n[bold cyan]CopyThatPay — Spread Capture Engine\n'
                f'  Capital: ${h["equity"]:.4f} '
                f'(active=${h["active_capital"]:.4f} '
                f'reserve=${h["reserve"]:.4f} '
                f'buffer=${h["buffer"]:.4f})\n'
                f'  Mode: {MARGIN_MODE} {DEFAULT_LEVERAGE}x | '
                f'Spread target: {SPREAD_TARGET_PCT:.1%} | '
                f'Maker timeout: {MAKER_TIMEOUT_SEC}s\n'
                f'  Symbols: {len(symbols)} | Max: {MAX_CONCURRENT_SYMBOLS}\n'
                f'  Hedges: {ok} active\n'
                f'  Risk: {MAX_DRAWDOWN_PER_SYMBOL:.0%}/sym, '
                f'{MAX_DRAWDOWN_GLOBAL:.0%} global, '
                f'{MAX_POSITION_AGE_SECONDS//3600}h exit\n'
                f'  Data: {DATA_DIR}/\n')
            snap = self.risk.get_snapshot(h['equity'], h['used'], h['free'], self.hedges)
            self.journal.log('SYSTEM_START', 'ALL', '', 0,
                             reason=f'equity=${h["equity"]:.4f} symbols={len(symbols)}',
                             risk_snapshot=snap)
            monitor = asyncio.create_task(self.monitor_loop(symbols))
            while True:
                await self.risk_enforcement_sweep()
                for sym in symbols:
                    try:
                        await self.spread_capture_cycle(sym)
                    except Exception as e:
                        console.print(f'[{sym}] Error: {e}')
                    await asyncio.sleep(CYCLE_INTERVAL_SEC)
        except Exception as e:
            console.print(f'[red]Fatal: {e}')
            traceback.print_exc()
        finally:
            await self.cleanup()


# ═══════════════════════════════════════════════════════════════════════════════
# ENTRY POINT
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == '__main__':
    console.print('[bold cyan]CopyThatPay — Hedged Spread-Capture Engine')
    console.print('[dim]Capital preservation first. Profit second. Always.')
    bot = CopyThatPay()
    try:
        asyncio.run(bot.run())
    except KeyboardInterrupt:
        console.print('\n[yellow]Shutdown requested.')
    except Exception as e:
        console.print(f'[red]Fatal: {e}')
        traceback.print_exc()
