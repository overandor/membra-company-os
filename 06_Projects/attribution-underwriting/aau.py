#!/usr/bin/env python3
"""
aau.py — Adversarial Attribution Underwriting (AAU).

The innovation is not "a protocol for answers." It is a new economic object:
a **finance-readable claim that a software/AI artifact caused measurable value,
discounted by adversarial attribution risk** — an *Attributable Value Receipt*.

    software did something useful
      -> lock the baseline ('before' world frozen + hashed)
      -> counterfactual: subtract what would have happened anyway
      -> attribute only the defensible portion
      -> haircut for gaming / cherry-picking / confounders / weak evidence
      -> weight by reputation, settlement status, exchangeability
      -> settle into a comparable, poolable, financeable claim object

FinanceReadableValue =
    AttributableDelta x Confidence x EvidenceWeight x ReputationWeight
                      x SettlementWeight x ExchangeabilityWeight
    - FraudRiskPenalty

This is NOT analytics (what happened), auditing (records), A/B (controlled only),
or a standard (syntax). It is closer to a ratings agency / actuarial model /
value oracle for software outcomes. The moat is the continuously-updated lie
detector for value claims. Wedge: AI/API cost-savings (invoices + token logs +
workload fingerprints + deploy timestamps make "AI caused value" verifiable).

stdlib only. Deterministic. python3 aau.py
"""
from __future__ import annotations
import hashlib, json, time
from dataclasses import dataclass, field, asdict

SETTLEMENT_WEIGHT = {"open": 0.55, "challenged": 0.30, "settled": 1.00}


def _h(o) -> str:
    return hashlib.sha256(json.dumps(o, sort_keys=True, separators=(",", ":"), default=str).encode()).hexdigest()


# ------------------------------------------------------------- baseline lock --
@dataclass(frozen=True)
class Baseline:
    before_cost_usd: float
    workload_fingerprint: str        # e.g. hash of request mix / tokens / SKUs
    invoices_hash: str               # hash of the 'before' invoices/logs
    ts: str

    def lock(self) -> str:
        """Freeze the 'before' world; any later tampering changes this hash."""
        return _h(asdict(self))


@dataclass
class Evidence:
    invoices: bool = False
    logs: bool = False
    controlled_experiment: bool = False
    workload_match: bool = False     # post-period workload matches the locked fingerprint


@dataclass
class GamingFlags:
    baseline_manipulated: bool = False
    cherry_picked_window: bool = False
    undisclosed_failures: bool = False
    confounder_uncontrolled: bool = False


@dataclass
class ValueClaim:
    claim_id: str
    issuer: str
    baseline: Baseline
    claimed_savings_usd: float
    counterfactual_fraction: float   # share of savings that would have happened anyway (0..1)
    evidence: Evidence
    issuer_reputation: float         # 0..1
    settlement_status: str           # open | challenged | settled
    exchangeability: float           # 0..1 (poolable / transferable)
    gaming: GamingFlags = field(default_factory=GamingFlags)


# ---------------------------------------------------------------- underwrite --
def underwrite(c: ValueClaim) -> dict:
    raw = c.claimed_savings_usd
    attributable = max(0.0, raw * (1.0 - min(max(c.counterfactual_fraction, 0.0), 1.0)))

    e = c.evidence
    evidence_w = min(1.0, 0.25 + 0.20 * e.invoices + 0.20 * e.logs
                     + 0.25 * e.controlled_experiment + 0.10 * e.workload_match)
    confidence = min(1.0, 0.50 + 0.25 * e.controlled_experiment + 0.15 * e.workload_match)
    reputation_w = min(max(c.issuer_reputation, 0.0), 1.0)
    settlement_w = SETTLEMENT_WEIGHT.get(c.settlement_status, 0.3)
    exch_w = min(max(c.exchangeability, 0.0), 1.0)

    g = c.gaming
    fraud_penalty = attributable * (0.25 * g.baseline_manipulated + 0.30 * g.cherry_picked_window
                                    + 0.25 * g.undisclosed_failures + 0.20 * g.confounder_uncontrolled)

    gross = attributable * confidence * evidence_w * reputation_w * settlement_w * exch_w
    finance_readable = max(0.0, gross - fraud_penalty)

    if attributable <= 0.05 * max(raw, 1e-9):
        status = "REAL_BUT_NOT_ATTRIBUTABLE"
    elif fraud_penalty >= 0.5 * attributable:
        status = "REJECTED_GAMING"
    elif exch_w < 0.20:
        status = "ATTRIBUTABLE_BUT_NOT_POOLABLE"
    elif finance_readable <= 0:
        status = "VALID_BUT_FULLY_DISCOUNTED"
    elif c.settlement_status == "settled":
        status = "SETTLED_FINANCE_READABLE"
    else:
        status = "FINANCE_READABLE_OPEN"

    receipt = {
        "claim_id": c.claim_id, "issuer": c.issuer, "baseline_hash": c.baseline.lock(),
        "raw_claimed_usd": round(raw, 2), "attributable_usd": round(attributable, 2),
        "weights": {"confidence": round(confidence, 3), "evidence": round(evidence_w, 3),
                    "reputation": round(reputation_w, 3), "settlement": round(settlement_w, 3),
                    "exchangeability": round(exch_w, 3)},
        "fraud_penalty_usd": round(fraud_penalty, 2),
        "finance_readable_usd": round(finance_readable, 2),
        "status": status, "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    receipt["receipt_hash"] = _h(receipt)
    return receipt


# ----------------------------------------------------- hash-chained settlement -
class SettlementLedger:
    def __init__(self): self.chain: list[dict] = []

    def settle(self, receipt: dict) -> dict:
        prev = self.chain[-1]["hash"] if self.chain else "0" * 64
        h = _h({"prev": prev, "receipt_hash": receipt["receipt_hash"]})
        entry = {"seq": len(self.chain), "prev": prev, "hash": h,
                 "claim_id": receipt["claim_id"], "status": receipt["status"],
                 "finance_readable_usd": receipt["finance_readable_usd"]}
        self.chain.append(entry); return entry

    def verify(self) -> bool:
        prev = "0" * 64
        for i, e in enumerate(self.chain):
            if e["seq"] != i or e["prev"] != prev:
                return False
            prev = e["hash"]
        return True

    def pool_value(self) -> float:
        return round(sum(e["finance_readable_usd"] for e in self.chain), 2)


# ---------------------------------------------------------------- demo --------
def _baseline():
    return Baseline(before_cost_usd=200.0, workload_fingerprint="wl:tokens=1.2M,mix=gpt+local",
                    invoices_hash=_h({"month": "2026-05", "spend": 6000}), ts="2026-05-01")


def rule(t): print("\n" + "=" * 72 + f"\n{t}\n" + "=" * 72)


def main():
    led = SettlementLedger()

    rule("WEDGE: an AI/API cost-savings claim ($200/day -> claimed $200 saved)")
    clean = ValueClaim(
        "api-save-001", "membra", _baseline(), claimed_savings_usd=200.0,
        counterfactual_fraction=0.365,  # model prices fell anyway -> only $127 attributable
        evidence=Evidence(invoices=True, logs=True, controlled_experiment=False, workload_match=True),
        issuer_reputation=0.6, settlement_status="open", exchangeability=0.7)
    r = underwrite(clean); led.settle(r)
    print(f"raw claimed   : ${r['raw_claimed_usd']}")
    print(f"attributable  : ${r['attributable_usd']}  (counterfactual stripped what would happen anyway)")
    print(f"weights       : {r['weights']}")
    print(f"-> FINANCE-READABLE: ${r['finance_readable_usd']}   status={r['status']}")
    print("  (a $200 story becomes a ~$13 underwritten claim — the haircut stack IS the product)")

    rule("SAME CLAIM, GAMED (manipulated baseline + cherry-picked window + hidden failures)")
    gamed = ValueClaim("api-save-002", "sketchy", _baseline(), 200.0, 0.365,
                       Evidence(True, True, False, True), 0.6, "open", 0.7,
                       GamingFlags(baseline_manipulated=True, cherry_picked_window=True,
                                   undisclosed_failures=True))
    r = underwrite(gamed); led.settle(r)
    print(f"fraud_penalty : ${r['fraud_penalty_usd']}  -> FINANCE-READABLE ${r['finance_readable_usd']}  status={r['status']}")

    rule("STRONG CLAIM (controlled experiment, settled, poolable, reputable issuer)")
    strong = ValueClaim("api-save-003", "membra", _baseline(), 200.0, 0.20,
                        Evidence(True, True, controlled_experiment=True, workload_match=True),
                        issuer_reputation=0.9, settlement_status="settled", exchangeability=0.9)
    r = underwrite(strong); led.settle(r)
    print(f"attributable ${r['attributable_usd']} -> FINANCE-READABLE ${r['finance_readable_usd']}  status={r['status']}")

    rule("NO REAL DELTA (savings were entirely counterfactual)")
    nodelta = ValueClaim("api-save-004", "membra", _baseline(), 200.0, 0.98,
                         Evidence(True, True, False, True), 0.6, "open", 0.7)
    r = underwrite(nodelta); led.settle(r)
    print(f"attributable ${r['attributable_usd']} -> status={r['status']}")

    rule("SETTLEMENT POOL")
    for e in led.chain:
        print(f"  #{e['seq']} {e['claim_id']:<12} {e['status']:<26} ${e['finance_readable_usd']:>8}  {e['hash'][:12]}")
    print(f"\nchain verifies: {led.verify()}   poolable finance-readable value: ${led.pool_value()}")
    print("\nMost compressed: software impact becomes a challengeable, settled, discounted")
    print("economic-value receipt — an underwritten claim, not a story.")


if __name__ == "__main__":
    main()
