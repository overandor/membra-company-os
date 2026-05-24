#!/bin/bash
# Install Solana CLI and Anchor toolchain for Membra Money devnet testing
# Run on macOS/Linux in Windsurf terminal

set -e

SOLANA_VERSION="1.17.0"
ANCHOR_VERSION="0.29.0"

echo "=== Solana/Anchor Toolchain Installer ==="
echo ""

# Check for cargo
if ! command -v cargo &> /dev/null; then
    echo "Rust not found. Installing rustup..."
    curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
    source "$HOME/.cargo/env"
fi

echo ""
echo "[1/4] Installing Solana CLI v${SOLANA_VERSION}..."
if command -v solana &> /dev/null; then
    echo "      Solana already installed: $(solana --version)"
else
    sh -c "$(curl -sSfL https://release.solana.com/v${SOLANA_VERSION}/install)"
    export PATH="$HOME/.local/share/solana/install/active_release/bin:$PATH"
    echo "      Installed: $(solana --version)"
fi

echo ""
echo "[2/4] Installing Anchor v${ANCHOR_VERSION} via avm..."
if command -v avm &> /dev/null; then
    echo "      avm already installed"
else
    cargo install --git https://github.com/coral-xyz/anchor avm --locked --force
fi
avm install ${ANCHOR_VERSION}
avm use ${ANCHOR_VERSION}
echo "      Anchor: $(anchor --version)"

echo ""
echo "[3/4] Configuring for devnet..."
solana config set --url devnet
if [ ! -f "$HOME/.config/solana/id.json" ]; then
    solana-keygen new --outfile "$HOME/.config/solana/id.json" --no-passphrase
fi
echo "      Wallet: $(solana address)"

echo ""
echo "[4/4] Requesting devnet airdrop..."
solana airdrop 2 || echo "      Airdrop failed — may already have SOL or devnet rate-limited"
solana balance || true

echo ""
echo "=== Installation Complete ==="
echo ""
echo "Next steps:"
echo "  1. cd bitcoin-bearer-notes"
echo "  2. anchor build"
echo "  3. anchor test"
echo "  4. anchor deploy --provider.cluster devnet"
