"""Tests for the compute token launch loop. python3 test_token_loop.py (or pytest)."""
import copy
import token_loop as T


def _good():
    n = copy.deepcopy(T.CC.SAMPLE_NODE); n["id"] = "good-1"; return n


def _gamed():
    n = copy.deepcopy(T.CC.SAMPLE_NODE); n["id"] = "gamed-1"
    n["gaming"] = {"baseline_manipulated": True, "cherry_picked_window": True, "undisclosed_failures": True}
    return n


def test_collateral_is_haircut_below_machine_value():
    r = T.collateralize(_good())
    assert r["finance_readable_usd"] > 0
    assert r["finance_readable_usd"] < r["machine_value_usd"]          # heavy haircut
    assert r["finance_readable_usd"] < r["net_recoverable_usd"]        # non-transferable exchangeability


def test_gamed_node_contributes_zero_backing():
    r = T.collateralize(_gamed())
    assert r["status"] == "REJECTED_GAMING"
    assert r["finance_readable_usd"] == 0.0


def test_liquidify_is_over_collateralized_and_excludes_gamed():
    snap = T.liquidify([_good(), _gamed()])
    assert snap["collateralization_ratio"] == T.OCR
    assert abs(snap["backing_per_token_usd"] - T.OCR * T.TOKEN_FACE) < 1e-6     # 200% backed
    assert abs(snap["token_supply"] - snap["pool_collateral_usd"] / (T.OCR * T.TOKEN_FACE)) < 1e-6
    # gamed node adds nothing -> pool equals the single good node's collateral
    only_good = T.liquidify([_good()])["pool_collateral_usd"]
    assert abs(snap["pool_collateral_usd"] - only_good) < 1e-6


def test_loop_grows_backing_as_work_accrues():
    res = T.run_loop([_good(), _good()], epochs=3)
    pools = [h["pool_collateral_usd"] for h in res["history"]]
    assert pools[1] > pools[0] and pools[2] > pools[1]                 # collateral compounds with work
    assert res["reserve_ledger_verifies"] is True


def test_reserve_ledger_tamper_detected():
    led = T.ReserveLedger()
    led.record(0, T.liquidify([_good()]))
    led.record(1, T.liquidify([_good(), _good()]))
    assert led.verify()
    led.chain[0]["pool_collateral_usd"] = 999999
    assert not led.verify()


def test_launch_manifest_is_honest():
    res = T.run_loop([_good()], epochs=2)
    m = res["launch_manifest"]
    assert m["collateralization_ratio"] == T.OCR
    assert m["circulating_supply"] == res["history"][-1]["token_supply"]
    assert any("not market price" in d.lower() or "nav" in d.lower() for d in m["disclaimers"])
    assert "NOT redemption-guaranteed" in m["peg_type"]


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for fn in fns:
        fn(); print(f"PASS {fn.__name__}")
    print(f"\n{len(fns)}/{len(fns)} tests passed")
