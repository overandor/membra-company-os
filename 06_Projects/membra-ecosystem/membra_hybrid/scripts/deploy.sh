#!/bin/bash

# Deployment automation script for Membra DNS system
# Handles deployment to devnet, testnet, and mainnet

set -e

echo "🚀 Membra DNS Deployment System"
echo "=============================="
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CONTRACTS_DIR="$PROJECT_ROOT/smart-contracts/membra-dns"
CLUSTER="devnet"
SKIP_BUILD=false
BACKUP=false

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --cluster)
            CLUSTER="$2"
            shift 2
            ;;
        --skip-build)
            SKIP_BUILD=true
            shift
            ;;
        --backup)
            BACKUP=true
            shift
            ;;
        --help)
            echo "Usage: $0 [OPTIONS]"
            echo "Options:"
            echo "  --cluster <name>  Target cluster (devnet, testnet, mainnet)"
            echo "  --skip-build     Skip building before deployment"
            echo "  --backup         Create backup before deployment"
            echo "  --help           Show this help message"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

echo "📋 Deployment Configuration:"
echo "   Cluster: $CLUSTER"
echo "   Skip Build: $SKIP_BUILD"
echo "   Backup: $BACKUP"
echo ""

# Validation
if [[ ! "$CLUSTER" =~ ^(devnet|testnet|mainnet)$ ]]; then
    echo -e "${RED}✗ Invalid cluster: $CLUSTER${NC}"
    echo "Valid clusters: devnet, testnet, mainnet"
    exit 1
fi

if [ "$CLUSTER" == "mainnet" ]; then
    echo -e "${YELLOW}⚠️  WARNING: Deploying to mainnet${NC}"
    echo "This will use real funds and cannot be undone."
    read -p "Are you sure? (yes/no): " confirm
    if [ "$confirm" != "yes" ]; then
        echo "Deployment cancelled"
        exit 0
    fi
fi

# Check prerequisites
echo "🔍 Checking prerequisites..."
echo "---------------------------"

# Check Solana CLI
if ! command -v solana &> /dev/null; then
    echo -e "${RED}✗ Solana CLI not found${NC}"
    echo "Install from: https://docs.solana.com/cli/install-solana-cli-tools"
    exit 1
fi

# Check Anchor CLI
if ! command -v anchor &> /dev/null; then
    echo -e "${RED}✗ Anchor CLI not found${NC}"
    echo "Install with: cargo install anchor-cli"
    exit 1
fi

# Check wallet
if ! solana address &> /dev/null; then
    echo -e "${RED}✗ Solana wallet not configured${NC}"
    exit 1
fi

WALLET_ADDRESS=$(solana address)
echo -e "${GREEN}✓ Solana CLI installed${NC}"
echo -e "${GREEN}✓ Anchor CLI installed${NC}"
echo -e "${GREEN}✓ Wallet configured: $WALLET_ADDRESS${NC}"
echo ""

# Check balance
BALANCE=$(solana balance --output json | jq '.amount')
echo "💰 Wallet balance: $BALANCE SOL"

if (( $(echo "$BALANCE < 0.1" | bc -l) )); then
    echo -e "${YELLOW}⚠️  Low balance. Consider airdropping SOL on devnet${NC}"
    if [ "$CLUSTER" == "devnet" ]; then
        read -p "Airdrop 2 SOL? (y/n): " airdrop
        if [ "$airdrop" == "y" ]; then
            solana airdrop 2
        fi
    fi
fi
echo ""

# Set cluster
echo "🔧 Setting cluster to $CLUSTER..."
solana config set --url $CLUSTER
CURRENT_CLUSTER=$(solana config get | grep "RPC URL" | awk '{print $3}')
echo -e "${GREEN}✓ Cluster set to: $CURRENT_CLUSTER${NC}"
echo ""

# Build if not skipped
if [ "$SKIP_BUILD" = false ]; then
    echo "🔨 Building smart contract..."
    cd "$CONTRACTS_DIR"
    cargo build-sbf
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ Build successful${NC}"
    else
        echo -e "${RED}✗ Build failed${NC}"
        exit 1
    fi
    echo ""
fi

# Backup if requested
if [ "$BACKUP" = true ]; then
    echo "💾 Creating backup..."
    BACKUP_DIR="$PROJECT_ROOT/backups/$(date +%Y%m%d_%H%M%S)"
    mkdir -p "$BACKUP_DIR"
    
    # Backup current program ID
    CURRENT_PROGRAM_ID=$(anchor keys list | grep membra_dns | awk '{print $2}')
    echo "$CURRENT_PROGRAM_ID" > "$BACKUP_DIR/previous_program_id.txt"
    
    # Backup keypairs
    cp -r "$CONTRACTS_DIR/target/deploy/" "$BACKUP_DIR/"
    
    echo -e "${GREEN}✓ Backup created at: $BACKUP_DIR${NC}"
    echo ""
fi

# Deploy smart contract
echo "🚀 Deploying smart contract to $CLUSTER..."
echo "--------------------------------------------"

cd "$CONTRACTS_DIR"
anchor deploy --cluster $CLUSTER

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Smart contract deployed successfully${NC}"
else
    echo -e "${RED}✗ Smart contract deployment failed${NC}"
    exit 1
fi

# Get program ID
PROGRAM_ID=$(anchor keys list | grep membra_dns | awk '{print $2}')
echo "Program ID: $PROGRAM_ID"
echo ""

# Verify deployment
echo "🔍 Verifying deployment..."
echo "-------------------------"

# Check if program exists
PROGRAM_INFO=$(solana program show $PROGRAM_ID --output json 2>/dev/null || echo "{}")
if [ "$PROGRAM_INFO" != "{}" ]; then
    echo -e "${GREEN}✓ Program verified on-chain${NC}"
    echo "Program: $PROGRAM_ID"
    echo "Owner: $(echo $PROGRAM_INFO | jq -r '.owner')"
else
    echo -e "${RED}✗ Program verification failed${NC}"
    exit 1
fi
echo ""

# Initialize the program
echo "🔧 Initializing program..."
echo "--------------------------"

# This would typically call the initialize instruction
# For now, we'll just provide guidance
echo "To initialize the program, run:"
echo "anchor test --skip-local-validator"
echo ""

# Update configuration
echo "📝 Updating configuration..."
echo "----------------------------"

CONFIG_FILE="$PROJECT_ROOT/dns-config.toml"
if [ -f "$CONFIG_FILE" ]; then
    sed -i.bak "s/program_id = .*/program_id = \"$PROGRAM_ID\"/" "$CONFIG_FILE"
    echo -e "${GREEN}✓ Configuration updated${NC}"
else
    echo "Creating new configuration file..."
    cat > "$CONFIG_FILE" << EOF
[on_chain_dns]
chain = "solana"
rpc_url = "$CURRENT_CLUSTER"
program_id = "$PROGRAM_ID"
enable_caching = true
cache_ttl_secs = 300
EOF
    echo -e "${GREEN}✓ Configuration created${NC}"
fi
echo ""

# Deployment summary
echo "================================"
echo -e "${GREEN}🎉 Deployment completed successfully!${NC}"
echo "================================"
echo ""
echo "📊 Deployment Summary:"
echo "   Cluster: $CLUSTER"
echo "   Program ID: $PROGRAM_ID"
echo "   Wallet: $WALLET_ADDRESS"
echo "   Config: $CONFIG_FILE"
echo ""
echo "🔗 Useful Commands:"
echo "   View program: solana program show $PROGRAM_ID"
echo "   Program logs: solana logs $PROGRAM_ID"
echo "   Test program: cd $CONTRACTS_DIR && anchor test"
echo ""
echo "📝 Next Steps:"
echo "   1. Initialize the program with admin authority"
echo "   2. Register DNS zones using the CLI"
echo "   3. Test the functionality"
echo "   4. Monitor the program logs"
echo ""

# Post-deployment checks
echo "🔍 Post-deployment checks..."
echo "---------------------------"

# Check if we can get program account
if solana account $PROGRAM_ID &> /dev/null; then
    echo -e "${GREEN}✓ Program account accessible${NC}"
else
    echo -e "${YELLOW}⚠️  Program account not immediately accessible${NC}"
    echo "This is normal for some clusters"
fi

echo ""
echo "✅ Deployment process completed!"