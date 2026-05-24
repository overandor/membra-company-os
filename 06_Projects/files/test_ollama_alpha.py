"""
Test script for LLM Alpha Judge with Ollama.

Tests the complete flow:
1. Create market indicators
2. Get LLM predictions
3. Record predictions
4. Verify markout (simulated)
"""

import asyncio
import logging
from decimal import Decimal

from app.llm.ollama_alpha_judge import OllamaAlphaJudge, MarketIndicators
from app.llm.prediction_journal import PredictionJournal
from app.strategy.llm_micro_burst import LLMMicroBurst

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("test_ollama_alpha")


async def test_ollama_alpha_judge():
    """Test LLM Alpha Judge with Ollama."""
    print("=" * 60)
    print("TESTING LLM ALPHA JUDGE WITH OLLAMA")
    print("=" * 60)
    
    # Create journal
    journal = PredictionJournal()
    
    # Create judge
    judge = OllamaAlphaJudge(
        ollama_url="http://localhost:11434",
        model="llama2:latest",  # Use the correct model name
        journal=journal,
    )
    
    # Create micro-burst strategy
    strategy = LLMMicroBurst(
        ollama_judge=judge,
        max_order_size_usdt=Decimal("0.10"),
        shadow_mode=True,  # Shadow mode for testing
    )
    
    # Create test candidates
    candidates = [
        MarketIndicators(
            symbol="PEPE_USDT",
            ofi=0.61,
            microprice=0.0000081,
            mid_price=0.0000080,
            spread_bps=7.2,
            toxicity_score=2.1,
            markout_1s=1.8,
            markout_5s=-0.4,
            queue_survival_ms=420,
            volume_ahead=10000,
            volume_behind=5000,
            volatility=0.15,
        ),
        MarketIndicators(
            symbol="SHIB_USDT",
            ofi=0.45,
            microprice=0.0000451,
            mid_price=0.0000450,
            spread_bps=8.5,
            toxicity_score=3.2,
            markout_1s=0.8,
            markout_5s=0.2,
            queue_survival_ms=350,
            volume_ahead=15000,
            volume_behind=8000,
            volatility=0.12,
        ),
        MarketIndicators(
            symbol="DOGE_USDT",
            ofi=-0.2,
            microprice=0.1499,
            mid_price=0.1500,
            spread_bps=5.0,
            toxicity_score=1.5,
            markout_1s=-0.5,
            markout_5s=-1.2,
            queue_survival_ms=500,
            volume_ahead=5000,
            volume_behind=3000,
            volatility=0.08,
        ),
    ]
    
    print(f"\nCreated {len(candidates)} test candidates")
    
    # Execute micro-burst
    print("\nExecuting LLM micro-burst...")
    predictions = await strategy.execute_micro_burst(candidates, top_n=3)
    
    print(f"\nReceived {len(predictions)} LLM predictions")
    
    for pred in predictions:
        print(f"\nPrediction:")
        print(f"  Symbol: {pred.symbol}")
        print(f"  Action: {pred.action}")
        print(f"  Confidence: {pred.confidence:.2f}")
        print(f"  Expected Edge: {pred.expected_edge_bps:.2f} bps")
        print(f"  Reason: {pred.llm_reason}")
    
    # Check pass criteria
    print("\nChecking pass criteria...")
    criteria = judge.check_pass_criteria()
    print(f"Pass criteria: {criteria}")
    
    # Get accuracy metrics
    print("\nGetting accuracy metrics...")
    accuracy = judge.get_accuracy_metrics()
    print(f"Accuracy metrics: {accuracy}")
    
    # Get profitability metrics
    print("\nGetting profitability metrics...")
    profitability = judge.get_profitability_metrics()
    print(f"Profitability metrics: {profitability}")
    
    print("\n" + "=" * 60)
    print("TEST COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_ollama_alpha_judge())
