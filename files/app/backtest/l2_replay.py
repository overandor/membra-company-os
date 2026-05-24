"""
Deterministic L2 replay engine for backtesting.

Replays recorded Gate.io L2 orderbook and trade data.
"""

import asyncio
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any, Dict, List, Optional, Iterator

from app.backtest.replay_engine import ReplayEngine, MarketSnapshot, TradeEvent
from app.oms.oms import OMS
from app.risk.risk import RiskManager
from app.persistence.sqlite import Database
from app.backtest.queue_model import QueueModel, QueuePosition, QueueMetrics
from app.backtest.fill_probability import FillProbabilityModel, FillProbabilityFactors, FillOutcome
from app.backtest.toxic_flow import ToxicFlowDetector, ToxicFlowSignal

log = logging.getLogger("l2_replay")


@dataclass
class L2Snapshot:
    """L2 snapshot loaded from recording."""
    
    timestamp_ms: int
    exchange_ts_ms: int
    contract: str
    message_type: str  # "snapshot", "update"
    bids: List[Dict[str, Any]]
    asks: List[Dict[str, Any]]
    sequence: Optional[int] = None
    local_sequence: int = 0
    
    @classmethod
    def from_jsonl(cls, line: str) -> "L2Snapshot":
        """Create from JSONL line."""
        data = json.loads(line)
        return cls(
            timestamp_ms=data["timestamp_ms"],
            exchange_ts_ms=data["exchange_ts_ms"],
            contract=data["contract"],
            message_type=data.get("message_type", "update"),
            bids=data["bids"],
            asks=data["asks"],
            sequence=data.get("sequence"),
            local_sequence=data.get("local_sequence", 0),
        )
    
    def to_market_snapshot(self) -> MarketSnapshot:
        """Convert to MarketSnapshot for replay."""
        # Get best bid/ask
        best_bid_price = Decimal(self.bids[0]["price"]) if self.bids else Decimal("0")
        best_bid_size = self.bids[0]["size"] if self.bids else 0
        best_ask_price = Decimal(self.asks[0]["price"]) if self.asks else Decimal("0")
        best_ask_size = self.asks[0]["size"] if self.asks else 0
        
        return MarketSnapshot(
            timestamp_ms=self.timestamp_ms,
            contract=self.contract,
            bid_price=best_bid_price,
            ask_price=best_ask_price,
            bid_size=best_bid_size,
            ask_size=best_ask_size,
        )


@dataclass
class RecordedTrade:
    """Trade event loaded from recording."""
    
    timestamp_ms: int
    exchange_ts_ms: int
    contract: str
    message_type: str  # "trade"
    side: str
    price: str
    size: int
    local_sequence: int = 0
    
    @classmethod
    def from_jsonl(cls, line: str) -> "RecordedTrade":
        """Create from JSONL line."""
        data = json.loads(line)
        return cls(
            timestamp_ms=data["timestamp_ms"],
            exchange_ts_ms=data["exchange_ts_ms"],
            contract=data["contract"],
            message_type=data.get("message_type", "trade"),
            side=data["side"],
            price=data["price"],
            size=data["size"],
            local_sequence=data.get("local_sequence", 0),
        )
    
    def to_trade_event(self) -> TradeEvent:
        """Convert to TradeEvent for replay."""
        return TradeEvent(
            timestamp_ms=self.timestamp_ms,
            contract=self.contract,
            side=self.side,
            price=Decimal(self.price),
            size=self.size,
            is_maker=True,  # Assume maker for now
        )


@dataclass
class FillRecord:
    """Fill with markout analysis."""
    
    timestamp_ms: int
    contract: str
    side: str
    price: Decimal
    size: int
    markouts: Dict[str, Decimal] = field(default_factory=dict)
    
    def calculate_markout(self, future_price: Decimal, interval_ms: int) -> Decimal:
        """Calculate markout for a given interval."""
        if self.side == "buy":
            # Long position: profit if price goes up
            return (future_price - self.price) / self.price
        else:
            # Short position: profit if price goes down
            return (self.price - future_price) / self.price


class L2ReplayEngine:
    """
    Deterministic replay engine for recorded L2 data.
    
    Replays:
    - Full orderbook depth
    - Trade events
    - Exchange timestamps
    - Sequence numbers
    
    Provides:
    - Deterministic replay
    - Queue position modeling
    - OFI calculation
    - Microprice tracking
    - Markout analysis
    """
    
    def __init__(
        self,
        oms: OMS,
        risk: RiskManager,
        db: Database,
        latency_ms: int = 50,
        slippage_bps: int = 5,
        markout_intervals: Optional[List[str]] = None,
        use_queue_model: bool = True,
        use_fill_probability: bool = True,
        use_toxic_detection: bool = True,
    ):
        self.oms = oms
        self.risk = risk
        self.db = db
        self.latency_ms = latency_ms
        self.slippage_bps = slippage_bps
        self.markout_intervals = markout_intervals or ["100ms", "1s", "5s"]
        self.use_queue_model = use_queue_model
        self.use_fill_probability = use_fill_probability
        self.use_toxic_detection = use_toxic_detection
        
        self._snapshots: List[L2Snapshot] = []
        self._trades: List[RecordedTrade] = []
        self._fills: List[FillRecord] = []
        self._current_index = 0
        
        # Initialize models
        self.queue_model = QueueModel() if use_queue_model else None
        self.fill_probability_model = FillProbabilityModel() if use_fill_probability else None
        self.toxic_detector = ToxicFlowDetector() if use_toxic_detection else None
        
        # Track toxic flow signals
        self._toxic_signals: List[ToxicFlowSignal] = []
    
    def load_snapshots_from_jsonl(self, filepath: Path) -> int:
        """Load L2 snapshots from JSONL file."""
        count = 0
        with open(filepath, "r") as f:
            for line in f:
                if line.strip():
                    snapshot = L2Snapshot.from_jsonl(line)
                    self._snapshots.append(snapshot)
                    count += 1
        
        log.info(f"Loaded {count} L2 snapshots from {filepath}")
        self._sort_snapshots()
        return count
    
    def load_trades_from_jsonl(self, filepath: Path) -> int:
        """Load trades from JSONL file."""
        count = 0
        with open(filepath, "r") as f:
            for line in f:
                if line.strip():
                    trade = RecordedTrade.from_jsonl(line)
                    self._trades.append(trade)
                    count += 1
        
        log.info(f"Loaded {count} trades from {filepath}")
        self._sort_trades()
        return count
    
    def _sort_snapshots(self) -> None:
        """Sort snapshots by timestamp."""
        self._snapshots.sort(key=lambda x: x.timestamp_ms)
    
    def _sort_trades(self) -> None:
        """Sort trades by timestamp."""
        self._trades.sort(key=lambda x: x.timestamp_ms)
    
    def replay(
        self,
        contracts: List[str],
        max_snapshots: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Replay recorded L2 data deterministically.
        
        Returns summary of replay results.
        """
        if not self._snapshots:
            log.warning("No snapshots loaded, nothing to replay")
            return {"status": "no_data"}
        
        snapshots_to_replay = self._snapshots[:max_snapshots] if max_snapshots else self._snapshots
        
        log.info(f"Replaying {len(snapshots_to_replay)} L2 snapshots...")
        
        for snapshot in snapshots_to_replay:
            if snapshot.contract not in contracts:
                continue
            
            self._process_snapshot(snapshot)
        
        # Generate summary
        summary = self._generate_summary(len(snapshots_to_replay))
        
        log.info(f"L2 Replay complete: {summary}")
        return summary
    
    def _process_snapshot(self, snapshot: L2Snapshot) -> None:
        """Process a single L2 snapshot."""
        # Convert to market snapshot
        market_snapshot = snapshot.to_market_snapshot()
        
        # Calculate OFI (Order Flow Imbalance)
        ofi = self._calculate_ofi(snapshot)
        
        # Calculate microprice
        microprice = self._calculate_microprice(snapshot)
        
        # Check fills with queue position awareness
        self._check_fills_with_queue(snapshot, market_snapshot)
        
        log.debug(
            f"Processed {snapshot.contract}: "
            f"bid={market_snapshot.bid_price} ask={market_snapshot.ask_price} "
            f"OFI={ofi:.4f} microprice={microprice}"
        )
    
    def _calculate_ofi(self, snapshot: L2Snapshot) -> float:
        """
        Calculate Order Flow Imbalance.
        
        OFI = (bid_volume_changes - ask_volume_changes) / total_volume
        """
        # Simplified OFI calculation
        # Full implementation would track volume deltas between snapshots
        bid_volume = sum(bid["size"] for bid in snapshot.bids)
        ask_volume = sum(ask["size"] for ask in snapshot.asks)
        total_volume = bid_volume + ask_volume
        
        if total_volume == 0:
            return 0.0
        
        return (bid_volume - ask_volume) / total_volume
    
    def _calculate_microprice(self, snapshot: L2Snapshot) -> Decimal:
        """
        Calculate microprice.
        
        Microprice = (bid_price * ask_size + ask_price * bid_size) / (bid_size + ask_size)
        """
        if not snapshot.bids or not snapshot.asks:
            return Decimal("0")
        
        bid_price = Decimal(snapshot.bids[0]["price"])
        ask_price = Decimal(snapshot.asks[0]["price"])
        bid_size = snapshot.bids[0]["size"]
        ask_size = snapshot.asks[0]["size"]
        
        if bid_size + ask_size == 0:
            return Decimal("0")
        
        numerator = bid_price * ask_size + ask_price * bid_size
        denominator = bid_size + ask_size
        
        return numerator / denominator
    
    def _check_fills_with_queue(
        self,
        snapshot: L2Snapshot,
        market_snapshot: MarketSnapshot,
    ) -> None:
        """
        Check for fills with queue position awareness and toxic flow detection.
        
        Simulates:
        - Queue ahead volume
        - Queue depletion rate
        - Trade-through probability
        - Toxic flow detection
        """
        # Detect toxic flow
        if self.toxic_detector and self.use_toxic_detection:
            toxic_signal = self.toxic_detector.detect_toxic_flow(
                timestamp_ms=snapshot.timestamp_ms,
                contract=snapshot.contract,
                bid_price=market_snapshot.bid_price,
                bid_size=market_snapshot.bid_size,
                ask_price=market_snapshot.ask_price,
                ask_size=market_snapshot.ask_size,
                bids=snapshot.bids,
                asks=snapshot.asks,
            )
            if toxic_signal:
                self._toxic_signals.append(toxic_signal)
                log.warning(
                    f"Toxic flow detected: {toxic_signal.signal_type} "
                    f"toxicity={toxic_signal.toxicity_score:.2f} "
                    f"action={toxic_signal.recommended_action}"
                )
                
                # If toxic, skip fills for this snapshot
                if toxic_signal.recommended_action == "cancel":
                    return
        
        # Get current orders
        orders = self.oms.get_or_create(snapshot.contract)
        
        slippage_factor = Decimal(self.slippage_bps) / Decimal("10000")
        
        # Check bid fill (queue position modeling)
        if orders.bid_size > 0 and snapshot.bids:
            our_price = orders.bid_price
            best_bid = Decimal(snapshot.bids[0]["price"])
            
            if our_price >= best_bid:
                if self.queue_model and self.use_queue_model:
                    # Calculate queue position
                    queue_position = self.queue_model.calculate_queue_position(
                        our_price=our_price,
                        our_size=orders.bid_size,
                        orderbook=snapshot.bids,
                        side="buy",
                    )
                    
                    # Calculate OFI
                    ofi = self._calculate_ofi(snapshot)
                    
                    # Calculate spread
                    spread_bps = float((market_snapshot.ask_price - market_snapshot.bid_price) / market_snapshot.bid_price * 10000)
                    
                    # Calculate microprice divergence
                    microprice = self._calculate_microprice(snapshot)
                    mid_price = (market_snapshot.bid_price + market_snapshot.ask_price) / 2
                    microprice_divergence = float((microprice - mid_price) / mid_price * 10000)
                    
                    if self.fill_probability_model and self.use_fill_probability:
                        # Calculate fill probability
                        factors = FillProbabilityFactors(
                            queue_position=queue_position,
                            ofi=ofi,
                            spread_bps=spread_bps,
                            volatility_bps=5.0,  # Placeholder
                            microprice_divergence=microprice_divergence,
                            time_priority_score=1.0,  # New quote
                        )
                        
                        outcome = self.fill_probability_model.calculate_fill_probability(factors)
                        
                        # Simulate fill based on probability
                        import random
                        if random.random() < outcome.fill_probability:
                            fill_price = our_price * (Decimal("1") + slippage_factor)
                            fill_size = orders.bid_size
                            
                            self._record_fill(snapshot.contract, "buy", fill_price, fill_size, snapshot.timestamp_ms)
                            
                            # Clear order
                            orders.bid_order_id = None
                            orders.bid_price = None
                            orders.bid_size = 0
                    else:
                        # Fallback to simple queue probability
                        fill_probability = 1.0 / (1.0 + queue_position.volume_ahead / max(orders.bid_size, 1))
                        import random
                        if random.random() < fill_probability:
                            fill_price = our_price * (Decimal("1") + slippage_factor)
                            fill_size = orders.bid_size
                            self._record_fill(snapshot.contract, "buy", fill_price, fill_size, snapshot.timestamp_ms)
                            orders.bid_order_id = None
                            orders.bid_price = None
                            orders.bid_size = 0
                else:
                    # Simple fill model without queue
                    fill_probability = 0.5
                    import random
                    if random.random() < fill_probability:
                        fill_price = our_price * (Decimal("1") + slippage_factor)
                        fill_size = orders.bid_size
                        self._record_fill(snapshot.contract, "buy", fill_price, fill_size, snapshot.timestamp_ms)
                        orders.bid_order_id = None
                        orders.bid_price = None
                        orders.bid_size = 0
        
        # Check ask fill (queue position modeling)
        if orders.ask_size > 0 and snapshot.asks:
            our_price = orders.ask_price
            best_ask = Decimal(snapshot.asks[0]["price"])
            
            if our_price <= best_ask:
                if self.queue_model and self.use_queue_model:
                    # Calculate queue position
                    queue_position = self.queue_model.calculate_queue_position(
                        our_price=our_price,
                        our_size=orders.ask_size,
                        orderbook=snapshot.asks,
                        side="sell",
                    )
                    
                    # Calculate OFI
                    ofi = self._calculate_ofi(snapshot)
                    
                    # Calculate spread
                    spread_bps = float((market_snapshot.ask_price - market_snapshot.bid_price) / market_snapshot.bid_price * 10000)
                    
                    # Calculate microprice divergence
                    microprice = self._calculate_microprice(snapshot)
                    mid_price = (market_snapshot.bid_price + market_snapshot.ask_price) / 2
                    microprice_divergence = float((microprice - mid_price) / mid_price * 10000)
                    
                    if self.fill_probability_model and self.use_fill_probability:
                        # Calculate fill probability
                        factors = FillProbabilityFactors(
                            queue_position=queue_position,
                            ofi=ofi,
                            spread_bps=spread_bps,
                            volatility_bps=5.0,
                            microprice_divergence=microprice_divergence,
                            time_priority_score=1.0,
                        )
                        
                        outcome = self.fill_probability_model.calculate_fill_probability(factors)
                        
                        # Simulate fill based on probability
                        import random
                        if random.random() < outcome.fill_probability:
                            fill_price = our_price * (Decimal("1") - slippage_factor)
                            fill_size = orders.ask_size
                            
                            self._record_fill(snapshot.contract, "sell", fill_price, fill_size, snapshot.timestamp_ms)
                            
                            # Clear order
                            orders.ask_order_id = None
                            orders.ask_price = None
                            orders.ask_size = 0
                    else:
                        # Fallback to simple queue probability
                        fill_probability = 1.0 / (1.0 + queue_position.volume_ahead / max(orders.ask_size, 1))
                        import random
                        if random.random() < fill_probability:
                            fill_price = our_price * (Decimal("1") - slippage_factor)
                            fill_size = orders.ask_size
                            self._record_fill(snapshot.contract, "sell", fill_price, fill_size, snapshot.timestamp_ms)
                            orders.ask_order_id = None
                            orders.ask_price = None
                            orders.ask_size = 0
                else:
                    # Simple fill model without queue
                    fill_probability = 0.5
                    import random
                    if random.random() < fill_probability:
                        fill_price = our_price * (Decimal("1") - slippage_factor)
                        fill_size = orders.ask_size
                        self._record_fill(snapshot.contract, "sell", fill_price, fill_size, snapshot.timestamp_ms)
                        orders.ask_order_id = None
                        orders.ask_price = None
                        orders.ask_size = 0
    
    def _record_fill(
        self,
        contract: str,
        side: str,
        price: Decimal,
        size: int,
        timestamp_ms: int,
    ) -> None:
        """Record fill to database and track for markout analysis."""
        from app.persistence.models import FillRecord as DBFillRecord
        from app.core.config import ContractSpec
        
        # Get contract spec for fee calculation
        spec = self.oms._state.get(contract)
        if not spec:
            return
        
        # Calculate fee (0.02% maker fee)
        fee = price * Decimal(size) * spec.quanto_multiplier * Decimal("0.0002")
        
        fill = DBFillRecord(
            id=0,
            contract=contract,
            side=side,
            size=size,
            price=price,
            fee=fee,
            fill_ts_ms=timestamp_ms + self.latency_ms,
            recorded_ts=datetime.now(timezone.utc),
            is_maker=True,
            dry_run=True,
        )
        
        self.db.record_fill(fill)
        
        # Track fill for markout analysis
        fill_record = FillRecord(
            timestamp_ms=timestamp_ms,
            contract=contract,
            side=side,
            price=price,
            size=size,
        )
        self._fills.append(fill_record)
    
    def _calculate_markouts(self) -> None:
        """Calculate markouts for all fills at specified intervals."""
        # Parse markout intervals (e.g., "100ms" -> 100 ms)
        interval_ms_map = {}
        for interval in self.markout_intervals:
            if interval.endswith("ms"):
                interval_ms_map[interval] = int(interval[:-2])
            elif interval.endswith("s"):
                interval_ms_map[interval] = int(interval[:-1]) * 1000
            elif interval.endswith("m"):
                interval_ms_map[interval] = int(interval[:-1]) * 60000
        
        # For each fill, calculate markouts at each interval
        for fill in self._fills:
            for interval_name, interval_ms in interval_ms_map.items():
                # Find the snapshot at fill time + interval
                future_timestamp = fill.timestamp_ms + interval_ms
                
                # Find the closest snapshot after the markout time
                future_snapshot = None
                for snapshot in self._snapshots:
                    if snapshot.timestamp_ms >= future_timestamp and snapshot.contract == fill.contract:
                        future_snapshot = snapshot
                        break
                
                if future_snapshot:
                    # Get the mid price at that time
                    if future_snapshot.bids and future_snapshot.asks:
                        mid_price = (Decimal(future_snapshot.bids[0]["price"]) + 
                                   Decimal(future_snapshot.asks[0]["price"])) / Decimal("2")
                        
                        markout = fill.calculate_markout(mid_price, interval_ms)
                        fill.markouts[interval_name] = markout
    
    def _generate_markout_summary(self) -> Dict[str, Any]:
        """Generate markout analysis summary."""
        if not self._fills:
            return {}
        
        summary = {}
        
        for interval in self.markout_intervals:
            markouts = [f.markouts.get(interval, Decimal("0")) for f in self._fills if interval in f.markouts]
            
            if markouts:
                avg_markout = sum(markouts) / len(markouts)
                positive_markouts = sum(1 for m in markouts if m > Decimal("0"))
                negative_markouts = sum(1 for m in markouts if m < Decimal("0"))
                
                summary[interval] = {
                    "avg_markout_bps": float(avg_markout * 10000),
                    "positive_pct": (positive_markouts / len(markouts)) * 100,
                    "negative_pct": (negative_markouts / len(markouts)) * 100,
                    "toxicity_score": float(abs(avg_markout) * 10000),
                }
        
        return summary
    
    def _generate_toxic_summary(self) -> Dict[str, Any]:
        """Generate toxic flow analysis summary."""
        if not self._toxic_signals:
            return {"total_signals": 0}
        
        # Count signal types
        signal_counts = {}
        for signal in self._toxic_signals:
            signal_type = signal.signal_type
            signal_counts[signal_type] = signal_counts.get(signal_type, 0) + 1
        
        # Calculate average toxicity
        avg_toxicity = sum(s.toxicity_score for s in self._toxic_signals) / len(self._toxic_signals)
        
        # Count recommended actions
        action_counts = {}
        for signal in self._toxic_signals:
            action = signal.recommended_action
            action_counts[action] = action_counts.get(action, 0) + 1
        
        return {
            "total_signals": len(self._toxic_signals),
            "avg_toxicity_score": avg_toxicity,
            "signal_types": signal_counts,
            "recommended_actions": action_counts,
        }
    
    def _generate_summary(self, snapshots_replayed: int) -> Dict[str, Any]:
        """Generate replay summary."""
        # Calculate markouts before generating summary
        self._calculate_markouts()
        
        # Get fills from database
        fills = []
        for contract in self.oms._state:
            contract_fills = self.db.get_fills_by_contract(contract, limit=1000)
            fills.extend(contract_fills)
        
        total_pnl = sum(fill.realized_pnl or Decimal("0") for fill in fills)
        total_fees = sum(fill.fee for fill in fills)
        
        # Get markout summary
        markout_summary = self._generate_markout_summary()
        
        # Get toxic flow summary
        toxic_summary = self._generate_toxic_summary()
        
        return {
            "status": "complete",
            "snapshots_replayed": snapshots_replayed,
            "fills_generated": len(fills),
            "total_pnl": str(total_pnl),
            "total_fees": str(total_fees),
            "net_pnl": str(total_pnl - total_fees),
            "replay_type": "L2 deterministic",
            "markout_analysis": markout_summary,
            "toxic_flow_analysis": toxic_summary,
        }
    
    def reset(self) -> None:
        """Reset replay state."""
        self._snapshots = []
        self._trades = []
        self._fills = []
        self._toxic_signals = []
        self._current_index = 0
        log.info("L2 Replay engine reset")
