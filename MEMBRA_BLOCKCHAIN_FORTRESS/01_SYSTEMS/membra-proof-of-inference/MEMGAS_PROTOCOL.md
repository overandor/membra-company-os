# MemGas Protocol

**Memory-collateralized gas abstraction protocol where verified inference artifacts create temporary execution credit for sponsored Solana transactions.**

## Core Thesis

```
Verified inference memory becomes temporary collateral for sponsored network execution.
```

## Architecture

The MemGas Protocol operates across three planes:

### Execution Plane
- Vercel APIs (request routing, auth, rate limits)
- GPU workers (llama.cpp/vLLM inference)
- Solana relayer (sponsored transaction execution)

### Proof Plane
- PoI receipts (cryptographic proof of inference)
- Telemetry hashes (execution traces)
- IPFS memory (immutable storage)
- Ed25519 signatures (attestation)

### Economic Plane
- Scoring engine (reuse, trust, validity)
- Credit issuance (lamport allocation)
- Decay mechanisms (time-based value erosion)
- Spend accounting (ledger tracking)
- Memory market (collateral valuation)

## Full Stack

```
┌──────────────────────────────────────────────┐
│  User Interfaces                             │
│  Telegram Bot / Web App / API Client         │
└──────────────────────┬───────────────────────┘
                       ↓
┌──────────────────────────────────────────────┐
│  Vercel Gateway                              │
│  Auth, rate limits, request routing           │
└──────────────────────┬───────────────────────┘
                       ↓
┌──────────────────────────────────────────────┐
│  Inference Runtime Layer                     │
│  GPU worker / llama.cpp / GGUF / IPFS model   │
└──────────────────────┬───────────────────────┘
                       ↓
┌──────────────────────────────────────────────┐
│  Proof + Telemetry Layer                     │
│  PoI receipt, hashes, worker trust, traces    │
└──────────────────────┬───────────────────────┘
                       ↓
┌──────────────────────────────────────────────┐
│  Memory Layer                                │
│  IPFS memory object + signed issuer record    │
└──────────────────────┬───────────────────────┘
                       ↓
┌──────────────────────────────────────────────┐
│  Collateral Layer                            │
│  reuse score, decay, trust, proof validity    │
└──────────────────────┬───────────────────────┘
                       ↓
┌──────────────────────────────────────────────┐
│  Gas Credit Ledger                           │
│  temporary spend allowance in lamports        │
└──────────────────────┬───────────────────────┘
                       ↓
┌──────────────────────────────────────────────┐
│  Relayer Layer                               │
│  signed user intent + relayer fee payment     │
└──────────────────────┬───────────────────────┘
                       ↓
┌──────────────────────────────────────────────┐
│  Settlement Layer                            │
│  Solana transaction + receipt audit trail     │
└──────────────────────────────────────────────┘
```

## Protocol Lifecycle

1. User submits prompt
2. GPU worker runs inference
3. Output + telemetry return to Vercel
4. PoI receipt is created and signed
5. Receipt is pinned to IPFS
6. Memory object is created from prompt/output/proof
7. Memory is scored as collateral
8. Score converts to gas credit
9. User signs transaction intent
10. Relayer verifies intent + credit
11. Relayer pays SOL fee and broadcasts transaction
12. Receipt is stored for audit

## Data Structures

### MemoryObject

```json
{
  "schema_version": "memgas/0.1",
  "type": "MemoryObject",
  "memory_cid": "ipfs://bafy...",
  "model_cid": "ipfs://bafy...",
  "prompt_hash": "sha256...",
  "output_hash": "sha256...",
  "poi_receipt_cid": "ipfs://bafy...",
  "reuse_score": 84,
  "decay_rate": 0.03,
  "gas_credit_lamports": 50000,
  "owner_pubkey": "solana_wallet",
  "created_at": "iso_timestamp",
  "expires_at": "iso_timestamp",
  "issuer_signature": "ed25519..."
}
```

### UserIntent

```json
{
  "owner_pubkey": "solana_wallet_address",
  "nonce": "unique_nonce_string",
  "requested_lamports": 50000,
  "memory_cid": "ipfs://bafy...",
  "tx_data": "base64_encoded_transaction",
  "signature": "ed25519_signature"
}
```

## Scoring Engine

Gas credit calculation:

```
gas_credit = base_credit
           × proof_validity
           × reuse_score
           × worker_trust
           × freshness_decay
           × anti_sybil_multiplier
```

Default parameters:
- `base_credit`: 50,000 lamports
- `decay_rate`: 3% per hour
- `daily_wallet_cap`: 1,000,000 lamports
- `memory_expiration`: 24 hours

## Ledgers

### Nonce Ledger
Prevents replay attacks by tracking used nonces.

```
Key: nonce:{owner_pubkey}:{nonce}
Value: { used_at, tx_signature }
```

### Spend Ledger
Tracks memory credit spending per memory object.

```
Key: memory:{memory_cid}
Value: { total_credit, remaining_credit, expires_at }
```

### Memory Market Ledger
Tracks collateral accounting and reuse metrics.

```
Key: market:{memory_cid}
Value: { reuse_score, collateral_value, total_uses, last_used_at }
```

### Daily Spend Ledger
Enforces per-wallet daily caps.

```
Key: wallet:{pubkey}:daily_spend
Value: { total_spend, last_reset }
```

## Relayer Validation

The relayer enforces the following checks before sponsoring a transaction:

```
signed_user_intent
+ valid memory object
+ valid PoI receipt
+ unspent nonce
+ unexpired collateral
+ sufficient remaining credit
= sponsored transaction
```

## Security Boundaries

```
Vercel may decide.
GPU may compute.
IPFS may preserve.
Solana may settle.
Only the relayer wallet may pay.
```

**Critical**: Relayer private key must be stored in Vercel encrypted environment variables or a proper custody service (HSM, Turnkey, Fireblocks). Never commit relayer secrets to code.

## CLI Usage

### Register Memory

```bash
cargo run -p poi-cli -- memgas register-memory \
  --memory-cid "bafy..." \
  --model-cid "bafy..." \
  --reuse-score 0.84 \
  --owner-pubkey "solana_wallet"
```

### Check Credit

```bash
cargo run -p poi-cli -- memgas check-credit \
  --memory-cid "bafy..."
```

### Validate Relay

```bash
cargo run -p poi-cli -- memgas validate-relay \
  --owner-pubkey "solana_wallet" \
  --nonce "unique_nonce" \
  --requested-lamports 50000 \
  --memory-cid "bafy..."
```

### Set Worker Trust

```bash
cargo run -p poi-cli -- memgas set-worker-trust \
  --worker-id "worker_001" \
  --trust-score 0.95
```

## Economic Engine

The feedback loop that makes MemGas a primitive:

```
Memory Market
  ↓
Reusable cognition gains demand
  ↓
Demand increases collateral value
  ↓
Collateral value increases gas credit
  ↓
More execution produces more memory
```

Core economic engine:

```
cognitive reuse → collateral depth → gas sponsorship capacity
```

## Integration with PoI Network

The MemGas protocol integrates with the PoI network:

1. PoI proof generated from inference
2. Proof registered on PoI network
3. Bridge relayer registers memory in MemGas market
4. Memory scored based on PoI validity
5. Gas credit issued based on score
6. Sponsored transactions executed via Solana bridge

## Production Considerations

### Security
- Use HSM or custody service for relayer keys
- Implement rate limiting on all endpoints
- Add IP whitelisting for relayer operations
- Monitor for unusual spending patterns

### Performance
- Cache memory market data
- Batch nonce checks
- Use persistent storage for ledgers (Redis/PostgreSQL)
- Implement ledger pruning for expired entries

### Monitoring
- Track daily spend per wallet
- Monitor memory expiration rates
- Alert on nonce replay attempts
- Track collateral value distribution

## Future Enhancements

1. **Persistent Ledger Storage**: Move from in-memory to Redis/PostgreSQL
2. **Memory Market**: Allow memory trading between users
3. **Dynamic Scoring**: ML-based reuse prediction
4. **Multi-Chain Support**: Extend beyond Solana
5. **Staking**: Allow staking memory for higher credit multipliers

## License

MIT
