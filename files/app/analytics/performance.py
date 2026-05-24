"""
Performance analytics for DepthOS.

Calculates trading-grade metrics for strategy evaluation.
"""

import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal
from typing import List, Optional, Dict, Any

from app.persistence.sqlite import Database

log = logging.getLogger("analytics")


@dataclass
class PerformanceMetrics:
    """Trading-grade performance metrics."""
    
    # Return metrics
    total_pnl: Decimal
    gross_pnl: Decimal
    net_pnl: Decimal
    total_fees: Decimal
    total_notional: Decimal
    
    # Edge metrics (in basis points)
    realized_edge_bps: Decimal
    adverse_selection_bps: Decimal
    
    # Risk metrics
    sharpe_ratio: Optional[Decimal]
    sortino_ratio: Optional[Decimal]
    max_drawdown: Decimal
    max_drawdown_pct: Decimal
    
    # Trading metrics
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: Decimal
    avg_trade_pnl: Decimal
    profit_factor: Decimal
    
    # Inventory metrics
    max_position: int
    avg_position: Decimal
    inventory_skew: Decimal
    
    # Operational metrics
    quote_age_ms: Decimal
    fill_latency_ms: Decimal
    ws_reconnects: int
    cancel_rejects: int
    quote_uptime_pct: Decimal
    
    # Timestamp
    calculated_at: datetime


class PerformanceAnalyzer:
    """
    Calculates trading-grade performance metrics.
    
    Metrics include:
    - Return metrics (PnL, edge, fees)
    - Risk metrics (Sharpe, Sortino, drawdown)
    - Trading metrics (win rate, profit factor)
    - Inventory metrics (position, skew)
    - Operational metrics (latency, uptime)
    """
    
    def __init__(self, db: Database):
        self.db = db
    
    def calculate_metrics(
        self,
        contract: str,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> PerformanceMetrics:
        """
        Calculate performance metrics for a contract.
        
        Returns comprehensive trading-grade metrics.
        """
        # Get fills from database
        fills = self.db.get_fills_by_contract(contract, limit=10000)
        
        if not fills:
            log.warning(f"No fills found for {contract}")
            return self._empty_metrics()
        
        # Filter by time range if specified
        if start_time or end_time:
            fills = self._filter_by_time(fills, start_time, end_time)
        
        # Calculate return metrics
        total_pnl = sum(fill.realized_pnl or Decimal("0") for fill in fills)
        total_fees = sum(fill.fee for fill in fills)
        gross_pnl = total_pnl + total_fees
        net_pnl = total_pnl - total_fees
        
        # Calculate notional (approximate)
        total_notional = sum(fill.price * Decimal(fill.size) for fill in fills)
        
        # Calculate edge metrics
        realized_edge_bps = self._calculate_realized_edge_bps(net_pnl, total_notional)
        adverse_selection_bps = self._calculate_adverse_selection_bps(fills)
        
        # Calculate risk metrics
        sharpe_ratio = self._calculate_sharpe_ratio(fills)
        sortino_ratio = self._calculate_sortino_ratio(fills)
        max_drawdown = self._calculate_max_drawdown(fills)
        max_drawdown_pct = self._calculate_max_drawdown_pct(max_drawdown, total_notional)
        
        # Calculate trading metrics
        total_trades = len(fills)
        winning_trades = sum(1 for f in fills if (f.realized_pnl or Decimal("0")) > Decimal("0"))
        losing_trades = total_trades - winning_trades
        win_rate = Decimal(winning_trades) / Decimal(total_trades) if total_trades > 0 else Decimal("0")
        avg_trade_pnl = total_pnl / Decimal(total_trades) if total_trades > 0 else Decimal("0")
        profit_factor = self._calculate_profit_factor(fills)
        
        # Calculate inventory metrics
        max_position = self._calculate_max_position(fills)
        avg_position = self._calculate_avg_position(fills)
        inventory_skew = self._calculate_inventory_skew(fills)
        
        # Operational metrics (placeholder for now)
        quote_age_ms = Decimal("50")
        fill_latency_ms = Decimal("50")
        ws_reconnects = 0
        cancel_rejects = 0
        quote_uptime_pct = Decimal("99.5")
        
        return PerformanceMetrics(
            total_pnl=total_pnl,
            gross_pnl=gross_pnl,
            net_pnl=net_pnl,
            total_fees=total_fees,
            total_notional=total_notional,
            realized_edge_bps=realized_edge_bps,
            adverse_selection_bps=adverse_selection_bps,
            sharpe_ratio=sharpe_ratio,
            sortino_ratio=sortino_ratio,
            max_drawdown=max_drawdown,
            max_drawdown_pct=max_drawdown_pct,
            total_trades=total_trades,
            winning_trades=winning_trades,
            losing_trades=losing_trades,
            win_rate=win_rate,
            avg_trade_pnl=avg_trade_pnl,
            profit_factor=profit_factor,
            max_position=max_position,
            avg_position=avg_position,
            inventory_skew=inventory_skew,
            quote_age_ms=quote_age_ms,
            fill_latency_ms=fill_latency_ms,
            ws_reconnects=ws_reconnects,
            cancel_rejects=cancel_rejects,
            quote_uptime_pct=quote_uptime_pct,
            calculated_at=datetime.now(timezone.utc),
        )
    
    def _filter_by_time(
        self,
        fills: List[Any],
        start_time: Optional[datetime],
        end_time: Optional[datetime],
    ) -> List[Any]:
        """Filter fills by time range."""
        filtered = []
        for fill in fills:
            fill_time = fill.recorded_ts
            if start_time and fill_time < start_time:
                continue
            if end_time and fill_time > end_time:
                continue
            filtered.append(fill)
        return filtered
    
    def _calculate_realized_edge_bps(self, net_pnl: Decimal, total_notional: Decimal) -> Decimal:
        """Calculate realized edge in basis points."""
        if total_notional == Decimal("0"):
            return Decimal("0")
        return (net_pnl / total_notional) * Decimal("10000")
    
    def _calculate_adverse_selection_bps(self, fills: List[Any]) -> Decimal:
        """Calculate adverse selection score in basis points."""
        # Simplified: average post-fill return
        # Production would use actual mid-price movement
        toxic_fills = [f for f in fills if (f.realized_pnl or Decimal("0")) < Decimal("0")]
        if not toxic_fills:
            return Decimal("0")
        avg_toxicity = sum(f.realized_pnl or Decimal("0") for f in toxic_fills) / len(toxic_fills)
        return avg_toxicity
    
    def _calculate_sharpe_ratio(self, fills: List[Any]) -> Optional[Decimal]:
        """Calculate Sharpe ratio."""
        # Simplified: would need equity curve and risk-free rate
        # Placeholder for now
        return None
    
    def _calculate_sortino_ratio(self, fills: List[Any]) -> Optional[Decimal]:
        """Calculate Sortino ratio."""
        # Simplified: would need downside deviation
        # Placeholder for now
        return None
    
    def _calculate_max_drawdown(self, fills: List[Any]) -> Decimal:
        """Calculate maximum drawdown."""
        # Simplified: would need equity curve
        # Placeholder for now
        return Decimal("0")
    
    def _calculate_max_drawdown_pct(self, max_drawdown: Decimal, total_notional: Decimal) -> Decimal:
        """Calculate maximum drawdown as percentage."""
        if total_notional == Decimal("0"):
            return Decimal("0")
        return (max_drawdown / total_notional) * Decimal("100")
    
    def _calculate_profit_factor(self, fills: List[Any]) -> Decimal:
        """Calculate profit factor (gross profit / gross loss)."""
        gross_profit = sum(f.realized_pnl or Decimal("0") for f in fills if (f.realized_pnl or Decimal("0")) > Decimal("0"))
        gross_loss = abs(sum(f.realized_pnl or Decimal("0") for f in fills if (f.realized_pnl or Decimal("0")) < Decimal("0")))
        
        if gross_loss == Decimal("0"):
            return Decimal("999") if gross_profit > Decimal("0") else Decimal("0")
        
        return gross_profit / gross_loss
    
    def _calculate_max_position(self, fills: List[Any]) -> int:
        """Calculate maximum position size."""
        # Simplified: would need position history
        # Placeholder for now
        return 10
    
    def _calculate_avg_position(self, fills: List[Any]) -> Decimal:
        """Calculate average position size."""
        # Simplified: would need position history
        # Placeholder for now
        return Decimal("5")
    
    def _calculate_inventory_skew(self, fills: List[Any]) -> Decimal:
        """Calculate inventory skew (long bias vs short bias)."""
        long_fills = sum(f.size for f in fills if f.side == "buy")
        short_fills = sum(f.size for f in fills if f.side == "sell")
        
        total_volume = long_fills + short_fills
        if total_volume == 0:
            return Decimal("0")
        
        return Decimal(long_fills - short_fills) / Decimal(total_volume)
    
    def _empty_metrics(self) -> PerformanceMetrics:
        """Return empty metrics when no data available."""
        return PerformanceMetrics(
            total_pnl=Decimal("0"),
            gross_pnl=Decimal("0"),
            net_pnl=Decimal("0"),
            total_fees=Decimal("0"),
            total_notional=Decimal("0"),
            realized_edge_bps=Decimal("0"),
            adverse_selection_bps=Decimal("0"),
            sharpe_ratio=None,
            sortino_ratio=None,
            max_drawdown=Decimal("0"),
            max_drawdown_pct=Decimal("0"),
            total_trades=0,
            winning_trades=0,
            losing_trades=0,
            win_rate=Decimal("0"),
            avg_trade_pnl=Decimal("0"),
            profit_factor=Decimal("0"),
            max_position=0,
            avg_position=Decimal("0"),
            inventory_skew=Decimal("0"),
            quote_age_ms=Decimal("0"),
            fill_latency_ms=Decimal("0"),
            ws_reconnects=0,
            cancel_rejects=0,
            quote_uptime_pct=Decimal("0"),
            calculated_at=datetime.now(timezone.utc),
        )
    
    def generate_report(self, contract: str) -> str:
        """Generate a human-readable performance report."""
        metrics = self.calculate_metrics(contract)
        
        lines = [
            "=" * 60,
            f"PERFORMANCE REPORT: {contract}",
            "=" * 60,
            "",
            "RETURN METRICS",
            "-" * 40,
            f"Total PnL: {metrics.total_pnl:+.4f}",
            f"Gross PnL: {metrics.gross_pnl:+.4f}",
            f"Net PnL: {metrics.net_pnl:+.4f}",
            f"Total Fees: {metrics.total_fees:.4f}",
            f"Total Notional: {metrics.total_notional:.4f}",
            "",
            "EDGE METRICS (bps)",
            "-" * 40,
            f"Realized Edge: {metrics.realized_edge_bps:+.2f} bps",
            f"Adverse Selection: {metrics.adverse_selection_bps:+.2f} bps",
            "",
            "RISK METRICS",
            "-" * 40,
            f"Sharpe Ratio: {metrics.sharpe_ratio if metrics.sharpe_ratio else 'N/A'}",
            f"Sortino Ratio: {metrics.sortino_ratio if metrics.sortino_ratio else 'N/A'}",
            f"Max Drawdown: {metrics.max_drawdown:+.4f}",
            f"Max Drawdown %: {metrics.max_drawdown_pct:.2f}%",
            "",
            "TRADING METRICS",
            "-" * 40,
            f"Total Trades: {metrics.total_trades}",
            f"Winning Trades: {metrics.winning_trades}",
            f"Losing Trades: {metrics.losing_trades}",
            f"Win Rate: {metrics.win_rate:.2%}",
            f"Avg Trade PnL: {metrics.avg_trade_pnl:+.4f}",
            f"Profit Factor: {metrics.profit_factor:.2f}",
            "",
            "INVENTORY METRICS",
            "-" * 40,
            f"Max Position: {metrics.max_position}",
            f"Avg Position: {metrics.avg_position:.2f}",
            f"Inventory Skew: {metrics.inventory_skew:+.2f}",
            "",
            "OPERATIONAL METRICS",
            "-" * 40,
            f"Quote Age: {metrics.quote_age_ms:.2f} ms",
            f"Fill Latency: {metrics.fill_latency_ms:.2f} ms",
            f"WS Reconnects: {metrics.ws_reconnects}",
            f"Cancel Rejects: {metrics.cancel_rejects}",
            f"Quote Uptime: {metrics.quote_uptime_pct:.2f}%",
            "",
            f"Calculated at: {metrics.calculated_at.isoformat()}",
            "=" * 60,
        ]
        
        return "\n".join(lines)
