"""
Edge Decomposition Pipeline

Decomposes realized PnL into component terms:
α = spread_capture - fees - toxicity - inventory_loss - latency_loss

This is the foundation of real execution research.
"""

import logging
from dataclasses import dataclass
from decimal import Decimal
from typing import Dict, List, Optional, Tuple

import numpy as np

log = logging.getLogger("edge_decomposition")


@dataclass
class EdgeComponents:
    """Decomposed edge components in basis points."""
    
    spread_capture_bps: float  # Gross edge from spread
    fees_bps: float  # Trading fees (maker/taker)
    toxicity_bps: float  # Adverse selection (negative markout)
    inventory_loss_bps: float  # Inventory decay loss
    latency_loss_bps: float  # Stale quote losses
    realized_edge_bps: float  # Net realized edge
    
    def __post_init__(self):
        """Calculate realized edge from components."""
        self.realized_edge_bps = (
            self.spread_capture_bps
            - self.fees_bps
            - self.toxicity_bps
            - self.inventory_loss_bps
            - self.latency_loss_bps
        )
    
    def to_dict(self) -> Dict[str, float]:
        """Convert to dictionary."""
        return {
            "spread_capture_bps": self.spread_capture_bps,
            "fees_bps": self.fees_bps,
            "toxicity_bps": self.toxicity_bps,
            "inventory_loss_bps": self.inventory_loss_bps,
            "latency_loss_bps": self.latency_loss_bps,
            "realized_edge_bps": self.realized_edge_bps,
        }


@dataclass
class FillAttribution:
    """Attribution of a fill to future price trajectory."""
    
    fill_price: Decimal
    fill_time_ms: int
    side: str  # "buy" or "sell"
    size: int
    
    # Markouts at different horizons
    markout_100ms: Decimal
    markout_1s: Decimal
    markout_5s: Decimal
    markout_10s: Decimal
    
    # Toxicity classification
    is_toxic: bool
    toxicity_score: float  # 0-1, higher = more toxic
    
    # Queue metrics at fill time
    queue_ahead: int
    queue_behind: int
    queue_survival_ms: int
    
    # Latency metrics
    quote_age_ms: int
    execution_latency_ms: int


class EdgeDecomposition:
    """
    Edge decomposition pipeline.
    
    Pipeline:
    1. Load L2 data
    2. Deterministic orderbook reconstruction
    3. Simulate order placement
    4. Fill attribution
    5. Markout analysis
    6. Toxicity scoring
    7. Inventory evolution
    8. Edge decomposition
    """
    
    def __init__(
        self,
        maker_fee_bps: float = 2.0,
        taker_fee_bps: float = 5.0,
        inventory_risk_aversion: float = 0.5,
    ):
        """
        Initialize edge decomposition.
        
        Args:
            maker_fee_bps: Maker fee in basis points
            taker_fee_bps: Taker fee in basis points
            inventory_risk_aversion: Risk aversion parameter for inventory
        """
        self.maker_fee_bps = maker_fee_bps
        self.taker_fee_bps = taker_fee_bps
        self.inventory_risk_aversion = inventory_risk_aversion
        
        # State tracking
        self._fills: List[FillAttribution] = []
        self._inventory: Decimal = Decimal("0")
        self._inventory_history: List[Tuple[int, Decimal]] = []
        self._pnl_history: List[Tuple[int, Decimal]] = []
    
    def load_l2_data(self, data_dir: str) -> None:
        """Load L2 data from directory."""
        from pathlib import Path
        
        data_path = Path(data_dir)
        unified_file = list(data_path.glob("unified_*.jsonl"))
        
        if not unified_file:
            raise ValueError(f"No unified event file found in {data_dir}")
        
        # Load unified events
        events = []
        with open(unified_file[0], "r") as f:
            for line in f:
                import json
                events.append(json.loads(line))
        
        log.info(f"Loaded {len(events)} events from {unified_file[0]}")
        return events
    
    def reconstruct_orderbook(self, events: List[Dict]) -> List[Dict]:
        """
        Deterministically reconstruct orderbook from events.
        
        Returns timeline of orderbook states.
        """
        orderbook_states = []
        
        for event in events:
            if event.get("message_type") in ("snapshot", "update"):
                orderbook_states.append({
                    "timestamp_ms": event["timestamp_ms"],
                    "bids": event.get("bids", []),
                    "asks": event.get("asks", []),
                    "contract": event["contract"],
                })
        
        log.info(f"Reconstructed {len(orderbook_states)} orderbook states")
        return orderbook_states
    
    def get_mid_price(self, orderbook: Dict) -> Optional[Decimal]:
        """Get mid price from orderbook."""
        bids = orderbook.get("bids", [])
        asks = orderbook.get("asks", [])
        
        if not bids or not asks:
            return None
        
        best_bid = Decimal(bids[0]["price"])
        best_ask = Decimal(asks[0]["price"])
        
        return (best_bid + best_ask) / 2
    
    def calculate_markout(
        self,
        fill_price: Decimal,
        fill_time_ms: int,
        side: str,
        orderbook_timeline: List[Dict],
        horizon_ms: int,
    ) -> Decimal:
        """
        Calculate markout at given horizon.
        
        Markout = (future_price - fill_price) / fill_price
        For buy: positive = profit, negative = loss
        For sell: negative = profit, positive = loss
        """
        # Find orderbook state at horizon
        target_time = fill_time_ms + horizon_ms
        
        for state in orderbook_timeline:
            if state["timestamp_ms"] >= target_time:
                mid_price = self.get_mid_price(state)
                if mid_price is None:
                    return Decimal("0")
                
                # Calculate markout
                if side == "buy":
                    markout = (mid_price - fill_price) / fill_price
                else:  # sell
                    markout = (fill_price - mid_price) / fill_price
                
                return markout
        
        return Decimal("0")
    
    def classify_toxicity(
        self,
        markout_100ms: Decimal,
        markout_1s: Decimal,
    ) -> Tuple[bool, float]:
        """
        Classify if fill was toxic (informed flow).
        
        Toxic = immediate adverse price move against position
        """
        # Convert to basis points
        markout_100ms_bps = float(markout_100ms * 10000)
        markout_1s_bps = float(markout_1s * 10000)
        
        # Toxicity thresholds
        immediate_toxic_threshold = -2.0  # -2 bps in 100ms
        short_term_toxic_threshold = -5.0  # -5 bps in 1s
        
        # Calculate toxicity score (0-1)
        toxicity_score = 0.0
        
        if markout_100ms_bps < immediate_toxic_threshold:
            toxicity_score += 0.7
        if markout_1s_bps < short_term_toxic_threshold:
            toxicity_score += 0.3
        
        toxicity_score = min(1.0, toxicity_score)
        
        is_toxic = toxicity_score > 0.5
        
        return is_toxic, toxicity_score
    
    def simulate_fills(
        self,
        orderbook_timeline: List[Dict],
        quote_spread_bps: float = 10.0,
        quote_size: int = 1000,
    ) -> List[FillAttribution]:
        """
        Simulate order placement and fill attribution.
        
        Args:
            orderbook_timeline: Reconstructed orderbook states
            quote_spread_bps: Spread to quote at
            quote_size: Size of quotes
            
        Returns:
            List of fill attributions
        """
        fills = []
        
        for i, state in enumerate(orderbook_timeline):
            mid_price = self.get_mid_price(state)
            if mid_price is None:
                continue
            
            # Calculate quote prices
            spread = mid_price * (quote_spread_bps / 10000)
            
            bid_quote = mid_price - spread / 2
            ask_quote = mid_price + spread / 2
            
            # Check if quotes would be filled
            # (simplified - in reality need queue position simulation)
            bids = state.get("bids", [])
            asks = state.get("asks", [])
            
            # Simulate fills when our quotes are best
            if bids and Decimal(bids[0]["price"]) >= bid_quote:
                # Bid fill (we buy)
                fill = self._create_fill_attribution(
                    fill_price=bid_quote,
                    fill_time_ms=state["timestamp_ms"],
                    side="buy",
                    size=quote_size,
                    orderbook_timeline=orderbook_timeline[i:],
                )
                fills.append(fill)
            
            if asks and Decimal(asks[0]["price"]) <= ask_quote:
                # Ask fill (we sell)
                fill = self._create_fill_attribution(
                    fill_price=ask_quote,
                    fill_time_ms=state["timestamp_ms"],
                    side="sell",
                    size=quote_size,
                    orderbook_timeline=orderbook_timeline[i:],
                )
                fills.append(fill)
        
        log.info(f"Simulated {len(fills)} fills")
        return fills
    
    def _create_fill_attribution(
        self,
        fill_price: Decimal,
        fill_time_ms: int,
        side: str,
        size: int,
        orderbook_timeline: List[Dict],
    ) -> FillAttribution:
        """Create fill attribution with markout analysis."""
        # Calculate markouts at different horizons
        markout_100ms = self.calculate_markout(
            fill_price, fill_time_ms, side, orderbook_timeline, 100
        )
        markout_1s = self.calculate_markout(
            fill_price, fill_time_ms, side, orderbook_timeline, 1000
        )
        markout_5s = self.calculate_markout(
            fill_price, fill_time_ms, side, orderbook_timeline, 5000
        )
        markout_10s = self.calculate_markout(
            fill_price, fill_time_ms, side, orderbook_timeline, 10000
        )
        
        # Classify toxicity
        is_toxic, toxicity_score = self.classify_toxicity(markout_100ms, markout_1s)
        
        # Queue metrics (placeholder - need real queue tracking)
        queue_ahead = 0
        queue_behind = 0
        queue_survival_ms = 1000
        
        # Latency metrics (placeholder)
        quote_age_ms = 10
        execution_latency_ms = 50
        
        return FillAttribution(
            fill_price=fill_price,
            fill_time_ms=fill_time_ms,
            side=side,
            size=size,
            markout_100ms=markout_100ms,
            markout_1s=markout_1s,
            markout_5s=markout_5s,
            markout_10s=markout_10s,
            is_toxic=is_toxic,
            toxicity_score=toxicity_score,
            queue_ahead=queue_ahead,
            queue_behind=queue_behind,
            queue_survival_ms=queue_survival_ms,
            quote_age_ms=quote_age_ms,
            execution_latency_ms=execution_latency_ms,
        )
    
    def calculate_inventory_loss(
        self,
        inventory: Decimal,
        price_change: Decimal,
    ) -> float:
        """
        Calculate inventory loss from price change.
        
        Loss = inventory * price_change * risk_aversion
        """
        return float(inventory * price_change * self.inventory_risk_aversion)
    
    def decompose_edge(
        self,
        fills: List[FillAttribution],
        avg_spread_bps: float = 10.0,
    ) -> EdgeComponents:
        """
        Decompose edge into components.
        
        α = spread_capture - fees - toxicity - inventory_loss - latency_loss
        """
        total_spread_capture = Decimal("0")
        total_fees = Decimal("0")
        total_toxicity = Decimal("0")
        total_inventory_loss = Decimal("0")
        total_latency_loss = Decimal("0")
        
        for fill in fills:
            # Spread capture (half of quoted spread)
            spread_capture = avg_spread_bps / 2
            total_spread_capture += Decimal(spread_capture)
            
            # Fees (maker fee)
            fees = self.maker_fee_bps
            total_fees += Decimal(fees)
            
            # Toxicity (negative markout if toxic)
            if fill.is_toxic:
                toxicity = abs(float(fill.markout_1s * 10000))
                total_toxicity += Decimal(toxicity)
            
            # Inventory loss (simplified)
            inventory_loss = 0.0  # Need proper inventory tracking
            total_inventory_loss += Decimal(inventory_loss)
            
            # Latency loss (stale quote penalty)
            latency_loss = fill.execution_latency_ms * 0.01  # 0.01 bps per ms
            total_latency_loss += Decimal(latency_loss)
        
        # Convert to average per fill
        num_fills = max(1, len(fills))
        
        return EdgeComponents(
            spread_capture_bps=float(total_spread_capture / num_fills),
            fees_bps=float(total_fees / num_fills),
            toxicity_bps=float(total_toxicity / num_fills),
            inventory_loss_bps=float(total_inventory_loss / num_fills),
            latency_loss_bps=float(total_latency_loss / num_fills),
            realized_edge_bps=0.0,  # Calculated in __post_init__
        )
    
    def run_pipeline(
        self,
        data_dir: str,
        quote_spread_bps: float = 10.0,
        quote_size: int = 1000,
    ) -> Dict[str, any]:
        """
        Run complete edge decomposition pipeline.
        
        Returns:
            Dictionary with all metrics and decompositions
        """
        log.info("=" * 60)
        log.info("EDGE DECOMPOSITION PIPELINE")
        log.info("=" * 60)
        
        # Step 1: Load L2 data
        log.info("Step 1: Loading L2 data...")
        events = self.load_l2_data(data_dir)
        
        # Step 2: Reconstruct orderbook
        log.info("Step 2: Reconstructing orderbook...")
        orderbook_timeline = self.reconstruct_orderbook(events)
        
        # Step 3: Simulate fills
        log.info("Step 3: Simulating fills...")
        fills = self.simulate_fills(
            orderbook_timeline,
            quote_spread_bps=quote_spread_bps,
            quote_size=quote_size,
        )
        
        # Step 4: Calculate markouts (done in simulate_fills)
        log.info("Step 4: Markout analysis complete")
        
        # Step 5: Toxicity scoring (done in simulate_fills)
        log.info("Step 5: Toxicity scoring complete")
        
        # Step 6: Decompose edge
        log.info("Step 6: Decomposing edge...")
        edge_components = self.decompose_edge(fills, quote_spread_bps)
        
        # Step 7: Calculate additional metrics
        log.info("Step 7: Calculating metrics...")
        
        metrics = {
            "edge_components": edge_components.to_dict(),
            "num_fills": len(fills),
            "toxic_fill_ratio": sum(1 for f in fills if f.is_toxic) / max(1, len(fills)),
            "avg_toxicity_score": np.mean([f.toxicity_score for f in fills]) if fills else 0.0,
            "avg_markout_100ms_bps": np.mean([float(f.markout_100ms * 10000) for f in fills]) if fills else 0.0,
            "avg_markout_1s_bps": np.mean([float(f.markout_1s * 10000) for f in fills]) if fills else 0.0,
            "avg_queue_survival_ms": np.mean([f.queue_survival_ms for f in fills]) if fills else 0.0,
            "avg_execution_latency_ms": np.mean([f.execution_latency_ms for f in fills]) if fills else 0.0,
        }
        
        log.info("=" * 60)
        log.info("EDGE DECOMPOSITION RESULTS")
        log.info("=" * 60)
        log.info(f"Spread capture: {edge_components.spread_capture_bps:.2f} bps")
        log.info(f"Fees: {edge_components.fees_bps:.2f} bps")
        log.info(f"Toxicity: {edge_components.toxicity_bps:.2f} bps")
        log.info(f"Inventory loss: {edge_components.inventory_loss_bps:.2f} bps")
        log.info(f"Latency loss: {edge_components.latency_loss_bps:.2f} bps")
        log.info("=" * 60)
        log.info(f"REALIZED EDGE: {edge_components.realized_edge_bps:.2f} bps")
        log.info("=" * 60)
        
        return metrics
