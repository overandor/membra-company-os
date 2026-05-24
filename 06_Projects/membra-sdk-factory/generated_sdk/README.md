# Generated MEMBRA L0 SDK

Generated from `membra.network.json`.

## Network

- Name: MEMBRA
- Layer: L0
- Environment: devnet
- Default RPC: https://api.devnet.solana.com

## Generated clients

- `membra_solana_sdk.ts`
- `membra_l0_sdk.py`

## Primitive flow

1. Create MIR locally.
2. Register MIR on Solana devnet through Anchor.
3. M5 node attests inference or compute.
4. Quorum validates the receipt.
5. MCR binds repo proof, memory proof, MIR roots, and collateral score.
6. MEMBRA L0 uses this state for appraisal, rewards, routing, and transaction sponsorship.

## Privacy rule

No raw source code, private prompts, secrets, private keys, or chain-of-thought should be sent on-chain.
Only hashes, summaries, attestations, and settlement metadata are registered.
