"""
SQLite database implementation for DepthOS persistence.

Uses WAL mode for crash recovery and concurrent access.
"""

import sqlite3
import logging
from contextlib import contextmanager
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import Optional, List, Dict, Any

from .models import (
    FillRecord,
    OrderRecord,
    PositionRecord,
    RiskEventRecord,
    KillSwitchRecord,
    ReconciliationSnapshot,
)

log = logging.getLogger("persistence")


class Database:
    """SQLite database with WAL mode for DepthOS."""
    
    def __init__(self, db_path: str = "depthos.db"):
        self.db_path = Path(db_path)
        self._conn: Optional[sqlite3.Connection] = None
        self._is_in_memory = db_path == ":memory:"
        self._init_db()
    
    def _init_db(self) -> None:
        """Initialize database with WAL mode and schema."""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # For in-memory databases, keep the connection alive
        if self._is_in_memory:
            self._conn = sqlite3.connect(self.db_path)
            conn = self._conn
        else:
            conn = sqlite3.connect(self.db_path)
        
        # Enable WAL mode
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA synchronous=NORMAL;")
        conn.execute("PRAGMA foreign_keys=ON;")
        
        # Create tables
        self._create_tables(conn)
        
        conn.commit()
        
        if not self._is_in_memory:
            conn.close()
        
        log.info(f"Database initialized at {self.db_path}")
    
    def _create_tables(self, conn: sqlite3.Connection) -> None:
        """Create all database tables."""
        
        # Fills table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS fills (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                contract TEXT NOT NULL,
                side TEXT NOT NULL,
                size INTEGER NOT NULL,
                price TEXT NOT NULL,
                fee TEXT NOT NULL,
                fill_ts_ms INTEGER NOT NULL,
                recorded_ts TEXT NOT NULL,
                realized_pnl TEXT,
                order_id INTEGER,
                trade_id TEXT,
                is_maker BOOLEAN DEFAULT 1,
                dry_run BOOLEAN DEFAULT 0
            );
        """)
        
        # Orders table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                contract TEXT NOT NULL,
                side TEXT NOT NULL,
                size INTEGER NOT NULL,
                price TEXT NOT NULL,
                order_id INTEGER,
                client_order_id TEXT,
                placed_ts_ms INTEGER NOT NULL,
                recorded_ts TEXT NOT NULL,
                filled_ts_ms INTEGER,
                cancelled_ts_ms INTEGER,
                status TEXT NOT NULL,
                fill_size INTEGER DEFAULT 0,
                remaining_size INTEGER DEFAULT 0,
                dry_run BOOLEAN DEFAULT 0
            );
        """)
        
        # Positions table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS positions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                contract TEXT NOT NULL,
                net_position INTEGER NOT NULL,
                avg_entry_price TEXT NOT NULL,
                realized_pnl TEXT NOT NULL,
                unrealized_pnl TEXT NOT NULL,
                total_fees TEXT NOT NULL,
                snapshot_ts TEXT NOT NULL,
                source TEXT NOT NULL
            );
        """)
        
        # Risk events table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS risk_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_type TEXT NOT NULL,
                contract TEXT,
                reason TEXT,
                net_position INTEGER,
                daily_pnl TEXT,
                event_ts TEXT NOT NULL,
                global_halt BOOLEAN DEFAULT 0
            );
        """)
        
        # Kill switch events table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS kill_switch_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                triggered BOOLEAN NOT NULL,
                reason TEXT NOT NULL,
                trigger_source TEXT NOT NULL,
                event_ts TEXT NOT NULL,
                reset_ts TEXT,
                operator TEXT
            );
        """)
        
        # Reconciliation snapshots table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS reconciliation_snapshots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                contract TEXT NOT NULL,
                local_orders INTEGER NOT NULL,
                local_fills INTEGER NOT NULL,
                local_position INTEGER NOT NULL,
                exchange_orders INTEGER NOT NULL,
                exchange_fills INTEGER NOT NULL,
                exchange_position INTEGER NOT NULL,
                order_drift INTEGER NOT NULL,
                fill_drift INTEGER NOT NULL,
                position_drift INTEGER NOT NULL,
                snapshot_ts TEXT NOT NULL,
                status TEXT NOT NULL,
                repair_action TEXT
            );
        """)
        
        # Indexes for common queries
        conn.execute("CREATE INDEX IF NOT EXISTS idx_fills_contract ON fills(contract);")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_fills_ts ON fills(fill_ts_ms);")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_orders_contract ON orders(contract);")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(status);")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_positions_contract ON positions(contract);")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_risk_events_ts ON risk_events(event_ts);")
        
        log.info("Database tables created")
    
    @contextmanager
    def get_connection(self):
        """Context manager for database connections."""
        if self._is_in_memory and self._conn:
            conn = self._conn
            conn.row_factory = sqlite3.Row
            try:
                yield conn
            except Exception:
                # Don't rollback for in-memory test DB
                raise
        else:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            try:
                yield conn
                conn.commit()
            except Exception:
                conn.rollback()
                raise
            finally:
                conn.close()
    
    # ─── Fill operations ─────────────────────────────────────────────────────
    
    def record_fill(self, fill: FillRecord) -> int:
        """Record a fill and return the record ID."""
        with self.get_connection() as conn:
            cursor = conn.execute(
                """
                INSERT INTO fills (
                    contract, side, size, price, fee, fill_ts_ms, recorded_ts,
                    realized_pnl, order_id, trade_id, is_maker, dry_run
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    fill.contract,
                    fill.side,
                    fill.size,
                    str(fill.price),
                    str(fill.fee),
                    fill.fill_ts_ms,
                    fill.recorded_ts.isoformat(),
                    str(fill.realized_pnl) if fill.realized_pnl else None,
                    fill.order_id,
                    fill.trade_id,
                    fill.is_maker,
                    fill.dry_run,
                ),
            )
            return cursor.lastrowid
    
    def get_fills_by_contract(self, contract: str, limit: int = 100) -> List[FillRecord]:
        """Get fills for a contract, most recent first."""
        with self.get_connection() as conn:
            cursor = conn.execute(
                """
                SELECT * FROM fills
                WHERE contract = ?
                ORDER BY fill_ts_ms DESC
                LIMIT ?
                """,
                (contract, limit),
            )
            return [self._row_to_fill(row) for row in cursor.fetchall()]
    
    def _row_to_fill(self, row: sqlite3.Row) -> FillRecord:
        """Convert database row to FillRecord."""
        return FillRecord(
            id=row["id"],
            contract=row["contract"],
            side=row["side"],
            size=row["size"],
            price=Decimal(row["price"]),
            fee=Decimal(row["fee"]),
            fill_ts_ms=row["fill_ts_ms"],
            recorded_ts=datetime.fromisoformat(row["recorded_ts"]),
            realized_pnl=Decimal(row["realized_pnl"]) if row["realized_pnl"] else None,
            order_id=row["order_id"],
            trade_id=row["trade_id"],
            is_maker=bool(row["is_maker"]),
            dry_run=bool(row["dry_run"]),
        )
    
    # ─── Order operations ────────────────────────────────────────────────────
    
    def record_order(self, order: OrderRecord) -> int:
        """Record an order and return the record ID."""
        with self.get_connection() as conn:
            cursor = conn.execute(
                """
                INSERT INTO orders (
                    contract, side, size, price, order_id, client_order_id,
                    placed_ts_ms, recorded_ts, filled_ts_ms, cancelled_ts_ms,
                    status, fill_size, remaining_size, dry_run
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    order.contract,
                    order.side,
                    order.size,
                    str(order.price),
                    order.order_id,
                    order.client_order_id,
                    order.placed_ts_ms,
                    order.recorded_ts.isoformat(),
                    order.filled_ts_ms,
                    order.cancelled_ts_ms,
                    order.status,
                    order.fill_size,
                    order.remaining_size,
                    order.dry_run,
                ),
            )
            return cursor.lastrowid
    
    def update_order_status(
        self,
        order_id: int,
        status: str,
        fill_size: Optional[int] = None,
        filled_ts_ms: Optional[int] = None,
        cancelled_ts_ms: Optional[int] = None,
    ) -> None:
        """Update order status."""
        with self.get_connection() as conn:
            updates = ["status = ?"]
            params = [status]
            
            if fill_size is not None:
                updates.append("fill_size = ?")
                params.append(fill_size)
            
            if filled_ts_ms is not None:
                updates.append("filled_ts_ms = ?")
                params.append(filled_ts_ms)
            
            if cancelled_ts_ms is not None:
                updates.append("cancelled_ts_ms = ?")
                params.append(cancelled_ts_ms)
            
            params.append(order_id)
            
            conn.execute(
                f"UPDATE orders SET {', '.join(updates)} WHERE order_id = ?",
                params,
            )
    
    def get_open_orders(self, contract: Optional[str] = None) -> List[OrderRecord]:
        """Get all open orders, optionally filtered by contract."""
        with self.get_connection() as conn:
            if contract:
                cursor = conn.execute(
                    "SELECT * FROM orders WHERE contract = ? AND status = 'open'",
                    (contract,),
                )
            else:
                cursor = conn.execute(
                    "SELECT * FROM orders WHERE status = 'open'",
                )
            return [self._row_to_order(row) for row in cursor.fetchall()]
    
    def _row_to_order(self, row: sqlite3.Row) -> OrderRecord:
        """Convert database row to OrderRecord."""
        return OrderRecord(
            id=row["id"],
            contract=row["contract"],
            side=row["side"],
            size=row["size"],
            price=Decimal(row["price"]),
            order_id=row["order_id"],
            client_order_id=row["client_order_id"],
            placed_ts_ms=row["placed_ts_ms"],
            recorded_ts=datetime.fromisoformat(row["recorded_ts"]),
            filled_ts_ms=row["filled_ts_ms"],
            cancelled_ts_ms=row["cancelled_ts_ms"],
            status=row["status"],
            fill_size=row["fill_size"],
            remaining_size=row["remaining_size"],
            dry_run=bool(row["dry_run"]),
        )
    
    # ─── Position operations ─────────────────────────────────────────────────
    
    def record_position(self, position: PositionRecord) -> int:
        """Record a position snapshot and return the record ID."""
        with self.get_connection() as conn:
            cursor = conn.execute(
                """
                INSERT INTO positions (
                    contract, net_position, avg_entry_price,
                    realized_pnl, unrealized_pnl, total_fees,
                    snapshot_ts, source
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    position.contract,
                    position.net_position,
                    str(position.avg_entry_price),
                    str(position.realized_pnl),
                    str(position.unrealized_pnl),
                    str(position.total_fees),
                    position.snapshot_ts.isoformat(),
                    position.source,
                ),
            )
            return cursor.lastrowid
    
    def get_latest_position(self, contract: str) -> Optional[PositionRecord]:
        """Get the latest position snapshot for a contract."""
        with self.get_connection() as conn:
            cursor = conn.execute(
                """
                SELECT * FROM positions
                WHERE contract = ?
                ORDER BY snapshot_ts DESC
                LIMIT 1
                """,
                (contract,),
            )
            row = cursor.fetchone()
            if row:
                return self._row_to_position(row)
            return None
    
    def _row_to_position(self, row: sqlite3.Row) -> PositionRecord:
        """Convert database row to PositionRecord."""
        return PositionRecord(
            id=row["id"],
            contract=row["contract"],
            net_position=row["net_position"],
            avg_entry_price=Decimal(row["avg_entry_price"]),
            realized_pnl=Decimal(row["realized_pnl"]),
            unrealized_pnl=Decimal(row["unrealized_pnl"]),
            total_fees=Decimal(row["total_fees"]),
            snapshot_ts=datetime.fromisoformat(row["snapshot_ts"]),
            source=row["source"],
        )
    
    # ─── Risk event operations ───────────────────────────────────────────────
    
    def record_risk_event(self, event: RiskEventRecord) -> int:
        """Record a risk event and return the record ID."""
        with self.get_connection() as conn:
            cursor = conn.execute(
                """
                INSERT INTO risk_events (
                    event_type, contract, reason, net_position,
                    daily_pnl, event_ts, global_halt
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    event.event_type,
                    event.contract,
                    event.reason,
                    event.net_position,
                    str(event.daily_pnl) if event.daily_pnl else None,
                    event.event_ts.isoformat(),
                    event.global_halt,
                ),
            )
            return cursor.lastrowid
    
    def get_recent_risk_events(self, limit: int = 50) -> List[RiskEventRecord]:
        """Get recent risk events."""
        with self.get_connection() as conn:
            cursor = conn.execute(
                """
                SELECT * FROM risk_events
                ORDER BY event_ts DESC
                LIMIT ?
                """,
                (limit,),
            )
            return [self._row_to_risk_event(row) for row in cursor.fetchall()]
    
    def _row_to_risk_event(self, row: sqlite3.Row) -> RiskEventRecord:
        """Convert database row to RiskEventRecord."""
        return RiskEventRecord(
            id=row["id"],
            event_type=row["event_type"],
            contract=row["contract"],
            reason=row["reason"],
            net_position=row["net_position"],
            daily_pnl=Decimal(row["daily_pnl"]) if row["daily_pnl"] else None,
            event_ts=datetime.fromisoformat(row["event_ts"]),
            global_halt=bool(row["global_halt"]),
        )
    
    # ─── Kill switch operations ──────────────────────────────────────────────
    
    def record_kill_switch(self, event: KillSwitchRecord) -> int:
        """Record a kill switch event and return the record ID."""
        with self.get_connection() as conn:
            cursor = conn.execute(
                """
                INSERT INTO kill_switch_events (
                    triggered, reason, trigger_source, event_ts, reset_ts, operator
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    event.triggered,
                    event.reason,
                    event.trigger_source,
                    event.event_ts.isoformat(),
                    event.reset_ts.isoformat() if event.reset_ts else None,
                    event.operator,
                ),
            )
            return cursor.lastrowid
    
    def get_latest_kill_switch(self) -> Optional[KillSwitchRecord]:
        """Get the latest kill switch event."""
        with self.get_connection() as conn:
            cursor = conn.execute(
                """
                SELECT * FROM kill_switch_events
                ORDER BY event_ts DESC
                LIMIT 1
                """,
            )
            row = cursor.fetchone()
            if row:
                return self._row_to_kill_switch(row)
            return None
    
    def _row_to_kill_switch(self, row: sqlite3.Row) -> KillSwitchRecord:
        """Convert database row to KillSwitchRecord."""
        return KillSwitchRecord(
            id=row["id"],
            triggered=bool(row["triggered"]),
            reason=row["reason"],
            trigger_source=row["trigger_source"],
            event_ts=datetime.fromisoformat(row["event_ts"]),
            reset_ts=datetime.fromisoformat(row["reset_ts"]) if row["reset_ts"] else None,
            operator=row["operator"],
        )
    
    # ─── Reconciliation operations ────────────────────────────────────────────
    
    def record_reconciliation(self, snapshot: ReconciliationSnapshot) -> int:
        """Record a reconciliation snapshot and return the record ID."""
        with self.get_connection() as conn:
            cursor = conn.execute(
                """
                INSERT INTO reconciliation_snapshots (
                    contract, local_orders, local_fills, local_position,
                    exchange_orders, exchange_fills, exchange_position,
                    order_drift, fill_drift, position_drift,
                    snapshot_ts, status, repair_action
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    snapshot.contract,
                    snapshot.local_orders,
                    snapshot.local_fills,
                    snapshot.local_position,
                    snapshot.exchange_orders,
                    snapshot.exchange_fills,
                    snapshot.exchange_position,
                    snapshot.order_drift,
                    snapshot.fill_drift,
                    snapshot.position_drift,
                    snapshot.snapshot_ts.isoformat(),
                    snapshot.status,
                    snapshot.repair_action,
                ),
            )
            return cursor.lastrowid
    
    def get_reconciliation_history(
        self, contract: str, limit: int = 100
    ) -> List[ReconciliationSnapshot]:
        """Get reconciliation history for a contract."""
        with self.get_connection() as conn:
            cursor = conn.execute(
                """
                SELECT * FROM reconciliation_snapshots
                WHERE contract = ?
                ORDER BY snapshot_ts DESC
                LIMIT ?
                """,
                (contract, limit),
            )
            return [self._row_to_reconciliation(row) for row in cursor.fetchall()]
    
    def _row_to_reconciliation(self, row: sqlite3.Row) -> ReconciliationSnapshot:
        """Convert database row to ReconciliationSnapshot."""
        return ReconciliationSnapshot(
            id=row["id"],
            contract=row["contract"],
            local_orders=row["local_orders"],
            local_fills=row["local_fills"],
            local_position=row["local_position"],
            exchange_orders=row["exchange_orders"],
            exchange_fills=row["exchange_fills"],
            exchange_position=row["exchange_position"],
            order_drift=row["order_drift"],
            fill_drift=row["fill_drift"],
            position_drift=row["position_drift"],
            snapshot_ts=datetime.fromisoformat(row["snapshot_ts"]),
            status=row["status"],
            repair_action=row["repair_action"],
        )


# Global database instance
_db: Optional[Database] = None


def get_db(db_path: str = "depthos.db") -> Database:
    """Get or create the global database instance."""
    global _db
    if _db is None:
        _db = Database(db_path)
    return _db
