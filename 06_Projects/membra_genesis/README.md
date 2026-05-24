# MEMBRA GENESIS — Multi-Language Validator Network

**C++ Core | Go P2P | Rust Runtime | Solana Fallback**

Membra Genesis is a proof-of-proof consensus network where LLM inference outputs serve as cryptographic votes. Built in three languages for maximum performance and resilience.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  MEMBRA GENESIS NODE                                       │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐            │
│  │   C++      │  │    Go      │  │   Rust     │            │
│  │  Hot Path  │  │  Network   │  │ Orchestrator│            │
│  │            │  │            │  │            │            │
│  │ - Tx verify│  │ - P2P      │  │ - FFI to   │            │
│  │ - Consensus│  │   gossip   │  │   C++      │            │
│  │ - Merkle   │  │ - Discovery│  │ - Solana   │            │
│  │ - State    │  │ - WebSocket│  │   fallback │            │
│  └─────┬──────┘  └─────┬──────┘  └─────┬──────┘            │
│        │               │               │                    │
│        └───────────────┼───────────────┘                    │
│                        │                                    │
│                 ┌──────┴──────┐                              │
│                 │  Solana     │                              │
│                 │  Fallback   │  (if local < 2/3)           │
│                 │  Validators │                              │
│                 └─────────────┘                              │
└─────────────────────────────────────────────────────────────┘
```

## Components

### C++ Core (`cpp/`)
- **Lock-free transaction pool** with shared_mutex for reads
- **Keccak256 Merkle tree** for batch roots
- **Proof-of-Proof consensus**: 2/3 agreement on inference hashes
- **FFI C API** for Rust integration

### Go P2P (`go/`)
- **Multicast discovery** (UDP 224.1.1.1:42424)
- **WebSocket gossip** protocol between agents
- **HTTP API** for prompt submission and status
- **gRPC** for inter-node communication

### Rust Runtime (`rust/`)
- **FFI bridge** to C++ consensus core
- **Solana fallback**: queries devnet validators if local consensus fails
- **Async orchestrator** with tokio channels
- **Auto-settlement** to Solana memo program

## Proof-of-Proof Consensus

```
Human Prompt → hash(prompt) = tx
       ↓
LLM Inference → hash(token) = micro-proof
       ↓
Response hash = merkle_root(all token hashes)
       ↓
3+ agents compare response hashes via P2P
       ↓
2/3 agreement = batch finalized
       ↓
If local fails → query Solana validators
       ↓
Settlement tx posted to Solana devnet
```

## Quick Start

```bash
# Build everything
./build.sh

# Start full stack
./scripts/start-all.sh

# Or start components individually:
# C++ core test
./bin/genesis_node genesis-cpp-001

# Go P2P node
./bin/membra-go-node genesis-go-001

# Rust runtime (with Solana fallback)
./bin/membra-genesis-rust genesis-rust-001
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/status` | GET | Node status (P2P + consensus stats) |
| `/api/p2p` | GET | P2P network statistics |
| `/api/consensus` | GET | Consensus round statistics |
| `/api/prompt` | POST | Submit prompt (becomes tx) |

## Multi-Language Build

```bash
# C++ (requires cmake, make)
cd cpp && mkdir build && cd build && cmake .. && make

# Rust (requires cargo)
cd rust && cargo build --release

# Go (requires go 1.21+)
cd go && go mod tidy && go build ./cmd/node.go
```

## Requirements

| Component | Needs |
|-----------|-------|
| C++ Core | cmake 3.16+, C++17 compiler |
| Go P2P | Go 1.21+ |
| Rust Runtime | Rust 1.75+, cargo |
| Solana Fallback | Internet (devnet RPC) |

## Solana Fallback

When local consensus can't reach 2/3 agreement within 60 seconds, the Rust runtime:

1. Queries Solana devnet `getBlockCommitment`
2. If >67% validator stake confirms, accepts as consensus
3. Posts settlement memo to Solana for on-chain proof
4. Falls back to standalone mode if Solana unreachable

## File Structure

```
membra_genesis/
├── cpp/
│   ├── include/consensus.hpp     # C API for FFI
│   ├── src/consensus.cpp         # Core engine
│   ├── src/main.cpp              # Test executable
│   └── CMakeLists.txt
├── go/
│   ├── cmd/node.go               # Entry point
│   ├── internal/
│   │   ├── p2p/network.go        # WebSocket + multicast
│   │   ├── consensus/handler.go   # Vote aggregation
│   │   └── network/server.go     # HTTP + gRPC
│   └── go.mod
├── rust/
│   ├── src/
│   │   ├── main.rs               # Entry point
│   │   ├── lib.rs                # Module exports
│   │   ├── ffi.rs                # C++ FFI bindings
│   │   ├── genesis.rs            # Orchestrator
│   │   └── solana_fallback.rs    # Devnet fallback
│   ├── Cargo.toml
│   └── build.rs                  # C++ compilation
├── scripts/
│   └── start-all.sh              # Full stack launcher
├── build.sh                      # Multi-language build
└── README.md
```

## License

MIT — Genesis begins with proof.
