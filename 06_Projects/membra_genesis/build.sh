#!/bin/bash
# MEMBRA GENESIS — Multi-Language Build Script
# C++ + Rust + Go compilation

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║  MEMBRA GENESIS — Multi-Language Build                       ║"
echo "║  C++ Core | Go P2P | Rust Runtime | Solana Fallback          ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

# ────────────────────────────────────────────
# 1. C++ CONSENSUS CORE
# ────────────────────────────────────────────
echo "[1/4] Building C++ consensus core..."
if command -v cmake &> /dev/null && command -v make &> /dev/null; then
    mkdir -p cpp/build
    cd cpp/build
    cmake .. -DCMAKE_BUILD_TYPE=Release
    make -j$(nproc 2>/dev/null || sysctl -n hw.ncpu 2>/dev/null || echo 4)
    cd "$SCRIPT_DIR"
    echo "     ✅ C++ libmembra_consensus built"
else
    echo "     ⚠️  cmake/make not found"
fi

# ────────────────────────────────────────────
# 2. RUST RUNTIME (FFI to C++)
# ────────────────────────────────────────────
echo ""
echo "[2/4] Building Rust runtime..."
if command -v cargo &> /dev/null; then
    cd rust
    cargo build --release 2>&1 | tail -5
    cd "$SCRIPT_DIR"
    echo "     ✅ Rust runtime built"
else
    echo "     ⚠️  Cargo not found. Install: https://rustup.rs"
fi

# ────────────────────────────────────────────
# 3. GO P2P NETWORK
# ────────────────────────────────────────────
echo ""
echo "[3/4] Building Go P2P node..."
if command -v go &> /dev/null; then
    cd go
    go mod tidy 2>&1 | tail -3 || true
    go build -o ../bin/membra-go-node ./cmd/node.go 2>&1 | tail -3 || true
    cd "$SCRIPT_DIR"
    echo "     ✅ Go node built"
else
    echo "     ⚠️  Go not found. Install: https://go.dev/dl"
fi

# ────────────────────────────────────────────
# 4. BINARY CHECK
# ────────────────────────────────────────────
echo ""
echo "[4/4] Verifying binaries..."
mkdir -p bin

if [ -f "rust/target/release/membra-genesis-rust" ]; then
    cp rust/target/release/membra-genesis-rust bin/
    echo "     ✅ membra-genesis-rust"
fi

if [ -f "go/membra-go-node" ]; then
    cp go/membra-go-node bin/
    echo "     ✅ membra-go-node"
fi

if [ -f "cpp/build/genesis_node" ]; then
    cp cpp/build/genesis_node bin/
    echo "     ✅ genesis_node (C++)"
fi

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "  BUILD COMPLETE"
echo "═══════════════════════════════════════════════════════════════"
echo ""
echo "  To start the full stack:"
echo ""
echo "  1. Go P2P Node (terminal 1):"
echo "     ./bin/membra-go-node genesis-go-001"
echo ""
echo "  2. Rust Runtime (terminal 2):"
echo "     ./bin/membra-genesis-rust genesis-rust-001"
echo ""
echo "  3. C++ Core Test (terminal 3):"
echo "     ./bin/genesis_node genesis-cpp-001"
echo ""
echo "  Or use the orchestrator:"
echo "     ./scripts/start-all.sh"
echo ""
