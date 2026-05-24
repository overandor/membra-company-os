"""
Prediction Journal - LLM Alpha Decision Recording

Records every LLM decision with reasoning, expected edge, and actual outcomes.
Provides auditable alpha forecaster capability.
"""

import json
import logging
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional
from decimal import Decimal

log = logging.getLogger("prediction_journal")


@dataclass
class EntryReason:
    """Reasoning factors for LLM decision."""
    ofi: float  # Order Flow Imbalance
    microprice_bias: str  # "up" or "down"
    spread_bps: float
    toxicity_score: float
    markout_1s: float
    queue_survival_ms: int


@dataclass
class LLMPrediction:
    """LLM alpha prediction."""
    timestamp: str
    symbol: str
    action: str  # "maker_bid", "maker_ask", "taker_buy", "taker_sell"
    confidence: float  # 0-1
    entry_reason: Dict
    expected_edge_bps: float
    llm_reason: str
    
    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class LLMObservation:
    """Actual outcome of LLM prediction."""
    timestamp: str
    symbol: str
    action: str
    actual_markout_100ms_bps: float
    actual_markout_1s_bps: float
    actual_markout_5s_bps: float
    realized_edge_bps: float
    prediction_correct: bool
    toxicity_observed: bool
    
    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class LLMSignalPattern:
    """Signal pattern for promotion/demotion/blacklisting."""
    pattern_id: str
    description: str
    accuracy: float
    avg_edge_bps: float
    win_rate: float
    toxicity_avg: float
    max_drawdown: float
    status: str  # "promoted", "demoted", "blacklisted"
    sample_count: int


class PredictionJournal:
    """
    Records and verifies LLM alpha predictions.
    
    Provides auditable alpha forecaster capability with real-time verification.
    """
    
    def __init__(self, journal_dir: str = "data/llm_journal"):
        self.journal_dir = Path(journal_dir)
        self.journal_dir.mkdir(parents=True, exist_ok=True)
        
        self.predictions_file = self.journal_dir / "predictions.jsonl"
        self.observations_file = self.journal_dir / "observations.jsonl"
        self.patterns_file = self.journal_dir / "patterns.json"
        
        # Signal patterns registry
        self.signal_patterns: Dict[str, LLMSignalPattern] = {}
        self._load_patterns()
    
    def record_prediction(self, prediction: LLMPrediction) -> None:
        """Record an LLM prediction."""
        with open(self.predictions_file, "a") as f:
            f.write(json.dumps(prediction.to_dict()) + "\n")
        
        log.info(f"Recorded LLM prediction: {prediction.symbol} {prediction.action} "
                f"confidence={prediction.confidence:.2f} expected_edge={prediction.expected_edge_bps:.2f}bps")
    
    def record_observation(self, observation: LLMObservation) -> None:
        """Record actual outcome of prediction."""
        with open(self.observations_file, "a") as f:
            f.write(json.dumps(observation.to_dict()) + "\n")
        
        log.info(f"Recorded observation: {observation.symbol} {observation.action} "
                f"markout_1s={observation.actual_markout_1s_bps:.2f}bps "
                f"realized_edge={observation.realized_edge_bps:.2f}bps "
                f"correct={observation.prediction_correct}")
    
    def get_predictions(self, symbol: Optional[str] = None, limit: int = 100) -> List[LLMPrediction]:
        """Get recent predictions."""
        predictions = []
        
        with open(self.predictions_file, "r") as f:
            for line in f:
                data = json.loads(line)
                if symbol and data["symbol"] != symbol:
                    continue
                predictions.append(LLMPrediction(**data))
                if len(predictions) >= limit:
                    break
        
        return predictions
    
    def get_observations(self, symbol: Optional[str] = None, limit: int = 100) -> List[LLMObservation]:
        """Get recent observations."""
        observations = []
        
        if not self.observations_file.exists():
            return observations
        
        with open(self.observations_file, "r") as f:
            for line in f:
                data = json.loads(line)
                if symbol and data["symbol"] != symbol:
                    continue
                observations.append(LLMObservation(**data))
                if len(observations) >= limit:
                    break
        
        return observations
    
    def calculate_accuracy(self, window: int = 100) -> Dict[str, float]:
        """Calculate LLM accuracy metrics."""
        observations = self.get_observations(limit=window)
        
        if not observations:
            return {"accuracy": 0.0, "win_rate": 0.0, "avg_edge_bps": 0.0}
        
        correct = sum(1 for obs in observations if obs.prediction_correct)
        total = len(observations)
        
        win_rate = correct / total if total > 0 else 0.0
        avg_edge_bps = sum(obs.realized_edge_bps for obs in observations) / total if total > 0 else 0.0
        
        return {
            "accuracy": win_rate,
            "win_rate": win_rate,
            "avg_edge_bps": avg_edge_bps,
            "sample_count": total,
        }
    
    def calculate_profitability(self, window: int = 100) -> Dict[str, float]:
        """Calculate LLM profitability metrics."""
        observations = self.get_observations(limit=window)
        
        if not observations:
            return {"llm_edge_bps": 0.0, "gross_pnl": 0.0, "max_drawdown": 0.0}
        
        # Calculate realized edge
        total_edge = sum(obs.realized_edge_bps for obs in observations)
        avg_edge_bps = total_edge / len(observations) if observations else 0.0
        
        # Calculate max drawdown
        cumulative = []
        running = 0
        for obs in observations:
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
        
        return {
            "llm_edge_bps": avg_edge_bps,
            "gross_pnl": total_edge,
            "max_drawdown": max_dd,
            "sample_count": len(observations),
        }
    
    def evaluate_pass_criteria(self) -> Dict[str, bool]:
        """Evaluate if LLM passes pass criteria."""
        metrics = self.calculate_accuracy(window=100)
        profitability = self.calculate_profitability(window=100)
        
        observations = self.get_observations(limit=100)
        avg_toxicity = sum(obs.toxicity_observed for obs in observations) / len(observations) if observations else 0.0
        
        return {
            "llm_win_rate_gt_55": metrics["win_rate"] > 0.55,
            "avg_markout_1s_gt_0": metrics["avg_edge_bps"] > 0,
            "realized_edge_bps_gt_2": profitability["llm_edge_bps"] > 2.0,
            "toxicity_score_lt_5": avg_toxicity < 5.0,
            "max_drawdown_lt_10": profitability["max_drawdown"] < 10.0,
        }
    
    def update_signal_pattern(self, pattern_id: str, pattern: LLMSignalPattern) -> None:
        """Update signal pattern status."""
        self.signal_patterns[pattern_id] = pattern
        self._save_patterns()
    
    def _load_patterns(self) -> None:
        """Load signal patterns from file."""
        if self.patterns_file.exists():
            with open(self.patterns_file, "r") as f:
                data = json.load(f)
                for pattern_id, pattern_data in data.items():
                    self.signal_patterns[pattern_id] = LLMSignalPattern(**pattern_data)
    
    def _save_patterns(self) -> None:
        """Save signal patterns to file."""
        patterns_dict = {pid: asdict(pattern) for pid, pattern in self.signal_patterns.items()}
        with open(self.patterns_file, "w") as f:
            json.dump(patterns_dict, f, indent=2)
    
    def get_signal_patterns(self) -> Dict[str, LLMSignalPattern]:
        """Get all signal patterns."""
        return self.signal_patterns
