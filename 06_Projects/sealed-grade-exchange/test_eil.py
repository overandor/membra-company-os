"""Tests for the Exoatomic Liquidity Carrier. Run: python test_eil.py (or pytest)."""
import eil as E

OMEGAS = [
    E.LiquidityState("clean-amm", 10_000, 20, 0.03, 0.15, 0.1),
    E.LiquidityState("dark-relay", 8_000, 8, 0.02, 0.85, 0.8),
    E.LiquidityState("batch-auction", 12_000, 12, 0.025, 0.25, 0.2),
]
CARRIER = E.compress(1_000.0, 100.0, ratio=0.8, cid="t-001")


def test_compress_retains_meaning_fraction():
    c = E.compress(1000, 100, 0.8, "c")
    assert abs(c.meaning_retained - 80.0) < 1e-9


def test_evolved_policy_settles_positive_and_atomic():
    best, res = E.evolve(OMEGAS, CARRIER, seed=7)
    assert res["atomic_ok"] is True
    assert res["gamma"] > 0
    assert res["dM"] <= E.EPS


def test_oversized_route_rolls_back_to_zero():
    over = E.RouteGenome(0, size_frac=5.0, slip_cap_bps=400, user_rebate=0.5, defer=False)
    r = E._resolve(over, OMEGAS, CARRIER)
    assert r["gates"]["atomicity"] == 0
    assert r["atomic_ok"] is False
    assert r["gamma"] == 0.0          # all-or-nothing


def test_predatory_route_is_gated_out():
    pred = E.RouteGenome(1, size_frac=0.5, slip_cap_bps=400, user_rebate=0.0, defer=False)
    r = E._resolve(pred, OMEGAS, CARRIER)
    assert r["gates"]["no_hidden_adverse"] == 0
    assert r["gamma"] == 0.0


def test_excess_meaning_drift_is_gated():
    lossy = E.compress(1000.0, 100.0, ratio=0.2, cid="lossy")   # only 20% meaning kept
    g = E.RouteGenome(0, size_frac=0.3, slip_cap_bps=400, user_rebate=0.5, defer=True)
    r = E._resolve(g, OMEGAS, lossy)
    assert r["dM"] > E.EPS
    assert r["gates"]["meaning_drift_ok"] == 0
    assert r["gamma"] == 0.0


def test_ga_beats_average_random_policy():
    import random
    rng = random.Random(1)
    best, res = E.evolve(OMEGAS, CARRIER, seed=7)
    rand_scores = [E.objective(E._rand_genome(rng, len(OMEGAS)), OMEGAS, CARRIER) for _ in range(40)]
    avg = sum(rand_scores) / len(rand_scores)
    assert res["gamma"] >= avg        # evolution should not underperform the mean


def test_objective_is_deterministic():
    b1 = E.evolve(OMEGAS, CARRIER, seed=7)[0]
    b2 = E.evolve(OMEGAS, CARRIER, seed=7)[0]
    assert b1 == b2


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for fn in fns:
        fn(); print(f"PASS {fn.__name__}")
    print(f"\n{len(fns)}/{len(fns)} tests passed")
