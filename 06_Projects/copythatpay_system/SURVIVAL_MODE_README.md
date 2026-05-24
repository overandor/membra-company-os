# CopyThatPay — $9 Survival Mode

**Lean, directional micro-scalper for micro-capital environments.**

## What Changed

The original bot was overengineered for micro-capital:
- ❌ Hedging (long+short on same symbol)
- ❌ Symmetric quoting (both sides)
- ❌ Maker-first entry (queue priority issues)
- ❌ Complex edge calculations
- ❌ DCA logic
- ❌ "Neutral exposure fantasy"

The survival mode is stripped down:
- ✅ **TAKER entry** (market order when edge exists)
- ✅ **Fast exits** (0.25% target / 0.15% stop / 30s timeout)
- ✅ **Directional only** (long OR short, never both)
- ✅ **Strict filters** (spread, volume, imbalance, momentum)
- ✅ **2% risk per trade**
- ✅ **Cooldown after loss** (30s revenge trading prevention)

## Strategy

```
WAIT → STRIKE → EXIT FAST → REPEAT
```

1. **WAIT**: Scan symbols for edge conditions
   - Orderbook imbalance > 0.3 (buy or sell pressure)
   - Micro momentum > 0.001 (1% move over 3 minutes)
   - Spread >= 0.2% (real edge, not fake)
   - Volume >= $50k (liquidity exists)

2. **STRIKE**: Enter via market order (taker)
   - Size: 2% of equity × leverage
   - With $9: ~$0.90–$1.50 notional per trade
   - Get in when signal exists, not 20 seconds later

3. **EXIT FAST**: Three exit conditions
   - **Take profit**: 0.25% move in your favor
   - **Stop loss**: 0.15% move against you
   - **Time stop**: 30 seconds max position age

4. **REPEAT**: Scan for next opportunity
   - 30s cooldown after loss (prevents revenge trading)
   - One position at a time (micro account discipline)

## Configuration

```python
# Capital and risk
TOTAL_CAPITAL_USD     = 9.0
RISK_PER_TRADE_PCT    = 0.02  # 2% of equity per trade
DEFAULT_LEVERAGE       = 5

# Exit parameters
TAKE_PROFIT_PCT       = 0.0025  # 0.25%
STOP_LOSS_PCT         = 0.0015  # 0.15%
TIME_EXIT_SEC         = 30      # 30 seconds

# Entry filters
MIN_SPREAD_PCT        = 0.002   # 0.2%
MIN_VOLUME_USD        = 50000   # $50k
IMBALANCE_THRESHOLD   = 0.3
MOMENTUM_THRESHOLD    = 0.001   # 0.1%
```

## Running

```bash
# Set your API credentials in .env
GATE_API_KEY=your_key
GATE_API_SECRET=your_secret

# Run the survival mode bot
python copythatpay_survival.py
```

## What Success Looks Like

With $9 capital, you are NOT:
- Building income ❌
- Scaling fast ❌
- Beating pros ❌

You ARE:
- Testing execution ✅
- Learning survival ✅
- Proving edge exists ✅

**Target metrics:**
- Win rate: 55–65%
- Avg win: 0.25%
- Avg loss: 0.15%
- Edge: tiny but REAL

If you can't hit these, your signal is garbage—not your code.

## Key Files

- `copythatpay_survival.py` — The lean survival mode bot
- `copythatpay_survival_data/journal.jsonl` — Trade log
- `copythatpay_survival_data/toxicity.jsonl` — Fill toxicity metrics
- `copythatpay_survival_data/equity_curve.csv` — Performance tracking

## Fill Toxicity Tracking

The bot tracks fill quality to measure execution performance:

**Metrics captured per trade:**
- Entry price vs mid price (slippage)
- Entry imbalance and momentum
- Duration of position
- Realized PnL vs expected PnL
- Toxicity ratio = realized / expected

**Classification:**
- **Good fill**: PnL > 0
- **Toxic fill**: PnL < 0

**Status display shows:**
- Fill quality percentage (good fills / total fills)
- Good fills count
- Toxic fills count
- Average toxicity ratio

**Why this matters:**
Most fills are toxic. Good fills happen when:
- Momentum continues in your direction
- You're not early (entering before move starts)
- You're not in chop (sideways markets)

Toxicity data is logged to `toxicity.jsonl` for analysis. After 20-50 trades, you'll discover patterns in your losing trades and can refine your entry conditions.

## Differences from Original

| Feature | Original | Survival Mode |
|---------|----------|---------------|
| Entry | Maker (limit orders) | Taker (market orders) |
| Hedging | Yes (long+short) | No (directional only) |
| Position size | Complex risk gating | Simple 2% of equity |
| Exits | Spread target | Target/stop/time |
| Filters | Edge score 0-2 | Strict thresholds |
| Complexity | ~2400 lines | ~450 lines |

## Why This Works for $9

1. **Taker entry**: You get fills when signals exist
2. **Fast exits**: No holding through adverse moves
3. **Small size**: 2% risk = survive losing streaks
4. **Strict filters**: Only trade real edges
5. **Cooldown**: Prevents revenge trading

The market will give you crumbs if you're disciplined.
