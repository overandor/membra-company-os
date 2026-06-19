"""Tests for the underwriting pipeline. Run: python test_underwrite.py  (or pytest)."""
import json, os
import underwrite as U

HERE = os.path.dirname(__file__)
M = json.load(open(os.path.join(HERE, "sample_input_overandor.json")))


def test_valuation_in_expected_band():
    v = U.value(M)
    assert 90_000 <= v["central_net_realizable_usd"] <= 300_000, v
    assert v["gross_replacement_ceiling_usd"] > v["central_net_realizable_usd"]
    assert v["tenure_months"] > 12


def test_benchmark_top_one_percent():
    b = U.benchmark(M)
    assert b["repo_top_percent_all"] < 1.0          # comfortably inside top 1%
    assert b["repo_rank_approx"] > 0
    assert "top" in b["claim"]


def test_risk_grade_is_conservative_when_pre_revenue():
    r = U.risk_score(M)
    assert r["grade"] in {"C", "D", "E"}            # no revenue + no IP entity => not investment grade
    assert 0.0 <= r["score"] <= 1.0


def test_borrowing_base_positive_and_bounded():
    v = U.value(M); r = U.risk_score(M); e = U.eligibility(v, r)
    assert 0 < e["borrowing_base_usd"] < v["central_net_realizable_usd"]
    assert 0 < e["advance_rate"] <= 0.5


def test_conditions_improve_terms():
    base = U.eligibility(U.value(M), U.risk_score(M))["borrowing_base_usd"]
    improved = U.with_conditions(M)["eligibility"]["borrowing_base_usd"]
    assert improved > base, (base, improved)        # IP + revenue must raise the base


def test_full_run_renders_memo():
    out = U.run(M)
    assert "Underwriting Memo" in out["memo_markdown"]
    assert out["decision"]["outcome"]
    assert out["scenario_conditions_met"]["risk"]["grade"]


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    passed = 0
    for fn in fns:
        fn(); passed += 1; print(f"PASS {fn.__name__}")
    print(f"\n{passed}/{len(fns)} tests passed")
