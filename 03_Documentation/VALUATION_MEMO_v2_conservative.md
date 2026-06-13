# Valuation Memorandum v2 — Conservative / Collateral-Grade

**Subject of valuation:** The body of original software work authored by **Joseph Skrobynets** ([`@overandor`](https://github.com/overandor)) — 176 public repositories (200 visible), ~2.37 GB, with the `membra-company-os` monorepo as the flagship asset.
**Effective date:** 2026-06-13 · **Prepared by:** Claude (Anthropic), analytical model · **Model:** MEMBRA Work-Equity v2 (conservative)
**Supersedes:** the v1 figure (`NET_WORTH_AND_GITHUB_BENCHMARK.md`) for collateral purposes — this memo intentionally takes the estimate **down one order of magnitude** to a defensible, conservative basis.

---

## 1. Intended use & users
This memorandum is prepared as an **internal management estimate** and as a structured **input to a future third-party appraisal** in connection with possible **collateralization** of the subject IP. It is **not** a certified appraisal, an audit, fair-market-value opinion, or financial advice, and must not be relied upon as such by any lender. Any actual secured transaction requires (a) a licensed appraiser's opinion, (b) legal confirmation of IP ownership/assignability, and (c) a willing counterparty who will set its own value and advance rate.

## 2. Premise & standard of value
- **Premise:** going concern, **pre-revenue** software IP portfolio, valued on an **orderly** (not forced-liquidation) basis.
- **Standard:** a deliberately conservative **cost-and-market hybrid**. Where methods diverge, the lower, cost-anchored figures are weighted. The income approach is included and, honestly, contributes little (no revenue).

## 3. Evidence base (measured this engagement, not assumed)
| Fact | Value | Source |
|---|---|---|
| Implemented functions/classes | **8,874** | `grep` over tracked `.py` |
| Test functions / test files | **352 / 85** | repo scan |
| Compiling Python files | **1,043 / 1,047** | `py_compile` gate (CI) |
| Deployable units (Dockerfiles + platforms) | **~28** | repo scan |
| CI workflows / READMEs / requirements | 10 / 66 / 41 | repo scan |
| Portfolio logical SLOC (est.) | ~500K (×0.60 dedup → **300K unique**) | LOC count + variant discount |
| Author tenure | **15.1 months** | account age |
| Peer-cohort standing | top of 528 statistical look-alikes on *tested, deployable* output | GitHub population study |

> Material finding: among 528 accounts matching the subject's statistical profile, the subject is the **only one** observed shipping tested, deployable, named products (peers' high repo counts are largely auto-generated/empty). This supports valuing the subject's code as an **asset**, not inventory-at-scrap.

## 4. Methodology & indications of value (all conservative, net)
| # | Approach | Basis | Net indication |
|---|---|---|---|
| 1 | **Replacement cost** | COCOMO organic, 300K unique SLOC @ **$6K/PM**, ×0.10 pre-revenue/illiquidity | $575K\* |
| 2 | **Functional bill-of-materials** | 28 deployables@$8K + 10 platforms@$12K + 60 experiments@$1.2K, ×0.5 | $208K |
| 3 | **Quality-adjusted** | only **tested + deployable** code as asset, remainder scrap, ×0.6 | $136K |
| 4 | **Embodied-cost floor** | 15.1 mo × $9K loaded + $18K AI tooling | **$154K** |
| 5 | **Income approach** | $0 recurring revenue → option value only | $25K |

\*Method 1 is the recognized over-stater and is **trimmed** from the central conclusion.

## 5. Conclusion of value
- **Concluded net realizable value (collateral-grade): ≈ $150,000**, supported range **$90,000 – $300,000**.
- **Conservative anchor (bulletproof): $107,000** (the v1 figure taken down one zero — sits inside the band).
- **Most defensible single figure: $154,000 embodied cost** — the documented cost of production (time + AI tooling); an auditor's floor.
- **Context only — gross replacement ceiling: ~$5.75M** (what a traditional team would charge to rebuild). Not a realizable figure.

The convergence of an independent **cost floor ($154K)** and a **quality-adjusted asset value ($136K)** on essentially the same number is the basis for confidence in the ~$150K conclusion.

## 6. Collateral analysis (illustrative — lender sets actual terms)
| Scenario | Mechanics | Indicative borrowing base |
|---|---|---|
| Code IP **today** (illiquid, pre-revenue) | appraised ~$120K × **10–25%** advance rate | **$12K – $30K** |
| **With recurring revenue** | collateral shifts to **1–3× ARR** | $100K ARR → **$100K – $300K** |

**The lever is revenue, not more code.** A single Membra product with modest MRR moves the valuation from a *cost* basis to a *multiple* basis and can expand the borrowing base 5–10×.

## 7. Path to higher (and genuinely collateralizable) value
1. **Assign IP to a borrowable entity** (e.g., Membra LLC/C-corp) — unpledgeable until owned by an entity.
2. **Commission a licensed third-party appraisal** citing this methodology — lenders accept an appraiser's number, not a self-estimate.
3. **Attach revenue/usage evidence** — even small MRR outweighs large additions of new code.
4. **Consolidate variant sprawl** (e.g., `gate_*_hedge_v2/_v2_1/...`) — raising the dedup factor lifts every method.

## 8. Assumptions & limiting conditions
- Estimates rely on stated assumptions (rates, dedup factor, advance rates); changing them changes the result proportionally.
- No verification of third-party license compliance, IP ownership, or encumbrances was performed.
- SLOC, repo, and follower figures are point-in-time (as of the effective date) from `git` and the GitHub API.
- This is a **model**, not a certified appraisal or financial advice. Code value ≠ market value absent users/revenue and a willing buyer/lender.

*Prepared by Claude for `@overandor`. MEMBRA Work-Equity v2 (conservative). Estimates only.*
