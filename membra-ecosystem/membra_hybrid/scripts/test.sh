#!/bin/bash

# Comprehensive test script for Membra DNS system
# Runs all tests across C++, Rust, and smart contracts

set -e

echo "🧪 Membra DNS Test Suite"
echo "======================"
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CPP_DIR="$PROJECT_ROOT/cpp-core"
FFI_DIR="$PROJECT_ROOT/ffi"
CONTRACTS_DIR="$PROJECT_ROOT/smart-contracts/membra-dns"
RUN_CPP=true
RUN_RUST=true
RUN_CONTRACTS=true
COVERAGE=false

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --skip-cpp)
            RUN_CPP=false
            shift
            ;;
        --skip-rust)
            RUN_RUST=false
            shift
            ;;
        --skip-contracts)
            RUN_CONTRACTS=false
            shift
            ;;
        --coverage)
            COVERAGE=true
            shift
            ;;
        --help)
            echo "Usage: $0 [OPTIONS]"
            echo "Options:"
            echo "  --skip-cpp         Skip C++ tests"
            echo "  --skip-rust        Skip Rust tests"
            echo "  --skip-contracts   Skip smart contract tests"
            echo "  --coverage         Generate coverage reports"
            echo "  --help             Show this help message"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

echo "📋 Test Configuration:"
echo "   C++ Tests: $RUN_CPP"
echo "   Rust Tests: $RUN_RUST"
echo "   Contract Tests: $RUN_CONTRACTS"
echo "   Coverage: $COVERAGE"
echo ""

# Test counters
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0

# Helper function to run tests
run_test() {
    local test_name="$1"
    local test_command="$2"
    
    echo "🔬 Running: $test_name"
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    
    if eval "$test_command"; then
        echo -e "${GREEN}✓ $test_name passed${NC}"
        PASSED_TESTS=$((PASSED_TESTS + 1))
        return 0
    else
        echo -e "${RED}✗ $test_name failed${NC}"
        FAILED_TESTS=$((FAILED_TESTS + 1))
        return 1
    fi
}

# C++ Tests
if [ "$RUN_CPP" = true ]; then
    echo "🔧 C++ Test Suite"
    echo "================"
    echo ""
    
    cd "$CPP_DIR"
    
    # Build tests first
    echo "Building C++ tests..."
    cd build
    cmake -DCMAKE_BUILD_TYPE=Debug .. >/dev/null 2>&1
    make dns_resolver_test >/dev/null 2>&1
    
    if [ ! -f "tests/dns_resolver_test" ]; then
        echo -e "${RED}✗ C++ test executable not found${NC}"
        echo "Run ./scripts/build.sh --test first"
        exit 1
    fi
    
    cd tests
    
    run_test "C++ Unit Tests" "./dns_resolver_test"
    
    # Performance tests
    if [ "$COVERAGE" = true ]; then
        run_test "C++ Performance Tests" "./dns_resolver_bench"
    fi
    
    echo ""
fi

# Rust Tests
if [ "$RUN_RUST" = true ]; then
    echo "🦀 Rust Test Suite"
    echo "=================="
    echo ""
    
    cd "$FFI_DIR"
    
    # Unit tests
    run_test "Rust Unit Tests" "cargo test --lib"
    
    # Integration tests
    run_test "Rust Integration Tests" "cargo test --test integration_test"
    
    # Documentation tests
    run_test "Rust Documentation Tests" "cargo test --doc"
    
    # Coverage
    if [ "$COVERAGE" = true ]; then
        echo "Generating Rust coverage..."
        cargo install cargo-tarpaulin >/dev/null 2>&1
        cargo tarpaulin --out Html --output-dir ../coverage/rust
        echo -e "${GREEN}✓ Rust coverage report generated${NC}"
    fi
    
    echo ""
fi

# Smart Contract Tests
if [ "$RUN_CONTRACTS" = true ]; then
    echo "⛓️  Smart Contract Test Suite"
    echo "============================"
    echo ""
    
    cd "$CONTRACTS_DIR"
    
    # Check if local validator is running
    if ! pgrep -x "solana-test-validator" > /dev/null; then
        echo "Starting local Solana validator..."
        solana-test-validator --reset --quiet &
        VALIDATOR_PID=$!
        
        # Wait for validator to be ready
        sleep 5
        
        # Set local config
        solana config set --url localhost
    fi
    
    # Build the program
    echo "Building smart contract..."
    cargo build-sbf >/dev/null 2>&1
    
    # Run Anchor tests
    run_test "Anchor Tests" "anchor test --skip-local-validator"
    
    # Clean up validator if we started it
    if [ ! -z "$VALIDATOR_PID" ]; then
        kill $VALIDATOR_PID 2>/dev/null || true
        echo "Local validator stopped"
    fi
    
    echo ""
fi

# Integration Tests
echo "🔗 Integration Test Suite"
echo "=========================="
echo ""

cd "$PROJECT_ROOT"

# Test C++ library loading
if [ "$RUN_CPP" = true ] && [ "$RUN_RUST" = true ]; then
    echo "Testing C++ library from Rust..."
    
    # This would require the library to be built and accessible
    # For now, we'll just check if the library exists
    if [ -f "$CPP_DIR/build/lib/libmembra_dns_ffi.so" ] || [ -f "$CPP_DIR/build/lib/libmembra_dns_ffi.dylib" ]; then
        echo -e "${GREEN}✓ C++ library found${NC}"
        PASSED_TESTS=$((PASSED_TESTS + 1))
        TOTAL_TESTS=$((TOTAL_TESTS + 1))
    else
        echo -e "${YELLOW}⚠️  C++ library not found (run build.sh first)${NC}"
    fi
fi

# Test smart contract deployment readiness
if [ "$RUN_CONTRACTS" = true ]; then
    echo "Testing smart contract deployment readiness..."
    
    if [ -f "$CONTRACTS_DIR/target/deploy/membra_dns.so" ]; then
        echo -e "${GREEN}✓ Smart contract built${NC}"
        PASSED_TESTS=$((PASSED_TESTS + 1))
        TOTAL_TESTS=$((TOTAL_TESTS + 1))
    else
        echo -e "${RED}✗ Smart contract not built${NC}"
        FAILED_TESTS=$((FAILED_TESTS + 1))
        TOTAL_TESTS=$((TOTAL_TESTS + 1))
    fi
fi

echo ""

# Test Summary
echo "================================"
echo "📊 Test Summary"
echo "================================"
echo "Total Tests: $TOTAL_TESTS"
echo -e "${GREEN}Passed: $PASSED_TESTS${NC}"
if [ $FAILED_TESTS -gt 0 ]; then
    echo -e "${RED}Failed: $FAILED_TESTS${NC}"
    echo ""
    echo -e "${RED}❌ Test suite failed${NC}"
    exit 1
else
    echo -e "${GREEN}✅ All tests passed!${NC}"
fi

echo ""

# Coverage Report
if [ "$COVERAGE" = true ]; then
    echo "📈 Coverage Reports"
    echo "=================="
    echo "Rust coverage: $PROJECT_ROOT/coverage/rust/index.html"
    echo "C++ coverage: Not yet implemented"
    echo ""
fi

echo "✅ Test suite completed successfully!"