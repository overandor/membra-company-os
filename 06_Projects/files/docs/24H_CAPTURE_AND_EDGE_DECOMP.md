# 24h L2 Capture and Edge Decomposition Guide

## Overview

This guide covers the 24h continuous L2 data capture for meme perps (SHIB, PEPE, FLOKI) and the edge decomposition pipeline that decomposes realized PnL into component terms.

## Critical Significance

**The transition from software correctness to microstructure falsification risk**

The most important capability added is:
```
fills → future price trajectory attribution
```

This enables empirical estimation of:
```
E[ΔP_{t+τ} | fill]
```

Which is the **core toxicity signal**:
- Positive markout = paid to provide liquidity
- Negative markout = informed flow selected quotes

This distinction **is the entire market-making business**.

## 24h L2 Capture

### Purpose

Capture 24 hours of continuous L2 orderbook and trade data for microstructure research on meme perps.

### Contracts

- **SHIB_USDT** - High volatility meme coin
- **PEPE_USDT** - High volatility meme coin
- **FLOKI_USDT** - High volatility meme coin

### Command

```bash
python -m app.main capture-24h \
    --contracts SHIB_USDT PEPE_USDT FLOKI_USDT \
    --output-dir data/l2_24h \
    --depth-levels 20
```

### Parameters

- `--contracts`: Contract symbols to capture (default: SHIB_PEPE_FLOKI)
- `--output-dir`: Output directory (default: data/l2_24h)
- `--depth-levels`: Orderbook depth levels (default: 20)
- `--duration-hours`: Duration in hours (default: 24)

### Output Structure

```
data/l2_24h/capture_YYYYMMDD_HHMMSS/
├── orderbook_YYYYMMDD_HHMMSS.jsonl
├── trades_YYYYMMDD_HHMMSS.jsonl
└── unified_YYYYMMDD_HHMMSS.jsonl
```

### Data Format

**Unified Event Stream (deterministic replay):**
```json
{
  "timestamp_ms": 1779048873521,
  "exchange_ts_ms": 1779048873393,
  "contract": "SHIB_USDT",
  "message_type": "trade",
  "side": "buy",
  "price": "0.000045",
  "size": 1000,
  "local_sequence": 1
}
```

**Message Types:**
- `snapshot` - Initial orderbook snapshot
- `update` - Incremental orderbook update
- `trade` - Trade event

**Key Fields:**
- `local_sequence` - Lossless event ordering
- `exchange_ts_ms` - Exchange timestamp
- `message_type` - Event classification

### Running in Background

```bash
nohup python -m app.main capture-24h \
    --contracts SHIB_USDT PEPE_USDT FLOKI_USDT \
    --output-dir data/l2_24h \
    > capture.log 2>&1 &
```

### Monitoring

```bash
# Check process
ps aux | grep capture-24h

# Check log
tail -f capture.log

# Check file sizes
ls -lh data/l2_24h/capture_*/
```

## Edge Decomposition Pipeline

### Purpose

Decompose realized PnL into component terms to understand true edge:
```
α = spread_capture - fees - toxicity - inventory_loss - latency_loss
```

### Command

```bash
python -m app.main edge-decomp \
    --data-dir data/l2_24h/capture_YYYYMMDD_HHMMSS \
    --quote-spread-bps 10.0 \
    --quote-size 1000
```

### Parameters

- `--data-dir`: L2 data directory (required)
- `--quote-spread-bps`: Quote spread in basis points (default: 10.0)
- `--quote-size`: Quote size (default: 1000)

### Pipeline Stages

```
raw L2
→ deterministic reconstruction
→ queue evolution
→ simulated order placement
→ fill attribution
→ markout analysis
→ toxicity scoring
→ inventory evolution
→ realized edge decomposition
```

### Edge Components

| Component | Description |
|-----------|-------------|
| `spread_capture_bps` | Gross edge from spread |
| `fees_bps` | Trading fees (maker/taker) |
| `toxicity_bps` | Adverse selection (negative markout) |
| `inventory_loss_bps` | Inventory decay loss |
| `latency_loss_bps` | Stale quote losses |
| `realized_edge_bps` | Net realized edge |

### Metrics Computed

| Metric | Purpose |
|--------|---------|
| `markout_100ms` | Immediate toxicity |
| `markout_1s` | Short-term adverse selection |
| `maker_fill_ratio` | Passive execution quality |
| `queue_survival_ms` | Queue realism |
| `realized_edge_bps` | True profitability |
| `inventory_half_life` | Inventory control quality |
| `spread_capture_bps` | Gross edge |
| `latency_loss_bps` | Infra penalty |

### Output Example

```
============================================================
EDGE DECOMPOSITION RESULTS
============================================================
Spread capture: 5.00 bps
Fees: 2.00 bps
Toxicity: 1.50 bps
Inventory loss: 0.50 bps
Latency loss: 0.10 bps
============================================================
REALIZED EDGE: 0.90 bps
============================================================
```

### Toxicity Classification

**Toxic Fill:** Informed flow selected quotes
- Immediate adverse price move against position
- Markout_100ms < -2.0 bps
- Markout_1s < -5.0 bps

**Non-Toxic Fill:** Normal market making
- Price moves favorably or stays flat
- Markout_100ms ≥ -2.0 bps

### Fill Attribution

Each fill is attributed with:
- Fill price and time
- Side and size
- Markouts at 100ms, 1s, 5s, 10s
- Toxicity classification (0-1 score)
- Queue metrics (ahead, behind, survival)
- Latency metrics (quote age, execution latency)

## Why This Matters

### Common Mistake

Most retail MM systems mistake:
```
gross spread capture
```
for:
```
actual alpha
```

### Reality

Without edge decomposition:
- Cannot separate spread capture from toxicity
- Cannot measure inventory decay
- Cannot quantify latency penalties
- Cannot determine true profitability

### With Edge Decomposition

- Isolate each component separately
- Identify which terms are profitable
- Optimize each component independently
- Make data-driven decisions

## Next Steps After 24h Capture

1. **Run edge decomposition** on captured data
2. **Analyze toxicity patterns** by time of day
3. **Measure queue survival** for different price levels
4. **Quantify inventory decay** rate
5. **Optimize quote parameters** based on results
6. **Validate edge components** are positive

## Critical Insight

**DepthOS is no longer "a bot."**

It is an **execution-research platform capable of falsifying its own assumptions.**

This is the important transition from hobby system to scientifically reproducible trading research infrastructure.

## Troubleshooting

### Capture Issues

**No data being captured:**
- Check WebSocket connection logs
- Verify contract symbols are correct
- Ensure Gate.io API credentials are valid

**Empty files:**
- Check if market is active
- Verify subscription was confirmed
- Check for network issues

### Edge Decomposition Issues

**No unified file:**
- Ensure capture completed successfully
- Check file exists in output directory

**Zero fills:**
- Adjust quote spread (may be too wide)
- Adjust quote size (may be too large)
- Check orderbook reconstruction

**Negative edge:**
- Review toxicity metrics
- Check inventory loss
- Analyze latency penalties

## Safety Notes

- **24h capture** runs for 24 hours - ensure sufficient disk space
- **Edge decomposition** processes all data - may take time
- **No real trading** - this is research/analysis only
- **Data files** can be large - monitor disk usage

## References

- Markout analysis methodology
- Order flow imbalance
- Queue position modeling
- Hazard-rate estimation
- Inventory-constrained quoting
