#!/bin/bash

set -e

echo "🚀 Overmanifold Self-Hosted Auto-Deploy"
echo "========================================"

# Configuration
APP_DIR="/opt/overmanifold"
BACKUP_DIR="/opt/overmanifold-backups"
LOG_FILE="/var/log/overmanifold-deploy.log"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

error() {
    echo -e "${RED}[ERROR] $1${NC}" | tee -a "$LOG_FILE"
    exit 1
}

success() {
    echo -e "${GREEN}[SUCCESS] $1${NC}" | tee -a "$LOG_FILE"
}

warning() {
    echo -e "${YELLOW}[WARNING] $1${NC}" | tee -a "$LOG_FILE"
}

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    error "Please run as root (use sudo)"
fi

# Create necessary directories
mkdir -p "$BACKUP_DIR"
mkdir -p "$APP_DIR/logs"
mkdir -p /var/log

# Create SSL directory if it doesn't exist
if [ ! -d "$APP_DIR/ssl" ]; then
    log "Creating self-signed SSL certificates..."
    mkdir -p "$APP_DIR/ssl"
    openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
      -keyout "$APP_DIR/ssl/key.pem" \
      -out "$APP_DIR/ssl/cert.pem" \
      -subj "/C=US/ST=State/L=City/O=Overmanifold/CN=localhost"
    success "SSL certificates created"
fi

# Generate random secrets
log "Generating security secrets..."
SECRET_KEY=$(openssl rand -hex 32)
JWT_SECRET_KEY=$(openssl rand -hex 32)

# Create environment file with generated secrets
cat > "$APP_DIR/.env" << EOF
# Self-Hosted Configuration (Auto-Generated)
SECRET_KEY=$SECRET_KEY
JWT_SECRET_KEY=$JWT_SECRET_KEY
EOF

# Append base configuration
cat "$APP_DIR/.env.selfhosted" >> "$APP_DIR/.env"

# Backup current deployment if it exists
if [ -d "$APP_DIR/overmanifold" ]; then
    log "Creating backup..."
    BACKUP_NAME="backup-$(date +%Y%m%d-%H%M%S)"
    cp -r "$APP_DIR/overmanifold" "$BACKUP_DIR/$BACKUP_NAME"
    success "Backup created: $BACKUP_NAME"
fi

# Navigate to app directory
cd "$APP_DIR"

# Clone or update repository
if [ ! -d "overmanifold" ]; then
    log "Cloning repository..."
    git clone https://github.com/overandor/membra_db.git overmanifold
else
    log "Pulling latest changes..."
    cd overmanifold
    git fetch origin
    git reset --hard origin/main
    cd ..
fi

# Copy deployment files to app directory
cd overmanifold
cp ../docker-compose.selfhosted.yml docker-compose.yml
cp ../nginx-selfhosted.conf nginx.conf
cp ../.env .env
cp ../mock_membra_bridge.py .
cp ../Dockerfile.mock .

# Build and start services
log "Building Docker containers..."
docker-compose build --no-cache
success "Docker images built"

log "Stopping existing containers..."
docker-compose down || true
success "Containers stopped"

log "Starting new containers..."
docker-compose up -d
success "Containers started"

# Wait for services to be healthy
log "Waiting for services to be healthy..."
sleep 15

MAX_ATTEMPTS=30
ATTEMPT=0

while [ $ATTEMPT -lt $MAX_ATTEMPTS ]; do
    if docker ps --filter name=dashboard --filter status=running | grep -q dashboard; then
        if docker ps --filter name=mock-membra-bridge --filter status=running | grep -q mock-membra-bridge; then
            success "All services are healthy!"
            break
        fi
    fi
    ATTEMPT=$((ATTEMPT+1))
    echo "Waiting for services... ($ATTEMPT/$MAX_ATTEMPTS)"
    sleep 2
done

if [ $ATTEMPT -eq $MAX_ATTEMPTS ]; then
    error "Services failed to start"
fi

# Clean up old backups (keep last 5)
log "Cleaning old backups..."
cd "$BACKUP_DIR"
ls -t | tail -n +6 | xargs -r rm -rf 2>/dev/null || true
success "Old backups cleaned"

# Set up auto-update cron job if not already set
if ! crontab -l 2>/dev/null | grep -q "auto-update.sh"; then
    log "Setting up auto-update cron job..."
    (crontab -l 2>/dev/null; echo "0 * * * * cd $APP_DIR/overmanifold && ./auto-update.sh") | crontab -
    success "Auto-update configured (runs hourly)"
fi

# Show status
log "Deployment status:"
docker-compose ps

# Get server IP
SERVER_IP=$(hostname -I | awk '{print $1}')

success "Deployment completed successfully!"
log "Dashboard available at: https://$SERVER_IP"
log "Mock Membra Bridge: http://$SERVER_IP:8001"
log "API Stats: https://$SERVER_IP/api/stats"
log ""
log "Next steps:"
log "1. Visit https://$SERVER_IP to access the dashboard"
log "2. Register phone numbers and test SMS payments"
log "3. Monitor logs: docker-compose logs -f"
log "4. Update deployment: cd $APP_DIR/overmanifold && ./deploy-selfhosted.sh"