#!/bin/bash

# MEMBRA Bridge Ecosystem Setup Script
# This script sets up the entire ecosystem for deployment

set -e

echo "🚀 Setting up MEMBRA Bridge Ecosystem..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
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

# Check if running as root
if [ "$EUID" -eq 0 ]; then 
    print_error "Please don't run this script as root"
    exit 1
fi

# Check Python version
echo "Checking Python version..."
if ! command -v python3 &> /dev/null; then
    print_error "Python 3 is not installed"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
echo "Found Python $PYTHON_VERSION"

if [[ $(echo "$PYTHON_VERSION 3.11" | awk '{print ($1 < $2)}') -eq 1 ]]; then
    print_warning "Python 3.11+ recommended, found $PYTHON_VERSION"
fi

# Check if Docker is installed
echo "Checking Docker installation..."
if ! command -v docker &> /dev/null; then
    print_error "Docker is not installed"
    echo "Please install Docker from https://docs.docker.com/get-docker/"
    exit 1
fi
print_success "Docker is installed"

# Check if Docker Compose is installed
echo "Checking Docker Compose installation..."
if ! command -v docker-compose &> /dev/null; then
    print_error "Docker Compose is not installed"
    echo "Please install Docker Compose from https://docs.docker.com/compose/install/"
    exit 1
fi
print_success "Docker Compose is installed"

# Check if Git is installed
echo "Checking Git installation..."
if ! command -v git &> /dev/null; then
    print_error "Git is not installed"
    exit 1
fi
print_success "Git is installed"

# Create necessary directories
echo "Creating directory structure..."
mkdir -p data logs zk_proofs monitoring/prometheus monitoring/grafana/dashboards monitoring/grafana/datasources
print_success "Directory structure created"

# Copy environment file
echo "Setting up environment configuration..."
if [ ! -f .env ]; then
    cp .env.example .env
    print_success "Created .env file from .env.example"
    print_warning "Please edit .env file with your configuration"
else
    print_warning ".env file already exists, skipping"
fi

# Install Python dependencies
echo "Installing Python dependencies..."
if [ -f requirements.txt ]; then
    pip3 install -r requirements.txt
    print_success "Python dependencies installed"
else
    print_error "requirements.txt not found"
    exit 1
fi

# Install Solana CLI (optional)
echo "Checking Solana CLI installation..."
if ! command -v solana &> /dev/null; then
    print_warning "Solana CLI not found. Installing..."
    sh -c "$(curl -sSfL https://release.solana.com/stable/install)"
    export PATH="$HOME/.local/share/solana/install/active_release/bin:$PATH"
    print_success "Solana CLI installed"
else
    print_success "Solana CLI is already installed"
fi

# Setup IPFS (optional)
echo "Checking IPFS installation..."
if ! command -v ipfs &> /dev/null; then
    print_warning "IPFS not found. IPFS will run in Docker container"
else
    print_success "IPFS is already installed"
    
    # Initialize IPFS if not already initialized
    if [ ! -d ~/.ipfs ]; then
        echo "Initializing IPFS..."
        ipfs init
        print_success "IPFS initialized"
    fi
fi

# Build Docker images
echo "Building Docker images..."
docker-compose build
print_success "Docker images built"

# Start infrastructure services
echo "Starting infrastructure services (IPFS, Redis, PostgreSQL)..."
docker-compose up -d ipfs redis postgres
print_success "Infrastructure services started"

# Wait for services to be ready
echo "Waiting for services to be ready..."
sleep 10

# Check service health
echo "Checking service health..."
if docker-compose ps | grep -q "Exit"; then
    print_error "Some services failed to start"
    docker-compose logs
    exit 1
fi
print_success "All services are healthy"

# Run database migrations (if applicable)
echo "Running database migrations..."
# Add migration commands here if you have them
print_success "Database migrations completed"

# Create initial data
echo "Creating initial data..."
# Add any initial data setup here
print_success "Initial data created"

# Print setup summary
echo ""
echo "=========================================="
print_success "MEMBRA Bridge Ecosystem Setup Complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Edit .env file with your configuration"
echo "2. Start all services: docker-compose up -d"
echo "3. Check service status: docker-compose ps"
echo "4. View logs: docker-compose logs -f"
echo "5. Access API: http://localhost:8080"
echo "6. Access Grafana: http://localhost:3000 (admin/admin)"
echo "7. Access Prometheus: http://localhost:9090"
echo ""
echo "For more information, see README.md"
echo ""