#!/bin/bash

# Auto-update script - runs every hour via cron
# This script checks for updates and deploys them automatically

set -e

LOG_FILE="/var/log/overmanifold-update.log"
APP_DIR="/opt/overmanifold"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> "$LOG_FILE"
}

error() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] [ERROR] $1" >> "$LOG_FILE"
    exit 1
}

success() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] [SUCCESS] $1" >> "$LOG_FILE"
}

log "Starting auto-update check..."

cd "$APP_DIR/overmanifold" || error "Cannot find application directory"

# Check for updates
log "Checking for updates..."
git fetch origin

LOCAL=$(git rev-parse HEAD)
REMOTE=$(git rev-parse origin/main)

if [ "$LOCAL" != "$REMOTE" ]; then
    log "Updates available, deploying..."
    
    # Run deployment script
    if [ -f "../deploy-selfhosted.sh" ]; then
        cd ..
        ./deploy-selfhosted.sh
        success "Auto-update completed"
    else
        error "Deployment script not found"
    fi
else
    log "No updates available - already at latest version"
fi

log "Auto-update check completed"