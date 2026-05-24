"""
Fill probability model for realistic fill simulation.

Calculates:
- P(fill | queue_position, OFI, spread, volatility)
- E[markout | fill]
- Toxic flow detection
"""

import logging
from dataclasses import dataclass
from decimal import Decimal
from typing import Dict, List, Optional

import numpy as np

from app.backtest.queue_model import QueueModel, QueuePosition, QueueMetrics

log = logging.getLogger("fill_probability")


@dataclass
class FillProbabilityFactors:
    """Factors affecting fill probability."""
    
    queue_position: QueuePosition
    ofi: float  # Order Flow Imbalance
    spread_bps: float
    volatility_bps: float
    microprice_divergence: float
    time_priority_score: float  # 0-1, higher is better
    
    @property
    def queue_score(self) -> float:
        """Queue position score (0-1)."""
        if self.queue_position.queue_depth == 0:
            return 1.0
        return 1.0 - float(self.queue_position.queue_fraction)


@dataclass
class FillOutcome:
    """Result of a fill probability simulation."""
    
    fill_probability: float
    expected_fill_time_ms: Optional[int]
    expected_markout_bps: float
    toxicity_score: float
    is_toxic: bool
    
    @property
    def is_profitable(self) -> bool:
        """Whether expected markout is positive."""
        return self.expected_markout_bps > 0


class FillProbabilityModel:
    """
    Calculates fill probability and expected markout.
    
    Model:
    P(fill) = base_rate * queue_factor * ofi_factor * spread_factor * volatility_penalty
    E[markout | fill] = f(queue_position, OFI, spread, microprice_divergence)
    """
    
    def __init__(
        self,
        base_fill_rate: float = 0.5,
        queue_decay_rate: float = 0.1,
        ofi_sensitivity: float = 0.3,
        spread_sensitivity: float = 0.2,
        toxicity_threshold_bps: float = -5.0,
    ):
        self.queue_model = QueueModel(
            base_fill_rate=base_fill_rate,
            queue_decay_rate=queue_decay_rate,
            ofi_sensitivity=ofi_sensitivity,
            spread_sensitivity=spread_sensitivity,
        )
        self.toxicity_threshold_bps = toxicity_threshold_bps
    
    def calculate_fill_probability(
        self,
        factors: FillProbabilityFactors,
    ) -> FillOutcome:
        """
        Calculate fill probability and expected markout.
        
        Returns fill outcome with probability, expected fill time, and toxicity score.
        """
        # Calculate fill probability
        fill_prob = self.queue_model.calculate_fill_probability(
            queue_position=factors.queue_position,
            ofi=factors.ofi,
            spread_bps=factors.spread_bps,
            volatility_bps=factors.volatility_bps,
        )
        
        # Calculate expected fill time
        metrics = QueueMetrics(
            price=factors.queue_position.price,
            total_volume=factors.queue_position.queue_depth,
            num_orders=1,
            avg_order_size=Decimal(factors.queue_position.size),
            queue_turnover_rate=0.5,
            cancel_rate=0.1,
            trade_through_rate=0.05,
        )
        expected_fill_time = self.queue_model.calculate_expected_fill_time(
            queue_position=factors.queue_position,
            metrics=metrics,
        )
        
        # Calculate expected markout
        expected_markout = self._calculate_expected_markout(factors)
        
        # Calculate toxicity score
        toxicity_score = self._calculate_toxicity_score(factors, expected_markout)
        
        return FillOutcome(
            fill_probability=fill_prob,
            expected_fill_time_ms=expected_fill_time,
            expected_markout_bps=expected_markout,
            toxicity_score=toxicity_score,
            is_toxic=expected_markout < self.toxicity_threshold_bps,
        )
    
    def _calculate_expected_markout(
        self,
        factors: FillProbabilityFactors,
    ) -> float:
        """
        Calculate expected markout in basis points.
        
        Model:
        E[markout] = base_edge * ofi_factor * spread_factor - toxicity_penalty
        """
        # Base edge from spread capture
        base_edge = factors.spread_bps / 2  # Capture half the spread on average
        
        # OFI factor: positive OFI increases markout for fills
        ofi_factor = 1.0 + factors.ofi * 2.0
        
        # Microprice divergence penalty
        microprice_penalty = abs(factors.microprice_divergence) * 10.0
        
        # Volatility penalty
        volatility_penalty = factors.volatility_bps * 0.5
        
        # Time priority penalty (older quotes have worse markout)
        time_priority_penalty = (1.0 - factors.time_priority_score) * 2.0
        
        expected_markout = (
            base_edge * ofi_factor
            - microprice_penalty
            - volatility_penalty
            - time_priority_penalty
        )
        
        return expected_markout
    
    def _calculate_toxicity_score(
        self,
        factors: FillProbabilityFactors,
        expected_markout: float,
    ) -> float:
        """
        Calculate toxicity score.
        
        Higher = more toxic.
        """
        # Base toxicity from expected markout
        if expected_markout < 0:
            markout_toxicity = abs(expected_markout)
        else:
            markout_toxicity = 0.0
        
        # Queue position toxicity (deeper queue = more toxic)
        queue_toxicity = factors.queue_position.rank * 0.5
        
        # OFI toxicity (extreme OFI = toxic flow)
        ofi_toxicity = abs(factors.ofi) * 2.0
        
        # Microprice divergence toxicity
        microprice_toxicity = abs(factors.microprice_divergence) * 5.0
        
        total_toxicity = (
            markout_toxicity
            + queue_toxicity
            + ofi_toxicity
            + microprice_toxicity
        )
        
        return total_toxicity
    
    def batch_calculate(
        self,
        factors_list: List[FillProbabilityFactors],
    ) -> List[FillOutcome]:
        """
        Calculate fill probability for multiple scenarios.
        
        Useful for Monte Carlo simulation.
        """
        return [self.calculate_fill_probability(f) for f in factors_list]
    
    def simulate_fill_distribution(
        self,
        factors: FillProbabilityFactors,
        num_simulations: int = 1000,
    ) -> Dict[str, float]:
        """
        Monte Carlo simulation of fill outcomes.
        
        Returns distribution statistics.
        """
        outcomes = []
        
        for _ in range(num_simulations):
            outcome = self.calculate_fill_probability(factors)
            
            # Simulate fill/no-fill based on probability
            import random
            if random.random() < outcome.fill_probability:
                outcomes.append(outcome.expected_markout_bps)
            else:
                outcomes.append(0.0)  # No fill, no markout
        
        if not outcomes:
            return {}
        
        return {
            "mean": np.mean(outcomes),
            "std": np.std(outcomes),
            "min": np.min(outcomes),
            "max": np.max(outcomes),
            "percentile_5": np.percentile(outcomes, 5),
            "percentile_25": np.percentile(outcomes, 25),
            "percentile_50": np.percentile(outcomes, 50),
            "percentile_75": np.percentile(outcomes, 75),
            "percentile_95": np.percentile(outcomes, 95),
        }
