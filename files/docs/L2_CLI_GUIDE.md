# L2 Data CLI Guide

## Overview

DepthOS provides CLI commands for recording and replaying L2 market data from Gate.io futures.

## Commands

### Record L2 Data

Record real L2 orderbook and trade data from Gate.io futures.

```bash
python -m app.main record-l2 \
    --symbols SHIB_USDT PEPE_USDT FLOKI_USDT \
    --duration 86400 \
    --output-dir data/l2 \
    --depth-levels 20
```

**Arguments:**
- `--symbols`: Contract symbols to record (required)
- `--duration`: Recording duration in seconds (default: indefinite)
- `--output-dir`: Output directory for recorded data (default: `data/l2`)
- `--depth-levels`: Number of orderbook levels to record (default: 20)

**Output:**
- `orderbook_YYYYMMDD_HHMMSS.jsonl`: Full depth orderbook snapshots
- `trades_YYYYMMDD_HHMMSS.jsonl`: Trade events with aggressor side

**Example:**
```bash
# Record 24 hours of SHIB_USDT data
python -m app.main record-l2 \
    --symbols SHIB_USDT \
    --duration 86400 \
    --output-dir data/l2/shib
```

### Replay L2 Data

Replay recorded L2 data with markout analysis.

```bash
python -m app.main replay-l2 \
    --input data/l2/shib \
    --markout 100ms 1s 5s \
    --latency-ms 50 \
    --slippage-bps 5
```

**Arguments:**
- `--input`: Path to L2 JSONL file or directory (required)
- `--markout`: Markout intervals for analysis (default: `100ms 1s 5s`)
- `--latency-ms`: Simulated latency in milliseconds (default: 50)
- `--slippage-bps`: Simulated slippage in basis points (default: 5)

**Output:**
- Replay summary with fill statistics
- Performance metrics report
- Alpha metrics (OFI, fill toxicity, realized edge)
- **Markout analysis** (new):
  - Average markout at each interval (bps)
  - Positive markout percentage
  - Negative markout percentage
  - Toxicity score
- **Toxic flow analysis** (new):
  - Total toxic signals detected
  - Average toxicity score
  - Signal types (microprice divergence, OFI spike, spread collapse, quote fade)
  - Recommended actions (hold, widen, flatten, cancel)

**Microstructure Realism Features:**
- Queue position modeling (rank, volume ahead, queue depth)
- Fill probability calculation based on queue position, OFI, spread, volatility
- Toxic flow detection (microprice divergence, OFI spikes, spread collapse)
- Expected markout calculation
- Queue evolution simulation

**Example:**
```bash
# Replay recorded SHIB data with custom latency and all models enabled
python -m app.main replay-l2 \
    --input data/l2/shib \
    --markout 50ms 200ms 1s \
    --latency-ms 30 \
    --slippage-bps 3
```

**Disable specific models:**
```bash
# Disable queue model (simpler fill logic)
python -m app.main replay-l2 \
    --input data/l2/shib \
    --no-queue-model

# Disable toxic flow detection
python -m app.main replay-l2 \
    --input data/l2/shib \
    --no-toxic-detection

# Disable fill probability model
python -m app.main replay-l2 \
    --input data/l2/shib \
    --no-fill-probability
```

## Metrics

The replay engine calculates:

**Return Metrics:**
- Total PnL, Gross PnL, Net PnL
- Total fees, Total notional
- Realized edge (bps)
- Adverse selection (bps)

**Risk Metrics:**
- Sharpe ratio, Sortino ratio
- Max drawdown, Max drawdown %

**Trading Metrics:**
- Total trades, Win rate
- Profit factor, Avg trade PnL

**Inventory Metrics:**
- Max position, Avg position
- Inventory skew

**Alpha Metrics:**
- Order Flow Imbalance (OFI)
- Fill toxicity
- Maker fill ratio
- Spread capture efficiency
- Quote survival time

**Markout Analysis:**
- Average markout at each interval (100ms, 1s, 5s, etc.)
- Positive markout percentage (fills that were profitable)
- Negative markout percentage (fills that were toxic)
- Toxicity score (absolute average markout in bps)

**Microstructure Realism Metrics:**
- Queue position (rank, volume ahead, queue depth)
- Fill probability (P(fill | queue_position, OFI, spread, volatility))
- Expected markout (E[markout | fill])
- Toxic flow signals (microprice divergence, OFI spikes, spread collapse)
- Queue evolution (depletion rate, cancel rate)

### Understanding Markout Analysis

Markout analysis measures how the price moves after a fill, which helps detect adverse selection and toxic flow.

**How it works:**
1. For each fill, find the mid price at markout intervals (e.g., 100ms, 1s, 5s later)
2. Calculate the price change from fill price to future price
3. Aggregate statistics across all fills

**Interpretation:**
- **Positive average markout**: Fills tend to be profitable (good alpha)
- **Negative average markout**: Fills tend to be toxic (picked off)
- **High toxicity score**: Significant adverse selection
- **Low positive percentage**: Most fills are losing money

**Example output:**
```
markout_analysis:
  100ms:
    avg_markout_bps: -2.5
    positive_pct: 35.0
    negative_pct: 65.0
    toxicity_score: 2.5
  1s:
    avg_markout_bps: -1.8
    positive_pct: 40.0
    negative_pct: 60.0
    toxicity_score: 1.8
```

This indicates toxic flow - fills are losing money on average.

### Understanding Microstructure Realism

The replay engine now supports microstructure-deterministic simulation, not just state-deterministic.

**State-deterministic (old):**
```python
if touched => probably filled
```

**Microstructure-deterministic (new):**
```python
if touched:
    maybe queue survives
    maybe hidden liquidity jumps
    maybe toxic sweep skips you
    maybe you are last in queue
    maybe spread collapses
```

**Queue Position Modeling:**
- Calculates rank in queue (0 = first)
- Measures volume ahead and behind
- Simulates queue evolution over time
- Estimates expected fill time

**Fill Probability Model:**
```
P(fill) = base_rate * queue_factor * ofi_factor * spread_factor * volatility_penalty
```

Factors:
- Queue position (deeper queue = lower probability)
- Order Flow Imbalance (positive OFI = higher fill probability for bids)
- Spread (wider spread = higher fill probability)
- Volatility (high volatility = lower fill probability due to stale quotes)

**Toxic Flow Detection:**
- Microprice divergence (informed flow)
- OFI spikes (aggressive flow)
- Spread collapse (adverse selection)
- Quote fade (stale quotes)

Recommended actions:
- **hold**: Maintain current quotes
- **widen**: Widen quotes to reduce toxicity
- **flatten**: Reduce position exposure
- **cancel**: Cancel all quotes (severe toxicity)

## Workflow

### Complete Validation Workflow

```bash
# 1. Record L2 data (24 hours)
python -m app.main record-l2 \
    --symbols SHIB_USDT PEPE_USDT \
    --duration 86400 \
    --output-dir data/l2

# 2. Replay with markout analysis
python -m app.main replay-l2 \
    --input data/l2 \
    --markout 100ms 1s 5s \
    --latency-ms 50 \
    --slippage-bps 5

# 3. Analyze results
# Check if:
# - Realized edge > 2 bps
# - Fill toxicity < 5 bps
# - Maker fill ratio > 80%
# - Sharpe ratio > 1.0
```

### Profitability Validation Criteria

**No profitability claim until:**
1. Real L2 replay shows positive edge after:
   - Fees (0.02% maker fee)
   - Latency (50ms realistic)
   - Slippage (5 bps)
   - Adverse selection (toxic flow)

2. Metrics thresholds:
   - Realized edge > 2 bps
   - Fill toxicity < 5 bps
   - Maker fill ratio > 80%
   - Sharpe ratio > 1.0
   - Max drawdown < 10%
   - **Markout analysis shows positive average markout** at 1s interval
   - **Toxicity score < 5 bps** at all markout intervals

## Notes

- Recording requires Gate.io WebSocket connection
- Replay works offline with recorded data
- Use `Ctrl-C` to stop indefinite recording
- Data stored in JSONL for efficient parsing
- Exchange timestamps preserved for deterministic replay
