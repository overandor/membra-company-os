"""
Ollama Alpha Judge - LLM-Based Alpha Signal Generation

Uses Ollama LLM to evaluate market conditions and recommend trading entries.
The LLM acts as an alpha forecaster, not an uncontrolled trader.
"""

import json
import logging
import requests
from dataclasses import dataclass
from decimal import Decimal
from typing import Dict, List, Optional

from app.llm.prediction_journal import (
    EntryReason,
    LLMPrediction,
    PredictionJournal,
)

log = logging.getLogger("ollama_alpha_judge")


@dataclass
class MarketIndicators:
    """Market indicators for LLM evaluation."""
    symbol: str
    ofi: float  # Order Flow Imbalance
    microprice: float
    mid_price: float
    spread_bps: float
    toxicity_score: float
    markout_1s: float
    markout_5s: float
    queue_survival_ms: int
    volume_ahead: int
    volume_behind: int
    volatility: float


class OllamaAlphaJudge:
    """
    LLM-based alpha signal generator.
    
    Evaluates market conditions and recommends trading entries.
    Important: LLM recommends, Risk engine decides, OMS executes only if risk passes.
    """
    
    def __init__(
        self,
        ollama_url: str = "http://localhost:11434",
        model: str = "llama2",
        journal: Optional[PredictionJournal] = None,
    ):
        self.ollama_url = ollama_url
        self.model = model
        self.journal = journal or PredictionJournal()
        
        # Pass criteria
        self.pass_criteria = {
            "llm_win_rate_gt_55": True,
            "avg_markout_1s_gt_0": True,
            "realized_edge_bps_gt_2": True,
            "toxicity_score_lt_5": True,
            "max_drawdown_lt_10": True,
        }
    
    def evaluate_candidates(
        self,
        candidates: List[MarketIndicators],
        top_n: int = 10,
    ) -> List[LLMPrediction]:
        """
        Evaluate candidate symbols and get LLM recommendations.
        
        Args:
            candidates: List of market indicators for candidate symbols
            top_n: Number of top candidates to pass to LLM
            
        Returns:
            List of LLM predictions
        """
        # Filter top candidates by expected edge
        sorted_candidates = sorted(
            candidates,
            key=lambda x: x.markout_1s,
            reverse=True,
        )
        top_candidates = sorted_candidates[:top_n]
        
        log.info(f"Evaluating {len(top_candidates)} top candidates with LLM")
        
        predictions = []
        for candidate in top_candidates:
            prediction = self._get_llm_prediction(candidate)
            if prediction:
                predictions.append(prediction)
                self.journal.record_prediction(prediction)
        
        return predictions
    
    def _get_llm_prediction(self, indicators: MarketIndicators) -> Optional[LLMPrediction]:
        """
        Get LLM prediction for a single candidate.
        
        Args:
            indicators: Market indicators for the symbol
            
        Returns:
            LLM prediction or None if LLM declines
        """
        # Build prompt for LLM
        prompt = self._build_prompt(indicators)
        
        try:
            response = self._call_ollama(prompt)
            
            # Parse LLM response
            prediction = self._parse_llm_response(response, indicators)
            
            if prediction:
                log.info(f"LLM prediction: {indicators.symbol} {prediction.action} "
                        f"confidence={prediction.confidence:.2f} "
                        f"expected_edge={prediction.expected_edge_bps:.2f}bps")
            
            return prediction
            
        except Exception as e:
            log.error(f"Failed to get LLM prediction for {indicators.symbol}: {e}")
            return None
    
    def _build_prompt(self, indicators: MarketIndicators) -> str:
        """Build prompt for LLM evaluation."""
        prompt = f"""You are a trading alpha forecaster. Evaluate the following market conditions and recommend whether to enter a position.

Symbol: {indicators.symbol}
Current Price: {indicators.mid_price}
Spread: {indicators.spread_bps:.2f} bps
Order Flow Imbalance (OFI): {indicators.ofi:.2f}
Microprice Bias: {"up" if indicators.microprice > indicators.mid_price else "down"}
Toxicity Score: {indicators.toxicity_score:.2f}
Markout 1s: {indicators.markout_1s:.2f} bps
Markout 5s: {indicators.markout_5s:.2f} bps
Queue Survival: {indicators.queue_survival_ms} ms
Volume Ahead: {indicators.volume_ahead}
Volume Behind: {indicators.volume_behind}
Volatility: {indicators.volatility:.2f}

Based on these indicators, recommend one of the following actions:
1. "maker_bid" - Place a bid (buy limit order)
2. "maker_ask" - Place an ask (sell limit order)
3. "no_action" - Do not trade

Provide your response in JSON format:
{{
  "action": "maker_bid" | "maker_ask" | "no_action",
  "confidence": 0.0-1.0,
  "expected_edge_bps": float,
  "reason": "brief explanation of your decision"
}}

If toxicity_score > 5.0 or markout_1s < 0, recommend "no_action".
"""
        return prompt
    
    def _call_ollama(self, prompt: str) -> str:
        """Call Ollama API."""
        url = f"{self.ollama_url}/api/generate"
        
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "format": "json",
        }
        
        response = requests.post(url, json=payload, timeout=30)
        response.raise_for_status()
        
        result = response.json()
        return result.get("response", "")
    
    def _parse_llm_response(
        self,
        response: str,
        indicators: MarketIndicators,
    ) -> Optional[LLMPrediction]:
        """Parse LLM response into prediction."""
        try:
            # Try to extract JSON from response
            start_idx = response.find("{")
            end_idx = response.rfind("}") + 1
            
            if start_idx == -1 or end_idx == 0:
                log.error(f"No JSON found in LLM response: {response}")
                return None
            
            json_str = response[start_idx:end_idx]
            data = json.loads(json_str)
            
            action = data.get("action", "no_action")
            confidence = data.get("confidence", 0.0)
            expected_edge = data.get("expected_edge_bps", 0.0)
            reason = data.get("reason", "")
            
            # If LLM recommends no action, return None
            if action == "no_action":
                return None
            
            # Build entry reason
            entry_reason = {
                "ofi": indicators.ofi,
                "microprice_bias": "up" if indicators.microprice > indicators.mid_price else "down",
                "spread_bps": indicators.spread_bps,
                "toxicity_score": indicators.toxicity_score,
                "markout_1s": indicators.markout_1s,
                "queue_survival_ms": indicators.queue_survival_ms,
            }
            
            # Create prediction
            from datetime import datetime, timezone
            prediction = LLMPrediction(
                timestamp=datetime.now(timezone.utc).isoformat(),
                symbol=indicators.symbol,
                action=action,
                confidence=confidence,
                entry_reason=entry_reason,
                expected_edge_bps=expected_edge,
                llm_reason=reason,
            )
            
            return prediction
            
        except Exception as e:
            log.error(f"Failed to parse LLM response: {e}")
            return None
    
    def check_pass_criteria(self) -> bool:
        """Check if LLM passes pass criteria."""
        criteria = self.journal.evaluate_pass_criteria()
        
        all_pass = all(criteria.values())
        
        if not all_pass:
            log.warning(f"LLM does not pass all criteria: {criteria}")
        
        return all_pass
    
    def get_accuracy_metrics(self) -> Dict[str, float]:
        """Get LLM accuracy metrics."""
        return self.journal.calculate_accuracy()
    
    def get_profitability_metrics(self) -> Dict[str, float]:
        """Get LLM profitability metrics."""
        return self.journal.calculate_profitability()
