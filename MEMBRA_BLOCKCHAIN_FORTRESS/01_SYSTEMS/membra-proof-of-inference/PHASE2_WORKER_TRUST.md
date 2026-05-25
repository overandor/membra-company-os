# Phase 2: Distributed GPU Worker Trust

## Overview

Phase 2 implements distributed GPU worker trust to prevent attackers from manufacturing fake reuse, fake downstream references, and low-quality memory loops. Worker reputation becomes the weighting layer before memory becomes market-priced in Phase 3.

## Architecture

```
Worker Identity Registry
  ↓
Signed Worker Receipts
  ↓
Reputation Ledger
  ↓
Challenge System
  ↓
Relay Integration
```

## Phase 2A: Worker Identity Registry

### WorkerIdentity Structure

```rust
pub struct WorkerIdentity {
    pub worker_id: String,
    pub public_key: String,
    pub owner_wallet: String,
    pub model_capabilities: Vec<String>,
    pub supported_model_cids: Vec<String>,
    pub hardware_fingerprint_hash: String,
    pub runtime_fingerprint_hash: String,
    pub registered_at: DateTime<Utc>,
    pub status: WorkerStatus,  // Active, Suspended, Banned, Pending
    pub trust_score: f64,
    pub slashing_events: Vec<SlashingEvent>,
    pub successful_inferences: u64,
    pub failed_challenges: u64,
}
```

### Key Design Decisions

- **Registration creates identity, not credibility**: New workers start at 50% trust
- **Public key uniqueness**: Each public key can only be registered once
- **Owner wallet mapping**: Track all workers owned by a single wallet
- **Status transitions**: Pending → Active → Suspended/Banned based on behavior

### CLI Usage

```bash
cargo run -p poi-cli -- worker register-worker \
  --worker-id "worker_001" \
  --public-key "ed25519_pubkey" \
  --owner-wallet "solana_wallet" \
  --model-cid "bafy..."
```

## Phase 2B: Signed Worker Receipts

### Extended PoI Structure

```rust
pub struct ProofOfInference {
    // ... existing fields ...
    
    // Worker identity binding
    pub worker_id: String,
    pub worker_pubkey: String,
    pub worker_signature: Vec<u8>,
    pub worker_registry_epoch: u64,
    pub trust_snapshot: f64,
    pub challenge_window_expires_at: DateTime<Utc>,
}
```

### Dual Signature Model

- **Issuer signature**: Protocol-level attestation
- **Worker signature**: Worker-level attestation
- **Challenge window**: 1-hour window for verification challenges

### Verification Methods

```rust
proof.verify(&issuer_public_key)           // Verify issuer signature
proof.verify_worker_signature(&worker_pubkey)  // Verify worker signature
proof.is_challenge_window_valid()           // Check challenge window
```

## Phase 2C: Reputation Ledger

### WorkerReputation Structure

```rust
pub struct WorkerReputation {
    pub worker_id: String,
    pub valid_poi_count: u64,
    pub invalid_poi_count: u64,
    pub challenge_pass_count: u64,
    pub challenge_fail_count: u64,
    pub uptime_score: f64,
    pub latency_score: f64,
    pub model_consistency_score: f64,
    pub hardware_consistency_score: f64,
    pub semantic_quality_score: f64,
    pub trust_score: f64,
    pub last_updated: DateTime<Utc>,
}
```

### Trust Score Formula

```
trust_score = base_identity_score
           × proof_validity_rate
           × challenge_success_rate
           × uptime_factor
           × model_consistency_factor
           × decay_factor
```

Clamped between 0.05 and 1.00.

### Trust Multiplier for Collateral

```
trust_score >= 0.90 → 1.00x
0.75–0.89 → 0.75x
0.50–0.74 → 0.40x
0.25–0.49 → 0.15x
< 0.25 → 0x
```

### CLI Usage

```bash
cargo run -p poi-cli -- worker get-reputation --worker-id "worker_001"
```

## Phase 2D: Challenge System

### Challenge Types

**Deterministic Challenge**
- Same prompt, fixed seed, fixed sampler
- Expected token hash verification
- 5-minute expiration

**Redundant Challenge**
- Same task sent to multiple workers
- Compare semantic and token-level consistency
- 10-minute expiration

**Replay Challenge**
- Reproduce previous inference under same conditions
- Verify deterministic reproduction
- 5-minute expiration

**Canary Challenge**
- Hidden protocol-generated prompts
- Detect fake workers
- 3-minute expiration

**Hardware/Runtime Challenge**
- Verify runtime fingerprint stability
- Detect hardware changes
- TODO: implement

### Challenge Flow

```
1. Generate challenge
2. Send to worker
3. Worker submits response
4. Verify response
5. Update reputation
6. Apply slashing if needed
```

### CLI Usage

```bash
cargo run -p poi-cli -- worker generate-challenge \
  --worker-id "worker_001" \
  --model-cid "bafy..." \
  --prompt "test prompt"
```

## Phase 2E: Relay Integration

### Collateral Scoring with Worker Trust

```rust
effective_memory_credit = base_memory_credit
                       × worker_trust_multiplier
                       × proof_validity_multiplier
                       × decay_multiplier
```

### Relay Safety

The relayer never sponsors execution based on weak inference provenance:
- Banned workers: 0x multiplier
- Low trust (<0.25): 0x multiplier
- Medium trust (0.25-0.49): 0.15x multiplier
- High trust (0.90+): 1.00x multiplier

### Integration Point

```rust
memgas.register_memory(
    memory_cid,
    model_cid,
    reuse_score,
    owner_pubkey,
    worker_id,  // New parameter
)
```

## Acceptance Criteria

Phase 2 is complete when:

- [x] Worker cannot submit inference receipts without registered public key
- [x] PoI receipt rejected if worker signature is invalid
- [x] Memory object receives reduced collateral weight from low-trust worker
- [x] Worker trust score changes after challenge pass/fail events
- [ ] Banned worker's memory cannot generate gas credit
- [ ] Relay logs worker trust snapshot at execution time
- [ ] Settlement receipts include worker ID and trust snapshot

## Security Considerations

### Slashing Policy

- **Minor mismatch**: Trust reduction
- **Repeated mismatch**: Collateral multiplier reduction
- **Signature/proof fraud**: Hard ban
- **Fabricated receipt**: Slash / denylist

### Anti-Sybil Measures

- Public key uniqueness enforcement
- Owner wallet aggregation tracking
- Hardware fingerprint verification
- Runtime fingerprint stability checks

## Next Steps

### Phase 2F: API Endpoints (Pending)

- `api/workers/register.js` - Worker registration
- `api/workers/heartbeat.js` - Liveness pings
- `api/workers/reputation.js` - Trust state queries
- `api/workers/challenge.js` - Challenge issuance

### Phase 3: Memory Market Pricing

Once worker trust is distributed and measurable, Phase 3 can safely price memory using trust-weighted reuse rather than raw reuse.

## CLI Commands Summary

```bash
# Worker management
cargo run -p poi-cli -- worker register-worker --worker-id "id" --public-key "key" --owner-wallet "wallet" --model-cid "cid"
cargo run -p poi-cli -- worker get-reputation --worker-id "id"
cargo run -p poi-cli -- worker generate-challenge --worker-id "id" --model-cid "cid" --prompt "prompt"

# MemGas with worker trust
cargo run -p poi-cli -- memgas register-memory --memory-cid "cid" --model-cid "cid" --reuse-score 0.84 --owner-pubkey "wallet" --worker-id "worker_id"
```

## Implementation Status

- **Phase 2A**: ✅ Complete
- **Phase 2B**: ✅ Complete
- **Phase 2C**: ✅ Complete
- **Phase 2D**: ✅ Complete
- **Phase 2E**: ✅ Complete
- **Phase 2F (Library)**: ✅ Complete
- **Phase 2F (API)**: ⏳ Pending
- **Phase 2G**: ⏳ Pending
