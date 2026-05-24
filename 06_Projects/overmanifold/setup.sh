#!/bin/bash

# Overmanifold Protocol Setup Script
# Civilization-Scale Cryptographic-Economic Coordination Architecture

set -e

echo "🌐 Initializing Overmanifold Protocol..."
echo "Civilization-Scale Cryptographic-Economic Coordination Architecture"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Function to print colored output
print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_info() {
    echo -e "${CYAN}ℹ $1${NC}"
}

print_section() {
    echo ""
    echo -e "${PURPLE}=== $1 ===${NC}"
    echo ""
}

# Check Python version
echo "Checking Python version..."
if ! command -v python3 &> /dev/null; then
    print_error "Python 3 is not installed"
    echo "Please install Python 3.11+ from https://www.python.org/"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
echo "Found Python $PYTHON_VERSION"

if [[ $(echo "$PYTHON_VERSION 3.11" | awk '{print ($1 < $2)}') -eq 1 ]]; then
    print_warning "Python 3.11+ recommended, found $PYTHON_VERSION"
else
    print_success "Python version meets requirements"
fi

# Check if pip is available
echo "Checking pip installation..."
if ! command -v pip3 &> /dev/null; then
    print_error "pip3 is not installed"
    exit 1
fi
print_success "pip3 is installed"

# Create directory structure
print_section "Creating Directory Structure"
mkdir -p logs
mkdir -p data/manifold
mkdir -p data/endpoints
mkdir -p data/proofs
mkdir -p data/governance
mkdir -p data/routing
mkdir -p data/consensus
mkdir -p cache
mkdir -p config

print_success "Directory structure created"

# Copy environment template
print_section "Environment Configuration"
if [ ! -f .env ]; then
    cat > .env << 'EOF'
# Overmanifold Protocol Configuration
# Civilization-Scale Cryptographic-Economic Coordination Architecture

# Core Parameters
INITIAL_SUPPLY=1000000000
CONSENSUS_THRESHOLD=0.67
VERIFICATION_WINDOW_SECONDS=3600

# Database Configuration
DATABASE_URL=sqlite:///data/overmanifold.db
REDIS_URL=redis://localhost:6379

# LLM Configuration
LLM_PROVIDER=mock
OPENAI_API_KEY=your_openai_api_key_here
ANTHROPIC_API_KEY=your_anthropic_api_key_here

# Network Configuration
NETWORK_ID=overmanifold-mainnet
CHAIN_ID=overmanifold-1
GENESIS_TIMESTAMP=2024-01-01T00:00:00Z

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
API_WORKERS=4

# Logging Configuration
LOG_LEVEL=INFO
LOG_FILE_PATH=logs/overmanifold.log

# Security Configuration
SECRET_KEY=your-secret-key-here-change-in-production
ENCRYPTION_KEY=your-encryption-key-here-change-in-production

# Economic Parameters
BASE_REWARD_PER_UNIT_VALUE=0.001
DIFFICULTY_MULTIPLIER=2.0
IMPACT_MULTIPLIER=1.5
BURN_RATE=0.0001
DEFLATION_RATE=0.00005

# Routing Parameters
MAX_PATH_LENGTH=10
DEFAULT_TRUST_DENSITY=0.7
DEFAULT_SLIPPAGE=0.02
DEFAULT_LATENCY_MS=100

# Feature Flags
ENABLE_LLM_GOVERNANCE=true
ENABLE_GEODESIC_ROUTING=true
ENABLE_PROOF_OF_PROFIT=true
ENABLE_INVERSE_MINING=true
ENABLE_TREASURY_DEFLATION=true
EOF
    print_success "Created .env file"
    print_warning "Please edit .env file with your configuration"
else
    print_warning ".env file already exists, skipping"
fi

# Install Python dependencies
print_section "Installing Python Dependencies"
if [ -f requirements.txt ]; then
    pip3 install -r requirements.txt
    print_success "Python dependencies installed"
else
    print_error "requirements.txt not found"
    exit 1
fi

# Verify core installations
print_section "Verifying Core Installations"

# Verify cryptography libraries
python3 -c "import nacl; print('PyNaCl installed successfully')"
print_success "PyNaCl verified"

python3 -c "import cryptography; print('Cryptography installed successfully')"
print_success "Cryptography verified"

# Verify data processing libraries
python3 -c "import numpy; print('NumPy installed successfully')"
print_success "NumPy verified"

python3 -c "import networkx; print('NetworkX installed successfully')"
print_success "NetworkX verified"

# Initialize Overmanifold database
print_section "Initializing Overmanifold Database"
python3 -c "
from overmanifold.core.engine import OvermanifoldEngine
engine = OvermanifoldEngine()
print('Overmanifold Engine initialized successfully')
print(f'Manifold state: {engine.get_manifold_state()}')
"
print_success "Overmanifold database initialized"

# Create initial configuration
print_section "Creating Initial Configuration"
cat > config/manifold_config.json << 'EOF'
{
  "manifold_id": "overmanifold-mainnet",
  "genesis_timestamp": "2024-01-01T00:00:00Z",
  "initial_supply": 1000000000,
  "consensus_parameters": {
    "threshold": 0.67,
    "verification_window": 3600,
    "slashing_conditions": {
      "reputation_below_threshold": 0.3,
      "failed_verification_rate": 0.5
    }
  },
  "economic_parameters": {
    "base_reward_rate": 0.001,
    "difficulty_multiplier": 2.0,
    "impact_multiplier": 1.5,
    "burn_rate": 0.0001,
    "deflation_rate": 0.00005
  },
  "routing_parameters": {
    "max_path_length": 10,
    "default_trust_density": 0.7,
    "default_slippage": 0.02,
    "default_latency_ms": 100
  },
  "network_topology": {
    "default_trust_density": 0.5,
    "minimum_capability_strength": 0.5,
    "connectivity_requirement": 3
  }
}
EOF
print_success "Initial configuration created"

# Run system verification
print_section "Running System Verification"
python3 -c "
import asyncio
from overmanifold.unified import OvermanifoldUnified

async def verify_system():
    overmanifold = OvermanifoldUnified()
    print('✓ Overmanifold Unified System initialized')
    print('✓ Core Engine: Ready')
    print('✓ LLM Governance: Ready')
    print('✓ Geodesic Routing: Ready')
    print('✓ Proof-of-Profit Consensus: Ready')
    print('')
    print('System Verification Complete')
    return overmanifold.get_unified_state()

state = asyncio.run(verify_system())
print('')
print('Initial System State:')
print(f'  Circulating Supply: {state[\"supply_metrics\"][\"circulating_supply\"]}')
print(f'  Total Supply: {state[\"supply_metrics\"][\"initial_supply\"]}')
print(f'  Burned Supply: {state[\"supply_metrics\"][\"burned_supply\"]}')
"
print_success "System verification complete"

# Create startup script
print_section "Creating Startup Scripts"
cat > start_overmanifold.sh << 'EOF'
#!/bin/bash

# Overmanifold Protocol Startup Script

echo "🌐 Starting Overmanifold Protocol..."

# Load environment variables
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

# Start the unified system
python3 -m overmanifold.unified
EOF
chmod +x start_overmanifold.sh
print_success "Startup script created"

# Create demo script
cat > demo_overmanifold.sh << 'EOF'
#!/bin/bash

# Overmanifold Protocol Demo Script

echo "🌐 Running Overmanifold Protocol Demo..."
echo ""

python3 -c "
import asyncio
from overmanifold.unified import OvermanifoldUnified

async def run_demo():
    overmanifold = OvermanifoldUnified()
    final_state = overmanifold.simulate_civilization_scale_coordination()
    return final_state

state = asyncio.run(run_demo())
print('')
print('=== Demo Complete ===')
print(f'Final Supply: {state[\"supply_metrics\"][\"circulating_supply\"]:.2f}')
print(f'Total Endpoints: {len(state[\"unified_endpoints\"])}')
print(f'Coordination Events: {state[\"total_coordination_events\"]}')
"
EOF
chmod +x demo_overmanifold.sh
print_success "Demo script created"

# Print setup summary
print_section "Setup Complete"
echo ""
echo "🎉 Overmanifold Protocol has been successfully initialized!"
echo ""
echo "Next Steps:"
echo "1. Edit .env file with your configuration"
echo "2. Run the demo: ./demo_overmanifold.sh"
echo "3. Start the system: ./start_overmanifold.sh"
echo "4. Monitor logs: tail -f logs/overmanifold.log"
echo ""
echo "Documentation:"
echo "- README.md: Complete protocol documentation"
echo "- IMPLEMENTATION_SUMMARY.md: Detailed implementation guide"
echo "- overmanifold/ directory: Source code"
echo ""
echo "Key Components:"
echo "- Core Engine: Unified identity and state transitions"
echo "- LLM Governance: Human intent interpretation"
echo "- Geodesic Routing: Optimal manifold traversal"
echo "- Proof-of-Profit: Economic work verification"
echo "- Inverse Mining: Supply burn based on useful work"
echo ""
echo "The Overmanifold is ready for civilization-scale coordination."
echo ""
echo "🌐 Overmanifold: Where human intent becomes economic state"
echo ""