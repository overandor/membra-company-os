"""
Market analytics metrics for microstructure analysis.

Calculates:
- Microprice
- Order Flow Imbalance (OFI)
- Queue ahead volume
- Spread state
- Realized volatility
- Cancel rate
- Sweep detection
- Markout metrics
"""

import logging
from dataclasses import dataclass
from decimal import Decimal
from typing import Dict, List, Optional, Tuple

import numpy as np

log = logging.getLogger("market_analytics")


@dataclass
class MicropriceMetrics:
    """Microprice analysis metrics."""
    
    mid_price: Decimal
    microprice: Decimal
    divergence_bps: float
    divergence_pct: float
    direction: str  # "bid_pressure", "ask_pressure", "balanced"
    timestamp_ms: int


@dataclass
class OFIMetrics:
    """Order Flow Imbalance metrics."""
    
    current_ofi: float
    ofi_slope: float
    ofi_momentum: float
    is_extreme: bool
    extreme_direction: str
    timestamp_ms: int


@dataclass
class SpreadState:
    """Spread state classification."""
    
    spread_bps: float
    spread_momentum: float
    state: str  # "tight", "normal", "wide", "widening", "narrowing"
    timestamp_ms: int


@dataclass
class VolatilityMetrics:
    """Volatility metrics."""
    
    realized_volatility_bps: float
    volatility_regime: str  # "low", "normal", "high"
    timestamp_ms: int


@dataclass
class SweepEvent:
    """Sweep detection event."""
    
    timestamp_ms: int
    contract: str
    side: str  # "buy" or "sell"
    sweep_level: int  # Number of levels swept
    total_volume: int
    avg_price: Decimal


class MarketAnalytics:
    """
    Calculates market microstructure analytics.
    
    Metrics:
    - Microprice
    - OFI
    Queue ahead volume
    - Spread state
    - Realized volatility
    - Cancel rate
    - Sweep detection
    - Markout metrics
    """
    
    def __init__(self, lookback_periods: int = 20):
        self.lookback_periods = lookback_periods
        
        # Historical data for calculations
        self._mid_price_history: List[Decimal] = []
        self._ofi_history: List[float] = []
        self._spread_history: List[float] = []
        self._trade_history: List[Tuple[int, Decimal, int]] = []  # (timestamp, price, size)
    
    def calculate_microprice(
        self,
        bid_price: Decimal,
        bid_size: int,
        ask_price: Decimal,
        ask_size: int,
        timestamp_ms: int,
    ) -> MicropriceMetrics:
        """
        Calculate microprice.
        
        Microprice = (bid_price * ask_size + ask_price * bid_size) / (bid_size + ask_size)
        """
        if bid_size + ask_size == 0:
            return MicropriceMetrics(
                mid_price=(bid_price + ask_price) / 2,
                microprice=Decimal("0"),
                divergence_bps=0.0,
                divergence_pct=0.0,
                direction="balanced",
                timestamp_ms=timestamp_ms,
            )
        
        mid_price = (bid_price + ask_price) / 2
        microprice = (bid_price * ask_size + ask_price * bid_size) / Decimal(bid_size + ask_size)
        
        # Calculate divergence in bps
        divergence = (microprice - mid_price) / mid_price * 10000
        divergence_pct = abs(divergence) / 100.0
        
        # Determine direction
        if divergence > 0:
            direction = "ask_pressure"  # Microprice above mid = sell pressure
        elif divergence < 0:
            direction = "bid_pressure"  # Microprice below mid = buy pressure
        else:
            direction = "balanced"
        
        return MicropriceMetrics(
            mid_price=mid_price,
            microprice=microprice,
            divergence_bps=float(divergence),
            divergence_pct=divergence_pct,
            direction=direction,
            timestamp_ms=timestamp_ms,
        )
    
    def calculate_ofi(
        self,
        bids: List[Dict],
        asks: List[Dict],
        previous_bids: Optional[List[Dict]] = None,
        previous_asks: Optional[List[Dict]] = None,
        timestamp_ms: int = 0,
    ) -> OFIMetrics:
        """
        Calculate Order Flow Imbalance.
        
        OFI = (bid_volume_changes - ask_volume_changes) / total_volume
        """
        bid_volume = sum(b["size"] for b in bids)
        ask_volume = sum(a["size"] for a in asks)
        total_volume = bid_volume + ask_volume
        
        if total_volume == 0:
            current_ofi = 0.0
        else:
            current_ofi = (bid_volume - ask_volume) / total_volume
        
        # Calculate slope (rate of change)
        self._ofi_history.append(current_ofi)
        if len(self._ofi_history) > self.lookback_periods:
            self._ofi_history.pop(0)
        
        if len(self._ofi_history) >= 2:
            ofi_slope = self._ofi_history[-1] - self._ofi_history[-2]
        else:
            ofi_slope = 0.0
        
        # Calculate momentum (acceleration)
        if len(self._ofi_history) >= 3:
            ofi_momentum = ofi_slope - (self._ofi_history[-2] - self._ofi_history[-3])
        else:
            ofi_momentum = 0.0
        
        # Detect extreme OFI
        is_extreme = abs(current_ofi) > 0.3
        if current_ofi > 0.3:
            extreme_direction = "extreme_buy"
        elif current_ofi < -0.3:
            extreme_direction = "extreme_sell"
        else:
            extreme_direction = "normal"
        
        return OFIMetrics(
            current_ofi=current_ofi,
            ofi_slope=ofi_slope,
            ofi_momentum=ofi_momentum,
            is_extreme=is_extreme,
            extreme_direction=extreme_direction,
            timestamp_ms=timestamp_ms,
        )
    
    def calculate_queue_ahead_volume(
        self,
        our_price: Decimal,
        our_size: int,
        orderbook: List[Dict],
    ) -> int:
        """
        Calculate volume ahead in queue.
        """
        volume_ahead = 0
        for order in orderbook:
            if Decimal(order["price"]) == our_price:
                break
            volume_ahead += order["size"]
        
        return volume_ahead
    
    def classify_spread_state(
        self,
        bid_price: Decimal,
        ask_price: Decimal,
        timestamp_ms: int = 0,
    ) -> SpreadState:
        """
        Classify spread state.
        """
        spread = ask_price - bid_price
        mid_price = (bid_price + ask_price) / 2
        spread_bps = float(spread / mid_price * 10000)
        
        # Calculate momentum
        self._spread_history.append(spread_bps)
        if len(self._spread_history) > self.lookback_periods:
            self._spread_history.pop(0)
        
        if len(self._spread_history) >= 2:
            spread_momentum = self._spread_history[-1] - self._spread_history[-2]
        else:
            spread_momentum = 0.0
        
        # Classify state
        if spread_bps < 2.0:
            state = "tight"
        elif spread_bps < 10.0:
            state = "normal"
        else:
            state = "wide"
        
        # Add momentum to state
        if spread_momentum > 0.5:
            state = "widening"
        elif spread_momentum < -0.5:
            state = "narrowing"
        
        return SpreadState(
            spread_bps=spread_bps,
            spread_momentum=spread_momentum,
            state=state,
            timestamp_ms=timestamp_ms,
        )
    
    def calculate_realized_volatility(
        self,
        window_seconds: int = 60,
        timestamp_ms: int = 0,
    ) -> VolatilityMetrics:
        """
        Calculate realized volatility.
        """
        if len(self._mid_price_history) < 2:
            return VolatilityMetrics(
                realized_volatility_bps=0.0,
                volatility_regime="normal",
                timestamp_ms=timestamp_ms,
            )
        
        # Calculate returns
        prices = [float(p) for p in self._mid_price_history[-window_seconds:]]
        if len(prices) < 2:
            returns = []
        else:
            returns = [np.log(prices[i] / prices[i-1]) for i in range(1, len(prices))]
        
        if not returns:
            realized_vol = 0.0
        else:
            realized_vol = np.std(returns) * np.sqrt(len(returns)) * 10000
        
        # Classify regime
        if realized_vol < 5.0:
            regime = "low"
        elif realized_vol < 20.0:
            regime = "normal"
        else:
            regime = "high"
        
        return VolatilityMetrics(
            realized_volatility_bps=realized_vol,
            volatility_regime=regime,
            timestamp_ms=timestamp_ms,
        )
    
    def detect_sweep(
        self,
        timestamp_ms: int,
        contract: str,
        bids: List[Dict],
        asks: List[Dict],
        previous_bids: Optional[List[Dict]] = None,
        previous_asks: Optional[List[Dict]] = None,
    ) -> Optional[SweepEvent]:
        """
        Detect sweep (aggressive trade consuming multiple levels).
        """
        if not previous_bids or not previous_asks:
            return None
        
        # Check for bid sweep (asks moving up)
        if previous_asks and asks:
            prev_best_ask = Decimal(previous_asks[0]["price"])
            curr_best_ask = Decimal(asks[0]["price"])
            
            if curr_best_ask > prev_best_ask:
                # Calculate how many levels were swept
                levels_swept = 0
                for ask in previous_asks:
                    if Decimal(ask["price"]) < curr_best_ask:
                        levels_swept += 1
                    else:
                        break
                
                if levels_swept >= 2:
                    total_volume = sum(a["size"] for a in previous_asks[:levels_swept])
                    avg_price = sum(Decimal(a["price"]) for a in previous_asks[:levels_swept]) / levels_swept
                    
                    return SweepEvent(
                        timestamp_ms=timestamp_ms,
                        contract=contract,
                        side="buy",
                        sweep_level=levels_swept,
                        total_volume=total_volume,
                        avg_price=avg_price,
                    )
        
        # Check for ask sweep (bids moving down)
        if previous_bids and bids:
            prev_best_bid = Decimal(previous_bids[0]["price"])
            curr_best_bid = Decimal(bids[0]["price"])
            
            if curr_best_bid < prev_best_bid:
                # Calculate how many levels were swept
                levels_swept = 0
                for bid in previous_bids:
                    if Decimal(bid["price"]) > curr_best_bid:
                        levels_swept += 1
                    else:
                        break
                
                if levels_swept >= 2:
                    total_volume = sum(b["size"] for b in previous_bids[:levels_swept])
                    avg_price = sum(Decimal(b["price"]) for b in previous_bids[:levels_swept]) / levels_swept
                    
                    return SweepEvent(
                        timestamp_ms=timestamp_ms,
                        contract=contract,
                        side="sell",
                        sweep_level=levels_swept,
                        total_volume=total_volume,
                        avg_price=avg_price,
                    )
        
        return None
    
    def update_mid_price(self, mid_price: Decimal) -> None:
        """Update mid price history."""
        self._mid_price_history.append(mid_price)
        if len(self._mid_price_history) > self.lookback_periods * 10:
            self._mid_price_history.pop(0)
    
    def record_trade(self, timestamp_ms: int, price: Decimal, size: int) -> None:
        """Record trade for analytics."""
        self._trade_history.append((timestamp_ms, price, size))
        if len(self._trade_history) > self.lookback_periods * 10:
            self._trade_history.pop(0)
    
    def calculate_cancel_rate(
        self,
        window_seconds: int = 60,
    ) -> float:
        """
        Calculate cancel rate (cancels per second).
        
        Simplified: ratio of trades to total volume changes.
        """
        if len(self._trade_history) < 2:
            return 0.0
        
        # Count trades in window
        now = self._trade_history[-1][0]
        window_start = now - window_seconds * 1000
        
        trades_in_window = [t for t in self._trade_history if t[0] >= window_start]
        
        if not trades_in_window:
            return 0.0
        
        # Simplified cancel rate estimate
        return len(trades_in_window) / window_seconds
