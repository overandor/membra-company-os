"""Tests for the computational-capital kernel. Run: python test_compute_capital.py (or pytest)."""
import copy
import compute_capital as CC

N = CC.SAMPLE_NODE


def test_hardware_depreciates_to_salvage_floor():
    assert CC.hardware_value(3000, 0) == 3000
    assert CC.hardware_value(3000, 24, 48) == 1500
    assert CC.hardware_value(3000, 999, 48, 0.10) == 300  # floored at salvage


def test_fresh_machine_has_near_zero_utility():
    fresh = copy.deepcopy(N)
    fresh["receipts"] = {"verified_fraction": 0, "restore_success_rate": 0}
    a = CC.appraise_node(fresh)
    assert a["recoverable_utility_value_usd"] == 0
    assert a["machine_value_usd"] == a["hardware_value_usd"]  # == resale


def test_accumulated_state_creates_premium_over_resale():
    a = CC.appraise_node(N)
    assert a["economic_premium_over_resale_usd"] > 0
    assert a["machine_value_usd"] > a["resale_value_usd"]


def test_unverified_receipts_are_excluded():
    a = CC.appraise_node(N)
    unv = copy.deepcopy(N); unv["receipts"]["verified_fraction"] = 0.0
    b = CC.appraise_node(unv)
    assert b["recoverable_utility_value_usd"] == 0      # nothing verified => nothing counts
    assert b["recoverable_utility_value_usd"] < a["recoverable_utility_value_usd"]


def test_restore_failure_zeroes_utility():
    bad = copy.deepcopy(N); bad["receipts"]["restore_success_rate"] = 0.0
    assert CC.appraise_node(bad)["recoverable_utility_value_usd"] == 0


def test_compression_liability_reduces_net():
    a = CC.appraise_node(N)
    assert a["net_recoverable_utility_usd"] == max(
        0, a["recoverable_utility_value_usd"] - a["reconstruction_liability_usd"])


def test_underwriting_overlay_is_conservative():
    a = CC.appraise_node(N)
    o = CC.node_underwriting_overlay(N)
    # eligible collateral must be far below raw machine value (illiquid, non-transferable)
    assert 0 < o["eligible_collateral_usd"] < a["machine_value_usd"]
    assert any("non_transferable" in f for f in o["risk_flags"])


def test_balance_sheet_balances():
    bs = CC.computational_balance_sheet(N)
    eq = bs["assets"]["hardware_resale"] + max(
        0, bs["assets"]["recoverable_utility"] - bs["liabilities"]["reconstruction_obligation"])
    assert bs["equity_machine_value"] == eq


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for fn in fns:
        fn(); print(f"PASS {fn.__name__}")
    print(f"\n{len(fns)}/{len(fns)} tests passed")
