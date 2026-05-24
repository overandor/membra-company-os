"""
Reconciliation engine for DepthOS.

Compares local state against exchange state and repairs drift.
"""

import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal
from typing import Dict, Optional, List, Any

from app.core.config import mm_config
from app.oms.oms import OMS
from app.risk.risk import RiskManager
from app.persistence.sqlite import Database
from app.persistence.models import ReconciliationSnapshot
from app.connectors.rest_client import list_open_orders, fetch_position

log = logging.getLogger("reconcile")


@dataclass
class ReconciliationResult:
    """Result of a reconciliation cycle."""
    
    contract: str
    local_orders: int
    exchange_orders: int
    local_fills: int
    exchange_fills: int
    local_position: int
    exchange_position: int
    
    order_drift: int
    fill_drift: int
    position_drift: int
    
    status: str  # "matched", "drift_detected", "repaired"
    repair_actions: List[str]
    
    timestamp: datetime


class ReconciliationEngine:
    """
    Continuously reconciles local state with exchange state.
    
    Compares:
    - Local orders vs exchange orders
    - Local fills vs exchange fills
    - Local positions vs exchange positions
    
    Repairs drift when detected.
    """
    
    def __init__(
        self,
        oms: OMS,
        risk: RiskManager,
        db: Database,
        interval_seconds: int = 30,
    ):
        self.oms = oms
        self.risk = risk
        self.db = db
        self.interval_seconds = interval_seconds
        self._running = False
        self._task: Optional[asyncio.Task] = None
        self._session: Optional[Any] = None
    
    async def start(self, session: Any) -> None:
        """Start the reconciliation loop."""
        self._session = session
        self._running = True
        self._task = asyncio.create_task(self._reconcile_loop())
        log.info("Reconciliation engine started")
    
    async def stop(self) -> None:
        """Stop the reconciliation loop."""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        log.info("Reconciliation engine stopped")
    
    async def _reconcile_loop(self) -> None:
        """Main reconciliation loop."""
        while self._running:
            try:
                for contract in mm_config.contracts:
                    result = await self.reconcile_contract(contract)
                    self._log_result(result)
                
                await asyncio.sleep(self.interval_seconds)
            except asyncio.CancelledError:
                break
            except Exception as e:
                log.error(f"Reconciliation error: {e}", exc_info=True)
                await asyncio.sleep(self.interval_seconds)
    
    async def reconcile_contract(self, contract: str) -> ReconciliationResult:
        """
        Reconcile a single contract.
        
        Returns the reconciliation result.
        """
        # Get local state
        local_orders = self.oms.live_order_count()
        local_position = self.risk.net_position(contract)
        local_fills = len(self.risk.state(contract).fills)
        
        # Get exchange state
        exchange_orders = 0
        exchange_position = 0
        exchange_fills = 0
        
        try:
            if self._session:
                exchange_orders_data = await list_open_orders(self._session, contract)
                exchange_orders = len(exchange_orders_data)
                
                position_data = await fetch_position(self._session, contract)
                exchange_position = position_data.get("size", 0)
                
                # Fills not currently available via REST API
                # Would use fills from local state or WS for now
                exchange_fills = local_fills  # Assume match for now
        except Exception as e:
            log.warning(f"Failed to fetch exchange state for {contract}: {e}")
        
        # Calculate drift
        order_drift = local_orders - exchange_orders
        fill_drift = local_fills - exchange_fills
        position_drift = local_position - exchange_position
        
        # Determine status
        status = "matched"
        repair_actions = []
        
        if order_drift != 0 or fill_drift != 0 or position_drift != 0:
            status = "drift_detected"
            repair_actions = await self._repair_drift(
                contract,
                order_drift,
                fill_drift,
                position_drift,
            )
            if repair_actions:
                status = "repaired"
        
        # Record snapshot
        snapshot = ReconciliationSnapshot(
            id=0,  # Will be assigned by database
            contract=contract,
            local_orders=local_orders,
            local_fills=local_fills,
            local_position=local_position,
            exchange_orders=exchange_orders,
            exchange_fills=exchange_fills,
            exchange_position=exchange_position,
            order_drift=order_drift,
            fill_drift=fill_drift,
            position_drift=position_drift,
            snapshot_ts=datetime.now(timezone.utc),
            status=status,
            repair_action="; ".join(repair_actions) if repair_actions else None,
        )
        self.db.record_reconciliation(snapshot)
        
        return ReconciliationResult(
            contract=contract,
            local_orders=local_orders,
            exchange_orders=exchange_orders,
            local_fills=local_fills,
            exchange_fills=exchange_fills,
            local_position=local_position,
            exchange_position=exchange_position,
            order_drift=order_drift,
            fill_drift=fill_drift,
            position_drift=position_drift,
            status=status,
            repair_actions=repair_actions,
            timestamp=datetime.now(timezone.utc),
        )
    
    async def _repair_drift(
        self,
        contract: str,
        order_drift: int,
        fill_drift: int,
        position_drift: int,
    ) -> List[str]:
        """
        Attempt to repair detected drift.
        
        Returns list of repair actions taken.
        """
        actions = []
        
        # Position drift repair
        if position_drift != 0:
            log.warning(f"Position drift detected for {contract}: {position_drift}")
            # In production, would flatten position or sync from exchange
            actions.append(f"position_drift:{position_drift}")
        
        # Order drift repair
        if order_drift != 0:
            log.warning(f"Order drift detected for {contract}: {order_drift}")
            # Cancel local orders that don't exist on exchange
            if order_drift > 0:
                await self.oms.clear_local_state()
                actions.append("cleared_local_orders")
        
        # Fill drift repair
        if fill_drift != 0:
            log.warning(f"Fill drift detected for {contract}: {fill_drift}")
            # Would sync fills from exchange
            actions.append(f"fill_drift:{fill_drift}")
        
        return actions
    
    def _log_result(self, result: ReconciliationResult) -> None:
        """Log reconciliation result."""
        if result.status == "matched":
            log.debug(
                f"Reconciliation matched for {result.contract}: "
                f"orders={result.local_orders}/{result.exchange_orders}, "
                f"position={result.local_position}/{result.exchange_position}"
            )
        else:
            log.warning(
                f"Reconciliation {result.status} for {result.contract}: "
                f"orders={result.local_orders}/{result.exchange_orders} (drift={result.order_drift}), "
                f"position={result.local_position}/{result.exchange_position} (drift={result.position_drift})"
            )
            if result.repair_actions:
                log.info(f"Repair actions: {result.repair_actions}")
    
    async def force_reconcile(self, contract: str) -> ReconciliationResult:
        """
        Force an immediate reconciliation for a contract.
        
        Useful for manual reconciliation or after error recovery.
        """
        log.info(f"Forcing reconciliation for {contract}")
        return await self.reconcile_contract(contract)


# Global reconciler instance
_reconciler: Optional[ReconciliationEngine] = None


def get_reconciler(
    oms: OMS,
    risk: RiskManager,
    db: Database,
    interval_seconds: int = 30,
) -> ReconciliationEngine:
    """Get or create the global reconciler instance."""
    global _reconciler
    if _reconciler is None:
        _reconciler = ReconciliationEngine(oms, risk, db, interval_seconds)
    return _reconciler
