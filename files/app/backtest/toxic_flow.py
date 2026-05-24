"""
Toxic flow detection and analysis.

Detects:
- Informed flow (market makers getting picked off)
- Microprice divergence
- OFI slope analysis
- Spread collapse prediction
- Quote fade logic
"""

import logging
from dataclasses import dataclass
from decimal import Decimal
from typing import Dict, List, Optional, Tuple

import numpy as np

log = logging.getLogger("toxic_flow")


@dataclass
class ToxicFlowSignal:
    """Toxic flow detection signal."""
    
    timestamp_ms: int
    contract: str
    is_toxic: bool
    toxicity_score: float  # 0-1, higher = more toxic
    signal_type: str  # "microprice_divergence", "ofi_spike", "spread_collapse", "quote_fade"
    confidence: float  # 0-1
    recommended_action: str  # "hold", "widen", "flatten", "cancel"


@dataclass
class MicropriceAnalysis:
    """Microprice analysis for toxic flow detection."""
    
    mid_price: Decimal
    microprice: Decimal
    divergence_bps: float
    divergence_pct: float
    direction: str  # "bid_pressure", "ask_pressure", "balanced"


@dataclass
class OFIAnalysis:
    """Order Flow Imbalance analysis."""
    
    current_ofi: float
    ofi_slope: float  # Rate of change
    ofi_momentum: float  # Acceleration
    is_extreme: bool
    extreme_direction: str  # "extreme_buy", "extreme_sell"


@dataclass
class SpreadAnalysis:
    """Spread analysis for toxic flow."""
    
    current_spread_bps: float
    spread_momentum: float  # Rate of change
    is_collapsing: bool
    collapse_rate: float


class ToxicFlowDetector:
    """
    Detects toxic flow and provides defensive recommendations.
    
    Signals:
    - Microprice divergence (informed flow)
    - OFI spikes (aggressive flow)
    - Spread collapse (adverse selection)
    - Quote fade (stale quotes)
    """
    
    def __init__(
        self,
        divergence_threshold_bps: float = 2.0,
        ofi_threshold: float = 0.3,
        spread_collapse_threshold_bps: float = 5.0,
        lookback_periods: int = 10,
    ):
        self.divergence_threshold_bps = divergence_threshold_bps
        self.ofi_threshold = ofi_threshold
        self.spread_collapse_threshold_bps = spread_collapse_threshold_bps
        self.lookback_periods = lookback_periods
        
        # Historical data for trend analysis
        self._ofi_history: List[float] = []
        self._spread_history: List[float] = []
        self._mid_price_history: List[Decimal] = []
    
    def analyze_microprice(
        self,
        bid_price: Decimal,
        bid_size: int,
        ask_price: Decimal,
        ask_size: int,
    ) -> MicropriceAnalysis:
        """
        Analyze microprice for toxic flow.
        
        Microprice = (bid_price * ask_size + ask_price * bid_size) / (bid_size + ask_size)
        """
        if bid_size + ask_size == 0:
            return MicropriceAnalysis(
                mid_price=(bid_price + ask_price) / 2,
                microprice=Decimal("0"),
                divergence_bps=0.0,
                divergence_pct=0.0,
                direction="balanced",
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
        
        return MicropriceAnalysis(
            mid_price=mid_price,
            microprice=microprice,
            divergence_bps=float(divergence),
            divergence_pct=divergence_pct,
            direction=direction,
        )
    
    def analyze_ofi(self, bids: List[Dict], asks: List[Dict]) -> OFIAnalysis:
        """
        Analyze Order Flow Imbalance.
        
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
        is_extreme = abs(current_ofi) > self.ofi_threshold
        if current_ofi > self.ofi_threshold:
            extreme_direction = "extreme_buy"
        elif current_ofi < -self.ofi_threshold:
            extreme_direction = "extreme_sell"
        else:
            extreme_direction = "normal"
        
        return OFIAnalysis(
            current_ofi=current_ofi,
            ofi_slope=ofi_slope,
            ofi_momentum=ofi_momentum,
            is_extreme=is_extreme,
            extreme_direction=extreme_direction,
        )
    
    def analyze_spread(
        self,
        bid_price: Decimal,
        ask_price: Decimal,
    ) -> SpreadAnalysis:
        """
        Analyze spread for collapse detection.
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
        
        # Detect collapse (rapid spread narrowing)
        is_collapsing = spread_momentum < -self.spread_collapse_threshold_bps / 10.0
        collapse_rate = abs(spread_momentum) if is_collapsing else 0.0
        
        return SpreadAnalysis(
            current_spread_bps=spread_bps,
            spread_momentum=spread_momentum,
            is_collapsing=is_collapsing,
            collapse_rate=collapse_rate,
        )
    
    def detect_toxic_flow(
        self,
        timestamp_ms: int,
        contract: str,
        bid_price: Decimal,
        bid_size: int,
        ask_price: Decimal,
        ask_size: int,
        bids: List[Dict],
        asks: List[Dict],
    ) -> Optional[ToxicFlowSignal]:
        """
        Detect toxic flow and generate signal.
        
        Returns signal if toxic flow detected.
        """
        # Analyze microprice
        microprice_analysis = self.analyze_microprice(bid_price, bid_size, ask_price, ask_size)
        
        # Analyze OFI
        ofi_analysis = self.analyze_ofi(bids, asks)
        
        # Analyze spread
        spread_analysis = self.analyze_spread(bid_price, ask_price)
        
        # Calculate toxicity score
        toxicity_score = self._calculate_toxicity_score(
            microprice_analysis,
            ofi_analysis,
            spread_analysis,
        )
        
        # Determine if toxic
        is_toxic = toxicity_score > 0.5
        
        if not is_toxic:
            return None
        
        # Determine signal type
        if microprice_analysis.divergence_bps > self.divergence_threshold_bps:
            signal_type = "microprice_divergence"
        elif ofi_analysis.is_extreme:
            signal_type = "ofi_spike"
        elif spread_analysis.is_collapsing:
            signal_type = "spread_collapse"
        else:
            signal_type = "quote_fade"
        
        # Calculate confidence
        confidence = min(1.0, toxicity_score)
        
        # Determine recommended action
        recommended_action = self._determine_action(
            signal_type,
            microprice_analysis,
            ofi_analysis,
            spread_analysis,
        )
        
        return ToxicFlowSignal(
            timestamp_ms=timestamp_ms,
            contract=contract,
            is_toxic=is_toxic,
            toxicity_score=toxicity_score,
            signal_type=signal_type,
            confidence=confidence,
            recommended_action=recommended_action,
        )
    
    def _calculate_toxicity_score(
        self,
        microprice_analysis: MicropriceAnalysis,
        ofi_analysis: OFIAnalysis,
        spread_analysis: SpreadAnalysis,
    ) -> float:
        """
        Calculate overall toxicity score (0-1).
        """
        # Microprice divergence score
        microprice_score = min(1.0, abs(microprice_analysis.divergence_bps) / 10.0)
        
        # OFI extreme score
        ofi_score = min(1.0, abs(ofi_analysis.current_ofi) / 0.5)
        
        # Spread collapse score
        spread_score = min(1.0, spread_analysis.collapse_rate / 5.0)
        
        # Weighted average
        toxicity_score = (
            0.4 * microprice_score
            + 0.3 * ofi_score
            + 0.3 * spread_score
        )
        
        return toxicity_score
    
    def _determine_action(
        self,
        signal_type: str,
        microprice_analysis: MicropriceAnalysis,
        ofi_analysis: OFIAnalysis,
        spread_analysis: SpreadAnalysis,
    ) -> str:
        """Determine recommended action based on signal type."""
        if signal_type == "microprice_divergence":
            if microprice_analysis.direction == "ask_pressure":
                return "flatten"  # Reduce position
            else:
                return "hold"
        elif signal_type == "ofi_spike":
            if ofi_analysis.extreme_direction == "extreme_buy":
                return "widen"  # Widen asks
            else:
                return "widen"  # Widen bids
        elif signal_type == "spread_collapse":
            return "cancel"  # Cancel all quotes
        else:  # quote_fade
            return "hold"
