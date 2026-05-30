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
- **Prioritization** (`/prioritization`) — Catacomb capital allocation engine with revival potential scoring and tier classification
- **Improvement Queue** (`/improvement`) — Action queue showing critical, high, and medium priority improvements

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
- `GET /api/catacomb/prioritization` — Catacomb capital allocation engine with revival potential scoring
- `GET /api/portfolio/improvement-queue` — Improvement queue with action priorities
- `GET /api/export/prioritization?format=json|csv` — Export Catacomb prioritization data

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
python build_index.py  # Build data/index.json and data/index_deploy.json
vercel --prod
```

## Catacomb Capital Allocation Engine

### Overview

Catacomb is the killer wedge of the Overandor/Membra software-capital formation system. It's a deterministic engine for discovering underpriced software assets, scoring revival potential, and converting neglected repositories into monetizable infrastructure.

### Thesis

**Not all software is worth saving.** Catacomb prioritizes assets with high strategic value, low collateral conversion, and achievable improvement paths. Archives the rest.

### Algorithm

The revival potential score uses weighted factors:
- **40%** - Raw value (replacement cost scaled by $100k)
- **30%** - Ease of realization (financeability score)
- **20%** - Foundation (proof level / 7 × 100)
- **10%** - Substance (source code volume)

### Tier Classification

- **Tier 1 - Core Asset** (≥70 score, ≥$1M value) - Immediate investment priority
- **Tier 2 - High Potential** (≥50 score, ≥$500K value) - High priority for improvement
- **Tier 3 - Medium Potential** (≥30 score) - Moderate priority, evaluate case-by-case
- **Tier 4 - Low Potential** (≥15 score) - Low priority, consider archival
- **Archive Candidate** (<15 score) - Archive unless strategic reasons exist

### ROI Calculation

ROI = (Collateral Support × (100 / (100 - Conversion Gap))) / Estimated Effort (weeks)

### Improvement Queue

The improvement queue categorizes all pending actions by priority:
- **Critical** - Must fix immediately (e.g., no license, env file detected)
- **High** - Fix soon for significant financeability gains
- **Medium** - Nice-to-have improvements

### Strategic Context

Catacomb indexes the broader Membra/Overandor repo estate, scores every repo as a software asset, writes the results into LiquidDB, snapshots the asset ledger, and publishes proof-backed capitalization reports.

This gives one coherent product: **Catacomb for software asset capitalization.**

Everything else becomes inventory in the software-capital formation stack.

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
