# Adversarial Attribution Underwriting (AAU)

The synthesis primitive of this repo's "value becomes financeable when verifiable" thesis.
A new economic object: **a finance-readable claim that a software/AI artifact caused
measurable value, discounted by adversarial attribution risk** — an *Attributable Value Receipt*.

```
software did something useful
  → lock the baseline ('before' world frozen + hashed)
  → counterfactual: subtract what would have happened anyway
  → attribute only the defensible portion
  → haircut for gaming / cherry-picking / confounders / weak evidence
  → weight by reputation, settlement status, exchangeability
  → settle into a comparable, poolable, financeable claim object
```

## The formula
```
FinanceReadableValue =
    AttributableDelta × Confidence × EvidenceWeight × ReputationWeight
                      × SettlementWeight × ExchangeabilityWeight
    − FraudRiskPenalty
```

## What it is / isn't
Not **analytics** (what happened), not **auditing** (verify records), not **A/B** (controlled
only), not a **standard** (syntax). It's closer to a **ratings agency / actuarial model /
value oracle** for software outcomes. The moat isn't owning a standard — it's owning the
continuously-updated **lie detector for value claims**.

## The four parts (and the kill criteria)
1. **Baseline locking** — the "before" world is frozen and hashed; later tampering is detectable.
2. **Counterfactual accounting** — not `before − after`, but minus *what would have happened anyway*.
3. **Adversarial haircuts** — discount for confounders, weak evidence, cherry-picking, issuer reputation, settlement status, non-exchangeability, and explicit gaming flags.
4. **Settled value objects** — machine-readable claim objects that can be compared, challenged, priced, insured, advanced against, **or rejected**.

Statuses the underwriter can return: `FINANCE_READABLE_OPEN`, `SETTLED_FINANCE_READABLE`,
`REAL_BUT_NOT_ATTRIBUTABLE`, `ATTRIBUTABLE_BUT_NOT_POOLABLE`, `VALID_BUT_FULLY_DISCOUNTED`,
`REJECTED_GAMING`.

## Wedge
**AI/API cost-savings claims** — because invoices, token logs, workload fingerprints, and
deploy timestamps make "AI caused value" verifiable without becoming fantasy.

## Run it
```bash
python aau.py          # worked example: $200 story -> $127 attributable -> ~$14 finance-readable
python test_aau.py     # 8 tests, or: pytest
```
Demo highlights: a $200 cost-savings *story* underwrites to a **~$14 finance-readable claim**;
the same claim **gamed** (manipulated baseline + cherry-picked window + hidden failures) is
**REJECTED**; a **controlled + settled + poolable** claim clears at ~$117.

## How it closes the loop
- **Response Backend Capsule** emits economic-activity events → **AAU underwrites** whether that value is real, attributable, and financeable.
- **ProofBook** — the settlement ledger is the same hash-chain; underwritten receipts are poolable.
- **Underwriting pipeline / computational-capital** — AAU is the per-claim engine; the pipeline pools settled receipts into a borrowing base.
- One line: *software impact becomes an underwritten claim, not a story.*
