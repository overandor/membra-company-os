# MEMBRA L3 RUNTIME — Proof-of-Proof Multi-Chain Consensus

**Rust + Solidity + Python + JavaScript**

Every human prompt becomes a transaction. Every LLM token generates money. Every inference output is cryptographic proof. Multiple agents reach consensus by comparing proof hashes. Settlement goes to Solana, Sui, and Berachain simultaneously.

## Architecture

```
membra_l3_runtime/
├── runtime/           # Rust core — tx processor, consensus, P2P
│   ├── src/
│   │   ├── main.rs         # Entry point
│   │   ├── lib.rs          # Module exports
│   │   ├── transaction.rs  # Tx types: Prompt, Inference, Response
│   │   ├── consensus.rs    # Proof-of-Proof consensus engine
│   │   ├── state.rs        # Lock-free global state (DashMap)
│   │   ├── network.rs      # P2P WebSocket gossip
│   │   └── proof.rs        # Inference proof hashing
│   └── Cargo.toml
├── contracts/         # Solidity — ERC20 token, consensus, bridge
│   ├── MembraToken.sol
│   ├── MembraConsensus.sol
│   └── MembraBridge.sol
├── agent/             # Python — LLM bridge (Ollama/Groq)
│   ├── llm_bridge.py
│   └── agent_node.py
├── frontend/          # JavaScript — Real-time dashboard
│   ├── index.html
│   └── src/main.js
├── build.sh           # Multi-language build script
└── scripts/
    └── orchestrate.sh # Full stack launcher
```

## Core Innovation: Proof-of-Proof

```
Human Prompt → hash(prompt) = tx_hash
       ↓
LLM Inference → each token hash = micro-proof
       ↓
Response hash = merkle_root(token_hashes)
       ↓
Multiple agents compare response hashes
       ↓
2/3 agreement = consensus reached
       ↓
Settle to Solana + Sui + Berachain
```

## Quick Start

```bash
# 1. Build everything
./build.sh

# 2. Start full stack
./scripts/orchestrate.sh

# 3. Open dashboard
open http://localhost:8080

# 4. Submit a prompt (each word = tx, each token = money)
curl -X POST http://localhost:8080/api/prompt \
  -H "Content-Type: application/json" \
  -d '{"prompt":"Write a smart contract","user":"alice"}'
```

## Individual Components

### Rust Runtime
```bash
cd runtime
cargo run --release
```
- WebSocket P2P on port 42425
- Transaction pool: 1M+ ops/sec capacity
- Consensus: 2/3 majority on inference hash agreement

### Solidity Contracts
```bash
cd contracts
solc --abi --bin -o out *.sol
```
- `MembraToken.sol`: ERC20 with per-inference minting
- `MembraConsensus.sol`: On-chain vote aggregation
- `MembraBridge.sol`: Cross-chain settlement recording

### Python Agent
```bash
cd agent
python3 agent_node.py          # Interactive mode
python3 agent_node.py --autonomous  # File mining mode
```
- Connects to Ollama (local) or Groq (API)
- Every prompt submitted as real transaction
- Every token earns 100 base units

### JavaScript Frontend
```bash
cd frontend
python3 -m http.server 8080
```
- Real-time WebSocket updates
- Live transaction log
- Prompt submission with immediate earnings

## Transaction Types

| Type | Trigger | Value |
|------|---------|-------|
| `Prompt` | Human submits prompt | -1 (small fee) |
| `Inference` | LLM generates each token | +100 per token |
| `Response` | Complete response delivered | +total |
| `ConsensusVote` | Agent validates batch | +validator fee |
| `CrossChain` | Settlement to L1 | +settlement reward |

## Multi-Chain Settlement

| Chain | Network | Role |
|-------|---------|------|
| Solana | devnet | Primary SPL tokens |
| Sui | testnet | Move object settlement |
| Berachain | bArtio | EVM consensus anchor |

Consensus requires 2/3 chain confirmations.

## Performance

- **Internal throughput**: 1M+ ops/sec (lock-free DashMap)
- **Consensus finality**: ~100ms (LLM inference latency)
- **P2P gossip**: Every 2 seconds
- **Settlement**: Every 30 seconds to L1

## Requirements

- Rust 1.75+ (runtime)
- Solidity 0.8.20+ (contracts)
- Python 3.11+ (agent)
- Node.js 20+ (frontend build, optional)
- Ollama or Groq API key

## License

MIT — Proof-of-Proof is the future of consensus.
