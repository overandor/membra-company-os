# CollateralOps — Software Collateral Execution Network

Turn developer work into capital-ready collateral.

## Overview

CollateralOps scans your codebase, builds a financial-grade appraisal, and gives you a balance sheet that lenders and buyers actually understand.

**Version:** 2.0.0  
**Design:** 2040 Futuristic UI with glassmorphism, neon accents, and particle animations

## Features

### Appraisal Engine (v2)
- **Eight valuation methods:** Replacement cost, as-is value, productized value, liquidation value, collateral support, market comparable, network effect, complexity adjusted
- **Eight quality subscores:** Ownership clarity, technical quality, market liquidity, security posture, documentation depth, activity recency, dependency health, complexity index
- **Risk matrix:** Legal, security, engineering, market, liquidity, overall
- **Granular deductions** with severity levels (critical/high/medium)
- **Improvement roadmap** with effort estimates

### Pages
- **Landing** (`/`) — Hero section, feature grid, animated stats, sample appraisal preview
- **Dashboard** (`/dashboard`) — Portfolio score ring, valuation bars, quality subscore grid, interactive asset register, action modal
- **Asset Detail** (`/asset/{name}`) — Dual score rings, eight-value appraisal, risk matrix, deductions, timeline, preview modal
- **Compare** (`/compare`) — Side-by-side asset comparison with winner highlighting
- **Lender View** (`/lender`) — Conservative collateral assessment with risk-adjusted estimates
- **Explorer** (`/explorer`) — File tree explorer with collateral evidence detail
- **Passport** (`/passport`) — Platform provenance passport

### API Endpoints
- `GET /health` — System health and version info
- `GET /api/balance-sheet` — Full portfolio with appraisals
- `GET /api/asset/{name}` — Single asset classification + appraisal
- `GET /api/asset/{name}/lender` — Lender summary
- `GET /api/asset/{name}/buyer` — Buyer summary
- `GET /api/compare?a=X&b=Y` — Side-by-side comparison
- `GET /api/timeline/{name}` — Historical appraisal timeline
- `GET /api/export/balance-sheet?format=json|csv` — Export full portfolio
- `GET /api/export/asset/{name}?format=json|csv` — Export single asset

## Local Development

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

Visit `http://localhost:8000`

## Deploy to Vercel

```bash
python build_index.py  # Build data/index.json
vercel --prod
```

## Tech Stack

- **Backend:** Python 3.14, FastAPI
- **Frontend:** Vanilla HTML/CSS/JS, Google Fonts (Space Grotesk, JetBrains Mono)
- **Styling:** Glassmorphism, CSS custom properties, canvas particle animations
- **Deployment:** Vercel (serverless)

## Design System

- **Colors:** Deep black backgrounds (`#020204`), cyan (`#00f0ff`), purple (`#c084fc`), orange (`#ff6b35`), green (`#34d399`)
- **Fonts:** Space Grotesk (UI), JetBrains Mono (data/monospace)
- **Effects:** Glassmorphism cards with gradient top borders, particle canvas backgrounds, SVG stroke animations

## License

Proprietary — CollateralOps 2040
