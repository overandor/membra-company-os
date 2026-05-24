# MEMBRA Finance Oracle

A production-ready full-stack oracle dashboard that treats letters, digits, and symbols as "linguistic primitives" with live-derived prices and rankings based on real market data.

## Features

- **Real Live Data**: Ingests data from 9+ public endpoints (CoinGecko, DexScreener, Gate.io, Binance, Kraken, etc.)
- **No Mock Data**: Every displayed value comes from real endpoints, cached responses, or locally computed derivatives
- **36 Linguistic Primitives**: Letters A-Z and numbers 0-9 with live-derived prices
- **Advanced Metrics**: normalized frequency, source diversity, topic diversity, price_lgu, rank, entropy, oracle flux density, semantic pressure ratio, resistance score
- **Dark Cyber-Finance UI**: Terminal-finance aesthetic with gold/orange accent
- **Source Monitoring**: Real-time health status for all data sources
- **60-Second TTL Cache**: Efficient caching with automatic expiration
- **Persistence**: SQLite database for historical snapshots

## Project Structure

```
membra-finance-oracle/
├── backend/
│   ├── main.py           # FastAPI backend with all endpoints
│   └── requirements.txt  # Python dependencies
├── frontend/
│   └── (React/Vite app)
└── README.md
```

## Live Endpoints

1. CoinGecko trending coins
2. CoinGecko simple price
3. DexScreener latest token pairs
4. Gate.io spot tickers
5. Binance 24hr ticker
6. Kraken asset pairs/ticker
7. Jupiter token list (optional)
8. Birdeye token market (optional)
9. GitHub trending/search API (optional)

## Required Pages

1. Home dashboard
2. Oracle primitive grid
3. Primitive detail page
4. Alchemist / formula builder
5. Alpha signals page
6. API Docs page
7. Health/status page
8. Source monitor
9. Backtest/dry-run page (optional)

## API Endpoints

- `GET /` - Root endpoint
- `GET /health` - Health check
- `GET /api/status` - API status with cache info
- `GET /api/sources` - Get source status
- `GET /api/primitives` - Get all primitives
- `GET /api/primitives/{symbol}` - Get specific primitive
- `GET /api/oracle/snapshot` - Get current oracle snapshot
- `GET /api/oracle/top` - Get top N primitives
- `GET /api/oracle/history` - Get primitive history
- `GET /api/topics` - Get topic information
- `GET /api/market` - Get market overview
- `GET /api/backtest` - Backtest/dry-run (placeholder)
- `GET /docs` - API documentation

## Computation Requirements

For each primitive A-Z, 0-9:
- Count appearances in all live records
- Count unique sources where it appears
- Count unique topics/pairs/tokens where it appears
- Compute normalized frequency
- Compute source diversity
- Compute topic diversity
- Compute price_lgu
- Compute rank
- Compute entropy
- Compute leader flag
- Compute volatility from repeated snapshots
- Compute resistance score
- Compute oracle flux density
- Compute semantic pressure ratio

## Formulas

```
price_lgu = normalized_frequency * market_factor * source_diversity_boost * liquidity_boost
oracle_flux_density = price_lgu * source_diversity / max(1, topic_diversity)
semantic_pressure_ratio = topic_frequency / max(0.0001, global_frequency)
resistance_score = source_diversity * topic_diversity / max(1, volatility)
entropy = -sum(p * log2(p)) across primitive distribution
```

## Setup

### Backend (FastAPI)

```bash
cd backend
pip install -r requirements.txt
python main.py
```

Backend will run on http://localhost:8000

### Frontend (React/Vite)

```bash
cd frontend
npm install
npm run dev
```

Frontend will run on http://localhost:5173

## Deployment

### Hugging Face Spaces

1. Create a new Space on Hugging Face
2. Upload the backend files
3. Create `app.py` that wraps FastAPI for Hugging Face Spaces
4. Add `requirements.txt`
5. Deploy

### Local Development

Run both backend and frontend concurrently for development.

## Acceptance Test

When you run the app:
- It must immediately fetch live endpoint data
- Populate at least 44 primitives (36 letters/numbers + optional symbols)
- Show source health
- Expose /api/primitives and /api/primitives/{symbol}
- Render an Oracle page where clicking a primitive opens its full detail with:
  - Price history
  - Source distribution
  - Topic appearances
  - Sample endpoints
  - Live KPI appraisal

## Data Architecture

- Async fetchers for concurrent endpoint calls
- 60-second TTL cache for all API responses
- SQLite persistence for historical snapshots
- Each source reports: name, endpoint URL, status, latency, last success, record count, error message

## Notes

- If an endpoint fails, show degraded status with error reason and last successful cache timestamp
- No Readdy branding
- No Replit preview warning inside app
- Mobile responsive design
- Compact terminal-finance aesthetic
