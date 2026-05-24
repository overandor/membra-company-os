# MEMBRA Layer-3 Protocol

Python-powered Solana L3 for proof-gated, community-approved, gas-deferred tokenomics.

## Architecture

```
┌──────────────────────────────────────────────┐
│  Python L3 (this repo)                       │
│  • Intents, proofs, relayers, oracles        │
│  • Identity linking, social scoring          │
│  • Governance proposals, voting              │
│  • Token routing, verified adapters          │
├──────────────────────────────────────────────┤
│  Solana L1                                   │
│  • Final settlement, token transfers         │
│  • Vaults, signatures                        │
├──────────────────────────────────────────────┤
│  Rust/Anchor                                 │
│  • On-chain program enforcement              │
└──────────────────────────────────────────────┘
```

## Core Modules

| Module | Purpose |
|--------|---------|
| `proof_book.py` | Immutable append-only proof log (hash-chained) |
| `gas_vault.py` | Fee credit accounting + relayer reimbursement |
| `volatility_oracle.py` | TWAP monitoring, Proof-of-Volatility signals |
| `intent_network.py` | Gas-deferred payment intents (7-day claim window) |
| `token_router.py` | Verified adapters for SPL and cross-chain routing |
| `identity.py` | Social/payment identity linking, reputation scoring |
| `relayer.py` | Submits txs, pays gas, gets reimbursed from GasVault |
| `governance.py` | Proposal system, voting, authorization gates |

## Key Rules

- **Computation does NOT create lamports.** ZK compute earns fee credits, not free SOL.
- **GasVault must contain real SOL.** Relayers pay real fees, get reimbursed from reserves.
- **Social metrics are reputation, not collateral.** Venmo balance is not backing unless escrowed.
- **Every dangerous action is proof-gated, capped, logged, and governed.**
- **No autonomous execution.** Governance must authorize tokenomic actions.

## Quick Start

```bash
# Install
pip install -r requirements.txt

# Run demo
python run_demo.py

# Run tests
python -m pytest tests/ -v
```

## Demo Flow

1. Alice links Venmo + GitHub identity
2. Alice performs ZK compute → earns fee credits
3. Market shows volatility → Proof-of-Volatility logged
4. Alice creates gasless payment intent to Bob (0 SOL for sender)
5. Relayer picks up intent, pays gas, settles on Solana
6. GasVault reimburses relayer from SOL reserves
7. Governance proposal for capped emission → voted → executed

## One-Sentence Thesis

MEMBRA is a Python-powered Solana Layer-3 and elastic token protocol that uses Proof-of-Volatility, Community-Approved Proof-of-Development, ZK-verified compute, GasVault fee credits, and verified token-routing adapters to enable capped, auditable, sender-gasless, governance-controlled tokenomic actions without pretending to create SOL, guarantee price, or manufacture value.
