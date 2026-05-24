# LIVE TRADING GUIDE - GATE.IO FUTURES

## ⚠️ CRITICAL WARNING

**THIS SCRIPT PLACES REAL ORDERS WITH REAL MONEY ON GATE.IO FUTURES**

- You will use your actual funds
- Orders are not simulated
- Losses are real
- Use at your own risk

## Prerequisites

1. **Gate.io Account**: You must have a Gate.io account with futures trading enabled
2. **API Keys**: Your API keys must have futures trading permissions
3. **Funds**: Your account must have sufficient margin for the orders
4. **Risk Understanding**: You must understand the risks of futures trading

## Configuration

The script uses API credentials from:
```
/Users/alep/Downloads/05_Config_Files/.env
```

Current credentials:
- `GATE_API_KEY`: 57897b69c76df6aa01a1a25b8d9c6bc8
- `GATE_API_SECRET`: ed43f2696c3767685e8470c4ba98ea0f7ea85e9adeb9c3d098182889756d79d9

## Safety Limits

The script includes these safety limits:

```python
MAX_POSITION_SIZE_USDT = 100  # Maximum position size
MAX_ORDER_SIZE_USDT = 50      # Maximum single order size
```

**Adjust these limits based on your risk tolerance and account size.**

## How to Run

```bash
cd /Users/alep/Downloads/files
python live_trade.py
```

## What the Script Does

1. **Loads API credentials** from .env file
2. **Configures live trading mode** (no dry-run, no simulation)
3. **Displays order details** before placement
4. **Requires explicit confirmation** (type "YES" to confirm)
5. **Places the order** on Gate.io futures
6. **Shows order result** (order ID, status)
7. **Offers option to cancel** immediately (for testing)

## Current Order Configuration

```python
contract = "BTC_USDT"
size = 1  # Buy 1 contract
price = current_btc_price * 0.999  # Slightly below market for maker order
tif = "poc"  # Post-only (maker-or-cancel)
reduce_only = False
```

**IMPORTANT**: Update the `current_btc_price` to the current market price before running.

## Customizing the Order

Edit these parameters in `live_trade.py`:

```python
# Contract to trade
contract = "BTC_USDT"  # or "ETH_USDT", "SHIB_USDT", etc.

# Order size (positive = buy, negative = sell)
size = 1

# Limit price
price = Decimal("78300")

# Time in force: "gtc", "ioc", or "poc"
tif = "poc"  # Post-only (recommended for maker orders)

# Reduce only (close position)
reduce_only = False
```

## Time in Force Options

- **gtc** (Good Till Cancelled): Order stays until filled or cancelled
- **ioc** (Immediate Or Cancel): Fill immediately or cancel
- **poc** (Post-Only Cancel): Maker only, cancelled if would take liquidity

**Recommendation**: Use `poc` for maker orders to avoid taker fees.

## Account Mode

Gate.io supports two account modes:

- **Single mode**: One position per contract (long/short)
- **Dual mode**: Separate long and short positions

The script defaults to `single` mode. Change if your account uses dual mode:

```python
mm_config.account_mode = "dual"
```

## Risk Management

Before trading, ensure you:

1. ✅ Understand futures trading risks
2. ✅ Have sufficient margin
3. ✅ Set appropriate position sizes
4. ✅ Use stop-loss orders (implement separately)
5. ✅ Monitor positions actively
6. ✅ Understand liquidation risks

## Testing

To test without real money:

1. Use the existing dry-run mode in the main system
2. Start with very small order sizes
3. Place orders and cancel them immediately
4. Verify order execution and fills

## Emergency Cancellation

If you need to cancel all orders immediately:

1. Log into Gate.io
2. Go to Futures Trading
3. Use "Cancel All Orders" button
4. Or close positions manually

## Troubleshooting

**"Order size exceeds limit"**
- Reduce the order size
- Increase MAX_ORDER_SIZE_USDT in the script

**"Insufficient margin"**
- Add funds to your Gate.io account
- Reduce position size

**"API key permissions"**
- Ensure API key has futures trading enabled
- Check IP whitelist settings

**"Contract not found"**
- Verify contract symbol is correct
- Check if contract is available for futures trading

## Important Notes

- The script uses your real API credentials
- Orders are placed on the live exchange
- There is no simulation or paper trading
- All profits and losses are real
- Gate.io fees apply (maker: 0.02%, taker: 0.05%)

## Disclaimer

This software is provided as-is without warranty. The authors are not responsible for any financial losses incurred through use of this software. Futures trading involves significant risk and is not suitable for all investors.

## Support

For issues with:
- **Gate.io API**: Contact Gate.io support
- **Script errors**: Check the error logs
- **Account issues**: Contact Gate.io customer service
