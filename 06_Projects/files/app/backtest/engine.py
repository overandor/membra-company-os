"""
Backtest engine for DepthOS.

Simulates the quoting strategy on historical order book data.
"""
from decimal import Decimal
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
import logging
import random

from app.core.config import ContractSpec, mm_config
from app.risk.risk import RiskManager, Fill
from app.oms.oms import OMS
from app.market_data.order_book import BBO
from .metrics import BacktestMetrics, Trade

log = logging.getLogger("backtest")


@dataclass
class MarketSnapshot:
    """A single snapshot of market data."""
    timestamp: int
    contract: str
    bid_price: Decimal
    bid_size: int
    ask_price: Decimal
    ask_size: int
    last_price: Optional[Decimal] = None


class BacktestEngine:
    """
    Backtest engine for DepthOS quoting strategy.
    
    Simulates market making on historical order book snapshots with realistic fill simulation.
    """
    
    def __init__(
        self,
        slippage_bps: int = 5,
        latency_ms: int = 50,
        fill_probability: float = 0.3,
    ):
        self.risk = RiskManager()
        self.oms = OMS()
        self.metrics = BacktestMetrics()
        self.snapshots: List[MarketSnapshot] = []
        self.current_positions: Dict[str, int] = {}
        
        # Simulation parameters
        self.maker_fee_rate = Decimal("0.0002")  # 0.02% maker fee on Gate.io
        self.taker_fee_rate = Decimal("0.0005")   # 0.05% taker fee
        self.slippage_bps = slippage_bps          # Slippage in basis points
        self.latency_ms = latency_ms              # Order execution latency
        self.fill_probability = fill_probability  # Probability of fill when price moves through
        
    def load_snapshots_from_csv(self, filepath: str, contract: str) -> None:
        """
        Load historical market snapshots from CSV file.
        
        Expected CSV format:
        timestamp,bid_price,bid_size,ask_price,ask_size,last_price
        """
        import csv
        
        log.info(f"Loading snapshots from {filepath}")
        
        with open(filepath, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                snapshot = MarketSnapshot(
                    timestamp=int(row['timestamp']),
                    contract=contract,
                    bid_price=Decimal(row['bid_price']),
                    bid_size=int(row['bid_size']),
                    ask_price=Decimal(row['ask_price']),
                    ask_size=int(row['ask_size']),
                    last_price=Decimal(row['last_price']) if row.get('last_price') else None,
                )
                self.snapshots.append(snapshot)
        
        log.info(f"Loaded {len(self.snapshots)} snapshots")
    
    def generate_synthetic_data(
        self,
        contract: str,
        num_snapshots: int = 10000,
        start_price: Decimal = Decimal("0.00005"),
        volatility: Decimal = Decimal("0.00001"),
        spread_bps: int = 20,
    ) -> None:
        """
        Generate synthetic market data for testing.
        
        Args:
            contract: Contract name
            num_snapshots: Number of snapshots to generate
            start_price: Starting price
            volatility: Price volatility per snapshot
            spread_bps: Spread in basis points
        """
        import random
        import time
        
        log.info(f"Generating {num_snapshots} synthetic snapshots for {contract}")
        
        current_price = start_price
        spread = start_price * Decimal(spread_bps) / Decimal("10000")
        
        for i in range(num_snapshots):
            # Random walk price
            change = Decimal(str(random.uniform(-1, 1))) * volatility
            current_price = max(current_price + change, Decimal("0.000001"))
            
            snapshot = MarketSnapshot(
                timestamp=int(time.time() * 1000) + i * 1000,
                contract=contract,
                bid_price=current_price - spread / 2,
                bid_size=random.randint(100, 10000),
                ask_price=current_price + spread / 2,
                ask_size=random.randint(100, 10000),
                last_price=current_price,
            )
            self.snapshots.append(snapshot)
        
        log.info(f"Generated {len(self.snapshots)} synthetic snapshots")
    
    def run_backtest(
        self,
        contracts: List[str],
        specs: Dict[str, ContractSpec],
        duration_seconds: Optional[int] = None,
    ) -> BacktestMetrics:
        """
        Run the backtest simulation.
        
        Args:
            contracts: List of contracts to backtest
            specs: Contract specifications
            duration_seconds: Optional limit on simulation duration
            
        Returns:
            BacktestMetrics with performance results
        """
        log.info("Starting backtest simulation")
        
        # Initialize
        self.metrics = BacktestMetrics()
        self.current_positions = {c: 0 for c in contracts}
        for c in contracts:
            self.risk.state(c)  # Initialize state
        
        if not self.snapshots:
            log.warning("No snapshots loaded, generating synthetic data")
            self.generate_synthetic_data(contracts[0])
        
        # Set start time
        if self.snapshots:
            self.metrics.start_time = self.snapshots[0].timestamp
        
        # Simulate
        open_orders: Dict[str, Dict] = {c: {"bid": None, "ask": None} for c in contracts}
        
        for i, snapshot in enumerate(self.snapshots):
            # Check duration limit
            if duration_seconds and self.metrics.start_time:
                elapsed = snapshot.timestamp - self.metrics.start_time
                if elapsed > duration_seconds * 1000:
                    break
            
            # Only process snapshots for our contracts
            if snapshot.contract not in contracts:
                continue
            
            contract = snapshot.contract
            spec = specs.get(contract)
            if not spec:
                continue
            
            # Check if we can quote
            if not self.risk.can_quote(contract, spec):
                continue
            
            # Get allowed sizes
            bid_size = self.risk.allowed_buy_size(contract, mm_config.order_size)
            ask_size = self.risk.allowed_sell_size(contract, mm_config.order_size)
            
            if bid_size == 0 and ask_size == 0:
                continue
            
            # Simulate order placement (post-only at BBO)
            new_bid_order = None
            new_ask_order = None
            
            if bid_size > 0 and snapshot.bid_price > 0:
                new_bid_order = {
                    "price": snapshot.bid_price,
                    "size": bid_size,
                    "timestamp": snapshot.timestamp,
                }
            
            if ask_size > 0 and snapshot.ask_price > 0:
                new_ask_order = {
                    "price": snapshot.ask_price,
                    "size": ask_size,
                    "timestamp": snapshot.timestamp,
                }
            
            # Check for fills (simplified: assume fill if price moves through our order)
            self._check_fills(contract, open_orders[contract], snapshot, spec)
            
            # Update orders
            open_orders[contract]["bid"] = new_bid_order
            open_orders[contract]["ask"] = new_ask_order
            
            # Update equity curve
            self.metrics.equity_curve.append(self.metrics.total_pnl)
        
        # Close all positions at end
        self._close_all_positions(contracts, specs, self.snapshots[-1] if self.snapshots else None)
        
        # Set end time
        if self.snapshots:
            self.metrics.end_time = self.snapshots[-1].timestamp
        
        # Calculate metrics
        self.metrics.calculate_metrics()
        
        log.info("Backtest simulation complete")
        log.info(self.metrics.summary())
        
        return self.metrics
    
    def _check_fills(
        self,
        contract: str,
        orders: Dict,
        snapshot: MarketSnapshot,
        spec: ContractSpec,
    ) -> None:
        """Check for order fills with realistic simulation."""
        
        # Calculate slippage factor
        slippage_factor = Decimal(self.slippage_bps) / Decimal("10000")
        
        # Check bid fill (we bought, price went up)
        if orders["bid"]:
            if snapshot.last_price and snapshot.last_price >= orders["bid"]["price"]:
                # Apply fill probability
                if random.random() > self.fill_probability:
                    return  # No fill this time
                
                # Apply slippage
                fill_price = orders["bid"]["price"] * (Decimal("1") + slippage_factor)
                fill_size = orders["bid"]["size"]
                fee = fill_price * fill_size * spec.quanto_multiplier * self.maker_fee_rate
                
                # Update position
                self.current_positions[contract] += fill_size
                self.metrics.max_position_size = max(self.metrics.max_position_size, abs(self.current_positions[contract]))
                
                # Create fill
                fill = Fill(
                    contract=contract,
                    size=fill_size,
                    price=fill_price,
                    fee=fee,
                    ts_ms=snapshot.timestamp + self.latency_ms,
                )
                self.risk.on_fill(fill)
                
                # Calculate P&L (simplified: mark-to-market at last price)
                if snapshot.last_price:
                    unrealized_pnl = (snapshot.last_price - fill_price) * fill_size * spec.quanto_multiplier
                    pnl = unrealized_pnl - fee
                else:
                    pnl = -fee
                
                # Record trade
                trade = Trade(
                    timestamp=snapshot.timestamp + self.latency_ms,
                    contract=contract,
                    side="buy",
                    price=fill_price,
                    size=fill_size,
                    fee=fee,
                    pnl=pnl,
                )
                self.metrics.add_trade(trade)
        
        # Check ask fill (we sold, price went down)
        if orders["ask"]:
            if snapshot.last_price and snapshot.last_price <= orders["ask"]["price"]:
                # Apply fill probability
                if random.random() > self.fill_probability:
                    return  # No fill this time
                
                # Apply slippage (worse price for seller)
                fill_price = orders["ask"]["price"] * (Decimal("1") - slippage_factor)
                fill_size = orders["ask"]["size"]
                fee = fill_price * fill_size * spec.quanto_multiplier * self.maker_fee_rate
                
                # Update position
                self.current_positions[contract] -= fill_size
                self.metrics.max_position_size = max(self.metrics.max_position_size, abs(self.current_positions[contract]))
                
                # Create fill
                fill = Fill(
                    contract=contract,
                    size=-fill_size,
                    price=fill_price,
                    fee=fee,
                    ts_ms=snapshot.timestamp + self.latency_ms,
                )
                self.risk.on_fill(fill)
                
                # Calculate P&L
                if snapshot.last_price:
                    unrealized_pnl = (fill_price - snapshot.last_price) * fill_size * spec.quanto_multiplier
                    pnl = unrealized_pnl - fee
                else:
                    pnl = -fee
                
                # Record trade
                trade = Trade(
                    timestamp=snapshot.timestamp + self.latency_ms,
                    contract=contract,
                    side="sell",
                    price=fill_price,
                    size=fill_size,
                    fee=fee,
                    pnl=pnl,
                )
                self.metrics.add_trade(trade)
    
    def _close_all_positions(
        self,
        contracts: List[str],
        specs: Dict[str, ContractSpec],
        last_snapshot: Optional[MarketSnapshot],
    ) -> None:
        """Close all positions at the end of the backtest."""
        for contract in contracts:
            position = self.current_positions.get(contract, 0)
            if position == 0:
                continue
            
            spec = specs.get(contract)
            if not spec:
                continue
            
            # Use last price if available, otherwise assume no P&L impact
            if last_snapshot and last_snapshot.last_price:
                close_price = last_snapshot.last_price
            else:
                continue
            
            # Close position
            size = abs(position)
            side = "sell" if position > 0 else "buy"
            fee = close_price * size * spec.quanto_multiplier * self.taker_fee_rate  # Taker fee on close
            
            # Calculate closing P&L
            if position > 0:
                # Closing long
                pnl = (close_price * size * spec.quanto_multiplier) - fee
            else:
                # Closing short
                pnl = (-close_price * size * spec.quanto_multiplier) - fee
            
            # Record trade
            trade = Trade(
                timestamp=last_snapshot.timestamp if last_snapshot else 0,
                contract=contract,
                side=side,
                price=close_price,
                size=size,
                fee=fee,
                pnl=pnl,
            )
            self.metrics.add_trade(trade)
            
            # Reset position
            self.current_positions[contract] = 0
