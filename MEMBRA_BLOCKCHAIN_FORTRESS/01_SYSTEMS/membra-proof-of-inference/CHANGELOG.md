# Changelog

## v0.1.0 — 2026-05-25

**First public release. All four phases operational. `poi demo --fast` exits 0.**

### Phase 1 — Proof-of-Inference Core (`poi-core`)
- `ProofOfInference` struct: Ed25519-signed attestation binding model CID, prompt hash, token Merkle root, KV commitment, runtime fingerprint, hardware attestation, worker identity
- `KVCommitment`: per-layer SHA-256 hashes + cache size bytes
- `SamplerState`, `RuntimeFingerprint`, `HardwareAttestation`
- Challenge window expiry timestamp on every proof

### Phase 2 — Worker Trust (`worker-reputation`)
- `WorkerRegistry`: Ed25519 worker registration, status management (Pending → Active → Banned)
- `ReputationLedger`: valid PoI count, challenge pass/fail rate, uptime score, model consistency
- Trust multiplier tiers: 1.00× (≥0.90), 0.75× (≥0.75), 0.40× (≥0.50), 0.15× (≥0.25), 0× (<0.25)
- `ChallengeSystem`: canary prompt challenges, verification windows
- `set_trust_score` helper for seeding established workers in demos/tests

### Phase 4 — KV-State Collateral (`kv-state-collateral`)
- Four collateral types: KV-state, prefill, attention state, reasoning context
- Freshness decay: `value(t) = value(0) × e^(-3t)` across all types
- Per-type TTL: 6h / 12h / 4h / 8h
- Reuse bonus: +10% / +15% / +8% / +12% per reuse event
- Daily spend tracking per wallet

### Phase 3 — Emergent Memory Market (`memory-market`)
- `RetrievalTracker`: 24h sliding window deque, normalised frequency, retrieval velocity
- `ReferenceGraph`: 48h unique downstream inference tracking, reference density
- `AttentionDensityTracker`: KV-layer activation ratio, 24h window, peak density
- `EmergentPricingEngine`: semantic clusters (model CID + fingerprint prefix), Hamming similarity, `score_to_price`
- Composite score: `retrieval×0.30 + references×0.25 + semantic×0.20 + attention×0.25`
- All signals gated by worker trust multiplier
- Pricing: `base × (1 + score × 9.0)`, floor 1,000 lam, max 10× at score=1.0
- `catalog_mut` for post-registration KV dimension updates

### MemGas Protocol (`memgas-protocol`)
- `MemGasProtocol`: spend ledger, nonce anti-replay, daily wallet caps, relay validation, credit deduction
- Integration of Phase 3 + Phase 4: rising market price syncs back to `remaining_credit`
- `set_memory_kv_params`: links KV token/layer dimensions to market record after collateralisation
- Public accessors: `worker_registry()`, `reputation_ledger()`, `spend_ledger_mut()`

### CLI (`poi-cli`)
- `poi demo [--fast] [--steps N]`: 7-step interactive console, all numbers from live Rust
- `poi status`: full protocol dashboard (Phase 1–4 + market)
- `poi memgas`: register-memory, check-credit, validate-relay, relay-stats
- `poi worker`: register-worker, get-reputation, generate-challenge, submit-response
- `poi kv-state`: register-kv-state, register-prefill, get-worker-collateral, increment-reuse
- `poi market`: record-retrieval, record-reference, record-attention-reuse, get-record, get-price-history, top-memories, liquidity, pricing-params

### Demo Console — step-by-step verified output
| Step | Key output |
|---|---|
| 1 | Worker ID, PoI signed, inference ID, challenge window |
| 2 | Trust 1.00×, initial credit 10,185 lam |
| 3 | 32 SHA-256 layer commitments, 163,840 lam KV collateral |
| 4 | Price bar: 36,375 → 76,382 lam over 8 retrieval cycles |
| 5 | Burst peak 99,595 lam, cool-3 floor 30,074 lam |
| 6 | 33,098 lam relay-authorised, 66,198 lam remaining |
| 7 | JSON receipt with all fields from live computation |

### Packaging
- `README.md`: hero section, protocol diagram, formula tables, full CLI reference
- `DEMO.md`: per-step guide, `asciinema` recording script, investor talking points
- `examples/proof-receipt-sample.json`: annotated canonical receipt
- `landing/index.html`: Vercel-deployable dark landing page
- `CHANGELOG.md`: this file
