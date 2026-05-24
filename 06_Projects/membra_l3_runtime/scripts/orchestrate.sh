#!/bin/bash
# MEMBRA L3 — Full Stack Orchestrator
# Starts all components: Rust runtime, Python agent, JS frontend

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_DIR"

LOG_DIR="$PROJECT_DIR/logs"
mkdir -p "$LOG_DIR"

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║  MEMBRA L3 — Starting Full Stack                            ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

# ────────────────────────────────────────────
# Start Rust Runtime
# ────────────────────────────────────────────
echo "[1/3] Starting Rust runtime..."
if [ -f "$PROJECT_DIR/runtime/target/release/membra-l3-runtime" ]; then
    "$PROJECT_DIR/runtime/target/release/membra-l3-runtime" > "$LOG_DIR/runtime.log" 2>&1 &
    RUNTIME_PID=$!
    echo "     PID: $RUNTIME_PID | Log: logs/runtime.log"
    sleep 2
else
    echo "     ⚠️  Rust runtime not built. Run ./build.sh first"
fi

# ────────────────────────────────────────────
# Start Python Agent
# ────────────────────────────────────────────
echo ""
echo "[2/3] Starting Python LLM agent..."
if command -v python3 &> /dev/null; then
    cd "$PROJECT_DIR/agent"
    python3 agent_node.py --autonomous > "$LOG_DIR/agent.log" 2>&1 &
    AGENT_PID=$!
    echo "     PID: $AGENT_PID | Log: logs/agent.log"
    cd "$PROJECT_DIR"
else
    echo "     ⚠️  python3 not available"
fi

# ────────────────────────────────────────────
# Start Frontend Server
# ────────────────────────────────────────────
echo ""
echo "[3/3] Starting frontend server..."
cd "$PROJECT_DIR/frontend"
if command -v python3 &> /dev/null; then
    python3 -m http.server 8080 > "$LOG_DIR/frontend.log" 2>&1 &
    FRONTEND_PID=$!
    echo "     PID: $FRONTEND_PID | URL: http://localhost:8080"
else
    echo "     ⚠️  python3 not available for static server"
fi
cd "$PROJECT_DIR"

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "  ALL SERVICES STARTED"
echo "═══════════════════════════════════════════════════════════════"
echo ""
echo "  Dashboard:  http://localhost:8080"
echo "  Runtime WS: ws://localhost:42425"
echo ""
echo "  Logs: logs/"
echo ""
echo "  Press Ctrl+C to stop all services"
echo ""

# Trap Ctrl+C to kill all children
trap 'echo ""; echo "[STOP] Shutting down..."; kill $RUNTIME_PID $AGENT_PID $FRONTEND_PID 2>/dev/null; exit 0' INT

# Keep script alive
wait
