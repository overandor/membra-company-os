# LLM Alpha Judge + Real-Time Verification Loop

## Overview

LLM-based alpha signal generation with real-time verification. The LLM acts as an **auditable alpha forecaster**, not an uncontrolled trader.

## Architecture

### Flow

```
600 symbols
→ compute all indicators
→ pass top filtered candidates to Ollama
→ Ollama chooses entries
→ record prediction + reasoning
→ send micro-burst / shadow order
→ verify markout in real time
→ score Ollama accuracy
→ promote, demote, or blacklist signal patterns
```

### Critical Rule

**LLM recommends. Risk engine decides. OMS executes only if risk passes.**

This ensures safety and prevents uncontrolled trading.

## Modules

### 1. Ollama Alpha Judge (`app/llm/ollama_alpha_judge.py`)

Evaluates market conditions and recommends trading entries using Ollama LLM.

**Key Features:**
- Evaluates 600 symbols
- Computes market indicators
- Passes top candidates to Ollama
- Gets LLM recommendations with reasoning
- Records predictions with confidence scores

**Usage:**
```python
from app.llm.ollama_alpha_judge import OllamaAlphaJudge, MarketIndicators

judge = OllamaAlphaJudge(
    ollama_url="http://localhost:11434",
    model="llama2",
)

candidates = [MarketIndicators(...), ...]
predictions = judge.evaluate_candidates(candidates, top_n=10)
```

### 2. Prediction Journal (`app/llm/prediction_journal.py`)

Records every LLM decision with reasoning, expected edge, and actual outcomes.

**Key Features:**
- Records LLM predictions with full reasoning
- Records actual observations (markout, toxicity)
- Calculates accuracy metrics
- Calculates profitability metrics
- Evaluates pass criteria
- Manages signal patterns (promote/demote/blacklist)

**Prediction Format:**
```json
{
  "timestamp": "2026-05-17T20:00:00Z",
  "symbol": "PEPE_USDT",
  "action": "maker_bid",
  "confidence": 0.74,
  "entry_reason": {
    "ofi": 0.61,
    "microprice_bias": "up",
    "spread_bps": 7.2,
    "toxicity_score": 2.1,
    "markout_1s": 1.8,
    "queue_survival_ms": 420
  },
  "expected_edge_bps": 2.4,
  "llm_reason": "Positive OFI, favorable microprice, low toxicity, stable spread."
}
```

**Observation Format:**
```json
{
  "timestamp": "2026-05-17T20:00:01Z",
  "symbol": "PEPE_USDT",
  "action": "maker_bid",
  "actual_markout_100ms_bps": 0.6,
  "actual_markout_1s_bps": 1.9,
  "actual_markout_5s_bps": -0.4,
  "realized_edge_bps": 1.2,
  "prediction_correct": true,
  "toxicity_observed": false
}
```

### 3. LLM Accuracy Analytics (`app/analytics/llm_accuracy.py`)

Calculates LLM accuracy, profitability, and signal pattern performance.

**Key Metrics:**

**Accuracy:**
```python
llm_accuracy = correct_positive_markouts / total_llm_entries
```

**Profitability:**
```python
llm_edge_bps = sum(realized_pnl_after_fees) / gross_notional * 10000
```

**Pass Criteria:**
- LLM win rate > 55%
- avg markout_1s > 0
- realized_edge_bps > 2
- toxicity_score < 5 bps
- max drawdown < 10%

**Signal Pattern Analysis:**
- Groups predictions by signal characteristics
- Evaluates performance per pattern
- Promotes high-performing patterns
- Demotes mediocre patterns
- Blacklists poor-performing patterns

### 4. LLM Micro-Burst Strategy (`app/strategy/llm_micro_burst.py`)

Sends micro-burst/shadow orders based on LLM recommendations.

**Key Features:**
- Executes orders based on LLM predictions
- Risk engine check before execution
- Shadow mode for testing
- Real-time markout verification
- Automatic cancellation
- Order tracking

**Risk Engine Checks:**
- Confidence threshold (> 0.5)
- Expected edge (> 1.0 bps)
- Toxicity score (< 5.0)
- Position limits
- Exposure limits
- Margin checks
- Kill switch

## Usage

### Setup Ollama

```bash
# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Pull model
ollama pull llama2

# Start Ollama server
ollama serve
```

### Run LLM Alpha Judge

```python
from app.llm.ollama_alpha_judge import OllamaAlphaJudge, MarketIndicators
from app.strategy.llm_micro_burst import LLMMicroBurst
from app.llm.prediction_journal import PredictionJournal

# Create journal
journal = PredictionJournal()

# Create judge
judge = OllamaAlphaJudge(
    ollama_url="http://localhost:11434",
    model="llama2",
    journal=journal,
)

# Create micro-burst strategy
strategy = LLMMicroBurst(
    ollama_judge=judge,
    max_order_size_usdt=Decimal("0.10"),
    shadow_mode=True,  # Start with shadow mode
)

# Create candidates
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
    # ... more candidates
]

# Execute micro-burst
predictions = await strategy.execute_micro_burst(candidates, top_n=10)

# Verify markouts
for prediction in predictions:
    observation = await strategy.verify_markout(prediction.symbol)
```

### Check Accuracy

```python
from app.analytics.llm_accuracy import LLMAccuracyAnalytics

analytics = LLMAccuracyAnalytics(journal)

# Get accuracy metrics
accuracy = analytics.calculate_llm_accuracy()
print(f"Accuracy: {accuracy['accuracy']:.2%}")

# Get profitability metrics
profitability = analytics.calculate_llm_edge()
print(f"LLM Edge: {profitability['llm_edge_bps']:.2f} bps")

# Evaluate pass criteria
criteria = analytics.evaluate_pass_criteria()
print(f"Pass criteria: {criteria}")

# Analyze signal patterns
patterns = analytics.analyze_signal_patterns()
for pattern_id, pattern in patterns.items():
    print(f"{pattern_id}: {pattern.status} (accuracy={pattern.accuracy:.2%})")
```

## Data Storage

### Journal Files

```
data/llm_journal/
├── predictions.jsonl    # LLM predictions
├── observations.jsonl   # Actual outcomes
└── patterns.json        # Signal patterns
```

### Format

Each line is a JSON object for easy streaming and analysis.

## Safety Features

### 1. Shadow Mode

Start with shadow mode to test without real trading:
```python
strategy = LLMMicroBurst(
    ollama_judge=judge,
    shadow_mode=True,  # No real orders
)
```

### 2. Risk Engine

Multiple layers of risk checks:
- Confidence threshold
- Expected edge threshold
- Toxicity threshold
- Position limits
- Exposure limits
- Margin checks
- Kill switch

### 3. Pass Criteria

LLM must meet all criteria before execution:
- LLM win rate > 55%
- avg markout_1s > 0
- realized_edge_bps > 2
- toxicity_score < 5 bps
- max drawdown < 10%

### 4. Signal Pattern Management

Automatically promotes/demotes/blacklists patterns:
- **Promoted**: win_rate > 60%, edge > 3 bps, drawdown < 5%
- **Blacklisted**: win_rate < 45%, edge < 0, drawdown > 15%
- **Demoted**: Between promoted and blacklisted

## Integration with DepthOS

This system integrates seamlessly with existing DepthOS components:

- **L2 Capture**: Provides real-time orderbook data
- **Replay Engine**: Tests predictions on historical data
- **Markout Analytics**: Verifies actual markouts
- **Toxicity Scoring**: Detects informed flow
- **Queue Model**: Estimates fill probability

## Next Steps

1. **Deploy Ollama**: Install and start Ollama server
2. **Test Shadow Mode**: Run in shadow mode to validate
3. **Collect Data**: Gather predictions and observations
4. **Analyze Accuracy**: Evaluate LLM performance
5. **Tune Thresholds**: Adjust pass criteria
6. **Enable Live Trading**: Disable shadow mode when ready

## Important Notes

- **LLM recommends, Risk engine decides, OMS executes only if risk passes**
- Always start with shadow mode
- Monitor accuracy metrics closely
- Adjust pass criteria based on performance
- Blacklist poor-performing patterns
- Promote high-performing patterns

## Troubleshooting

### Ollama Connection Failed

```bash
# Check Ollama is running
curl http://localhost:11434/api/tags

# Restart Ollama
ollama serve
```

### No Predictions

- Check candidate indicators are valid
- Verify Ollama model is loaded
- Check log for LLM response errors

### Low Accuracy

- Review pass criteria thresholds
- Analyze signal patterns
- Adjust LLM prompt
- Consider different LLM model
