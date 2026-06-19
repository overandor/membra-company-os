# Repo Underwriting Pipeline

Turns a GitHub subject (an account + its body of work) into a **collateral-grade
underwriting decision** — the way a lender underwrites an asset. It operationalizes
the valuation, benchmark, and rank-claim analysis from this repo's valuation memos
(`03_Documentation/NET_WORTH_AND_GITHUB_BENCHMARK.md`, `VALUATION_MEMO_v2_conservative.md`)
into one deterministic, testable pipeline.

```
intake → collect → value → benchmark → risk → eligibility → decide → memo
```

## Stages
| Stage | What it does |
|-------|--------------|
| **intake** | Normalize subject identity (login, name, entity, dates) |
| **collect** | Gather metrics (repos, SLOC, tests, deployables, followers, tenure). Use the JSON input, or wire live GitHub/local-git collectors (queries documented in the memo's "Receipts") |
| **value** | 5-method conservative valuation → triangulated **net realizable value** (replacement/COCOMO, functional BOM, quality-adjusted, embodied-cost, income) |
| **benchmark** | Percentile/rank vs the GitHub population CDF → a defensible **top-X% claim** |
| **risk** | 8 weighted factors → **risk grade A–E** (revenue, IP ownership, liquidity, key-person, test coverage, security, duplication, deployability) |
| **eligibility** | Advance-rate matrix by grade → **borrowing base** |
| **decide** | APPROVE / APPROVE-WITH-CONDITIONS / DECLINE + conditions precedent + covenants |
| **memo** | Renders a lender-ready Markdown memo + machine-readable `decision.json` |

## Usage
```bash
cd 06_Projects/underwriting-pipeline
python underwrite.py --input sample_input_overandor.json --out out
python test_underwrite.py        # 6 tests, or: pytest
```
Outputs `out/underwriting_memo.md` and `out/decision.json`.

## Underwrite any GitHub user
Copy `sample_input_overandor.json`, fill in the subject's metrics, and run. The
benchmark CDF (in `config.py`, `GITHUB_POPULATION`) is sourced from GitHub's
`search/users` `total_count` and can be refreshed with the queries in the memo's
**Receipts** section, so every claim is reproducible by a third party.

## Worked example (this account, as-of 2026-06-15)
- **Decision:** APPROVE — WITH CONDITIONS PRECEDENT · **risk grade E** · **borrowing base ≈ $14,190**
- **Central net realizable value:** ≈ $177K (range $25K–$208K); gross replacement ceiling ≈ $5.7M
- **Rank claim:** top **0.062%** of 131.3M GitHub users by public-repo output; top **3.15%** by followers
- **Scenario — conditions met** (IP assigned to entity + first $100K ARR): grade **C**, advance 27%,
  **borrowing base rises to ≈ $41.6K** (**+$27K**) — the revenue + IP lever, quantified.

## Design notes
- **Conservative by construction.** Pre-revenue, no IP entity, single-author, and illiquid
  collateral all push the grade down (honest E today). The pipeline also computes the
  *post-conditions* scenario so the path to better terms is explicit.
- **Not financial advice / not a certified appraisal.** It's a credit *screen* and the
  structured input to a licensed appraisal + a willing lender, who set their own terms.
- All constants live in `config.py`. Tune rates, the advance matrix, and the population CDF.
