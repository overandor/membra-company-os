"""Tests for Adversarial Attribution Underwriting. python3 test_aau.py (or pytest)."""
import aau as A


def _baseline():
    return A.Baseline(200.0, "wl:tokens=1.2M", A._h({"spend": 6000}), "2026-05-01")


def _clean(**kw):
    d = dict(claim_id="c", issuer="membra", baseline=_baseline(), claimed_savings_usd=200.0,
             counterfactual_fraction=0.365,
             evidence=A.Evidence(invoices=True, logs=True, controlled_experiment=False, workload_match=True),
             issuer_reputation=0.6, settlement_status="open", exchangeability=0.7,
             gaming=A.GamingFlags())
    d.update(kw)
    return A.ValueClaim(**d)


def test_baseline_lock_deterministic_and_tamper_evident():
    b = _baseline()
    assert b.lock() == _baseline().lock()
    tampered = A.Baseline(150.0, "wl:tokens=1.2M", A._h({"spend": 6000}), "2026-05-01")
    assert tampered.lock() != b.lock()


def test_counterfactual_strips_what_would_happen_anyway():
    r = A.underwrite(_clean())
    assert r["attributable_usd"] == 127.0      # 200 * (1 - 0.365)
    assert r["attributable_usd"] < r["raw_claimed_usd"]


def test_clean_claim_is_positive_but_heavily_haircut():
    r = A.underwrite(_clean())
    assert 0 < r["finance_readable_usd"] < r["attributable_usd"]   # the haircut stack
    assert r["status"] == "FINANCE_READABLE_OPEN"


def test_gaming_is_rejected():
    g = A.GamingFlags(baseline_manipulated=True, cherry_picked_window=True, undisclosed_failures=True)
    r = A.underwrite(_clean(gaming=g))
    assert r["status"] == "REJECTED_GAMING"
    assert r["finance_readable_usd"] == 0.0


def test_strong_claim_beats_weak_claim():
    weak = A.underwrite(_clean())
    strong = A.underwrite(_clean(counterfactual_fraction=0.20, issuer_reputation=0.9,
                                 settlement_status="settled", exchangeability=0.9,
                                 evidence=A.Evidence(True, True, True, True)))
    assert strong["finance_readable_usd"] > weak["finance_readable_usd"]
    assert strong["status"] == "SETTLED_FINANCE_READABLE"


def test_no_real_delta_is_flagged():
    r = A.underwrite(_clean(counterfactual_fraction=0.98))
    assert r["status"] == "REAL_BUT_NOT_ATTRIBUTABLE"


def test_non_poolable_is_flagged():
    r = A.underwrite(_clean(exchangeability=0.1))
    assert r["status"] == "ATTRIBUTABLE_BUT_NOT_POOLABLE"


def test_settlement_pool_chain_verifies():
    led = A.SettlementLedger()
    led.settle(A.underwrite(_clean()))
    led.settle(A.underwrite(_clean(claim_id="c2")))
    assert led.verify()
    assert led.pool_value() > 0
    led.chain[0]["prev"] = "x" * 64          # tamper
    assert not led.verify()


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for fn in fns:
        fn(); print(f"PASS {fn.__name__}")
    print(f"\n{len(fns)}/{len(fns)} tests passed")
