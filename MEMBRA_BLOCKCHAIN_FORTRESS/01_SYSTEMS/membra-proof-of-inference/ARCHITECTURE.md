# Proof-of-Inference (PoI) Network

## Overview
Custom blockchain for cryptographically attestable LLM inference with Solana bridge.

## Architecture
```
Inference Workers → PoI Generation → PoI Network → Solana Bridge → Solana
```

## PoI Proof Structure
- model_cid: IPFS CID of GGUF
- prompt_hash: SHA256 of input
- token_sequence_hash: Merkle root of output
- kv_commitment: KV cache commitment
- sampler_state: generation parameters
- hardware_attestation: runtime fingerprint
- signature: cryptographic proof

## Consensus
Proof-of-Inference: validators verify proof validity before inclusion.
