# Agent Workforce Platform

A proprietary multi-agent system featuring **30 specialized LLM agents** with real-time API endpoints, Stripe billing, Twilio SMS/voice, email delivery, GitHub repository creation, and Vercel deployment capabilities.

---

## Quick Start

```bash
# Clone and setup
cd agent-workforce
cp .env.example .env
# Edit .env with your API keys

# Run with Docker Compose
docker-compose up --build

# Or run locally
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Open `http://localhost:8000/docs` for interactive Swagger UI.

---

## Architecture

```
agent-workforce/
├── app/
│   ├── main.py                 # FastAPI entry point
│   ├── core/                   # Config, logging, security
│   ├── models/                 # Pydantic schemas
│   ├── services/               # Stripe, Twilio, Email, Vercel, GitHub, LLM
│   ├── agents/                 # 30 agent implementations
│   ├── routers/                # API routes
│   └── appraisal/              # Worker valuation engine
├── Dockerfile                  # Multi-stage production build
├── docker-compose.yml          # App + PostgreSQL + Redis
├── requirements.txt            # Python dependencies
└── .env.example                # Environment template
```

---

## The 30 Agents

| # | Agent ID | Name | Category | Price/Run |
|---|----------|------|----------|-----------|
| 1 | `web_research` | Web Research Agent | Research | $1.50 |
| 2 | `academic_research` | Academic Research Agent | Research | $2.00 |
| 3 | `seo_audit` | SEO Audit Agent | Marketing | $1.20 |
| 4 | `social_monitor` | Social Media Monitor Agent | Marketing | $1.30 |
| 5 | `competitor_analysis` | Competitor Analysis Agent | Strategy | $1.80 |
| 6 | `price_tracker` | Price Tracker Agent | E-commerce | $1.00 |
| 7 | `content_summarizer` | Content Summarizer Agent | Content | $0.80 |
| 8 | `fact_checker` | Fact Checker Agent | Research | $1.70 |
| 9 | `trend_analyzer` | Trend Analyzer Agent | Strategy | $1.60 |
| 10 | `news_aggregator` | News Aggregator Agent | Media | $1.10 |
| 11 | `legal_analyzer` | Legal Document Analyzer Agent | Legal | $2.50 |
| 12 | `patent_research` | Patent Research Agent | Legal | $2.20 |
| 13 | `job_market` | Job Market Research Agent | HR | $1.00 |
| 14 | `real_estate` | Real Estate Research Agent | Finance | $1.40 |
| 15 | `stock_data` | Stock Market Data Agent | Finance | $1.80 |
| 16 | `crypto_data` | Crypto Market Data Agent | Finance | $1.70 |
| 17 | `review_analyzer` | Product Review Analyzer Agent | E-commerce | $1.10 |
| 18 | `sentiment` | Sentiment Analysis Agent | NLP | $0.90 |
| 19 | `lead_gen` | Lead Generation Agent | Sales | $1.30 |
| 20 | `email_outreach` | Email Outreach Agent | Sales | $1.00 |
| 21 | `github_trends` | GitHub Trends Agent | Dev | $0.90 |
| 22 | `doc_writer` | Documentation Writer Agent | Dev | $1.20 |
| 23 | `code_review` | Code Review Agent | Dev | $1.50 |
| 24 | `security_audit` | Security Audit Agent | Dev | $2.00 |
| 25 | `api_docs` | API Documentation Agent | Dev | $1.30 |
| 26 | `devops_monitor` | DevOps Monitor Agent | Dev | $1.60 |
| 27 | `customer_support` | Customer Support Agent | Operations | $0.80 |
| 28 | `translator` | Translation Agent | NLP | $0.60 |
| 29 | `data_viz` | Data Visualization Agent | Analytics | $1.40 |
| 30 | `report_gen` | Report Generation Agent | Content | $1.90 |

---

## Live Endpoints

### Agent Execution
- `GET /agents/` - List all agents
- `GET /agents/{id}` - Get agent metadata
- `POST /agents/{id}/run` - Execute agent synchronously
- `POST /agents/{id}/run-async` - Queue agent run
- `POST /agents/{id}/action` - Unified action (run + bill + notify + deploy)

### Billing (Stripe)
- `POST /agents/{id}/checkout` - Create checkout session
- `POST /agents/{id}/product` - Create Stripe product for agent

### Notifications (Twilio & Email)
- `POST /agents/{id}/notify/sms` - Send SMS
- `POST /agents/{id}/notify/voice` - Initiate voice call
- `POST /agents/{id}/notify/email` - Send email

### GitHub & Vercel
- `POST /agents/{id}/repo` - Create GitHub repository
- `POST /agents/{id}/deploy` - Deploy to Vercel

### Appraisal
- `GET /agents/{id}/appraisal` - Worker valuation
- `GET /agents/portfolio/appraisal` - Portfolio summary
- `GET /agents/portfolio/appraisals` - All appraisals

### System
- `GET /` - Root info
- `GET /health` - Health check
- `GET /metrics` - Prometheus metrics
- `GET /docs` - Swagger UI

---

## Example Usage

### Run an Agent
```bash
curl -X POST http://localhost:8000/agents/web_research/run \
  -H "Content-Type: application/json" \
  -d '{
    "query": "latest developments in solid-state batteries",
    "notify_email": "user@example.com",
    "create_repo": true,
    "repo_name": "battery-research"
  }'
```

### Stripe Checkout
```bash
curl -X POST http://localhost:8000/agents/seo_audit/checkout \
  -H "Content-Type: application/json" \
  -d '{
    "agent_id": "seo_audit",
    "success_url": "https://example.com/success",
    "cancel_url": "https://example.com/cancel",
    "customer_email": "user@example.com"
  }'
```

### Deploy to Vercel
```bash
curl -X POST http://localhost:8000/agents/api_docs/deploy \
  -H "Content-Type: application/json" \
  -d '{
    "repo_url": "https://github.com/your-org/api-docs",
    "project_name": "api-docs"
  }'
```

---

## Worker Appraisal System

Each agent is appraised as a digital worker with:

- **Code Value**: $800 (production-ready algorithms)
- **IP Value**: $500 (proprietary methodology)
- **Infrastructure Value**: $300 (deployment config)
- **Documentation Value**: $200
- **Provenance Value**: $200
- **Complexity Premium**: $200-$500 (domain expertise)
- **Revenue Premium**: $400-$800 (monetization potential)

**Total Portfolio**: 30 agents × ~$2,500 avg = **~$75,000**

---

## Environment Variables

| Variable | Description |
|----------|-------------|
| `OPENAI_API_KEY` | OpenAI LLM access |
| `ANTHROPIC_API_KEY` | Claude LLM access |
| `GROQ_API_KEY` | Groq fast inference |
| `STRIPE_SECRET_KEY` | Payment processing |
| `TWILIO_ACCOUNT_SID` / `TWILIO_AUTH_TOKEN` | SMS/Voice |
| `SENDGRID_API_KEY` | Email delivery |
| `GITHUB_TOKEN` | Repo creation |
| `VERCEL_TOKEN` | Deployment |
| `DATABASE_URL` | PostgreSQL |
| `REDIS_URL` | Cache/queue |

---

## Tech Stack

- **Python 3.11** + **FastAPI**
- **PostgreSQL 15** + **Redis 7**
- **Stripe** (billing) + **Twilio** (SMS/voice) + **SendGrid** (email)
- **GitHub API** (repo creation) + **Vercel API** (deployment)
- **OpenAI / Anthropic / Groq** (LLM backends)
- **Docker** + **Docker Compose**
- **Prometheus** metrics + **Sentry** error tracking

---

## License

Proprietary - All rights reserved.
