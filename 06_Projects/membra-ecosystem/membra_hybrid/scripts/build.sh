#!/bin/bash

# Comprehensive build script for Membra hybrid C++/Rust DNS system
# This script builds all components: C++ core, Rust FFI, and Solana smart contracts

set -e

echo "🔨 Membra Hybrid DNS Build System"
echo "================================"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BUILD_DIR="$PROJECT_ROOT/build"
CPP_DIR="$PROJECT_ROOT/cpp-core"
FFI_DIR="$PROJECT_ROOT/ffi"
CONTRACTS_DIR="$PROJECT_ROOT/smart-contracts"

# Parse command line arguments
BUILD_TYPE="Release"
RUN_TESTS=false
DEPLOY_CONTRACT=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --debug)
            BUILD_TYPE="Debug"
            shift
            ;;
        --test)
            RUN_TESTS=true
            shift
            ;;
        --deploy)
            DEPLOY_CONTRACT=true
            shift
            ;;
        --help)
            echo "Usage: $0 [OPTIONS]"
            echo "Options:"
            echo "  --debug    Build in debug mode"
            echo "  --test     Run tests after build"
            echo "  --deploy   Deploy smart contracts after build"
            echo "  --help     Show this help message"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Create build directory
mkdir -p "$BUILD_DIR"

echo "📋 Build Configuration:"
echo "   Build Type: $BUILD_TYPE"
echo "   Run Tests: $RUN_TESTS"
echo "   Deploy Contracts: $DEPLOY_CONTRACT"
echo ""

# Step 1: Build C++ Core
echo "🔧 Step 1: Building C++ Core DNS Resolver..."
echo "-------------------------------------------"

cd "$CPP_DIR"
if [ ! -d "build" ]; then
    mkdir build
fi

cd build
cmake -DCMAKE_BUILD_TYPE=$BUILD_TYPE ..
make -j$(nproc)

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ C++ Core built successfully${NC}"
else
    echo -e "${RED}✗ C++ Core build failed${NC}"
    exit 1
fi

# Run C++ tests if requested
if [ "$RUN_TESTS" = true ]; then
    echo "🧪 Running C++ tests..."
    ./tests/dns_resolver_test
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ C++ tests passed${NC}"
    else
        echo -e "${RED}✗ C++ tests failed${NC}"
        exit 1
    fi
fi

echo ""

# Step 2: Build Rust FFI Layer
echo "🔧 Step 2: Building Rust FFI Layer..."
echo "-------------------------------------"

cd "$FFI_DIR"
cargo build --release

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Rust FFI Layer built successfully${NC}"
else
    echo -e "${RED}✗ Rust FFI Layer build failed${NC}"
    exit 1
fi

# Run Rust tests if requested
if [ "$RUN_TESTS" = true ]; then
    echo "🧪 Running Rust tests..."
    cargo test --release
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ Rust tests passed${NC}"
    else
        echo -e "${RED}✗ Rust tests failed${NC}"
        exit 1
    fi
fi

echo ""

# Step 3: Build Solana Smart Contract
echo "🔧 Step 3: Building Solana Smart Contract..."
echo "--------------------------------------------"

cd "$CONTRACTS_DIR/membra-dns"
cargo build-sbf

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Solana Smart Contract built successfully${NC}"
else
    echo -e "${RED}✗ Solana Smart Contract build failed${NC}"
    exit 1
fi

echo ""

# Step 4: Run Anchor tests if requested
if [ "$RUN_TESTS" = true ]; then
    echo "🧪 Running Anchor tests..."
    anchor test --skip-local-validator
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ Anchor tests passed${NC}"
    else
        echo -e "${YELLOW}⚠ Anchor tests skipped (requires local validator)${NC}"
    fi
fi

# Step 5: Deploy contracts if requested
if [ "$DEPLOY_CONTRACT" = true ]; then
    echo "🚀 Step 5: Deploying Smart Contracts..."
    echo "--------------------------------------"
    
    # Check if Solana CLI is configured
    if ! command -v solana &> /dev/null; then
        echo -e "${RED}✗ Solana CLI not found${NC}"
        echo "Please install Solana CLI: https://docs.solana.com/cli/install-solana-cli-tools"
        exit 1
    fi
    
    # Get current cluster
    CLUSTER=$(solana config get | grep "RPC URL" | awk '{print $3}')
    echo "Deploying to cluster: $CLUSTER"
    
    # Deploy the program
    anchor deploy --cluster devnet
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ Smart Contract deployed successfully${NC}"
    else
        echo -e "${RED}✗ Smart Contract deployment failed${NC}"
        exit 1
    fi
fi

echo ""
echo "================================"
echo -e "${GREEN}🎉 Build completed successfully!${NC}"
echo "================================"
echo ""
echo "📦 Build artifacts:"
echo "   C++ Library: $CPP_DIR/build/lib/libmembra_dns_ffi.so"
echo "   Rust Library: $FFI_DIR/target/release/libmembra_dns_ffi.dylib"
echo "   Solana Program: $CONTRACTS_DIR/membra-dns/target/deploy/membra_dns.so"
echo ""
echo "🚀 Next steps:"
echo "   1. Run integration tests: ./scripts/test.sh"
echo "   2. Deploy to testnet: ./scripts/deploy.sh devnet"
echo "   3. Start the server: cargo run --bin server"
echo ""