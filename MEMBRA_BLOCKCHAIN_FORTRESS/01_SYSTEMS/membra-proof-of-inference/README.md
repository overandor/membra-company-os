# MEMBRA — Proof-of-Inference + MemGas Protocol

> **MEMBRA proves and prices AI cognition. It turns verified inference memory and reusable transformer state into temporary execution collateral.**

Run the live demo in one command:

```bash
cargo build --release && ./target/release/poi demo --fast
```

---

## What it does

When a GPU worker runs an LLM inference, MEMBRA:

1. **Proves** it happened — cryptographic Ed25519 attestation binding model, prompt, tokens, sampler, hardware, and worker identity
2. **Prices** the memory — an emergent market scores it by retrieval frequency, downstream references, semantic cluster cohesion, and KV-layer activation density
3. **Collateralises** the KV-state — live transformer caches become collateral with freshness decay
4. **Issues MemGas credit** — that credit sponsors Solana transactions; the user pays nothing
5. **Enforces trust** — every signal is gated by the worker's reputation multiplier; untrusted workers produce zero credit

```
Inference
  → Proof-of-Inference (Ed25519 signed)
  → Worker Trust (Phase 2)
  → Memory / KV-State Collateral (Phase 4)
  → Emergent Market Pricing (Phase 3)
  → MemGas Credit
  → Relay → Solana
```

---

## Quick start

```bash
# Clone and build (Rust 1.75+, no external dependencies)
git clone <repo>
cd membra-proof-of-inference
cargo build --release

# Run the 7-step live demo
./target/release/poi demo --fast

# Non-interactive (for CI / screen recording)
./target/release/poi demo --fast --steps 7

# Full protocol status dashboard
./target/release/poi status
```

---

## The 7-step demo

```
Step 1/7  Generate Inference Proof
          Ed25519 keypair → PoI attestation → signed by worker key

Step 2/7  Register Memory in Market
          Worker trust seeded → memory registered → MemGas credit issued

Step 3/7  Register KV-State Collateral
          32-layer × 4096-token KV cache → SHA256 commitments → lamport value

Step 4/7  Simulate Retrieval & Reuse Cycles
          8 retrieval events, downstream references, layer activation →
          live price bar + score breakdown per cycle

Step 5/7  Price Rise & Decay Simulation
          5 burst rounds → price climbs →
          cooling period → decay toward trust-only floor

Step 6/7  Spend MemGas Credit
          UserIntent → relay validation → lamports authorised

Step 7/7  Export Proof Receipt
          JSON audit receipt: worker, inference, KV-state, memgas, scores
```

Sample receipt: [`examples/proof-receipt-sample.json`](examples/proof-receipt-sample.json)

---

## Emergent pricing formula (Phase 3)

```
score = retrieval × 0.30
      + downstream_references × 0.25
      + semantic_cluster_cohesion × 0.20
      + attention_reuse_density × 0.25

score = score × worker_trust_multiplier   ← Phase 2 gate

price = base_lamports × (1 + score × 9.0)
price = max(price, 1_000)                 ← floor
```

| Signal | Window | Cap | Weight |
|---|---|---|---|
| Retrieval frequency | 24 h | 100 | 30 % |
| Downstream references | 48 h | 50 | 25 % |
| Semantic cluster cohesion | cluster | — | 20 % |
| Attention reuse density | 24 h | — | 25 % |

Worker trust multipliers:

| Trust score | Multiplier |
|---|---|
| ≥ 0.90 | 1.00× |
| 0.75–0.89 | 0.75× |
| 0.50–0.74 | 0.40× |
| 0.25–0.49 | 0.15× |
| < 0.25 | 0.00× (rejected) |

---

## KV-State Collateral (Phase 4)

Freshness decay: `value(t) = value(0) × e^(-3t)`

| Type | Rate | TTL | Reuse bonus |
|---|---|---|---|
| KV-state | 10 lam / KB | 6 h | +10 % / reuse |
| Prefill | 50 lam / token | 12 h | +15 % / reuse |
| Attention state | 5 lam / layer·token | 4 h | +8 % / reuse |
| Reasoning context | 100 lam / step | 8 h | +12 % / reuse |

---

## Crate structure

| Crate | Role |
|---|---|
| `poi-core` | `ProofOfInference` struct, Ed25519 signing, KV commitment |
| `poi-network` | Custom PoI consensus chain |
| `poi-bridge` | Solana relayer + MemGas integration |
| `memgas-protocol` | Gas credit ledger, relay validation, daily caps |
| `worker-reputation` | Ed25519 worker registry, challenge system, trust scoring |
| `kv-state-collateral` | KV-state / prefill / attention / reasoning collateral |
| `memory-market` | Emergent pricing engine, retrieval tracker, reference graph |
| `poi-cli` | `poi` binary — all CLI commands + demo console |

---

## Full CLI reference

```bash
poi status                           # Protocol dashboard
poi demo --fast                      # 7-step live demo
poi demo --steps 3                   # Run only first 3 steps

poi memgas register-memory ...       # Register memory → issue credit
poi memgas check-credit ...          # Query remaining credit
poi memgas validate-relay ...        # Consume credit for relay

poi worker register-worker ...       # Register GPU worker
poi worker get-reputation ...        # Query trust score
poi worker generate-challenge ...    # Issue verification challenge

poi kv-state register-kv-state ...   # Collateralise KV cache
poi kv-state register-prefill ...    # Collateralise prefill
poi kv-state get-worker-collateral . # Total worker collateral
poi kv-state increment-reuse ...     # Mark reuse → reprice

poi market record-retrieval ...      # Signal: memory retrieved
poi market record-reference ...      # Signal: downstream inference used memory
poi market record-attention-reuse .. # Signal: KV layers activated
poi market get-record ...            # Full market record + score breakdown
poi market top-memories ...          # Leaderboard by emergent score
poi market liquidity                 # Total priced lamports in market
poi market pricing-params            # Pricing formula + signal weights
```

---

## Build notes

Optimised for Apple Silicon M5 Pro (`aarch64-apple-darwin`):
- `-C target-cpu=native` + NEON SIMD + ARMv8.5-A
- Fat LTO, LLD linker
- Configuration in `.cargo/config.toml`

Works on any `aarch64` or `x86_64` target with Rust ≥ 1.75.

---

## Documentation

| File | Contents |
|---|---|
| `MEMGAS_PROTOCOL.md` | Full MemGas protocol specification |
| `PHASE2_WORKER_TRUST.md` | Distributed worker trust system |
| `ARCHITECTURE.md` | PoI network architecture |
| `DEPLOYMENT.md` | Solana bridge deployment guide |
| `DEMO.md` | Screen recording script + local demo walkthrough |
| `examples/proof-receipt-sample.json` | Annotated sample proof receipt |
