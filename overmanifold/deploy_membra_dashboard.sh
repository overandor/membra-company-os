#!/bin/bash

# Membra Dashboard Remote Deployment Script
# This script deploys the Membra dashboard to a remote server

set -e

# Configuration
REMOTE_HOST="${REMOTE_HOST:-user@membra-server.com}"
REMOTE_DIR="${REMOTE_DIR:-/opt/membra-dashboard}"
DEPLOY_KEY="${DEPLOY_KEY:-~/.ssh/membra_deploy}"
ENV_FILE="${ENV_FILE:-.env.production}"
COMPOSE_FILE="membra_dashboard_deployment.yml"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "🚀 Membra Dashboard Remote Deployment"
echo "======================================"

# Check if environment file exists
if [ ! -f "$ENV_FILE" ]; then
    echo -e "${RED}Error: Environment file $ENV_FILE not found${NC}"
    echo "Please create .env.production with required variables:"
    echo "  - SOLANA_RPC_URL"
    echo "  - MEMBRA_PRIVATE_KEY"
    echo "  - SENTRY_DSN (optional)"
    exit 1
fi

# Check if deploy key exists
if [ ! -f "$DEPLOY_KEY" ]; then
    echo -e "${YELLOW}Warning: Deploy key not found at $DEPLOY_KEY${NC}"
    echo "Using default SSH key"
    DEPLOY_KEY=""
fi

# Function to execute remote command
execute_remote() {
    if [ -n "$DEPLOY_KEY" ]; then
        ssh -i "$DEPLOY_KEY" "$REMOTE_HOST" "$1"
    else
        ssh "$REMOTE_HOST" "$1"
    fi
}

# Function to copy file to remote
copy_to_remote() {
    if [ -n "$DEPLOY_KEY" ]; then
        scp -i "$DEPLOY_KEY" "$1" "$REMOTE_HOST:$2"
    else
        scp "$1" "$REMOTE_HOST:$2"
    fi
}

echo -e "${GREEN}Step 1: Preparing deployment package...${NC}"
# Create deployment package
DEPLOY_DIR="deploy_package"
rm -rf "$DEPLOY_DIR"
mkdir -p "$DEPLOY_DIR"

# Copy necessary files
cp -r overmanifold "$DEPLOY_DIR/"
cp Dockerfile.dashboard "$DEPLOY_DIR/"
cp membra_dashboard_deployment.yml "$DEPLOY_DIR/docker-compose.yml"
cp nginx.conf "$DEPLOY_DIR/"
cp "$ENV_FILE" "$DEPLOY_DIR/.env"

# Create deployment package tar
tar -czf membra-dashboard-deploy.tar.gz "$DEPLOY_DIR"
rm -rf "$DEPLOY_DIR"

echo -e "${GREEN}Step 2: Connecting to remote server...${NC}"
# Test connection
execute_remote "echo 'Connection successful'"

echo -e "${GREEN}Step 3: Uploading deployment package...${NC}"
# Create remote directory if it doesn't exist
execute_remote "mkdir -p $REMOTE_DIR"

# Upload deployment package
copy_to_remote "membra-dashboard-deploy.tar.gz" "$REMOTE_DIR/"

echo -e "${GREEN}Step 4: Extracting and deploying on remote server...${NC}"
# Extract and deploy
execute_remote "cd $REMOTE_DIR && tar -xzf membra-dashboard-deploy.tar.gz && rm membra-dashboard-deploy.tar.gz"

echo -e "${GREEN}Step 5: Stopping existing services...${NC}"
execute_remote "cd $REMOTE_DIR && docker-compose down || true"

echo -e "${GREEN}Step 6: Building and starting new services...${NC}"
execute_remote "cd $REMOTE_DIR && docker-compose build --no-cache"
execute_remote "cd $REMOTE_DIR && docker-compose up -d"

echo -e "${GREEN}Step 7: Waiting for services to be healthy...${NC}"
sleep 10

# Check service health
MAX_ATTEMPTS=30
ATTEMPT=0
while [ $ATTEMPT -lt $MAX_ATTEMPTS ]; do
    if execute_remote "docker ps --filter name=membra-dashboard --filter status=running | grep -q membra-dashboard"; then
        echo -e "${GREEN}Services are healthy!${NC}"
        break
    fi
    ATTEMPT=$((ATTEMPT+1))
    echo "Waiting for services to start... ($ATTEMPT/$MAX_ATTEMPTS)"
    sleep 2
done

if [ $ATTEMPT -eq $MAX_ATTEMPTS ]; then
    echo -e "${RED}Error: Services failed to start${NC}"
    execute_remote "cd $REMOTE_DIR && docker-compose logs"
    exit 1
fi

echo -e "${GREEN}Step 8: Cleaning up...${NC}"
rm -f membra-dashboard-deploy.tar.gz

echo -e "${GREEN}Step 9: Verifying deployment...${NC}"
# Check if dashboard is responding
if execute_remote "curl -f http://localhost:8000/api/stats > /dev/null 2>&1"; then
    echo -e "${GREEN}✓ Dashboard is responding${NC}"
else
    echo -e "${YELLOW}⚠ Dashboard is not yet responding (this may be normal during startup)${NC}"
fi

echo ""
echo -e "${GREEN}======================================"
echo "Deployment completed successfully!"
echo "======================================${NC}"
echo ""
echo "Dashboard URL: http://$REMOTE_HOST:8000"
echo "API Stats: http://$REMOTE_HOST:8000/api/stats"
echo ""
echo "To view logs:"
echo "  ssh $REMOTE_HOST 'cd $REMOTE_DIR && docker-compose logs -f'"
echo ""
echo "To stop services:"
echo "  ssh $REMOTE_HOST 'cd $REMOTE_DIR && docker-compose down'"
echo ""
echo "To restart services:"
echo "  ssh $REMOTE_HOST 'cd $REMOTE_DIR && docker-compose restart'"
echo ""