# Production Agent Service

Autonomous workspace scanner, production readiness evaluator, codebase appraiser, and paid API service.

## Features

- **Scan** any directory tree and auto-detect project boundaries (git, package.json, Cargo.toml, etc.)
- **Readiness Scoring** across 9 dimensions: CI/CD, tests, docs, typing, linting, Docker, secrets, dependencies, structure
- **Deterministic Appraisal** — file-level LOC valuation with language/domain rate tables (no LLM required)
- **Secret Detection** — scans staged and uncommitted files for API keys, tokens, private keys
- **Payment Integration** — Stripe checkout with tiered pricing (Basic free, Pro $29, Enterprise $99)
- **Dashboard** — built-in dark-mode web UI at `/ui` and `/dashboard`

## Quick Start

```bash
pip install -r requirements.txt
python main.py
```

Open `http://localhost:8000/ui` for the dashboard.

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/scan` | POST | Scan workspace, return project inventory |
| `/api/batch-appraise` | POST | Scan + appraise every project found |
| `/api/appraise` | POST | Appraise a single project path |
| `/api/appraisals` | GET | List all appraisals |
| `/api/pricing` | GET | Show pricing tiers |
| `/api/payment/intent` | POST | Create payment intent |
| `/api/payment/confirm` | POST | Confirm payment |
| `/ui` | GET | Dashboard |

## Environment Variables

| Variable | Description |
|----------|-------------|
| `STRIPE_SECRET_KEY` | Stripe secret key for live payments |
| `STRIPE_WEBHOOK_SECRET` | Stripe webhook endpoint secret |
| `PORT` | Server port (default 8000) |

## Architecture

```
scanner.py      →  Project boundary detection + file inventory
readiness.py    →  Production readiness scoring engine
appraiser.py    →  Deterministic LOC-based valuation
agent.py        →  Orchestrates scan + readiness + appraisal
payments.py     →  Stripe checkout + credit tracking
api.py          →  FastAPI service layer
dashboard/      →  Static HTML dashboard
```

## License

MIT
