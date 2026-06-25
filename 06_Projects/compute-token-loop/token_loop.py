#!/usr/bin/env python3
"""
token_loop.py — the full compute token launch loop.

Wires the modules already on main into one cycle ("compute becomes liquidity"):

  AMORTIZE      machine_value = hardware (depreciating) + recoverable utility (accruing)
   -> COLLATERALIZE   underwrite that utility into a finance-readable Attributable Value Receipt
     -> BENCHMARK     rank nodes; pool eligible, settled collateral
       -> LIQUIDIFY   over-collateralized backing -> token supply + NAV
         -> LOOP      new work -> new receipts -> re-amortize -> re-back -> updated NAV

HONEST BY CONSTRUCTION (the whole-session throughline):
  * Backed by MODELED, UNDERWRITTEN, pre-revenue compute value with heavy haircuts.
  * Recoverable state is largely NON-TRANSFERABLE -> low exchangeability -> big haircut.
  * Over-collateralized: each $1 of token face is backed by OCR dollars of collateral.
  * NAV here = modeled backing-per-token, NOT a market price; "launch" = a backing model
    + auditable reserve ledger, NOT a securities offering or redemption guarantee.
  * A token is honest iff its underlying receipts are real/verified. Gamed receipts are
    rejected by the underwriter and contribute ZERO backing.

Imports compute_capital (amortization) and aau (collateralization) from sibling projects.
stdlib only. Deterministic. python3 token_loop.py
"""
from __future__ import annotations
import copy, hashlib, json, os, sys, time
from dataclasses import dataclass

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, "..", "attribution-underwriting"))
sys.path.insert(0, os.path.join(_HERE, "..", "underwriting-pipeline"))
import aau as AAU                      # noqa: E402
import compute_capital as CC          # noqa: E402

OCR = 2.0            # over-collateralization ratio (200% backed)
TOKEN_FACE = 1.0     # $ face value per token


def _h(o) -> str:
    return hashlib.sha256(json.dumps(o, sort_keys=True, separators=(",", ":"), default=str).encode()).hexdigest()


# ---------------------------------------------------------- 1+2. amortize+collateralize
def collateralize(node: dict) -> dict:
    """Amortize a node, then underwrite its recoverable utility into finance-readable collateral."""
    appr = CC.appraise_node(node)
    r = node["receipts"]
    baseline = AAU.Baseline(before_cost_usd=node["purchase_price_usd"],
                            workload_fingerprint=f"node:{node['id']}",
                            invoices_hash=_h(r), ts=node.get("as_of", "2026-06-21"))
    claim = AAU.ValueClaim(
        claim_id=f"node:{node['id']}", issuer=node["id"], baseline=baseline,
        claimed_savings_usd=appr["net_recoverable_utility_usd"],
        counterfactual_fraction=0.20,                       # some utility would exist anyway
        evidence=AAU.Evidence(invoices=False, logs=True,
                              controlled_experiment=r.get("verified_fraction", 0) >= 0.8,
                              workload_match=True),
        issuer_reputation=r.get("uptime_ratio", 0.9),
        settlement_status="settled" if r.get("verified_fraction", 0) >= 0.9 else "open",
        exchangeability=0.25,                               # recoverable state is non-transferable
        gaming=AAU.GamingFlags(**node.get("gaming", {})))
    receipt = AAU.underwrite(claim)
    return {"node": node["id"], "machine_value_usd": appr["machine_value_usd"],
            "net_recoverable_usd": appr["net_recoverable_utility_usd"],
            "finance_readable_usd": receipt["finance_readable_usd"],
            "status": receipt["status"], "appraisal": appr, "receipt": receipt}


# ---------------------------------------------------------- 3+4. benchmark + liquidify
def liquidify(nodes: list[dict]) -> dict:
    rows = sorted((collateralize(n) for n in nodes), key=lambda x: -x["finance_readable_usd"])
    pool = round(sum(r["finance_readable_usd"] for r in rows), 2)
    supply = round(pool / (OCR * TOKEN_FACE), 4)            # mint so each $1 face is OCR-backed
    backing_per_token = round(pool / supply, 4) if supply else 0.0
    return {"rows": rows, "pool_collateral_usd": pool, "token_supply": supply,
            "collateralization_ratio": OCR, "backing_per_token_usd": backing_per_token,
            "machine_value_total_usd": round(sum(r["machine_value_usd"] for r in rows), 2)}


# --------------------------------------------------------------- 5. launch loop
class ReserveLedger:
    def __init__(self): self.chain: list[dict] = []

    def record(self, epoch: int, snap: dict) -> dict:
        prev = self.chain[-1]["hash"] if self.chain else "0" * 64
        body = {"epoch": epoch, "pool_collateral_usd": snap["pool_collateral_usd"],
                "token_supply": snap["token_supply"], "ratio": snap["collateralization_ratio"]}
        e = {**body, "prev": prev, "hash": _h({"prev": prev, **body})}
        self.chain.append(e); return e

    def verify(self) -> bool:
        prev = "0" * 64
        for e in self.chain:
            if e["prev"] != prev or e["hash"] != _h({"prev": prev, "epoch": e["epoch"],
                    "pool_collateral_usd": e["pool_collateral_usd"], "token_supply": e["token_supply"],
                    "ratio": e["ratio"]}):
                return False
            prev = e["hash"]
        return True


def accrue(node: dict, factor: float = 1.4) -> dict:
    """One epoch of real work: the node's recoverable receipts grow (more cache/restore/tasks)."""
    n = copy.deepcopy(node)
    r = n["receipts"]
    r["compute_saved_usd"] = round(r.get("compute_saved_usd", 0) * factor, 2)
    r["cloud_cost_avoided_usd"] = round(r.get("cloud_cost_avoided_usd", 0) * factor, 2)
    r["tasks_completed"] = int(r.get("tasks_completed", 0) * factor)
    return n


def run_loop(nodes: list[dict], epochs: int = 3) -> dict:
    led = ReserveLedger()
    state = nodes
    history = []
    for ep in range(epochs):
        snap = liquidify(state)
        led.record(ep, snap)
        history.append({"epoch": ep, **{k: snap[k] for k in
                        ("pool_collateral_usd", "token_supply", "backing_per_token_usd", "machine_value_total_usd")}})
        state = [accrue(n) for n in state]            # real work between epochs
    return {"history": history, "reserve_ledger_verifies": led.verify(),
            "launch_manifest": launch_manifest(history[-1])}


def launch_manifest(final: dict) -> dict:
    return {
        "token": "COMP", "name": "Compute-Collateral Coordination Token",
        "backing_model": "over-collateralized by underwritten, amortized, non-transferable compute value",
        "collateralization_ratio": OCR, "token_face_usd": TOKEN_FACE,
        "circulating_supply": final["token_supply"], "backing_pool_usd": final["pool_collateral_usd"],
        "peg_type": "coordination claim on verified recoverable compute state (NOT redemption-guaranteed)",
        "disclaimers": ["modeled/underwritten pre-revenue collateral with heavy haircuts",
                        "NAV = backing-per-token, not market price",
                        "'launch' = backing model + auditable reserve ledger, not a securities offering"]}


# ---------------------------------------------------------------- demo --------
def _fleet() -> list[dict]:
    base = CC.SAMPLE_NODE
    a = copy.deepcopy(base); a["id"] = "mac-node-01"
    b = copy.deepcopy(base); b["id"] = "mac-node-02"; b["receipts"]["verified_fraction"] = 0.95
    c = copy.deepcopy(base); c["id"] = "linux-shadow-03"; c["receipts"]["restore_success_rate"] = 0.6
    g = copy.deepcopy(base); g["id"] = "sketchy-04"
    g["gaming"] = {"baseline_manipulated": True, "cherry_picked_window": True, "undisclosed_failures": True}
    return [a, b, c, g]


def main() -> None:
    fleet = _fleet()
    print("=" * 74, "\nAMORTIZE -> COLLATERALIZE -> BENCHMARK (per node)\n", "=" * 74, sep="")
    snap = liquidify(fleet)
    for r in snap["rows"]:
        print(f"  {r['node']:<16} machine ${r['machine_value_usd']:>6} | net_recoverable "
              f"${r['net_recoverable_usd']:>6} | collateral ${r['finance_readable_usd']:>7} | {r['status']}")
    print(f"\nLIQUIDIFY: pool collateral ${snap['pool_collateral_usd']} "
          f"-> supply {snap['token_supply']} COMP @ {int(OCR*100)}% backed "
          f"(${snap['backing_per_token_usd']}/token)")
    print(f"  (machine value total ${snap['machine_value_total_usd']} -> only "
          f"${snap['pool_collateral_usd']} is finance-readable collateral after haircuts)")

    print("\n" + "=" * 74 + "\nLAUNCH LOOP (work accrues -> collateral grows -> re-back)\n" + "=" * 74)
    res = run_loop(fleet, epochs=3)
    for h in res["history"]:
        print(f"  epoch {h['epoch']}: pool ${h['pool_collateral_usd']:>8} | supply "
              f"{h['token_supply']:>9} COMP | backing ${h['backing_per_token_usd']}/tok")
    print(f"\nreserve ledger verifies: {res['reserve_ledger_verifies']}")
    print("\nLAUNCH MANIFEST:")
    print(json.dumps(res["launch_manifest"], indent=2))
    print("\nMost compressed: amortized + underwritten compute value, pooled and "
          "over-collateralized into a coordination token — backed by verified receipts, not by story.")


if __name__ == "__main__":
    main()
