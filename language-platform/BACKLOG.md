# CollateralOps Development Backlog

## Phase 1: Core API & Data Layer

- [ ] **T1** — Add SQLite + SQLAlchemy models (`Asset`, `ValuationSet`, `ProofEvent`, `RiskFlag`, `PacketSection`, `BuyerTarget`, `AgentWorkRecord`, `ImprovementTask`)
- [ ] **T2** — Wire dashboard HTML to real `/api/assets`, `/api/valuation`, `/api/proofs` endpoints (replace demo data)
- [ ] **T3** — Build Asset Register CRUD API with pagination, sorting, filtering
- [ ] **T4** — Build Financeability Score API with live calculation from asset attributes
- [ ] **T5** — Build Collateral Packet API with section completion tracking
- [ ] **T6** — Build Evidence Chain API with tamper-evident hash chaining
- [ ] **T7** — Add CSV/JSON bulk import endpoint for asset register
- [ ] **T8** — Add collateral packet PDF/JSON export endpoint

## Phase 2: Intelligence & Scoring Engine

- [ ] **T9** — Implement real financeability scoring engine with weighted components
- [ ] **T10** — Add GitHub/GitLab repo metadata integration (stars, forks, contributors, issues)
- [ ] **T11** — Build automated code quality scanner (cyclomatic complexity, test coverage)
- [ ] **T12** — Add dependency vulnerability scanner (CVE check against OSV/Snyk)
- [ ] **T13** — License compliance analyzer (SPDX parsing, conflict detection)
- [ ] **T14** — IP ownership verification pipeline (contributor agreement checks)
- [ ] **T15** — Risk flag detection engine (automated risk classification)

## Phase 3: Lender & Buyer Marketplace

- [ ] **T16** — Lender portal API with financeability-filtered asset views
- [ ] **T17** — Buyer discovery and matching engine (tech-stack compatibility scoring)
- [ ] **T18** — Liquidation route calculator with recovery percentage estimates
- [ ] **T19** — Recovery value estimation using comparable transaction data
- [ ] **T20** — Term sheet generator API (loan-to-value, covenants, collateral release)
- [ ] **T21** — Due diligence checklist API with completion tracking
- [ ] **T22** — NDA and access control for external lender/buyer parties

## Phase 4: Agent & Automation

- [ ] **T23** — LLM agent for asset improvement recommendations (uses Groq/Ollama)
- [ ] **T24** — Automated collateral packet assembly from scanned repo data
- [ ] **T25** — Agent work accounting API with time/cost tracking per asset
- [ ] **T26** — Improvement queue auto-prioritization by financeability impact
- [ ] **T27** — Scheduled re-appraisal cron job with delta alerting

## Phase 5: Platform, Security & Real-Time

- [ ] **T28** — WebSocket real-time updates for dashboard (live score changes, new proofs)
- [ ] **T29** — JWT authentication with role-based access (Builder, Lender, Buyer, Auditor)
- [ ] **T30** — Audit logging with cryptographic tamper-evident record chain
