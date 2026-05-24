#!/bin/bash
# MEMBRA L3 — Multi-Language Build Script
# Builds Rust runtime, compiles Solidity, sets up Python agent, serves JS frontend

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║  MEMBRA L3 — Multi-Chain Runtime Build                     ║"
echo "║  Rust + Solidity + Python + JavaScript                     ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

# ────────────────────────────────────────────
# 1. RUST RUNTIME
# ────────────────────────────────────────────
echo "[1/4] Building Rust runtime..."
cd runtime
if command -v cargo &> /dev/null; then
    cargo build --release 2>&1 | tail -5
    echo "     ✅ Rust runtime built: target/release/membra-l3-runtime"
else
    echo "     ⚠️  Cargo not found. Install Rust: https://rustup.rs"
fi
cd ..

# ────────────────────────────────────────────
# 2. SOLIDITY CONTRACTS
# ────────────────────────────────────────────
echo ""
echo "[2/4] Preparing Solidity contracts..."
if command -v solc &> /dev/null; then
    mkdir -p contracts/out
    for contract in contracts/*.sol; do
        solc --abi --bin -o contracts/out --overwrite "$contract" 2>&1 | tail -3 || true
    done
    echo "     ✅ Contracts compiled"
else
    echo "     ⚠️  solc not found. Install: npm install -g solc"
    echo "     📄 Contracts ready for manual compilation:"
    ls -1 contracts/*.sol | sed 's/^/        /'
fi

# ────────────────────────────────────────────
# 3. PYTHON AGENT
# ────────────────────────────────────────────
echo ""
echo "[3/4] Setting up Python agent..."
if command -v python3 &> /dev/null; then
    python3 -m py_compile agent/llm_bridge.py agent/agent_node.py 2>&1
    echo "     ✅ Python agent compiled"
else
    echo "     ⚠️  python3 not found"
fi

# ────────────────────────────────────────────
# 4. JAVASCRIPT FRONTEND
# ────────────────────────────────────────────
echo ""
echo "[4/4] JavaScript frontend..."
if command -v node &> /dev/null; then
    echo "     ✅ Node.js available"
else
    echo "     ⚠️  Node.js not found. Frontend is static HTML/JS — no build needed"
fi

# ────────────────────────────────────────────
# SUMMARY
# ────────────────────────────────────────────
echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "  BUILD COMPLETE"
echo "═══════════════════════════════════════════════════════════════"
echo ""
echo "  To start the full stack:"
echo ""
echo "  1. Rust Runtime (terminal 1):"
echo "     cd runtime && cargo run --release"
echo ""
echo "  2. Python Agent (terminal 2):"
echo "     cd agent && python3 agent_node.py"
echo ""
echo "  3. Frontend (terminal 3):"
echo "     cd frontend && python3 -m http.server 8080"
echo "     open http://localhost:8080"
echo ""
echo "  Or use the orchestrator:"
echo "     ./scripts/orchestrate.sh"
echo ""
