#!/usr/bin/env bash
# Pre-flight deployment checklist for Membra Money
# Run before each devnet deployment to catch issues early

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

PASS=0
FAIL=0
WARN=0

check() {
    local msg="$1"
    local cmd="$2"
    echo -n "[CHECK] $msg ... "
    if eval "$cmd" >/dev/null 2>&1; then
        echo -e "${GREEN}PASS${NC}"
        PASS=$((PASS + 1))
    else
        echo -e "${RED}FAIL${NC}"
        FAIL=$((FAIL + 1))
    fi
}

warn() {
    local msg="$1"
    echo -e "${YELLOW}[WARN] $msg${NC}"
    WARN=$((WARN + 1))
}

echo "=== Membra Money Pre-Flight Deployment Checklist ==="
echo ""

# --- Git hygiene ---
echo "## 1. Git Hygiene"
check "Git working tree is clean" "git diff --quiet && git diff --cached --quiet"
check "On main branch" "git branch --show-current | grep -q '^main$'"
check "Remote origin is set" "git remote | grep -q origin"

# --- Secret scanning ---
echo ""
echo "## 2. Secret Scanning"
if command -v ggshield >/dev/null 2>&1; then
    check "ggshield finds no secrets" "ggshield secret scan repo ."
else
    warn "ggshield not installed — skipping secret scan"
fi

# Check for common hardcoded secrets
check "No hardcoded GH tokens in source" "! grep -rE 'ghp_[a-zA-Z0-9]{36}' --include='*.py' --include='*.ts' --include='*.sh' --include='*.md' ."
check "No .env files committed" "! git ls-files | grep -qE '^\\.env$|^\\.env\\.'"

# --- Backend validation ---
echo ""
echo "## 3. Backend Validation"
check "Backend compiles" "python3 -m compileall backend/"
check "Backend tests pass" "PYTHONPATH=backend:\${PYTHONPATH:-} python3 -m pytest tests/ -q"

# Check .env.example completeness
if grep -q "POSTGRES_PASSWORD=change-this" backend/.env.example; then
    warn "backend/.env.example still has placeholder passwords"
fi
if grep -q "SECRET_KEY=change-me" backend/.env.example; then
    warn "backend/.env.example still has placeholder SECRET_KEY"
fi

# --- Anchor validation ---
echo ""
echo "## 4. Anchor / Rust Validation"
check "Cargo.toml exists" "test -f Cargo.toml"
check "Anchor.toml exists" "test -f Anchor.toml"
check "Program source exists" "test -f programs/bitcoin-bearer-notes/src/lib.rs"

# Check for placeholder program ID
if grep -q 'Fg6PaFpoGXkYsidMpWTK6W2BeZ7FEfcYkg476zPFsLnS' Anchor.toml; then
    warn "Anchor.toml still has placeholder program ID — update after devnet deploy"
fi
if grep -q 'Fg6PaFpoGXkYsidMpWTK6W2BeZ7FEfcYkg476zPFsLnS' programs/bitcoin-bearer-notes/src/lib.rs; then
    warn "lib.rs still has placeholder declare_id! — update after devnet deploy"
fi

# Check toolchain availability
if command -v cargo >/dev/null 2>&1; then
    check "Rust / cargo available" "cargo --version"
    check "Anchor program compiles (cargo check)" "cargo check --manifest-path programs/bitcoin-bearer-notes/Cargo.toml"
else
    warn "Rust / cargo not available — cannot verify Anchor build"
fi

if command -v anchor >/dev/null 2>&1; then
    check "Anchor CLI available" "anchor --version"
else
    warn "Anchor CLI not available — install with scripts/install_solana.sh"
fi

# --- Frontend validation ---
echo ""
echo "## 5. Frontend Validation"
check "Frontend app directory exists" "test -d app"
check "Vercel config exists" "test -f vercel.json"

# --- Infrastructure validation ---
echo ""
echo "## 6. Infrastructure Validation"
check "Docker Compose prod config exists" "test -f docker-compose.prod.yml"
check "nginx config exists" "test -f nginx.conf"
check "Render config exists" "test -f render.yaml"

# Validate docker-compose.prod.yml syntax
if command -v docker >/dev/null 2>&1; then
    check "Docker Compose config is valid" "docker compose -f docker-compose.prod.yml config -q"
else
    warn "Docker not available — skipping compose validation"
fi

# --- Documentation ---
echo ""
echo "## 7. Documentation"
check "DEVNET_DEPLOYMENT.md exists" "test -f docs/DEVNET_DEPLOYMENT.md"
check "MAINNET_READINESS.md exists" "test -f MAINNET_READINESS.md"
check "SECURITY.md exists" "test -f SECURITY.md"

# --- Summary ---
echo ""
echo "========================================"
echo -e "Results: ${GREEN}$PASS passed${NC}, ${RED}$FAIL failed${NC}, ${YELLOW}$WARN warnings${NC}"
echo "========================================"

if [ "$FAIL" -gt 0 ]; then
    echo -e "${RED}Deployment blocked — fix failures before continuing.${NC}"
    exit 1
elif [ "$WARN" -gt 0 ]; then
    echo -e "${YELLOW}Deployment possible with warnings — review above.${NC}"
    exit 0
else
    echo -e "${GREEN}All checks passed. Ready for deployment.${NC}"
    exit 0
fi
