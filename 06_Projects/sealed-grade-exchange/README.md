# Sealed-Grade Exchange + Exoatomic Liquidity — pre-semantic finance primitives

Two reference mechanisms for pricing/settling value **before it becomes a fully
interpreted object** — the micro-layer under the MEMBRA "provenance becomes
collateral" thesis. Both are deterministic, stdlib-only, tested, and emit
hash-chained receipts (the same primitive as `06_Projects/underwriting-pipeline/proofbook.py`).

| File | What it is | Run |
|---|---|---|
| `assay.py` | **Sealed-Grade Exchange (SGE)** — price a *bonded, deterministically-checkable grade* instead of the answer | `python assay.py` |
| `eil.py` | **Exoatomic Liquidity Carrier (XLC / EIL)** — intercept value *above the meaning layer* and settle it **atomically** | `python eil.py` |
| `test_assay.py` / `test_eil.py` | 6 + 7 tests, all passing | `python test_assay.py` |

## 1. SGE — "sell the assay, not the answer"
Answers don't sell themselves because of three classic failures, each threaded here:
- **Arrow's paradox** (can't value info until you hold it) → the buyer values a *public, content-addressed grade*, never the hidden answer.
- **Akerlof's lemons** (quality claims are cheap talk) → the seller bonds the grade; anyone re-runs the deterministic grader on reveal and **slashes the bond** if the claim was false. Cheap talk becomes costly talk.
- **Non-rivalry** (copies → price 0) → answer ships encrypted; payment releases the key (first sale).

Trust **relocates** from the unverifiable answer onto a reusable, auditable grader. Demo shows honest seller **SETTLED**, grade-liar **SLASHED**, bait-and-switch **SLASHED**, a second grader (set-cover) **SETTLED**, money conserved, chain verified.

**Boundary (the kill criterion):** sound *only* where quality is a deterministic, machine-checkable predicate (preimage, constraint solution, held-out test pass, route length). For prose/strategy/explanations with no honest grader, the market can't form — those sell time, liability, a resolving event, or a relationship. *The opportunity is building cheap graders for domains that lack them.*

## 2. EIL — atomic interception above meaning
Pipeline: `μ → C̄ → R → Ⓐ → Σ → V ⊖ γ` (latent → compress → route → **atomic** activate → aggregate → verify → subtract semantic residue → settle).

**Defensible kernel (real):**
- **Atomicity** — all-or-nothing (ACID / atomic-swap). Any failed gate rolls the whole interception back to `γ = 0`. No half-settled value. *(Demo: an oversized route rolls back to 0.)*
- **Meaning-distance** `D_vm = V_retained − M_retained` — value and meaning accounted separately; a carrier can keep value while shedding meaning. *(Excess meaning-drift `δM > ε` is gated out.)*
- **Anti-MEV objective** — predatory extraction `Π_interceptor·δM·H·O` is penalized; surplus returned to the originator is rewarded. The genetic search *learns* to prefer clean, high-rebate, deferred (TWAP-sliced) routes. *(Demo: `Ξ*` evolves to the clean venue, 62% surplus returned to the user, γ=$940; the predatory dark-relay is gated out.)*

**Analogy, not proof (honest):** the "exoatmospheric / midcourse interception" framing is evocative; the giant master equation is *implemented as code, not asserted as a proven optimum*. EIL settles only where value resolution is atomically verifiable — the same boundary as SGE's grader.

## How they connect to the rest of MEMBRA
Both are the **micro-settlement layer** beneath the macro stack:
- **ProofBook** — both emit hash-chained receipts; in production they write to the shared `proofbook.py` ledger.
- **Underwriting pipeline** — a bonded grade (SGE) or an atomically-settled interception (EIL) is exactly the kind of *audited receipt* that `compute_capital` / the underwriter count as real, verified output.
- **The thesis line** — value becomes financeable the moment its quality/settlement is *deterministically verifiable*. SGE verifies a grade; EIL verifies an atomic resolution. Everything else is the metaphor we refuse to bond.
