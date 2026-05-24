#!/bin/bash

# Overmanifold Protocol Deployment Script
# Supports local, staging, and production deployments

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
ENVIRONMENT="${1:-local}"
VERSION="${2:-latest}"

echo -e "${GREEN}Overmanifold Protocol Deployment${NC}"
echo "Environment: $ENVIRONMENT"
echo "Version: $VERSION"
echo ""

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check prerequisites
check_prerequisites() {
    print_status "Checking prerequisites..."
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed"
        exit 1
    fi
    
    # Check Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        print_error "Docker Compose is not installed"
        exit 1
    fi
    
    # Check kubectl for K8s deployment
    if [ "$ENVIRONMENT" != "local" ]; then
        if ! command -v kubectl &> /dev/null; then
            print_error "kubectl is not installed"
            exit 1
        fi
    fi
    
    print_status "Prerequisites check passed"
}

# Function to setup environment
setup_environment() {
    print_status "Setting up environment..."
    
    cd "$PROJECT_ROOT"
    
    # Create .env file if it doesn't exist
    if [ ! -f .env ]; then
        if [ -f .env.example ]; then
            cp .env.example .env
            print_warning "Created .env from .env.example - please update with your values"
        else
            print_error ".env.example not found"
            exit 1
        fi
    fi
    
    # Create necessary directories
    mkdir -p logs
    mkdir -p monitoring/grafana/dashboards
    mkdir -p monitoring/grafana/datasources
    mkdir -p monitoring/prometheus
    
    # Generate secret key if not set
    if ! grep -q "SECRET_KEY=" .env || grep -q "SECRET_KEY=$" .env; then
        SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
        sed -i.bak "s/SECRET_KEY=.*/SECRET_KEY=$SECRET_KEY/" .env
        rm .env.bak
        print_status "Generated new SECRET_KEY"
    fi
    
    print_status "Environment setup complete"
}

# Function to deploy locally
deploy_local() {
    print_status "Deploying to local environment..."
    
    cd "$PROJECT_ROOT"
    
    # Stop existing containers
    print_status "Stopping existing containers..."
    docker-compose down
    
    # Build and start services
    print_status "Building and starting services..."
    docker-compose up -d --build
    
    # Wait for services to be healthy
    print_status "Waiting for services to be healthy..."
    sleep 10
    
    # Check health
    if curl -f http://localhost:8000/health > /dev/null 2>&1; then
        print_status "Local deployment successful!"
        echo "API available at: http://localhost:8000"
        echo "Documentation at: http://localhost:8000/docs"
        echo "Grafana at: http://localhost:3000 (admin/admin)"
    else
        print_error "Health check failed"
        docker-compose logs
        exit 1
    fi
}

# Function to deploy to Kubernetes
deploy_kubernetes() {
    print_status "Deploying to Kubernetes environment: $ENVIRONMENT"
    
    cd "$PROJECT_ROOT"
    
    # Set namespace
    NAMESPACE="overmanifold-$ENVIRONMENT"
    
    # Create namespace
    print_status "Creating namespace: $NAMESPACE"
    kubectl create namespace "$NAMESPACE" --dry-run=client -o yaml | kubectl apply -f -
    
    # Create secrets
    print_status "Creating secrets..."
    kubectl create secret generic overmanifold-secrets \
        --from-literal=db-password="${DB_PASSWORD:-change_me}" \
        --from-literal=secret-key="${SECRET_KEY:-change_me}" \
        --namespace="$NAMESPACE" \
        --dry-run=client -o yaml | kubectl apply -f -
    
    # Apply configurations
    print_status "Applying Kubernetes configurations..."
    
    # Apply in order
    kubectl apply -f k8s/configmap.yaml --namespace="$NAMESPACE"
    kubectl apply -f k8s/secrets.yaml --namespace="$NAMESPACE"
    kubectl apply -f k8s/postgres.yaml --namespace="$NAMESPACE"
    kubectl apply -f k8s/redis.yaml --namespace="$NAMESPACE"
    kubectl apply -f k8s/api.yaml --namespace="$NAMESPACE"
    kubectl apply -f k8s/ingress.yaml --namespace="$NAMESPACE"
    
    # Wait for deployment
    print_status "Waiting for deployment to be ready..."
    kubectl wait --for=condition=available --timeout=300s \
        deployment/overmanifold-api -n "$NAMESPACE"
    
    # Get service URL
    SERVICE_URL=$(kubectl get svc overmanifold-api -n "$NAMESPACE" -o jsonpath='{.status.loadBalancer.ingress[0].hostname}')
    
    if [ -n "$SERVICE_URL" ]; then
        print_status "Kubernetes deployment successful!"
        echo "API available at: http://$SERVICE_URL"
    else
        print_status "Kubernetes deployment completed (using port-forward)"
        echo "Run: kubectl port-forward svc/overmanifold-api -n $NAMESPACE 8000:80"
    fi
}

# Function to run tests
run_tests() {
    print_status "Running tests..."
    
    cd "$PROJECT_ROOT"
    
    # Install test dependencies
    pip install pytest pytest-asyncio pytest-cov
    
    # Run tests
    pytest tests/ -v --cov=overmanifold --cov-report=html --cov-fail-under=80
    
    if [ $? -eq 0 ]; then
        print_status "All tests passed!"
    else
        print_error "Tests failed"
        exit 1
    fi
}

# Function to build Docker image
build_image() {
    print_status "Building Docker image: overmanifold/protocol:$VERSION"
    
    cd "$PROJECT_ROOT"
    
    docker build -t "overmanifold/protocol:$VERSION" .
    
    if [ $? -eq 0 ]; then
        print_status "Docker image built successfully!"
        
        # Tag as latest if version is not latest
        if [ "$VERSION" != "latest" ]; then
            docker tag "overmanifold/protocol:$VERSION" overmanifold/protocol:latest
        fi
    else
        print_error "Docker build failed"
        exit 1
    fi
}

# Function to push Docker image
push_image() {
    print_status "Pushing Docker image: overmanifold/protocol:$VERSION"
    
    docker push "overmanifold/protocol:$VERSION"
    
    if [ "$VERSION" != "latest" ]; then
        docker push overmanifold/protocol:latest
    fi
    
    print_status "Docker image pushed successfully!"
}

# Main deployment logic
main() {
    check_prerequisites
    setup_environment
    
    case "$ENVIRONMENT" in
        local)
            deploy_local
            ;;
        staging|production)
            build_image
            push_image
            deploy_kubernetes
            ;;
        test)
            run_tests
            ;;
        *)
            print_error "Unknown environment: $ENVIRONMENT"
            echo "Usage: $0 [local|staging|production|test] [version]"
            exit 1
            ;;
    esac
    
    print_status "Deployment completed successfully!"
}

# Run main function
main