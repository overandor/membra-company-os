"""
LLM Accuracy Analytics - Scoring and Evaluation

Calculates LLM accuracy, profitability, and signal pattern performance.
"""

import logging
from typing import Dict, List, Optional
from collections import defaultdict

from app.llm.prediction_journal import (
    PredictionJournal,
    LLMPrediction,
    LLMObservation,
    LLMSignalPattern,
)

log = logging.getLogger("llm_accuracy")


class LLMAccuracyAnalytics:
    """
    Calculates LLM accuracy and profitability metrics.
    
    Provides scoring for:
    - LLM accuracy (correct_positive_markouts / total_llm_entries)
    - LLM edge (sum(realized_pnl_after_fees) / gross_notional * 10000)
    """
    
    def __init__(self, journal: PredictionJournal):
        self.journal = journal
    
    def calculate_llm_accuracy(self, window: int = 100) -> Dict[str, float]:
        """
        Calculate LLM accuracy.
        
        Formula: correct_positive_markouts / total_llm_entries
        """
        observations = self.journal.get_observations(limit=window)
        
        if not observations:
            return {
                "accuracy": 0.0,
                "correct_positive_markouts": 0,
                "total_llm_entries": 0,
            }
        
        correct_positive = sum(
            1 for obs in observations
            if obs.prediction_correct and obs.actual_markout_1s_bps > 0
        )
        total = len(observations)
        
        accuracy = correct_positive / total if total > 0 else 0.0
        
        return {
            "accuracy": accuracy,
            "correct_positive_markouts": correct_positive,
            "total_llm_entries": total,
        }
    
    def calculate_llm_edge(self, window: int = 100) -> Dict[str, float]:
        """
        Calculate LLM edge in basis points.
        
        Formula: sum(realized_pnl_after_fees) / gross_notional * 10000
        """
        observations = self.journal.get_observations(limit=window)
        
        if not observations:
            return {
                "llm_edge_bps": 0.0,
                "total_realized_pnl": 0.0,
                "sample_count": 0,
            }
        
        # Sum realized edge (already in bps)
        total_edge = sum(obs.realized_edge_bps for obs in observations)
        avg_edge = total_edge / len(observations) if observations else 0.0
        
        return {
            "llm_edge_bps": avg_edge,
            "total_realized_pnl": total_edge,
            "sample_count": len(observations),
        }
    
    def calculate_win_rate(self, window: int = 100) -> Dict[str, float]:
        """Calculate LLM win rate."""
        observations = self.journal.get_observations(limit=window)
        
        if not observations:
            return {"win_rate": 0.0, "wins": 0, "total": 0}
        
        wins = sum(1 for obs in observations if obs.prediction_correct)
        total = len(observations)
        
        win_rate = wins / total if total > 0 else 0.0
        
        return {
            "win_rate": win_rate,
            "wins": wins,
            "total": total,
        }
    
    def calculate_toxicity_metrics(self, window: int = 100) -> Dict[str, float]:
        """Calculate toxicity metrics."""
        observations = self.journal.get_observations(limit=window)
        
        if not observations:
            return {
                "avg_toxicity": 0.0,
                "toxicity_rate": 0.0,
                "sample_count": 0,
            }
        
        toxic_count = sum(1 for obs in observations if obs.toxicity_observed)
        total = len(observations)
        
        return {
            "avg_toxicity": toxic_count / total if total > 0 else 0.0,
            "toxicity_rate": toxic_count / total if total > 0 else 0.0,
            "sample_count": total,
        }
    
    def calculate_drawdown(self, window: int = 100) -> Dict[str, float]:
        """Calculate maximum drawdown."""
        observations = self.journal.get_observations(limit=window)
        
        if not observations:
            return {"max_drawdown": 0.0, "sample_count": 0}
        
        # Calculate cumulative PnL
        cumulative = []
        running = 0.0
        for obs in observations:
            running += obs.realized_edge_bps
            cumulative.append(running)
        
        # Calculate max drawdown
        max_dd = 0.0
        peak = 0.0
        for val in cumulative:
            if val > peak:
                peak = val
            dd = peak - val
            if dd > max_dd:
                max_dd = dd
        
        return {
            "max_drawdown": max_dd,
            "sample_count": len(observations),
        }
    
    def evaluate_pass_criteria(self, window: int = 100) -> Dict[str, bool]:
        """
        Evaluate pass criteria.
        
        Pass criteria:
        - LLM win rate > 55%
        - avg markout_1s > 0
        - realized_edge_bps > 2
        - toxicity_score < 5 bps
        - max drawdown < 10%
        """
        accuracy = self.calculate_llm_accuracy(window)
        edge = self.calculate_llm_edge(window)
        toxicity = self.calculate_toxicity_metrics(window)
        drawdown = self.calculate_drawdown(window)
        
        return {
            "llm_win_rate_gt_55": accuracy["accuracy"] > 0.55,
            "avg_markout_1s_gt_0": edge["llm_edge_bps"] > 0,
            "realized_edge_bps_gt_2": edge["llm_edge_bps"] > 2.0,
            "toxicity_score_lt_5": toxicity["avg_toxicity"] < 5.0,
            "max_drawdown_lt_10": drawdown["max_drawdown"] < 10.0,
        }
    
    def analyze_signal_patterns(self, window: int = 100) -> Dict[str, LLMSignalPattern]:
        """
        Analyze signal patterns for promotion/demotion/blacklisting.
        
        Groups predictions by signal characteristics and evaluates performance.
        """
        predictions = self.journal.get_predictions(limit=window)
        observations = self.journal.get_observations(limit=window)
        
        # Group by signal pattern
        pattern_groups = defaultdict(lambda: {"predictions": [], "observations": []})
        
        for pred in predictions:
            # Create pattern ID based on key factors
            pattern_id = self._create_pattern_id(pred)
            pattern_groups[pattern_id]["predictions"].append(pred)
        
        for obs in observations:
            # Find corresponding prediction
            pattern_id = self._create_pattern_id_from_obs(obs)
            pattern_groups[pattern_id]["observations"].append(obs)
        
        # Analyze each pattern
        patterns = {}
        for pattern_id, group in pattern_groups.items():
            obs_list = group["observations"]
            
            if not obs_list:
                continue
            
            # Calculate metrics
            correct = sum(1 for obs in obs_list if obs.prediction_correct)
            total = len(obs_list)
            win_rate = correct / total if total > 0 else 0.0
            
            avg_edge = sum(obs.realized_edge_bps for obs in obs_list) / total if total > 0 else 0.0
            toxicity_avg = sum(1 for obs in obs_list if obs.toxicity_observed) / total if total > 0 else 0.0
            
            # Calculate max drawdown
            cumulative = []
            running = 0.0
            for obs in obs_list:
                running += obs.realized_edge_bps
                cumulative.append(running)
            
            max_dd = 0.0
            peak = 0.0
            for val in cumulative:
                if val > peak:
                    peak = val
                dd = peak - val
                if dd > max_dd:
                    max_dd = dd
            
            # Determine status
            if win_rate > 0.60 and avg_edge > 3.0 and max_dd < 5.0:
                status = "promoted"
            elif win_rate < 0.45 or avg_edge < 0 or max_dd > 15.0:
                status = "blacklisted"
            else:
                status = "demoted"
            
            patterns[pattern_id] = LLMSignalPattern(
                pattern_id=pattern_id,
                description=self._describe_pattern(pattern_id),
                accuracy=win_rate,
                avg_edge_bps=avg_edge,
                win_rate=win_rate,
                toxicity_avg=toxicity_avg,
                max_drawdown=max_dd,
                status=status,
                sample_count=total,
            )
        
        return patterns
    
    def _create_pattern_id(self, prediction: LLMPrediction) -> str:
        """Create pattern ID from prediction."""
        reason = prediction.entry_reason
        return f"{prediction.action}_{reason['ofi']:.1f}_{reason['toxicity_score']:.1f}"
    
    def _create_pattern_id_from_obs(self, observation: LLMObservation) -> str:
        """Create pattern ID from observation (simplified)."""
        return f"{observation.action}"
    
    def _describe_pattern(self, pattern_id: str) -> str:
        """Describe pattern in human-readable form."""
        parts = pattern_id.split("_")
        action = parts[0]
        return f"Action: {action}"
