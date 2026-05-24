# DepthOS — Production-Candidate Micro-Price Market Maker

**⚠️ PRODUCTION-CANDIDATE STATUS — NOT AUDITED FOR PRODUCTION USE**

Gate.io Futures · 0–10 cent perpetuals · Top-of-book passive quoting

---

## Status: Production-Candidate

This is a **production-candidate** implementation of a market-making system for Gate.io micro-price perpetual contracts. It has been designed with safety-first principles but has not undergone a full security audit or production hardening.

### Safety Features

✅ **Dry-run first** - Default mode requires no API keys and sends no orders  
✅ **Explicit live trading confirmation** - Requires `LIVE_TRADING=1` AND `LIVE_TRADING_CONFIRM=I_UNDERSTAND_RISK`  
✅ **Kill switch** - HTTP endpoint to immediately halt all quoting  
✅ **Cancel-all-on-shutdown** - Graceful shutdown cancels all orders  
✅ **Symbol allowlist** - Only trades configured contracts  
✅ **Risk limits** - Inventory limits, daily loss halt, skew reduction  
✅ **Observable** - HTTP API for health, metrics, orders, positions, fills, risk, PnL  

### ⚠️ Disclaimers

- **NOT audited** - This code has not undergone a security audit
- **NO profit guarantees** - Market making carries significant risk of loss
- **Use at your own risk** - You are responsible for all trading decisions
- **Test thoroughly** - Always test in dry-run mode before live trading

---

## Quick Start

### Installation

```bash
pip install -r requirements.txt
```

### Dry-Run Mode (No API Keys Required)

```bash
python -m depthos --mode dry-run --duration 60
```

This will run the system for 60 seconds in simulation mode with no orders sent to the exchange.

### Live Trading (Requires Explicit Confirmation)

```bash
export GATE_API_KEY=your_key
export GATE_API_SECRET=your_secret
export LIVE_TRADING=1
export LIVE_TRADING_CONFIRM=I_UNDERSTAND_RISK

python -m depthos --mode live
```

### API Server

```bash
uvicorn app.api.server:app --host 127.0.0.1 --port 8000
```

Then test the endpoints:
```bash
curl http://127.0.0.1:8000/health
curl http://127.0.0.1:8000/risk
```

### Backtesting

Run backtest with synthetic data:
```bash
python run_backtest.py --synthetic --snapshots 10000 --duration 60
```

Run backtest with historical CSV data:
```bash
python run_backtest.py --csv data/shib_usdt.csv --contract SHIB_USDT
```

Expected CSV format:
```csv
timestamp,bid_price,bid_size,ask_price,ask_size,last_price
1234567890000,0.00005,1000,0.00006,1000,0.000055
```

---

## Project Structure

```
app/
  api/              # FastAPI REST API
    server.py       # Health, metrics, kill switch endpoints
  backtest/         # Backtesting engine
    engine.py       # Backtest simulation
    metrics.py      # Performance metrics
  connectors/       # Exchange connectivity
    auth.py         # HMAC-SHA512 signing
    rest_client.py  # REST API client
    ws_manager.py   # WebSocket manager
  core/             # Configuration
    config.py       # All constants and safety flags
  market_data/      # Market data handling
    order_book.py   # Local order book
  oms/              # Order Management System
    oms.py          # Order tracking and lifecycle
  risk/             # Risk management
    risk.py         # Inventory limits, P&L, halts
  strategy/         # Trading strategy
    quoting_engine.py # Core quoting logic
  main.py           # Entry point with safety validation
tests/              # Test suite
  test_backtest.py  # Backtest tests
  main.py           # Legacy entry point (deprecated)
```

---

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/ready` | GET | Readiness check |
| `/metrics` | GET | System metrics |
| `/orders` | GET | Current live orders |
| `/positions` | GET | Current positions |
| `/fills` | GET | Recent fills |
| `/risk` | GET | Risk state |
| `/pnl` | GET | P&L summary |
| `/kill-switch` | POST | Activate kill switch |
| `/cancel-all` | POST | Cancel all orders |

---

## Risk Controls

| Control | Default | Description |
|---------|---------|-------------|
| `max_inventory_contracts` | 50 | Hard position limit per contract |
| `skew_threshold_contracts` | 20 | Begin reducing size when net pos > this |
| `daily_loss_limit_usdt` | $5.00 | Halt all quoting if daily PnL < -limit |
| BBO stale guard | 2 000 ms | Suppress quotes if BBO not updated |
| Price ceiling | $0.10 | Skip any contract whose ask > $0.10 |
| `order_size` | 1 contract | Base quote size (minimum) |

---

## Testing

Run the test suite:

```bash
python -m pytest -q
```

Run with coverage:

```bash
python -m pytest --cov=app --cov-report=html
```

---

## Module Responsibilities

| Module | Role |
|--------|------|
| `app/core/config.py` | All constants, safety flags, `MMConfig`, `ContractSpec` |
| `app/connectors/auth.py` | HMAC-SHA512 signing for REST + WS |
| `app/connectors/rest_client.py` | HTTP order lifecycle + bootstrap queries |
| `app/market_data/order_book.py` | Local LOB state, BBO tracking |
| `app/risk/risk.py` | Inventory limits, daily loss halt, fill recording |
| `app/oms/oms.py` | Idempotent quote updates, cancel/replace logic |
| `app/strategy/quoting_engine.py` | Per-contract event-driven quoting coroutines |
| `app/connectors/ws_manager.py` | Public + private WS with auto-reconnect |
| `app/api/server.py` | FastAPI REST API for observability and control |
| `app/backtest/engine.py` | Backtest simulation engine |
| `app/backtest/metrics.py` | Performance metrics tracking |
| `app/main.py` | Entry point with safety validation and CLI |

---

## Configuration

Environment variables:

| Variable | Required | Description |
|----------|----------|-------------|
| `GATE_API_KEY` | Live only | Gate.io API key |
| `GATE_API_SECRET` | Live only | Gate.io API secret |
| `DRY_RUN` | No | Set to "1" for dry-run mode |
| `LIVE_TRADING` | No | Set to "1" to enable live trading |
| `LIVE_TRADING_CONFIRM` | Live only | Set to "I_UNDERSTAND_RISK" to confirm live trading |
| `LOG_LEVEL` | No | Set to DEBUG, INFO, WARN, or ERROR |

---

## C++ Implementation

A C++ implementation exists in `files_cpp/` but is **not production-ready**. It lacks:
- Unit tests
- Mock exchange tests  
- Dry-run quote loop tests
- Build verification

The C++ version should be considered a skeleton/performance prototype only.

---

## Known Limitations / Extension Points

1. **Position FIFO P&L** — `risk.py` uses a simplified average-entry model.
   Replace `_avg_entry_price` with a proper FIFO lot tracker for exact P&L.

2. **Multi-level quoting** — currently 1 order per side per contract.
   Extend `QuotingEngine._evaluate_and_quote` to post N levels.

3. **Mark-price unrealized P&L** — subscribe to `futures.tickers` and call
   `risk.on_pnl_delta()` for live unrealized tracking.

4. **Persistence** — add SQLite/Redis fill logging for audit trail.

5. **Spread filter** — currently only requires ≥ 1 tick spread.
   Add minimum spread in USDT if needed for fee coverage.

6. **Backtest accuracy** — current backtest uses simplified fill logic.
   Improve with realistic order queue simulation and slippage models.

---

## License

MIT License - See LICENSE file for details.

---

## Support

For issues, questions, or contributions, please open an issue on the project repository.
