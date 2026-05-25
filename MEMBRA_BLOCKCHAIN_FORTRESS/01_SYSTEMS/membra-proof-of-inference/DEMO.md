# MEMBRA Demo Guide

> Run `poi demo --fast` and watch verified AI memory become gas credit.

---

## One-command local demo

```bash
# Prerequisites: Rust 1.75+
git clone <repo>
cd membra-proof-of-inference
cargo build --release
./target/release/poi demo --fast
```

Expected output: all 7 steps complete, exit 0, ~3 seconds.

### Flags

| Flag | Effect |
|---|---|
| `--fast` | Skip interactive pauses (non-blocking, for recording) |
| `--steps N` | Run only the first N steps (1–7) |

---

## What each step proves

### Step 1 — Generate Inference Proof
Generates a fresh Ed25519 keypair, builds a `ProofOfInference` struct with real
SHA-256 prompt hash, token Merkle root, KV commitment, hardware attestation, and
signs it with both the issuer key and the worker key. The challenge window
timestamp is printed — after it expires the proof can no longer be contested.

**What to show:** worker ID, public key prefix, inference ID, challenge window.

---

### Step 2 — Register Memory in Market
Registers the worker in `WorkerRegistry`, sets its trust score to 0.95
(representing an established worker with a proven track record), then calls
`MemGasProtocol::register_memory`. The resulting MemGas credit is the initial
collateral value: `base_credit × reuse_score × trust_multiplier`.

**What to show:** trust multiplier = 1.00×, initial gas credit in lamports.

---

### Step 3 — Register KV-State Collateral
Constructs 32 SHA-256 layer hashes and calls `KVStateCollateral::register_kv_state`
with the actual 32 MB cache size (32 layers × 4096 tokens × 128 heads × 2 bytes).
The collateral value is computed as `10 lam/KB × size × trust_multiplier`.

**What to show:** 32 SHA-256 commitments, KV collateral value, total protocol collateral.

---

### Step 4 — Simulate Retrieval & Reuse Cycles
Fires 8 rounds of `record_market_retrieval` + `record_market_reference` +
`record_attention_reuse`. Each round activates 4 more KV layers (4 → 8 → … → 32).
After each round the composite emergent score is printed alongside a live price bar.
The score formula: `retrieval×0.30 + references×0.25 + semantic×0.20 + attention×0.25 × trust`.

**What to show:** score climbing 0.04 → 0.20 per cycle, all 4 signal components.

---

### Step 5 — Price Rise & Decay Simulation
Runs 5 burst rounds (3 retrievals + high-density attention each), then shows
3 cooling steps where price decays linearly toward the trust-only floor.
The floor is `(base_tokens × 5 + base_layers × 200) × trust`.

**What to show:** burst ▲ rows, cool ▼ rows, peak vs floor values.

---

### Step 6 — Spend MemGas Credit
Constructs a `UserIntent` with a unique nonce, calls `MemGasProtocol::validate_relay`
which checks: nonce not replayed, memory not expired, sufficient credit,
daily cap not exceeded — then deducts and authorises.

**What to show:** nonce, requested lamports, relay ✓, remaining credit.

---

### Step 7 — Export Proof Receipt
Assembles a structured JSON receipt combining worker, inference, KV-state,
memory market, and MemGas fields into an auditable document.
See [`examples/proof-receipt-sample.json`](examples/proof-receipt-sample.json).

**What to show:** full JSON with all numeric fields from live computation.

---

## Screen recording script

For a 90-second recording (e.g. with `asciinema`):

```bash
# Install asciinema
brew install asciinema

# Record
asciinema rec membra-demo.cast --cols 90 --rows 40

# Inside the recording:
./target/release/poi demo --fast

# Stop recording: Ctrl-D

# Upload
asciinema upload membra-demo.cast
```

Recommended terminal: iTerm2, 90×40, JetBrains Mono 13pt, dark theme.

---

## Investor talking points per step

| Step | One-liner |
|---|---|
| 1 | "Every inference is cryptographically notarised — no trust required" |
| 2 | "Proven workers generate credit automatically — no token purchase" |
| 3 | "The live KV cache is worth lamports the moment it's computed" |
| 4 | "Price is a market signal, not an admin decision" |
| 5 | "Unused memory decays. High-reuse memory appreciates. Natural pricing." |
| 6 | "The user's Solana tx is sponsored by AI memory. Gas abstraction is real." |
| 7 | "Every proof is auditable, exportable, and submittable on-chain" |

---

## Protocol stack summary

```
poi demo --fast
│
├─ poi-core          ProofOfInference (Ed25519, SHA-256, KV Merkle)
├─ worker-reputation WorkerRegistry + ReputationLedger + ChallengeSystem
├─ kv-state-collateral KVState / Prefill / Attention / Reasoning (e^-3t decay)
├─ memory-market     RetrievalTracker + ReferenceGraph + AttentionDensity
│                    + EmergentPricingEngine (semantic clusters)
├─ memgas-protocol   MemGasProtocol: credit ledger, relay, daily caps
└─ poi-cli           demo.rs — orchestrates all of the above
```

---

## Troubleshooting

**Build fails on non-Apple target:** remove `.cargo/config.toml` RUSTFLAGS line
(`-C target-cpu=native`) or add `--target x86_64-unknown-linux-gnu`.

**`poi demo` exits non-zero:** run `RUST_BACKTRACE=1 ./target/release/poi demo --fast`
and check for a string slice out-of-bounds — report the line number.

**Price bar stays empty:** this is expected when worker trust < 0.50;
the demo pre-seeds trust to 0.95 for the full run.
