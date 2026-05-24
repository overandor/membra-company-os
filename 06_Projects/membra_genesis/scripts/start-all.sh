#!/bin/bash
# MEMBRA GENESIS — Full Stack Launcher
# Starts C++ core, Go P2P, and Rust runtime in parallel

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_DIR"

LOG_DIR="$PROJECT_DIR/logs"
mkdir -p "$LOG_DIR"

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║  MEMBRA GENESIS — Starting Full Stack                        ║"
echo "║  C++ Core | Go P2P | Rust Runtime | Solana Fallback          ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

# ────────────────────────────────────────────
# Start Go P2P Node
# ────────────────────────────────────────────
echo "[1/3] Starting Go P2P node..."
if [ -f "$PROJECT_DIR/bin/membra-go-node" ]; then
    "$PROJECT_DIR/bin/membra-go-node" genesis-go-001 > "$LOG_DIR/go-p2p.log" 2>&1 &
    GO_PID=$!
    echo "     PID: $GO_PID | Log: logs/go-p2p.log"
    sleep 2
else
    echo "     ⚠️  membra-go-node not built. Run ./build.sh first"
fi

# ────────────────────────────────────────────
# Start Rust Runtime
# ────────────────────────────────────────────
echo ""
echo "[2/3] Starting Rust runtime..."
if [ -f "$PROJECT_DIR/bin/membra-genesis-rust" ]; then
    "$PROJECT_DIR/bin/membra-genesis-rust" genesis-rust-001 > "$LOG_DIR/rust-runtime.log" 2>&1 &
    RUST_PID=$!
    echo "     PID: $RUST_PID | Log: logs/rust-runtime.log"
    sleep 2
else
    echo "     ⚠️  membra-genesis-rust not built. Run ./build.sh first"
fi

# ────────────────────────────────────────────
# Start C++ Core (optional, for testing)
# ────────────────────────────────────────────
echo ""
echo "[3/3] Starting C++ core test..."
if [ -f "$PROJECT_DIR/bin/genesis_node" ]; then
    echo "genesis-cpp-001" | "$PROJECT_DIR/bin/genesis_node" genesis-cpp-001 > "$LOG_DIR/cpp-core.log" 2>&1 &
    CPP_PID=$!
    echo "     PID: $CPP_PID | Log: logs/cpp-core.log"
else
    echo "     ⚠️  genesis_node not built"
fi

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "  ALL SERVICES STARTED"
echo "═══════════════════════════════════════════════════════════════"
echo ""
echo "  HTTP API:    http://localhost:8080/api/status"
echo "  gRPC:        localhost:50051"
echo "  P2P WS:      ws://localhost:42425/p2p"
echo ""
echo "  Logs: logs/"
echo ""
echo "  Press Ctrl+C to stop all services"
echo ""

trap 'echo ""; echo "[STOP] Shutting down..."; kill $GO_PID $RUST_PID $CPP_PID 2>/dev/null; exit 0' INT

wait
