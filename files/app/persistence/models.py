"""
Persistence models for DepthOS database tables.

All records are immutable snapshots for audit trail.
"""

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Optional


@dataclass
class FillRecord:
    """Immutable record of a confirmed trade."""
    
    # Primary key
    id: int
    
    # Trade details
    contract: str
    side: str  # "buy" or "sell"
    size: int
    price: Decimal
    fee: Decimal
    
    # Timestamps
    fill_ts_ms: int
    recorded_ts: datetime
    
    # PnL impact
    realized_pnl: Optional[Decimal] = None
    
    # Exchange reference
    order_id: Optional[int] = None
    trade_id: Optional[str] = None
    
    # Metadata
    is_maker: bool = True
    dry_run: bool = False


@dataclass
class OrderRecord:
    """Immutable record of an order placement."""
    
    # Primary key
    id: int
    
    # Order details
    contract: str
    side: str  # "buy" or "sell"
    size: int
    price: Decimal
    
    # Timestamps
    placed_ts_ms: int
    recorded_ts: datetime
    filled_ts_ms: Optional[int] = None
    cancelled_ts_ms: Optional[int] = None
    
    # Exchange reference
    order_id: Optional[int] = None
    client_order_id: Optional[str] = None
    
    # Status
    status: str = "open"
    fill_size: int = 0
    remaining_size: int = 0
    
    # Metadata
    dry_run: bool = False


@dataclass
class PositionRecord:
    """Immutable snapshot of position state."""
    
    # Primary key
    id: int
    
    # Position details
    contract: str
    net_position: int
    avg_entry_price: Decimal
    
    # PnL
    realized_pnl: Decimal
    unrealized_pnl: Decimal
    total_fees: Decimal
    
    # Timestamps
    snapshot_ts: datetime
    
    # Metadata
    source: str  # "local", "exchange", "reconciliation"


@dataclass
class RiskEventRecord:
    """Immutable record of risk management events."""
    
    # Primary key
    id: int
    
    # Event details
    event_type: str  # "halt", "limit", "skew", "daily_loss", "stale_book"
    event_ts: datetime
    
    # Optional fields
    contract: Optional[str] = None
    reason: str = ""
    net_position: Optional[int] = None
    daily_pnl: Optional[Decimal] = None
    global_halt: bool = False


@dataclass
class KillSwitchRecord:
    """Immutable record of kill switch events."""
    
    # Primary key
    id: int
    
    # Event details
    triggered: bool
    reason: str
    trigger_source: str  # "api", "manual", "risk", "heartbeat"
    
    # Timestamps
    event_ts: datetime
    reset_ts: Optional[datetime] = None
    
    # Metadata
    operator: Optional[str] = None


@dataclass
class ReconciliationSnapshot:
    """Immutable snapshot of reconciliation state."""
    
    # Primary key
    id: int
    
    # Reconciliation details
    contract: str
    
    # Local state
    local_orders: int
    local_fills: int
    local_position: int
    
    # Exchange state
    exchange_orders: int
    exchange_fills: int
    exchange_position: int
    
    # Drift detection
    order_drift: int
    fill_drift: int
    position_drift: int
    
    # Timestamps
    snapshot_ts: datetime
    
    # Status
    status: str  # "matched", "drift_detected", "repaired"
    repair_action: Optional[str] = None
