"""
Backtest metrics and performance tracking.
"""
from dataclasses import dataclass, field
from decimal import Decimal
from typing import List, Dict, Optional
from datetime import datetime


@dataclass
class Trade:
    """A single trade in the backtest."""
    timestamp: int
    contract: str
    side: str  # 'buy' or 'sell'
    price: Decimal
    size: int
    fee: Decimal
    pnl: Decimal


@dataclass
class BacktestMetrics:
    """Performance metrics for a backtest."""
    
    # Basic stats
    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    
    # P&L
    total_pnl: Decimal = Decimal("0")
    gross_pnl: Decimal = Decimal("0")
    total_fees: Decimal = Decimal("0")
    max_drawdown: Decimal = Decimal("0")
    max_drawdown_pct: Decimal = Decimal("0")
    
    # Risk metrics
    sharpe_ratio: Optional[Decimal] = None
    sortino_ratio: Optional[Decimal] = None
    max_position_size: int = 0
    avg_position_size: Decimal = Decimal("0")
    
    # Time-based metrics
    cent_per_second: Decimal = Decimal("0")  # P&L per second in cents
    cent_per_hour: Decimal = Decimal("0")    # P&L per hour in cents
    
    # Time-based
    start_time: Optional[int] = None
    end_time: Optional[int] = None
    duration_seconds: Optional[int] = None
    
    # Per-contract breakdown
    contract_metrics: Dict[str, Dict] = field(default_factory=dict)
    
    # Trade history
    trades: List[Trade] = field(default_factory=list)
    
    # Equity curve
    equity_curve: List[Decimal] = field(default_factory=list)
    
    def add_trade(self, trade: Trade) -> None:
        """Add a trade to the metrics."""
        self.trades.append(trade)
        self.total_trades += 1
        
        if trade.pnl > 0:
            self.winning_trades += 1
        elif trade.pnl < 0:
            self.losing_trades += 1
        
        self.total_pnl += trade.pnl
        self.gross_pnl += trade.pnl + trade.fee
        self.total_fees += trade.fee
        
        # Track per-contract metrics
        if trade.contract not in self.contract_metrics:
            self.contract_metrics[trade.contract] = {
                "trades": 0,
                "pnl": Decimal("0"),
                "fees": Decimal("0"),
                "max_position": 0,
            }
        
        self.contract_metrics[trade.contract]["trades"] += 1
        self.contract_metrics[trade.contract]["pnl"] += trade.pnl
        self.contract_metrics[trade.contract]["fees"] += trade.fee
    
    def calculate_metrics(self) -> None:
        """Calculate derived metrics including Sharpe ratio and cent per second."""
        if not self.trades:
            return
        
        # Win rate
        if self.total_trades > 0:
            self.win_rate = Decimal(self.winning_trades) / Decimal(self.total_trades)
        
        # Average trade
        if self.total_trades > 0:
            self.avg_trade_pnl = self.total_pnl / Decimal(self.total_trades)
        
        # Max drawdown from equity curve
        if len(self.equity_curve) > 1:
            peak = self.equity_curve[0]
            for equity in self.equity_curve:
                if equity > peak:
                    peak = equity
                drawdown = peak - equity
                if drawdown > self.max_drawdown:
                    self.max_drawdown = drawdown
            
            if peak > 0:
                self.max_drawdown_pct = (self.max_drawdown / peak) * Decimal("100")
        
        # Duration
        if self.start_time and self.end_time:
            self.duration_seconds = self.end_time - self.start_time
        
        # Cent per second and cent per hour
        if self.duration_seconds and self.duration_seconds > 0:
            # Convert P&L to cents (1 USDT = 100 cents)
            pnl_cents = self.total_pnl * Decimal("100")
            self.cent_per_second = pnl_cents / Decimal(self.duration_seconds)
            self.cent_per_hour = self.cent_per_second * Decimal("3600")
        
        # Sharpe ratio calculation (simplified)
        if len(self.equity_curve) > 2 and self.duration_seconds:
            # Calculate returns
            returns = []
            for i in range(1, len(self.equity_curve)):
                if self.equity_curve[i-1] != 0:
                    ret = (self.equity_curve[i] - self.equity_curve[i-1]) / self.equity_curve[i-1]
                    returns.append(ret)
            
            if returns:
                import math
                avg_return = sum(returns) / len(returns)
                variance = sum((r - avg_return) ** 2 for r in returns) / len(returns)
                std_dev = Decimal(str(math.sqrt(float(variance)))) if variance > 0 else Decimal("0.000001")
                
                # Annualized Sharpe (assuming 252 trading days)
                if std_dev > 0:
                    periods_per_year = Decimal("252") * Decimal("24") * Decimal("3600") / Decimal(self.duration_seconds)
                    self.sharpe_ratio = (avg_return * periods_per_year) / (std_dev * Decimal(str(math.sqrt(float(periods_per_year)))))
        
        # Sortino ratio (downside deviation)
        if len(self.equity_curve) > 2:
            negative_returns = [r for r in returns if r < 0]
            if negative_returns:
                avg_negative = sum(negative_returns) / len(negative_returns)
                downside_variance = sum((r - avg_negative) ** 2 for r in negative_returns) / len(negative_returns)
                downside_deviation = Decimal(str(math.sqrt(float(downside_variance)))) if downside_variance > 0 else Decimal("0.000001")
                
                if downside_deviation > 0:
                    self.sortino_ratio = (avg_return * periods_per_year) / (downside_deviation * Decimal(str(math.sqrt(float(periods_per_year)))))
    
    def summary(self) -> str:
        """Generate a summary string."""
        lines = [
            "=" * 60,
            "BACKTEST METRICS SUMMARY",
            "=" * 60,
            f"Total Trades: {self.total_trades}",
            f"Winning Trades: {self.winning_trades}",
            f"Losing Trades: {self.losing_trades}",
            f"Win Rate: {getattr(self, 'win_rate', Decimal('0')):.2%}",
            "",
            f"Total P&L: {self.total_pnl:+.4f} USDT",
            f"Gross P&L: {self.gross_pnl:+.4f} USDT",
            f"Total Fees: {self.total_fees:.4f} USDT",
            f"Average Trade: {getattr(self, 'avg_trade_pnl', Decimal('0')):+.4f} USDT",
            "",
            f"Max Drawdown: {self.max_drawdown:.4f} USDT ({self.max_drawdown_pct:.2f}%)",
            f"Max Position: {self.max_position_size} contracts",
            "",
        ]
        
        # Risk metrics
        if self.sharpe_ratio is not None:
            lines.append(f"Sharpe Ratio: {self.sharpe_ratio:.2f}")
        if self.sortino_ratio is not None:
            lines.append(f"Sortino Ratio: {self.sortino_ratio:.2f}")
        
        # Time-based metrics
        lines.append("")
        lines.append(f"Cent per Second: {self.cent_per_second:.4f}")
        lines.append(f"Cent per Hour: {self.cent_per_hour:.4f}")
        
        if self.duration_seconds:
            hours = self.duration_seconds / 3600
            lines.append(f"Duration: {hours:.2f} hours")
            lines.append("")
        
        if self.contract_metrics:
            lines.append("Per-Contract Breakdown:")
            lines.append("-" * 60)
            for contract, metrics in self.contract_metrics.items():
                lines.append(
                    f"  {contract}: {metrics['trades']} trades, "
                    f"P&L: {metrics['pnl']:+.4f}, "
                    f"Fees: {metrics['fees']:.4f}"
                )
        
        lines.append("=" * 60)
        return "\n".join(lines)
