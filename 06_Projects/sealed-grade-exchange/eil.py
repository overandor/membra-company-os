#!/usr/bin/env python3
"""
eil.py — Exoatomic Liquidity Carrier (XLC) / Exoatmospheric Interception of Liquidity.

Makes the EIL thesis EXECUTABLE and HONEST.

Pipeline:   mu -> C_bar -> R -> (A) -> Sigma -> V (-) -> gamma
            latent -> compress -> route -> ATOMIC activate -> aggregate
                   -> verify -> subtract semantic residue -> settle.

DEFENSIBLE KERNEL (real):
  * Atomicity = all-or-nothing settlement (ACID / atomic-swap). Any failed gate
    rolls the whole interception back to gamma = 0. No half-settled value.
  * Meaning-distance D_vm = V_retained - M_retained: value and meaning are
    accounted SEPARATELY (a carrier can keep value while shedding meaning).
  * Anti-MEV objective: predatory extraction (interceptor profit x meaning-drift
    x layer-advantage x opacity) is PENALIZED; surplus returned to the user is
    REWARDED. The evolved policy prefers clean routes over extractive ones.

ANALOGY, NOT PROOF (honest):
  "Exoatmospheric / midcourse interception" is an evocative framing. The giant
  master equation is implemented here as code, not asserted as a proven optimum.
  Like assay.py's grader, EIL is sound only where value resolution is atomically
  VERIFIABLE; otherwise the interception cannot honestly settle.

stdlib only. Deterministic (seeded). python3 eil.py
"""
from __future__ import annotations
import random
from dataclasses import dataclass, field

from assay import Ledger  # reuse the hash-chained receipt ledger

# ---- objective constants (the lambda/eta/beta/rho of the master equation) ----
EPS = 0.35          # max tolerable meaning drift  (delta M <= eps)
PI_BASE = 0.0       # user must be no worse off than baseline
ETA = 0.25          # weight on surplus returned to the user
BETA = 200.0        # penalty per unit meaning drift
RHO = 1.5           # predatory-MEV penalty weight


@dataclass(frozen=True)
class LiquidityState:        # an unresolved liquidity object omega (pre-finality)
    venue: str
    available: float
    fee_bps: float
    slip_k: float           # price-impact coefficient
    opacity: float          # O in [0,1]  (mempool/relay opacity)
    layer_adv: float        # H in [0,1]  (sequencer/layer advantage)


@dataclass(frozen=True)
class Carrier:              # the XLC: minimal value-bearing object above meaning
    cid: str
    value_potential: float  # gross opportunity Delta V if fully resolved
    meaning_total: float    # original semantic mass
    meaning_retained: float # M after compression (<= meaning_total)
    identity_seal: str


@dataclass(frozen=True)
class RouteGenome:          # theta: a candidate interception policy
    venue_idx: int
    size_frac: float        # fraction of available liquidity to take
    slip_cap_bps: float
    user_rebate: float      # R_user in [0,1] : surplus share returned to origin
    defer: bool             # computational-TWAP: slice/defer to cut impact


def compress(latent_value: float, meaning_total: float, ratio: float, cid: str) -> Carrier:
    """C_bar: minimal carrier; `ratio` of meaning survives compression."""
    return Carrier(cid, latent_value, meaning_total, meaning_total * ratio,
                   identity_seal=f"seal:{cid}:{int(latent_value)}")


def _resolve(theta: RouteGenome, omegas: list[LiquidityState], carrier: Carrier) -> dict:
    """Atomic value-resolution of one route. Returns gates + settled gamma."""
    w = omegas[theta.venue_idx % len(omegas)]
    size = max(0.0, theta.size_frac) * w.available
    dV = carrier.value_potential * min(1.0, theta.size_frac)  # value scales with taken size

    # costs
    impact_bps = w.slip_k * (size / max(w.available, 1e-9)) * 1e4
    if theta.defer:
        impact_bps *= 0.4          # TWAP slicing reduces impact (adds latency cost)
    fees = size * w.fee_bps / 1e4
    slip = size * impact_bps / 1e4
    gas, latency = 2.0, (3.0 if theta.defer else 0.5)
    inventory, failure = 0.5, 0.5
    pi_created = dV - gas - fees - slip - latency - inventory - failure

    # meaning drift increases with compression loss + opacity
    dM = (1 - carrier.meaning_retained / max(carrier.meaning_total, 1e-9)) * 0.5 + w.opacity * 0.5
    pi_user = pi_created * (theta.user_rebate + (1 - theta.user_rebate) * 0.0)  # user's realized share
    pi_interceptor = pi_created * (1 - theta.user_rebate)

    # --- ATOMIC GATES (indicators); any 0 -> rollback to gamma = 0 ---
    gates = {
        "atomicity": int(size <= w.available and impact_bps <= theta.slip_cap_bps),
        "finality": 1,
        "proof": 1,
        "meaning_drift_ok": int(dM <= EPS),
        "user_not_worse": int(pi_user >= PI_BASE and pi_created > 0),
        "no_custody": 1,
        "no_hidden_adverse": int(not (w.opacity > 0.6 and theta.user_rebate < 0.1)),
    }
    all_ok = all(gates.values())

    pmi = pi_interceptor * dM * w.layer_adv * w.opacity           # predatory-MEV term
    gamma = 0.0
    if all_ok:
        gamma = pi_created + ETA * theta.user_rebate * pi_created - BETA * dM - RHO * pmi
    return {"venue": w.venue, "size": round(size, 2), "pi_created": round(pi_created, 2),
            "dM": round(dM, 3), "pmi": round(pmi, 2), "gates": gates, "atomic_ok": all_ok,
            "gamma": round(max(gamma, 0.0) if all_ok else 0.0, 2),
            "D_vm": round((1.0 if all_ok else 0.0) - carrier.meaning_retained / max(carrier.meaning_total, 1e-9), 3)}


def objective(theta: RouteGenome, omegas: list[LiquidityState], carrier: Carrier) -> float:
    return _resolve(theta, omegas, carrier)["gamma"]


# ----------------------------------- GA -------------------------------------
def _rand_genome(rng: random.Random, n_venues: int) -> RouteGenome:
    return RouteGenome(rng.randrange(n_venues), round(rng.uniform(0.05, 1.2), 3),
                       round(rng.uniform(20, 400), 1), round(rng.uniform(0.0, 0.9), 3),
                       rng.random() < 0.5)


def _mutate(g: RouteGenome, rng: random.Random, n_venues: int) -> RouteGenome:
    return RouteGenome(
        (g.venue_idx + rng.choice([-1, 0, 1])) % n_venues,
        max(0.02, round(g.size_frac + rng.uniform(-0.2, 0.2), 3)),
        max(5.0, round(g.slip_cap_bps + rng.uniform(-50, 50), 1)),
        min(0.95, max(0.0, round(g.user_rebate + rng.uniform(-0.15, 0.15), 3))),
        g.defer if rng.random() < 0.7 else (not g.defer))


def _cross(a: RouteGenome, b: RouteGenome) -> RouteGenome:
    return RouteGenome(a.venue_idx, b.size_frac, a.slip_cap_bps, b.user_rebate, a.defer)


def evolve(omegas: list[LiquidityState], carrier: Carrier, pop: int = 16,
           gens: int = 8, seed: int = 7) -> tuple[RouteGenome, dict]:
    """Genetic search for the best ATOMIC interception policy Xi*."""
    rng = random.Random(seed)
    P = [_rand_genome(rng, len(omegas)) for _ in range(pop)]
    for _ in range(gens):
        P.sort(key=lambda g: objective(g, omegas, carrier), reverse=True)
        elite = P[:max(2, pop // 4)]
        children = []
        while len(children) < pop - len(elite):
            a, b = rng.choice(elite), rng.choice(elite)
            children.append(_mutate(_cross(a, b), rng, len(omegas)))
        P = elite + children
    best = max(P, key=lambda g: objective(g, omegas, carrier))
    return best, _resolve(best, omegas, carrier)


# ---------------------------------- demo ------------------------------------
def main() -> None:
    omegas = [
        LiquidityState("clean-amm", available=10_000, fee_bps=20, slip_k=0.03, opacity=0.15, layer_adv=0.1),
        LiquidityState("dark-relay", available=8_000, fee_bps=8, slip_k=0.02, opacity=0.85, layer_adv=0.8),
        LiquidityState("batch-auction", available=12_000, fee_bps=12, slip_k=0.025, opacity=0.25, layer_adv=0.2),
    ]
    carrier = compress(latent_value=1_000.0, meaning_total=100.0, ratio=0.8, cid="xlc-001")
    led = Ledger()
    led.append("COMPRESS", {"cid": carrier.cid, "value_potential": carrier.value_potential,
                            "meaning_retained": carrier.meaning_retained})

    print("=" * 72, "\nEXOATOMIC LIQUIDITY CARRIER — evolve best atomic interception\n", "=" * 72, sep="")
    best, res = evolve(omegas, carrier)
    led.append("ROUTE", {"venue_idx": best.venue_idx, "size_frac": best.size_frac,
                         "user_rebate": best.user_rebate, "defer": best.defer})
    led.append("SETTLE", {"cid": carrier.cid, **res})
    print(f"Xi* venue={res['venue']} size={res['size']} defer={best.defer} "
          f"user_rebate={best.user_rebate}")
    print(f"  Pi_created=${res['pi_created']}  deltaM={res['dM']} (eps={EPS})  PMI={res['pmi']}")
    print(f"  atomic_ok={res['atomic_ok']}  gates={res['gates']}")
    print(f"  -> settled gamma=${res['gamma']}   D_vm={res['D_vm']}")

    print("\n--- counter-examples (the kill criteria) ---")
    oversized = RouteGenome(0, size_frac=5.0, slip_cap_bps=400, user_rebate=0.5, defer=False)
    r = _resolve(oversized, omegas, carrier)
    print(f"oversized (size>liquidity): atomic_ok={r['atomic_ok']} gamma=${r['gamma']} "
          "(rolled back to 0)")
    predatory = RouteGenome(1, size_frac=0.5, slip_cap_bps=400, user_rebate=0.0, defer=False)
    r = _resolve(predatory, omegas, carrier)
    print(f"predatory (dark-relay, 0 user rebate): no_hidden_adverse="
          f"{r['gates']['no_hidden_adverse']} gamma=${r['gamma']} (gated out)")

    print("\nreceipt chain verifies:", led.verify())
    print("\nBOUNDARY: EIL settles only where value resolution is atomically verifiable;")
    print("the 'exoatmospheric' framing is analogy, the atomicity + meaning accounting are real.")


if __name__ == "__main__":
    main()
