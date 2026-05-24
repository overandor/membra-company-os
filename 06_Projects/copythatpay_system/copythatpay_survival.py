#!/usr/bin/env python3
"""
CopyThatPay — $9 Survival Mode

Lean, directional micro-scalper designed for micro-capital environments.
No hedging. No symmetric quoting. Just execution discipline.

Strategy: WAIT → STRIKE → EXIT FAST → REPEAT

Entry: TAKER (market order) when edge exists
Exit: Fast target (0.25%) / stop loss (0.15%) / time stop (30s)
Risk: 2% of equity per trade
Filters: Spread >= 0.2%, Volume >= $50k, Imbalance > 0.3, Momentum > 0.001

⚠️  WARNING: This is experimental software. Trading involves significant risk.
"""

import ccxt.async_support as ccxt
import asyncio
import json
import os
import time
import traceback
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from dotenv import load_dotenv
from pathlib import Path
from typing import Dict, Optional
from rich.console import Console
from rich.table import Table

load_dotenv()
console = Console()

# ═══════════════════════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════════

API_KEY    = os.getenv('GATE_API_KEY', '')
API_SECRET = os.getenv('GATE_API_SECRET', '')

if not API_KEY or not API_SECRET:
    console.print('[bold red]FATAL: GATE_API_KEY and GATE_API_SECRET must be set in .env')
    exit(1)

# File paths
DATA_DIR          = Path('copythatpay_survival_data')
STATE_FILE        = DATA_DIR / 'state.json'
TRADE_JOURNAL     = DATA_DIR / 'journal.jsonl'
EQUITY_CURVE_CSV  = DATA_DIR / 'equity_curve.csv'
TOXICITY_LOG      = DATA_DIR / 'toxicity.jsonl'

# Capital and risk
TOTAL_CAPITAL_USD     = 9.0
RISK_PER_TRADE_PCT    = 0.02  # 2% of equity per trade
DEFAULT_LEVERAGE       = 5
MARGIN_MODE           = 'isolated'
FEE_RATE              = 0.00075  # 0.075% per side

# Exit parameters
TAKE_PROFIT_PCT       = 0.0025  # 0.25%
STOP_LOSS_PCT         = 0.0015  # 0.15%
TIME_EXIT_SEC         = 30      # 30 seconds max position time

# Entry filters
MIN_SPREAD_PCT        = 0.002   # 0.2% minimum spread
MIN_VOLUME_USD        = 50000   # $50k minimum 24h volume
IMBALANCE_THRESHOLD   = 0.3     # 0.3 imbalance threshold
MOMENTUM_THRESHOLD    = 0.001   # 0.1% momentum threshold

# Risk controls
MAX_DRAWDOWN_GLOBAL   = 0.10    # 10% global drawdown limit
COOLDOWN_AFTER_LOSS   = 30      # 30 seconds cooldown after loss
MAX_POSITIONS         = 1       # Only one position at a time for micro account

# Timing
CYCLE_INTERVAL_SEC    = 2       # Seconds between symbol cycles

# Diagnostic mode (bypass entry filters to test execution)
DIAGNOSTIC_MODE       = False   # If True, force enter first symbol (TESTING ONLY)

# ═══════════════════════════════════════════════════════════════════════════════
# DATA STRUCTURES
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class Position:
    """Active position state."""
    symbol: str = ''
    side: str = ''  # 'long' or 'short'
    contracts: float = 0
    entry_price: float = 0
    entry_mid_price: float = 0  # Mid price at entry (for slippage calc)
    entry_time: float = 0
    entry_expected_profit: float = 0
    entry_imbalance: float = 0   # Imbalance at entry
    entry_momentum: float = 0    # Momentum at entry

@dataclass
class TradeRecord:
    """Auditable trade record."""
    timestamp: str = ''
    epoch: float = 0
    action: str = ''
    symbol: str = ''
    side: str = ''
    contracts: float = 0
    price: float = 0
    pnl: float = 0
    reason: str = ''
    equity: float = 0

@dataclass
class ToxicityRecord:
    """Fill toxicity metrics."""
    timestamp: str = ''
    epoch: float = 0
    symbol: str = ''
    side: str = ''
    entry_price: float = 0
    entry_mid: float = 0
    exit_price: float = 0
    entry_imbalance: float = 0
    entry_momentum: float = 0
    duration_sec: float = 0
    slippage_pct: float = 0
    realized_pnl: float = 0
    expected_pnl: float = 0
    toxicity_ratio: float = 0  # realized / expected
    classification: str = ''  # 'good' or 'toxic'
    exit_reason: str = ''

@dataclass
class Performance:
    """Performance tracking."""
    start_time: float = 0
    start_equity: float = 0
    trades: list = field(default_factory=list)
    wins: int = 0
    losses: int = 0
    timeouts: int = 0
    total_pnl: float = 0
    peak_equity: float = 0
    # Toxicity metrics
    toxicity_records: list = field(default_factory=list)
    good_fills: int = 0
    toxic_fills: int = 0
    avg_toxicity: float = 0

# ═══════════════════════════════════════════════════════════════════════════════
# SURVIVAL BOT
# ═══════════════════════════════════════════════════════════════════════════════

class SurvivalBot:
    """Lean directional micro-scalper."""

    def __init__(self):
        self.exchange = None
        self.position: Optional[Position] = None
        self.perf = Performance()
        self.last_trade_loss_time: float = 0
        self.symbols: list = []

    async def init_exchange(self) -> None:
        """Initialize exchange connection."""
        self.exchange = ccxt.gateio({
            'apiKey': API_KEY,
            'secret': API_SECRET,
            'enableRateLimit': True,
            'timeout': 60000,
            'options': {
                'defaultType': 'swap',
                'defaultSettle': 'usdt',
                'adjustForTimeDifference': True,
                'recvWindow': 60000,
            },
            'headers': {'User-Agent': 'Mozilla/5.0'}
        })
        
        for attempt in range(5):
            try:
                await self.exchange.load_markets()
                console.print('[green]Exchange connected[/green]')
                return
            except Exception as e:
                console.print(f'[yellow]Load markets failed ({attempt+1}/5): {e}[/yellow]')
                if attempt < 4:
                    await asyncio.sleep(2 ** attempt)

        console.print('[red]WARNING: running without full market load[/red]')

    async def cleanup(self) -> None:
        """Cleanup on shutdown."""
        if self.exchange:
            try:
                await self.exchange.close()
            except Exception:
                pass

    async def get_balance(self) -> float:
        """Get USDT balance."""
        try:
            bal = await self.exchange.fetch_balance()
            return float(bal.get('total', {}).get('USDT', 0) or 0)
        except Exception as e:
            console.print(f'[red]Balance error: {e}')
            return 0

    async def get_orderbook_imbalance(self, symbol: str) -> float:
        """Returns imbalance: +1 = heavy buy pressure, -1 = heavy sell pressure."""
        try:
            ob = await self.exchange.fetch_order_book(symbol, 10)
            bids = sum(b[1] for b in ob['bids'])
            asks = sum(a[1] for a in ob['asks'])
            total = bids + asks
            if total == 0:
                return 0.0
            return (bids - asks) / total
        except Exception as e:
            console.print(f'[dim][{symbol}] Imbalance error: {e}')
            return 0.0

    async def get_micro_momentum(self, symbol: str) -> float:
        """Returns 1-minute momentum: positive = rising, negative = falling."""
        try:
            ohlcv = await self.exchange.fetch_ohlcv(symbol, '1m', limit=3)
            if len(ohlcv) < 3:
                return 0.0
            closes = [c[4] for c in ohlcv]
            if closes[0] == 0:
                return 0.0
            return (closes[-1] - closes[0]) / closes[0]
        except Exception as e:
            console.print(f'[dim][{symbol}] Momentum error: {e}')
            return 0.0

    async def get_mid_price(self, symbol: str) -> float:
        """Returns mid price (bid + ask) / 2."""
        try:
            book = await self.exchange.fetch_order_book(symbol, limit=5)
            bid = book['bids'][0][0] if book['bids'] else 0
            ask = book['asks'][0][0] if book['asks'] else 0
            if bid == 0 or ask == 0:
                return 0
            return (bid + ask) / 2
        except Exception:
            return 0

    async def should_enter(self, symbol: str) -> Optional[str]:
        """Check if entry conditions are met. Returns 'long', 'short', or None."""
        
        # DIAGNOSTIC MODE: Force entry on first symbol to test execution
        if DIAGNOSTIC_MODE:
            console.print(f'[bold yellow][DIAGNOSTIC] Forcing LONG entry on {symbol}')
            return 'long'
        
        # Check cooldown after loss
        if self.last_trade_loss_time > 0:
            if time.time() - self.last_trade_loss_time < COOLDOWN_AFTER_LOSS:
                return None

        # Get market data
        imbalance = await self.get_orderbook_imbalance(symbol)
        momentum = await self.get_micro_momentum(symbol)

        # Check spread and volume
        try:
            book = await self.exchange.fetch_order_book(symbol, limit=20)
            bid = book['bids'][0][0] if book['bids'] else 0
            ask = book['asks'][0][0] if book['asks'] else 0
            if bid == 0 or ask == 0:
                return None
            spread_pct = (ask - bid) / ((bid + ask) / 2)

            ticker = await self.exchange.fetch_ticker(symbol)
            volume_usd = ticker.get('quoteVolume', 0) or 0

            # Critical filters
            if spread_pct < MIN_SPREAD_PCT:
                console.print(f'[dim][{symbol}] Spread too tight: {spread_pct:.3%}')
                return None
            if volume_usd < MIN_VOLUME_USD:
                console.print(f'[dim][{symbol}] Volume too low: ${volume_usd:,.0f}')
                return None
        except Exception as e:
            console.print(f'[dim][{symbol}] Data error: {e}')
            return None

        # Strong directional agreement ONLY
        if imbalance > IMBALANCE_THRESHOLD and momentum > MOMENTUM_THRESHOLD:
            console.print(f'[green][{symbol}] LONG SIGNAL: imbalance={imbalance:.3f}, momentum={momentum:.4f}')
            return 'long'
        if imbalance < -IMBALANCE_THRESHOLD and momentum < -MOMENTUM_THRESHOLD:
            console.print(f'[green][{symbol}] SHORT SIGNAL: imbalance={imbalance:.3f}, momentum={momentum:.4f}')
            return 'short'

        # Log why no signal
        short_sym = symbol.split('/')[0]
        console.print(f'[dim][{short_sym}] NO SIGNAL: imbalance={imbalance:.3f} (need >{IMBALANCE_THRESHOLD}), momentum={momentum:.4f} (need >{MOMENTUM_THRESHOLD})')
        return None

    async def calculate_position_size(self, symbol: str) -> float:
        """Calculate position size based on 2% risk per trade."""
        try:
            equity = await self.get_balance()
            if equity <= 0:
                return 0

            risk_amount = equity * RISK_PER_TRADE_PCT
            notional = risk_amount * DEFAULT_LEVERAGE

            ticker = await self.exchange.fetch_ticker(symbol)
            price = float(ticker['last'])
            if price <= 0:
                return 0

            market = self.exchange.market(symbol)
            contract_size = float(market.get('contractSize', 1) or 1)
            min_amount = int(market.get('limits', {}).get('amount', {}).get('min') or 1)

            contracts = notional / (price * contract_size)
            contracts = max(min_amount, int(contracts))

            console.print(f'[cyan][{symbol}] Size: {contracts} contracts (equity=${equity:.2f}, notional=${notional:.2f})')
            return contracts
        except Exception as e:
            console.print(f'[red][{symbol}] Size error: {e}')
            return 0

    async def enter_trade(self, symbol: str, side: str, contracts: float) -> bool:
        """Enter position via market order (taker)."""
        try:
            # Capture entry metrics BEFORE order
            entry_imbalance = await self.get_orderbook_imbalance(symbol)
            entry_momentum = await self.get_micro_momentum(symbol)
            entry_mid = await self.get_mid_price(symbol)
            
            order_side = 'buy' if side == 'long' else 'sell'
            order = await self.exchange.create_market_order(
                symbol,
                order_side,
                contracts,
                {'marginMode': MARGIN_MODE, 'type': 'swap'}
            )
            
            # Get fill price
            ticker = await self.exchange.fetch_ticker(symbol)
            entry_price = float(ticker['last'])
            
            # Calculate expected profit (target - 2*fees)
            expected_move = TAKE_PROFIT_PCT
            expected_profit = expected_move - 2 * FEE_RATE
            
            self.position = Position(
                symbol=symbol,
                side=side,
                contracts=contracts,
                entry_price=entry_price,
                entry_mid_price=entry_mid,
                entry_time=time.time(),
                entry_expected_profit=expected_profit,
                entry_imbalance=entry_imbalance,
                entry_momentum=entry_momentum
            )
            
            console.print(f'[bold green][{symbol}] ENTERED {side.upper()} {contracts}ct @ ${entry_price:.8f} (mid=${entry_mid:.8f})')
            self.log_trade('ENTER', symbol, side, contracts, entry_price, 0, f'expected EV={expected_profit:.3%}')
            return True
        except Exception as e:
            console.print(f'[red][{symbol}] Enter failed: {e}')
            return False

    async def manage_trade(self) -> Optional[str]:
        """Manage active position. Returns 'win', 'loss', 'timeout', or None."""
        if not self.position:
            return None

        pos = self.position
        start = pos.entry_time
        equity = await self.get_balance()

        while True:
            try:
                # Check time stop
                if time.time() - start > TIME_EXIT_SEC:
                    console.print(f'[yellow][{pos.symbol}] TIMEOUT EXIT ({time.time() - start:.0f}s)')
                    await self.close_position('timeout')
                    return 'timeout'

                # Get current price
                ticker = await self.exchange.fetch_ticker(pos.symbol)
                current_price = float(ticker['last'])

                # Calculate move
                if pos.side == 'long':
                    move = (current_price - pos.entry_price) / pos.entry_price
                else:  # short
                    move = (pos.entry_price - current_price) / pos.entry_price

                # Check take profit
                if move >= TAKE_PROFIT_PCT:
                    console.print(f'[bold green][{pos.symbol}] TAKE PROFIT: {move:.3%}')
                    await self.close_position('win')
                    return 'win'

                # Check stop loss
                if move <= -STOP_LOSS_PCT:
                    console.print(f'[bold red][{pos.symbol}] STOP LOSS: {move:.3%}')
                    await self.close_position('loss')
                    return 'loss'

                # Wait before next check
                await asyncio.sleep(1)

            except Exception as e:
                console.print(f'[red][{pos.symbol}] Management error: {e}')
                await asyncio.sleep(1)

    async def close_position(self, reason: str) -> None:
        """Close position via market order and log toxicity."""
        if not self.position:
            return

        pos = self.position
        try:
            close_side = 'sell' if pos.side == 'long' else 'buy'
            order = await self.exchange.create_market_order(
                pos.symbol,
                close_side,
                pos.contracts,
                {'marginMode': MARGIN_MODE, 'type': 'swap'}
            )

            # Calculate realized PnL
            ticker = await self.exchange.fetch_ticker(pos.symbol)
            exit_price = float(ticker['last'])
            
            if pos.side == 'long':
                pnl_pct = (exit_price - pos.entry_price) / pos.entry_price - 2 * FEE_RATE
            else:
                pnl_pct = (pos.entry_price - exit_price) / pos.entry_price - 2 * FEE_RATE
            
            notional = pos.entry_price * pos.contracts
            pnl = notional * pnl_pct
            
            # Calculate slippage (entry price vs mid at entry)
            if pos.entry_mid_price > 0:
                slippage_pct = abs(pos.entry_price - pos.entry_mid_price) / pos.entry_mid_price
            else:
                slippage_pct = 0
            
            # Calculate toxicity ratio
            expected_pnl = notional * pos.entry_expected_profit
            toxicity_ratio = pnl / expected_pnl if expected_pnl != 0 else 0
            
            # Classify fill
            classification = 'good' if pnl > 0 else 'toxic'
            
            # Log toxicity
            duration = time.time() - pos.entry_time
            self.log_toxicity(pos, exit_price, duration, slippage_pct, pnl, expected_pnl, toxicity_ratio, classification, reason)
            
            # Update performance
            self.perf.trades.append({
                'pnl': pnl,
                'reason': reason,
                'time': time.time()
            })
            self.perf.total_pnl += pnl
            
            if reason == 'win':
                self.perf.wins += 1
            elif reason == 'loss':
                self.perf.losses += 1
                self.last_trade_loss_time = time.time()
            elif reason == 'timeout':
                self.perf.timeouts += 1
            
            # Update toxicity metrics
            self.perf.toxicity_records.append(toxicity_ratio)
            if classification == 'good':
                self.perf.good_fills += 1
            else:
                self.perf.toxic_fills += 1
            
            # Update average toxicity
            if self.perf.toxicity_records:
                self.perf.avg_toxicity = sum(self.perf.toxicity_records) / len(self.perf.toxicity_records)

            equity = await self.get_balance()
            if equity > self.perf.peak_equity:
                self.perf.peak_equity = equity

            console.print(f'[cyan][{pos.symbol}] CLOSED {reason.upper()}: PnL=${pnl:.6f} ({pnl_pct:.3%}) | Toxicity: {toxicity_ratio:.2f} ({classification})')
            self.log_trade('EXIT', pos.symbol, pos.side, pos.contracts, exit_price, pnl, reason, equity)

            self.position = None

        except Exception as e:
            console.print(f'[red][{pos.symbol}] Close failed: {e}')

    def log_toxicity(self, pos: Position, exit_price: float, duration: float,
                     slippage_pct: float, realized_pnl: float, expected_pnl: float,
                     toxicity_ratio: float, classification: str, exit_reason: str) -> None:
        """Log toxicity metrics to separate file."""
        record = ToxicityRecord(
            timestamp=datetime.now(timezone.utc).isoformat(),
            epoch=time.time(),
            symbol=pos.symbol,
            side=pos.side,
            entry_price=pos.entry_price,
            entry_mid=pos.entry_mid_price,
            exit_price=exit_price,
            entry_imbalance=pos.entry_imbalance,
            entry_momentum=pos.entry_momentum,
            duration_sec=duration,
            slippage_pct=slippage_pct,
            realized_pnl=realized_pnl,
            expected_pnl=expected_pnl,
            toxicity_ratio=toxicity_ratio,
            classification=classification,
            exit_reason=exit_reason
        )
        
        try:
            DATA_DIR.mkdir(exist_ok=True)
            with open(TOXICITY_LOG, 'a') as f:
                f.write(json.dumps(asdict(record)) + '\n')
        except Exception:
            pass

    def log_trade(self, action: str, symbol: str, side: str, contracts: float,
                  price: float, pnl: float, reason: str, equity: float = 0) -> None:
        """Log trade to journal."""
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
            equity=equity
        )
        
        try:
            DATA_DIR.mkdir(exist_ok=True)
            with open(TRADE_JOURNAL, 'a') as f:
                f.write(json.dumps(asdict(record)) + '\n')
        except Exception:
            pass

    async def fetch_eligible_symbols(self) -> list:
        """Fetch eligible trading symbols."""
        try:
            markets = await self.exchange.load_markets()
            symbols = []
            for sym, mkt in markets.items():
                if mkt.get('type') == 'swap' and mkt.get('settle') == 'usdt':
                    if mkt.get('active', True) and mkt.get('contractSize', 1) > 0:
                        symbols.append(sym)
            console.print(f'[green]Found {len(symbols)} eligible symbols[/green]')
            return symbols[:20]  # Limit to top 20 for micro account
        except Exception as e:
            console.print(f'[red]Symbol fetch error: {e}')
            return []

    async def check_global_risk(self, equity: float) -> bool:
        """Check global risk limits."""
        if self.perf.start_equity > 0:
            drawdown = (self.perf.start_equity - equity) / self.perf.start_equity
            if drawdown > MAX_DRAWDOWN_GLOBAL:
                console.print(f'[red]GLOBAL DRAWDOWN: {drawdown:.1%} > {MAX_DRAWDOWN_GLOBAL:.0%} — PAUSING')
                return False
        return True

    async def run(self) -> None:
        """Main trading loop."""
        try:
            DATA_DIR.mkdir(exist_ok=True)
            
            await self.init_exchange()
            self.symbols = await self.fetch_eligible_symbols()
            
            if not self.symbols:
                console.print('[red]No eligible symbols. Exiting.')
                return

            equity = await self.get_balance()
            self.perf.start_time = time.time()
            self.perf.start_equity = equity
            self.perf.peak_equity = equity

            console.print(
                f'\n[bold cyan]CopyThatPay — $9 Survival Mode\n'
                f'  Capital: ${equity:.2f}\n'
                f'  Risk per trade: {RISK_PER_TRADE_PCT:.1%} (${equity * RISK_PER_TRADE_PCT:.2f})\n'
                f'  Target: {TAKE_PROFIT_PCT:.2%} | Stop: {STOP_LOSS_PCT:.2%} | Time: {TIME_EXIT_SEC}s\n'
                f'  Filters: Spread>={MIN_SPREAD_PCT:.2%}, Vol>=${MIN_VOLUME_USD:,.0f}\n'
                f'  Signals: Imbalance>{IMBALANCE_THRESHOLD}, Momentum>{MOMENTUM_THRESHOLD}\n'
                f'  Symbols: {len(self.symbols)}\n'
            )

            while True:
                equity = await self.get_balance()
                
                # Global risk check
                if not await self.check_global_risk(equity):
                    await asyncio.sleep(60)
                    continue

                # If no position, look for entry
                if not self.position:
                    for sym in self.symbols:
                        short_sym = sym.split('/')[0]
                        console.print(f'[dim]Checking {short_sym}...')
                        try:
                            signal = await self.should_enter(sym)
                            if signal:
                                size = await self.calculate_position_size(sym)
                                if size > 0:
                                    if await self.enter_trade(sym, signal, size):
                                        break  # Only one position at a time
                        except Exception as e:
                            console.print(f'[{sym}] Error: {e}')
                            continue
                        await asyncio.sleep(0.5)
                
                # If position exists, manage it
                else:
                    result = await self.manage_trade()
                    if result:
                        console.print(f'[cyan]Trade result: {result.upper()}')
                
                # Print status
                self.print_status(equity)
                
                await asyncio.sleep(CYCLE_INTERVAL_SEC)

        except Exception as e:
            console.print(f'[red]Fatal: {e}')
            traceback.print_exc()
        finally:
            await self.cleanup()

    def print_status(self, equity: float) -> None:
        """Print trading status with toxicity metrics."""
        try:
            table = Table(title='Survival Mode Status', show_header=True, header_style='bold magenta')
            table.add_column('Metric', style='cyan')
            table.add_column('Value', style='green')
            
            elapsed = time.time() - self.perf.start_time
            win_rate = self.perf.wins / max(self.perf.wins + self.perf.losses + self.perf.timeouts, 1)
            total_fills = self.perf.good_fills + self.perf.toxic_fills
            fill_quality = self.perf.good_fills / max(total_fills, 1)
            
            table.add_row('Equity', f'${equity:.2f}')
            table.add_row('Peak', f'${self.perf.peak_equity:.2f}')
            table.add_row('PnL', f'${self.perf.total_pnl:.6f}')
            table.add_row('Trades', f'{self.perf.wins}W / {self.perf.losses}L / {self.perf.timeouts}T')
            table.add_row('Win Rate', f'{win_rate:.1%}')
            table.add_row('Fill Quality', f'{fill_quality:.1%} ({self.perf.good_fills}g / {self.perf.toxic_fills}t)')
            table.add_row('Avg Toxicity', f'{self.perf.avg_toxicity:.2f}')
            table.add_row('Position', f'{self.position.symbol if self.position else "None"}')
            table.add_row('Uptime', f'{elapsed:.0f}s')
            
            console.print(table)
        except Exception:
            pass


# ═══════════════════════════════════════════════════════════════════════════════
# ENTRY POINT
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == '__main__':
    console.print('[bold cyan]CopyThatPay — $9 Survival Mode')
    console.print('[dim]WAIT → STRIKE → EXIT FAST → REPEAT[/dim]')
    bot = SurvivalBot()
    try:
        asyncio.run(bot.run())
    except KeyboardInterrupt:
        console.print('\n[yellow]Shutdown requested.')
    except Exception as e:
        console.print(f'[red]Fatal: {e}')
        traceback.print_exc()
