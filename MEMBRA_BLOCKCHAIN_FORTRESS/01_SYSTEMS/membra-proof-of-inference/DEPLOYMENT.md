# PoI Network Deployment Guide

## Prerequisites

- Rust 1.75+
- Solana CLI 1.18+
- Anchor 0.30+
- IPFS node (for model CID storage)

## 1. Deploy Solana Bridge

### Configure Solana

```bash
# Set to devnet for testing
solana config set --url devnet

# Create new keypair
solana-keygen new --outfile ~/.config/solana/id.json

# Airdrop SOL for fees
solana airdrop 2
```

### Deploy Anchor Program

```bash
cd poi-solana/programs/poi-bridge

# Build program
anchor build

# Deploy to devnet
anchor deploy --provider.cluster devnet

# Note the program ID
```

### Initialize Bridge

```bash
# Initialize the bridge with your authority
anchor run initialize --provider.cluster devnet
```

## 2. Start PoI Network Node

### Generate Validator Keypair

```bash
cargo run -p poi-cli -- generate-keypair
```

Save the output (public_key and secret_key) securely.

### Configure Node

Create `config.toml`:

```toml
[network]
block_time = 5
validator_keypair = "validator_keypair.json"

[bridge]
solana_rpc_url = "https://api.devnet.solana.com"
bridge_program_id = "YOUR_PROGRAM_ID"
relayer_keypair = "~/.config/solana/id.json"

[ipfs]
gateway_url = "https://ipfs.io"
```

### Start Node

```bash
cargo run -p poi-cli -- start-node --block-time 5
```

## 3. Integrate with Inference Workers

### Python Integration

```python
from examples.worker_integration import generate_poi_proof, compute_merkle_root

# After inference completes
proof = generate_poi_proof(prompt, tokens, model_cid)
submit_to_poi_network(proof)
```

### Rust Integration

```rust
use poi_core::{ProofOfInference, SamplerState, KVCommitment, RuntimeFingerprint, HardwareAttestation};
use poi_network::PoiNetwork;

let proof = ProofOfInference::new(
    model_cid,
    prompt.as_bytes(),
    &tokens,
    sampler_state,
    seed,
    kv_commitment,
    runtime_fingerprint,
    hardware_attestation,
    &keypair,
);

network.submit_proof(proof)?;
```

## 4. Start Bridge Relayer

```bash
# The relayer watches PoI network and relays to Solana
# TODO: implement relayer binary
cargo run -p poi-bridge -- relay
```

## 5. Verify Proofs on Solana

```bash
# Check if proof is registered
solana account <PROOF_PDA>

# Verify proof
anchor run verify-proof --inference-id <ID>
```

## Production Considerations

### Security
- Use hardware wallets for validator keys
- Enable SGX/Nitro attestation for hardware proofs
- Rotate keys regularly
- Use multi-sig for bridge authority

### Performance
- Tune block time based on TPS requirements
- Use dedicated relayer infrastructure
- Cache model CIDs locally
- Batch proof submissions

### Monitoring
- Monitor block production rate
- Track proof submission latency
- Alert on bridge relay failures
- Monitor Solana transaction costs

## Architecture Diagram

```
┌─────────────────┐
│ Inference Worker│
│ (llama.cpp/vLLM)│
└────────┬────────┘
         │ Generate PoI
         ↓
┌─────────────────┐
│  PoI Network    │
│  (Custom Chain) │
└────────┬────────┘
         │ Bridge Relayer
         ↓
┌─────────────────┐
│  Solana Bridge  │
│  (Anchor)       │
└─────────────────┘
```

## Troubleshooting

### Bridge deployment fails
- Check SOL balance: `solana balance`
- Verify program ID in Anchor.toml
- Check network is set correctly

### Proof submission fails
- Verify validator keypair exists
- Check PoI network is running
- Verify model CID format

### Relayer not syncing
- Check Solana RPC endpoint
- Verify relayer keypair has SOL
- Check network connectivity
