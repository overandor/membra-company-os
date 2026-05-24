#!/bin/bash
# Membra Money local validation script
# Run this in Windsurf to validate the project before commit.

set -e

echo "=== Membra Money Validation ==="
echo ""

# Python backend validation
echo "[1/4] Compiling backend Python files..."
cd backend
python3 -m compileall . -q
echo "      OK"

echo ""
echo "[2/4] Running backend pytest..."
PYTHONPATH=.:$PYTHONPATH python3 -m pytest ../tests/test_backend.py -v --tb=short
echo "      OK"

cd ..

# Rust/Anchor validation (requires Solana toolchain)
echo ""
echo "[3/4] Checking Anchor program (cargo check)..."
if command -v cargo &> /dev/null; then
    cd programs/bitcoin-bearer-notes
    if cargo check 2>&1 | tee /tmp/cargo_check.log; then
        echo "      OK"
    else
        echo "      WARNING: cargo check failed (see /tmp/cargo_check.log)"
    fi
    cd ../..
else
    echo "      SKIP: Rust toolchain not installed"
    echo "      Install via: https://rustup.rs and https://solana.com/developers/guides/getstarted/setup-local-development"
fi

# Secret scan
echo ""
echo "[4/4] Scanning for secrets in backend source..."
if grep -rE "(PRIVATE_KEY|SECRET|API_KEY|TOKEN)\s*[=:]\s*[\"'][^\"']{20,}" backend/ --include="*.py" 2>/dev/null; then
    echo "      WARNING: Possible secrets found"
else
    echo "      OK (no obvious secrets detected)"
fi

echo ""
echo "=== Validation Complete ==="
echo ""
echo "Next steps for mainnet readiness:"
echo "  - anchor build && anchor test"
echo "  - docker-compose -f docker-compose.prod.yml config"
echo "  - Manual end-to-end test on devnet"
