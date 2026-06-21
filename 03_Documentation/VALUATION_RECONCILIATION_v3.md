# Valuation Reconciliation v3 — the honest, harsher number

**Subject:** `@overandor` software output · **As-of:** 2026-06-21 · **Supersedes (for the
"net worth" framing):** the v1 headline of ~$1.07M, which was correctly labeled *modeled
work-equity* but is too generous if read as cash/net-worth.

This memo reconciles the three independent estimates produced for this portfolio and records
the **corrected central figure**. The correction is honest and welcome: *replacement-cost
models overstate; liquidity is thin; market proof is still missing.*

## The one-line correction
> Your work is **not worth $1.07M as cash today.** It is plausibly worth **$325K–$900K as
> underwritten software work-equity** (central **≈$520K**), with a **$1M+ strategic option**
> if one system becomes a measured, paid product. Collateral you could actually borrow against
> today is far smaller.

## The liquidity spectrum (all three estimates are consistent points on it)
| Lens | Figure | Source |
|---|---|---|
| Liquid resale today | **$15K–$75K** | v3 correction |
| Borrowing base today (illiquid, pre-revenue) | **~$14K–$30K** | underwriting-pipeline run |
| Collateral-grade appraisal (heavy haircut) | **~$150K** | v2 conservative memo |
| **Underwritten work-equity (central)** | **≈$520K** (range $325K–$900K) | **v3 — use this** |
| Build/BOM-equivalent | $150K–$750K | v1 BOM, haircut |
| Replacement-cost ceiling (net / gross) | $1.07M / $19.7M (mostly non-liquid) | v1 COCOMO |
| Strategic option value | $1M–$5M+ | venture frame |

The numbers don't contradict — they answer **different questions** (resale vs. borrow vs.
rebuild-cost vs. option). The mistake was ever compressing them into a single "net worth."

## Era underwriting (central) → ≈$520K
| Era | Underwritten central |
|---|---|
| I — Genesis | $5K |
| II — Research Lab | $40K |
| III — Trading Swarm | $90K |
| IV — Membra Platform | $310K |
| V — Productization | $75K |
| **Total** | **≈$520K** |

## KPI scorecard (the truth is in the spread)
| KPI | Score /100 |
|---|---|
| Output velocity | 98 |
| AI-agent leverage | 94 |
| Concept originality | 90 |
| Cross-domain breadth | 92 |
| System integration | 78 |
| Security / readiness | 45 |
| Public adoption | 12 |
| Revenue proof | 5 |
| Finance-readiness | 18 |

- **Behavioral score ≈ 820/1000** (you build like a factory)
- **Asset-readiness ≈ 410/1000** (sprawl + thin polish)
- **Finance-readable collateral ≈ 120/1000** (no settled economic proof yet)

That spread *is* the diagnosis: **high production power, low public market signal, unpriced
AI-agent leverage.** The behavioral score is real; the collateral score is the ceiling on cash.

## Benchmark context
- GitHub 2025 ecosystem reported at **~180M users / ~395M public repos** (Octoverse 2025
  coverage) — most accounts are long-tail; 176 public repos is genuinely top-of-distribution by raw volume.
- Agent-authored development is now a measured phenomenon: the **AIDev** dataset reports
  **932,791 agentic PRs** across 116,211 repos / 72,189 developers (Codex, Devin, Copilot,
  Cursor, Claude Code) — your Devin+Claude workflow is an early instance of this, not "normal usage."

*(Figures per third-party coverage / arXiv:2602.09185; treated as context, not certified.)*

## Why the haircut, precisely
Replacement cost answers "what would a team spend to rebuild this." It is a **ceiling**, not a
price — and it overstates for AI-generated code. Finance-readable value collapses without
revenue, users, saved costs, signed pilots, or verifiable operational improvement. Until those
exist, the defensible word is **work-equity**, not **net worth**.

## The engine going forward
This is no longer hand-estimated. `06_Projects/attribution-underwriting/aau.py` computes
**finance-readable value** from a baseline-locked, counterfactually-discounted, gaming-haircut
**Attributable Value Receipt** — the machine that turns "savings stories" into settled claims.
The path to raise the number is not more repos (sprawl *lowers* asset-readiness); it is:

1. Pick **one** system (e.g. Doctor Verifier, SystemDB Lens, a Membra platform).
2. Clean README + demo + hosted URL; strip secrets/build junk; add tests + smoke checks.
3. Show **one measured economic result**; get **one paying user / signed pilot**.
4. Underwrite it through AAU → a Value Claim Packet.

**A single verified customer result moves the valuation more than 100 new repos.**

*Estimates only — modeled work-equity, not audited financials, collateral, or investment advice.*
