"""
Queue position modeling for realistic fill simulation.

Models:
- Queue position (rank, volume ahead)
- Queue depletion rate
- Time priority
- Cancel rate
- Trade-through probability
"""

import logging
from dataclasses import dataclass
from decimal import Decimal
from typing import Dict, List, Optional, Any

log = logging.getLogger("queue_model")


@dataclass
class QueuePosition:
    """Queue position for a quote."""
    
    price: Decimal
    size: int
    rank: int  # Position in queue (0 = first)
    volume_ahead: int  # Total volume ahead in queue
    volume_behind: int  # Total volume behind in queue
    time_in_queue_ms: int  # How long this quote has been in queue
    
    @property
    def queue_depth(self) -> int:
        """Total queue depth."""
        return self.volume_ahead + self.size + self.volume_behind
    
    @property
    def queue_fraction(self) -> Decimal:
        """Fraction of queue that is ahead of us."""
        if self.queue_depth == 0:
            return Decimal("0")
        return Decimal(self.volume_ahead) / Decimal(self.queue_depth)


@dataclass
class QueueMetrics:
    """Queue metrics for a price level."""
    
    price: Decimal
    total_volume: int
    num_orders: int
    avg_order_size: Decimal
    queue_turnover_rate: float  # Orders per second
    cancel_rate: float  # Cancelations per second
    trade_through_rate: float  # Probability of trade skipping queue
    trade_intensity: float  # Trades per second (new)
    toxicity_score: float  # 0-1, higher = more toxic (new)
    
    @classmethod
    def from_snapshot(cls, price: Decimal, orders: List[Dict], toxicity_score: float = 0.0) -> "QueueMetrics":
        """Create queue metrics from snapshot data."""
        total_volume = sum(o.get("size", 0) for o in orders)
        num_orders = len(orders)
        avg_order_size = Decimal(total_volume) / Decimal(num_orders) if num_orders > 0 else Decimal("0")
        
        return cls(
            price=price,
            total_volume=total_volume,
            num_orders=num_orders,
            avg_order_size=avg_order_size,
            queue_turnover_rate=0.5,  # Placeholder
            cancel_rate=0.1,  # Placeholder
            trade_through_rate=0.05,  # Placeholder
            trade_intensity=1.0,  # Placeholder
            toxicity_score=toxicity_score,
        )


class QueueModel:
    """
    Models queue position and fill probability.
    
    Factors:
    - Queue position (rank, volume ahead)
    - Order Flow Imbalance (OFI)
    - Spread
    - Volatility
    - Time priority
    """
    
    def __init__(
        self,
        base_fill_rate: float = 0.5,
        queue_decay_rate: float = 0.1,
        ofi_sensitivity: float = 0.3,
        spread_sensitivity: float = 0.2,
    ):
        self.base_fill_rate = base_fill_rate
        self.queue_decay_rate = queue_decay_rate
        self.ofi_sensitivity = ofi_sensitivity
        self.spread_sensitivity = spread_sensitivity
    
    def calculate_queue_position(
        self,
        our_price: Decimal,
        our_size: int,
        orderbook: List[Dict[str, Any]],
        side: str,
    ) -> QueuePosition:
        """
        Calculate queue position for our order.
        
        Returns rank, volume ahead, volume behind.
        """
        # Filter orders at our price level
        orders_at_price = []
        for order in orderbook:
            if Decimal(order["price"]) == our_price:
                orders_at_price.append(order)
        
        # Sort by time (assuming orders have timestamp)
        orders_at_price.sort(key=lambda x: x.get("timestamp_ms", 0))
        
        # Find our position (simplified - assume we're last for now)
        volume_ahead = sum(o["size"] for o in orders_at_price[:-1])
        volume_behind = 0  # We're at the end
        rank = len(orders_at_price) - 1
        
        return QueuePosition(
            price=our_price,
            size=our_size,
            rank=rank,
            volume_ahead=volume_ahead,
            volume_behind=volume_behind,
            time_in_queue_ms=0,  # New order
        )
    
    def calculate_fill_probability(
        self,
        queue_position: QueuePosition,
        ofi: float,
        spread_bps: float,
        volatility_bps: float,
        trade_intensity: float = 1.0,
        toxicity_score: float = 0.0,
    ) -> float:
        """
        Calculate fill probability based on queue position and market conditions.
        
        Formula:
        P(fill) = base_rate * queue_decay * ofi_factor * spread_factor * trade_intensity_factor * toxicity_penalty
        """
        # Queue decay: probability decreases with queue position
        queue_factor = 1.0 / (1.0 + self.queue_decay_rate * queue_position.rank)
        
        # OFI factor: positive OFI (buy pressure) increases fill probability for bids
        ofi_factor = 1.0 + self.ofi_sensitivity * ofi
        
        # Spread factor: wider spreads increase fill probability
        spread_factor = 1.0 + self.spread_sensitivity * (spread_bps / 100.0)
        
        # Trade intensity factor: higher trade intensity increases fill probability
        trade_intensity_factor = min(2.0, trade_intensity)
        
        # Volatility penalty: high volatility reduces fill probability
        volatility_penalty = 1.0 / (1.0 + volatility_bps / 50.0)
        
        # Toxicity penalty: high toxicity reduces fill probability
        toxicity_penalty = 1.0 / (1.0 + toxicity_score * 2.0)
        
        fill_prob = (
            self.base_fill_rate
            * queue_factor
            * ofi_factor
            * spread_factor
            * trade_intensity_factor
            * volatility_penalty
            * toxicity_penalty
        )
        
        return max(0.0, min(1.0, fill_prob))
    
    def simulate_queue_evolution(
        self,
        queue_position: QueuePosition,
        elapsed_ms: int,
        metrics: QueueMetrics,
    ) -> QueuePosition:
        """
        Simulate how queue evolves over time.
        
        Models:
        - Queue depletion (fills)
        - Cancellations
        - New orders joining queue
        """
        # Calculate expected fills based on turnover rate and trade intensity
        expected_fills = int(
            metrics.queue_turnover_rate
            * metrics.trade_intensity
            * (elapsed_ms / 1000.0)
            * queue_position.size
        )
        
        # Calculate expected cancellations
        expected_cancels = int(
            metrics.cancel_rate
            * (elapsed_ms / 1000.0)
            * queue_position.size
        )
        
        # Update volume ahead (simplified)
        new_volume_ahead = max(0, queue_position.volume_ahead - expected_fills)
        
        # Update rank based on volume changes
        new_rank = max(0, queue_position.rank - expected_fills)
        
        return QueuePosition(
            price=queue_position.price,
            size=max(0, queue_position.size - expected_fills),
            rank=new_rank,
            volume_ahead=new_volume_ahead,
            volume_behind=queue_position.volume_behind,
            time_in_queue_ms=queue_position.time_in_queue_ms + elapsed_ms,
        )
    
    def calculate_expected_fill_time(
        self,
        queue_position: QueuePosition,
        metrics: QueueMetrics,
    ) -> int:
        """
        Calculate expected time to fill in milliseconds.
        
        Based on queue position and turnover rate.
        """
        if metrics.queue_turnover_rate == 0:
            return float('inf')
        
        # Time = volume_ahead / turnover_rate
        seconds_to_clear = queue_position.volume_ahead / metrics.queue_turnover_rate
        return int(seconds_to_clear * 1000)
