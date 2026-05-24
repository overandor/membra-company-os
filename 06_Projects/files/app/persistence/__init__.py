"""
Persistence layer for DepthOS.

Provides durable storage for:
- Fills
- Orders
- Positions
- PnL
- Risk events
- Kill switch events
- Reconciliation snapshots

Uses SQLite with WAL mode for crash recovery.
"""

from .sqlite import Database, get_db
from .models import FillRecord, OrderRecord, PositionRecord, RiskEventRecord

__all__ = [
    'Database',
    'get_db',
    'FillRecord',
    'OrderRecord',
    'PositionRecord',
    'RiskEventRecord',
]
