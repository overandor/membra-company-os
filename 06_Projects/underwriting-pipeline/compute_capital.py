#!/usr/bin/env python3
"""
Computational Capital — node valuation kernel
=============================================
Makes the thesis equation executable and *honest*:

    machine_value = hardware_value(t)            # depreciates
                  + net_recoverable_utility(t)    # accrues from VERIFIED receipts,
                                                  # net of a reconstruction liability

Discipline baked in (see COMPUTATIONAL_CAPITAL_THESIS.md):
  * only the *verified* fraction of receipts counts (sybil/audit haircut);
  * restore-success gates everything (state you can't recover is worth ~0);
  * compression is NOT free liquidity — compressed state carries a
    reconstruction liability (future compute) subtracted from utility;
  * recoverable state is largely non-transferable, so its *collateral*
    eligibility is heavily haircut vs. its accounting value.

Run:  python compute_capital.py   |   tests: python test_compute_capital.py
"""
from __future__ import annotations
import json

CFG = {
    "fidelity_haircut": 0.20,        # quality/fidelity risk on recovered state
    "utility_eligible_fraction": 0.25,  # recoverable utility is illiquid/non-transferable
    "hardware_eligible_fraction": 0.60,  # hardware has a resale market
}


# ---------------------------------------------------------------- hardware ----
def hardware_value(purchase_price: float, age_months: float,
                   useful_life_months: float = 48, salvage_frac: float = 0.10) -> float:
    """Straight-line depreciation floored at salvage value."""
    frac = max(salvage_frac, 1.0 - age_months / max(useful_life_months, 1))
    return purchase_price * frac


# ----------------------------------------------------- recoverable utility ----
def recoverable_utility_value(r: dict) -> float:
    """Dollarized, VERIFIED, quality- and staleness-adjusted reusable state."""
    base = (r.get("compute_saved_usd", 0)
            + r.get("cloud_cost_avoided_usd", 0)
            + r.get("tasks_completed", 0) * r.get("usd_per_task", 0))
    # restore-success gates reusability; cache-hit scales it
    quality = (0.5 + 0.5 * r.get("cache_hit_rate", 0)) * r.get("restore_success_rate", 0)
    gross = base * quality * (1.0 - r.get("state_staleness", 0))
    # only verified receipts count; weight by uptime; apply fidelity haircut
    return gross * r.get("verified_fraction", 0) * r.get("uptime_ratio", 1.0) * (1 - CFG["fidelity_haircut"])


def reconstruction_liability(r: dict) -> float:
    """Future compute owed to rebuild compressed/recoverable state (compression is collateralized)."""
    return r.get("compressed_state_gb", 0) * r.get("reconstruct_cost_per_gb_usd", 0)


# --------------------------------------------------------------- appraisal ----
def appraise_node(node: dict) -> dict:
    r = node["receipts"]
    hw = hardware_value(node["purchase_price_usd"], node["age_months"],
                        node.get("useful_life_months", 48), node.get("salvage_frac", 0.10))
    ruv = recoverable_utility_value(r)
    liab = reconstruction_liability(r)
    net_recov = max(0.0, ruv - liab)
    machine = hw + net_recov
    cum_depreciation = node["purchase_price_usd"] - hw
    classification = "APPRECIATING (utility offsets depreciation)" if net_recov > cum_depreciation \
        else "DECLINING (depreciation outpaces accrued utility)"
    flags = []
    if r.get("verified_fraction", 0) < 1.0:
        flags.append("attestation_required: unverified receipts excluded; sybil risk")
    if r.get("restore_success_rate", 0) < 0.90:
        flags.append("low_restore_reliability: recoverability not proven")
    if r.get("state_staleness", 0) > 0.5:
        flags.append("stale_state: utility decaying")
    flags.append("non_transferable_state: limits liquidation-under-default")
    return {
        "hardware_value_usd": round(hw),
        "recoverable_utility_value_usd": round(ruv),
        "reconstruction_liability_usd": round(liab),
        "net_recoverable_utility_usd": round(net_recov),
        "machine_value_usd": round(machine),
        "resale_value_usd": round(hw),
        "economic_premium_over_resale_usd": round(machine - hw),
        "classification": classification,
        "risk_flags": flags,
    }


def computational_balance_sheet(node: dict) -> dict:
    a = appraise_node(node)
    return {
        "assets": {"hardware_resale": a["hardware_value_usd"],
                   "recoverable_utility": a["recoverable_utility_value_usd"]},
        "liabilities": {"reconstruction_obligation": a["reconstruction_liability_usd"]},
        "equity_machine_value": a["machine_value_usd"],
    }


def node_underwriting_overlay(node: dict) -> dict:
    """Convert a node appraisal into eligible collateral for the underwriting pipeline."""
    a = appraise_node(node)
    eligible = (a["hardware_value_usd"] * CFG["hardware_eligible_fraction"]
                + a["net_recoverable_utility_usd"] * CFG["utility_eligible_fraction"])
    return {
        "eligible_collateral_usd": round(eligible),
        "basis": {"hardware_pct": CFG["hardware_eligible_fraction"],
                  "utility_pct": CFG["utility_eligible_fraction"]},
        "risk_flags": a["risk_flags"],
        "note": "Feed eligible_collateral_usd into underwrite.eligibility as a node-collateral line.",
    }


SAMPLE_NODE = {
    "id": "membra-mac-node-01",
    "purchase_price_usd": 3000, "age_months": 12, "useful_life_months": 48, "salvage_frac": 0.10,
    "receipts": {
        "compute_saved_usd": 4000, "cloud_cost_avoided_usd": 2500,
        "tasks_completed": 1200, "usd_per_task": 1.5,
        "cache_hit_rate": 0.70, "restore_success_rate": 0.95, "uptime_ratio": 0.98,
        "verified_fraction": 0.60, "state_staleness": 0.20,
        "compressed_state_gb": 40, "reconstruct_cost_per_gb_usd": 5,
    },
}


def main() -> None:
    node = SAMPLE_NODE
    a = appraise_node(node)
    print(f"Node {node['id']}: bought ${node['purchase_price_usd']:,}, age {node['age_months']}mo")
    print(f"  resale (hardware) value     ${a['hardware_value_usd']:,}")
    print(f"  + net recoverable utility   ${a['net_recoverable_utility_usd']:,} "
          f"(gross ${a['recoverable_utility_value_usd']:,} - liab ${a['reconstruction_liability_usd']:,})")
    print(f"  = machine (economic) value  ${a['machine_value_usd']:,}  "
          f"[+${a['economic_premium_over_resale_usd']:,} over resale]")
    print(f"  {a['classification']}")
    print("  flags: " + "; ".join(a["risk_flags"]))
    print("  underwriting overlay: $%s eligible collateral"
          % f"{node_underwriting_overlay(node)['eligible_collateral_usd']:,}")


if __name__ == "__main__":
    main()
