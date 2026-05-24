# MEMBRA CompanyOS

**The orchestration layer where AI builds, governs, and operates real-world companies through proof, permission, and local execution.**

## The Doctrine

Every apartment is the nearest warehouse.  
Every person is a possible operator.  
Every surface is possible media.  
Every object is possible inventory.  
Every chat is possible intent.  
Every intent is possible work.  
Every work unit requires proof.  
Every proof can become governance.  
Every governed flow can become a company function.  
Every repeated company function can become an autonomous operating layer.

## Architecture

MEMBRA CompanyOS is composed of **9 operating-system modules**:

| Module | Purpose |
|--------|---------|
| **IntentOS** | Converts human chat into structured objectives |
| **TaskOS** | Breaks objectives into executable tasks with dependencies |
| **AgentOS** | Registry of 10 AI agent types with tools, permissions, and output schemas |
| **JobOS** | Converts tasks into paid jobs, bounties, work orders, and marketplace actions |
| **CompanyOS** | Turns repeated workflows into departments, SOPs, KPIs, and operating units |
| **GovernanceOS** | Approval gates, policies, consent records, risk classification, escalation rules |
| **ProofBook** | Hashes every task, agent output, approval, listing, KPI report, and settlement record |
| **SettlementOS** | Tracks payout eligibility and sends settlement instructions to external rails (Stripe, Solana, Ethereum) |
| **WorldBridge** | Connects apartments, vehicles, windows, wearables, tools, people, vendors, and local routes |

## Agent Registry

| Agent | Role |
|-------|------|
| Strategy | Decides what MEMBRA should build next |
| Product | Converts strategy into product requirements |
| Engineering | Builds software and deploys services |
| Operations | Creates SOPs, fulfillment flows, and support processes |
| Sales | Generates offers, landing pages, outreach, and partner flows |
| Finance | Tracks unit economics, payout eligibility, margin, and runway |
| Legal/Risk | Flags lease, local-rule, privacy, insurance, and campaign risks |
| Governance | Controls approvals, policies, permissions, and escalation |
| Proof | Writes every meaningful action into ProofBook |
| Concierge | Front-facing LLM that maps user intent to MEMBRA actions |

## Tech Stack

- **Backend**: Python 3.11, FastAPI 0.109, SQLAlchemy 2.0, PostgreSQL 15, Pydantic 2.5
- **Frontend**: Vanilla HTML/JS, Dark-Gold Neomorphic CSS (no build step)
- **Infrastructure**: Docker, Docker Compose, Alembic migrations, Render + Vercel
- **LLM**: Groq (Llama 3.3 70B) or OpenAI (GPT-4o) with deterministic fallback
- **Auth**: MetaMask wallet signature verification + JWT tokens
- **Proof**: SHA3-256 hashing with chain linking

## Quick Start

```bash
cd membra-companyos/backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Or with Docker:

```bash
cd membra-companyos
docker-compose up --build
```

## API Endpoints

All endpoints are prefixed with `/v1`.

### Core Modules

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Root info |
| `/health/` | GET | Health check |
| `/auth/register` | POST | Register user |
| `/auth/login` | POST | Login (wallet or email) |
| `/auth/refresh` | POST | Refresh access token |
| `/intents/` | POST | Create intent |
| `/intents/` | GET | List intents |
| `/tasks/` | POST | Create task |
| `/tasks/` | GET | List tasks |
| `/tasks/{id}/status` | POST | Update task status |
| `/agents/` | POST | Register agent |
| `/agents/` | GET | List agents |
| `/agents/{id}/actions` | POST | Log agent action |
| `/jobs/` | POST | Create job |
| `/jobs/` | GET | List jobs |
| `/jobs/{id}/complete` | POST | Complete job |
| `/companies/` | POST | Create company |
| `/companies/{id}` | GET | Company dashboard |
| `/companies/{id}/departments` | POST | Create department |
| `/companies/{id}/kpis` | POST | Record KPI |
| `/governance/approval-gates` | POST | Create approval gate |
| `/governance/approval-gates/{id}/approve` | POST | Approve gate |
| `/governance/consent` | POST | Record consent |
| `/governance/risk` | POST | Classify risk |
| `/proofbook/entries` | POST | Write proof entry |
| `/proofbook/entries` | GET | List proof entries |
| `/proofbook/chains/{id}/verify` | GET | Verify chain integrity |
| `/settlements/records` | POST | Create settlement record |
| `/settlements/records/{id}/settled` | POST | Mark settled |
| `/worldbridge/assets` | POST | Register asset |
| `/worldbridge/assets` | GET | List assets |
| `/worldbridge/listings/{id}/approve` | POST | Approve listing |
| `/concierge/chat` | POST | Chat with LLM Concierge |

## Production Boundaries

MEMBRA CompanyOS is an orchestration and governance layer. It does not replace legal, financial, or regulatory obligations.

- **MEMBRA does not guarantee income.** All projections are estimates.
- **MEMBRA does not custody funds.** Settlement happens through external rails (Stripe, Solana, Ethereum).
- **Owner confirmation is required** before any asset becomes visible on a marketplace.
- **Governance approval is required** for high-risk actions (payouts, production deployments, data sharing).
- **AI agents recommend and prepare** — they do not bypass human or policy gates.
- **All ProofBook entries are demonstrations** of audit-trail capability, not legal evidence.

## Deployment

### Local Development (SQLite)

```bash
cd membra-companyos/backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # edit SECRET_KEY and optional LLM keys
export SECRET_KEY="dev-secret-key-must-be-at-least-32-characters-long"
export DATABASE_URL="sqlite:///./tmp_companyos.db"
alembic upgrade head
python seed.py
uvicorn app.main:app --reload
```

### Docker Compose (production-like)

```bash
cd membra-companyos
export SECRET_KEY="your-32-char-minimum-secret-key-here"
docker compose up --build
```

API: `http://localhost:8000` · Health: `http://localhost:8000/v1/health/`

### Render (Backend API)

1. Push this repo to GitHub.
2. On Render: **New → Blueprint** and point at `membra-companyos/backend/render.yaml` (or create a Web Service with root directory `backend`).
3. Set sync=false secrets in the dashboard: `GROQ_API_KEY`, `OPENAI_API_KEY`, and `CORS_ORIGINS` to your Vercel dashboard URL (e.g. `https://your-app.vercel.app`).
4. Deploy. Migrations run via `preDeployCommand`; health check hits `/v1/health/`.

### Vercel (Dashboard)

1. Create a Vercel project with root directory `membra-companyos/frontend`.
2. Update `frontend/vercel.json` rewrite destination to your Render API URL (`/v1/:path*` proxy).
3. Deploy. The dashboard calls `/v1` on the same origin; Vercel proxies to Render (no CORS issues).

Optional: set `<meta name="membra-api-base" content="https://api.example.com/v1">` in `index.html` if not using the Vercel proxy.

### Production checklist

- [ ] `SECRET_KEY` — 32+ chars, unique per environment
- [ ] `DATABASE_URL` — managed PostgreSQL (Render DB or RDS)
- [ ] `alembic upgrade head` on deploy (automated in Docker/Render)
- [ ] `CORS_ORIGINS` — your frontend origin(s), not `*`
- [ ] `GROQ_API_KEY` or `OPENAI_API_KEY` for Concierge
- [ ] `SENTRY_DSN` (optional) for error tracking
- [ ] Update `vercel.json` rewrite URL to match Render service name

## Environment Variables

See `backend/.env.example` for the full list of configuration options.

Key variables:
- `DATABASE_URL` — PostgreSQL or SQLite connection string
- `SECRET_KEY` — JWT signing secret (min 32 chars)
- `GROQ_API_KEY` / `OPENAI_API_KEY` — LLM provider keys
- `STRIPE_SECRET_KEY` — External settlement via Stripe
- `SOLANA_RPC_URL` / `SOLANA_PRIVATE_KEY` — On-chain settlement
- `GOVERNANCE_ADMIN_WALLET` — Super-admin wallet address

## Dashboard

The dark-gold neomorphic dashboard is served as static files:

```bash
cd membra-companyos/frontend
python -m http.server 8080
```

Open `http://localhost:8080` to access the CompanyOS control center.

## License

Proprietary — MEMBRA Autonomous Systems.
