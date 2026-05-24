# MEMBRA L3 — Multi-Chain Autonomous Compute Network

**Solana + Sui + Berachain | LLM Consensus | P2P Agent Network**

Every M5 Pro Mac runs an autonomous Membra L3 node that mines files, runs LLM inference as consensus votes, communicates with peer agents, and settles state roots to three blockchains simultaneously.

## Architecture

```
                    ┌─────────────────────────────┐
                    │     M5 Pro Mac Node        │
                    │  ┌─────┐ ┌─────┐ ┌──────┐ │
                    │  │File │ │ LLM │ │Compute│ │
                    │  │Mine │ │Con- │ │Engine │ │
                    │  └─────┘ │sensus│ └──────┘ │
                    │          └─────┘           │
                    │              │             │
                    │       ┌──────┴──────┐      │
                    │       │  L3 Batcher │      │
                    │       │  1M+ ops/s  │      │
                    │       └──────┬──────┘      │
                    │              │             │
                    │  ┌──────┬─────┼──────┬──────┐
                    │  │      │     │      │      │
                    │ Solana  Sui Berachain P2P  │
                    │ devnet testnet bArtio gossip│
                    └─────────────────────────────┘
```

## What It Does

- **Multi-Chain Settlement**: Posts state roots to Solana devnet, Sui testnet, and Berachain bArtio. 2/3 consensus required.
- **LLM Consensus**: Every token generation produces a cryptographic vote. Multiple agents run inference; agreement creates consensus.
- **P2P Agent Network**: M5 Pro Macs discover each other via multicast, gossip resources, and trade compute.
- **File Mining + Tokenization**: LLM autonomously appraises files and tokenizes value on-chain.
- **Real SPL Tokens**: Creates real tokens on Solana devnet (no simulation).
- **Compute Rewards**: Tasks completed earn real on-chain COMPUTE tokens.

## File Structure

```
mac_compute_node/
├── core/                  # Compute engine, containers, models, file miner
├── l2/                    # Original L2 simulation (kept for reference)
├── marketplace/           # Compute marketplace pricing
├── dashboard/             # FastAPI + WebSocket dashboard
├── real_chain.py          # Real Solana devnet autonomous agent
├── multi_chain_bridge.py  # Solana + Sui + Berachain bridges
├── agent_consensus.py     # LLM-driven consensus engine
├── agent_p2p.py           # Peer-to-peer agent network
├── membra_l3.py           # Main L3 orchestrator
├── chain_bridge.py        # Compute → on-chain rewards bridge
├── main.py                # Entry point
├── config.yaml            # Configuration
├── requirements.txt       # Dependencies
└── .env                   # API keys
```

## Quick Start

```bash
cd mac_compute_node

# 1. Install dependencies
pip install -r requirements.txt

# 2. Add your Groq API key to .env (for LLM consensus)
echo "GROQ_API_KEY=your_key_here" >> .env

# 3. Start the L3 node with terminal dashboard
python main.py --l3

# 4. Or start full autonomous mode
python main.py

# 5. Open web dashboard
open http://localhost:7777
```

## Usage Modes

```bash
# Terminal dashboard (shows all chains + consensus + P2P)
python main.py --cli

# Full L3 multi-chain autonomous mode
python main.py --l3

# Web dashboard only
python main.py --dashboard

# Real chain interactive commands
python real_chain.py --cli
```

## Multi-Chain Wallets

Wallets are auto-generated on first run:

- `~/.mac_compute_node/wallets/solana.json` — Solana devnet
- `~/.mac_compute_node/wallets/sui.json` — Sui testnet
- `~/.mac_compute_node/wallets/bera.json` — Berachain bArtio

## How Consensus Works

1. Agent mines files and creates operations
2. Operations are batched into a state root
3. Each agent runs LLM inference: "Is this state root valid?"
4. The LLM output is hashed → consensus vote
5. Agents gossip votes via P2P
6. When 2/3 agree, the batch is settled
7. Settlement tx is sent to all 3 chains
8. 2/3 chain confirmations = finality

## Requirements

- macOS (Apple Silicon M3/M4/M5 Pro recommended)
- Python 3.11+
- Groq API key (for LLM consensus)
- 8GB+ RAM, 16GB recommended for concurrent inference

## Chains

| Chain | Network | Purpose |
|-------|---------|---------|
| Solana | devnet | Primary settlement, SPL tokens |
| Sui | testnet | Secondary settlement |
| Berachain | bArtio | EVM settlement |

## Safety

- All on-chain operations use testnets only
- Files scanned read-only
- P2P uses local multicast (no external exposure)
- Resource limits prevent system overload
