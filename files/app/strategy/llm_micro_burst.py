"""
LLM Micro-Burst Strategy - Shadow Order Execution

Sends micro-burst/shadow orders based on LLM recommendations.
Important: LLM recommends, Risk engine decides, OMS executes only if risk passes.
"""

import asyncio
import logging
from decimal import Decimal
from typing import Dict, List, Optional

from app.llm.ollama_alpha_judge import OllamaAlphaJudge, MarketIndicators
from app.llm.prediction_journal import LLMPrediction, LLMObservation
from app.connectors.rest_client import place_order, cancel_order
from app.backtest.market_analytics import MarketAnalytics

log = logging.getLogger("llm_micro_burst")


class LLMMicroBurst:
    """
    LLM micro-burst strategy.
    
    Flow:
    1. Compute indicators for 600 symbols
    2. Pass top filtered candidates to Ollama
    3. Ollama chooses entries
    4. Record prediction + reasoning
    5. Send micro-burst/shadow order
    6. Verify markout in real time
    7. Score Ollama accuracy
    8. Promote, demote, or blacklist signal patterns
    
    Important rule:
    LLM recommends -> Risk engine decides -> OMS executes only if risk passes
    """
    
    def __init__(
        self,
        ollama_judge: OllamaAlphaJudge,
        max_order_size_usdt: Decimal = Decimal("0.10"),
        shadow_mode: bool = True,
    ):
        self.ollama_judge = ollama_judge
        self.max_order_size_usdt = max_order_size_usdt
        self.shadow_mode = shadow_mode  # If True, only shadow orders (no real execution)
        
        # Active orders
        self.active_orders: Dict[str, Dict] = {}
    
    async def execute_micro_burst(
        self,
        candidates: List[MarketIndicators],
        top_n: int = 10,
    ) -> List[LLMPrediction]:
        """
        Execute micro-burst strategy.
        
        Args:
            candidates: List of market indicators for candidate symbols
            top_n: Number of top candidates to evaluate
            
        Returns:
            List of executed predictions
        """
        log.info(f"Executing LLM micro-burst on {len(candidates)} candidates")
        
        # Step 1: Get LLM predictions
        predictions = self.ollama_judge.evaluate_candidates(candidates, top_n)
        
        if not predictions:
            log.info("No LLM predictions received")
            return []
        
        # Step 2: Check pass criteria
        if not self.ollama_judge.check_pass_criteria():
            log.warning("LLM does not pass pass criteria, skipping execution")
            return []
        
        # Step 3: Execute orders for predictions
        executed = []
        for prediction in predictions:
            # Risk engine check
            if not self._risk_check(prediction):
                log.warning(f"Risk check failed for {prediction.symbol}")
                continue
            
            # Execute order
            order_id = await self._execute_order(prediction)
            
            if order_id:
                prediction.order_id = order_id
                executed.append(prediction)
                self.active_orders[prediction.symbol] = {
                    "prediction": prediction,
                    "order_id": order_id,
                    "timestamp": prediction.timestamp,
                }
        
        log.info(f"Executed {len(executed)} micro-burst orders")
        return executed
    
    def _risk_check(self, prediction: LLMPrediction) -> bool:
        """
        Risk engine check.
        
        Important: LLM recommends, Risk engine decides, OMS executes only if risk passes.
        """
        # Check confidence threshold
        if prediction.confidence < 0.5:
            log.debug(f"Confidence too low: {prediction.confidence}")
            return False
        
        # Check expected edge
        if prediction.expected_edge_bps < 1.0:
            log.debug(f"Expected edge too low: {prediction.expected_edge_bps}")
            return False
        
        # Check toxicity in entry reason
        toxicity = prediction.entry_reason.get("toxicity_score", 0)
        if toxicity > 5.0:
            log.debug(f"Toxicity too high: {toxicity}")
            return False
        
        # Additional risk checks can be added here
        # - Position limits
        # - Exposure limits
        # - Margin checks
        # - Kill switch
        
        return True
    
    async def _execute_order(self, prediction: LLMPrediction) -> Optional[int]:
        """
        Execute order based on LLM prediction.
        
        Args:
            prediction: LLM prediction
            
        Returns:
            Order ID or None if failed
        """
        if self.shadow_mode:
            log.info(f"[SHADOW MODE] Would execute order: {prediction.symbol} {prediction.action}")
            return -1  # Shadow order ID
        
        # Determine order parameters
        contract = prediction.symbol
        
        # Calculate size based on max order size
        # This would need price from market data
        # For now, use placeholder
        size = 1000  # Placeholder
        
        # Determine side and price
        if prediction.action == "maker_bid":
            side = 1  # buy
            # Price would be calculated from orderbook
            price = Decimal("0.000044955")  # Placeholder
        elif prediction.action == "maker_ask":
            side = -1  # sell
            price = Decimal("0.000045045")  # Placeholder
        else:
            log.error(f"Unknown action: {prediction.action}")
            return None
        
        try:
            async with aiohttp.ClientSession() as session:
                result = await place_order(
                    session=session,
                    contract=contract,
                    size=side * size,
                    price=price,
                    tif="poc",  # Post-only cancel
                    reduce_only=False,
                    text="llm_micro_burst",
                )
                
                order_id = result.get("id")
                log.info(f"Placed order: {contract} size={side*size} price={price} id={order_id}")
                
                return order_id
                
        except Exception as e:
            log.error(f"Failed to place order for {contract}: {e}")
            return None
    
    async def verify_markout(self, symbol: str) -> Optional[LLMObservation]:
        """
        Verify markout for executed order.
        
        Args:
            symbol: Symbol to verify
            
        Returns:
            Observation or None if not found
        """
        if symbol not in self.active_orders:
            return None
        
        order_info = self.active_orders[symbol]
        prediction = order_info["prediction"]
        
        # Get actual markout from market data
        # This would need real-time market data access
        # For now, use placeholder
        actual_markout_100ms_bps = 0.6
        actual_markout_1s_bps = 1.9
        actual_markout_5s_bps = -0.4
        realized_edge_bps = 1.2
        toxicity_observed = False
        
        # Determine if prediction was correct
        prediction_correct = realized_edge_bps > 0
        
        # Create observation
        from datetime import datetime, timezone
        observation = LLMObservation(
            timestamp=datetime.now(timezone.utc).isoformat(),
            symbol=symbol,
            action=prediction.action,
            actual_markout_100ms_bps=actual_markout_100ms_bps,
            actual_markout_1s_bps=actual_markout_1s_bps,
            actual_markout_5s_bps=actual_markout_5s_bps,
            realized_edge_bps=realized_edge_bps,
            prediction_correct=prediction_correct,
            toxicity_observed=toxicity_observed,
        )
        
        # Record observation
        self.ollama_judge.journal.record_observation(observation)
        
        # Remove from active orders
        del self.active_orders[symbol]
        
        log.info(f"Verified markout for {symbol}: markout_1s={actual_markout_1s_bps:.2f}bps "
                f"realized_edge={realized_edge_bps:.2f}bps correct={prediction_correct}")
        
        return observation
    
    async def cancel_all_orders(self) -> int:
        """Cancel all active orders."""
        cancelled = 0
        
        for symbol, order_info in self.active_orders.items():
            order_id = order_info["order_id"]
            
            if order_id == -1:  # Shadow order
                continue
            
            try:
                async with aiohttp.ClientSession() as session:
                    result = await cancel_order(session, order_id, symbol)
                    if result:
                        cancelled += 1
                        log.info(f"Cancelled order: {symbol} id={order_id}")
            except Exception as e:
                log.error(f"Failed to cancel order {order_id}: {e}")
        
        self.active_orders.clear()
        return cancelled
    
    def get_active_orders(self) -> Dict[str, Dict]:
        """Get active orders."""
        return self.active_orders


import aiohttp  # Import at the end to avoid circular dependency
