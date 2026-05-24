# Self-Hosted Auto-Deploy Guide (No API Keys Required)

## Overview

This guide shows you how to deploy the Overmanifold Membra Dashboard completely self-hosted without any external API keys or paid services.

## What You Need

- **VPS or home server** (DigitalOcean $6/mo, Linode $5/mo, or your own hardware)
- **Domain name** (optional, can use IP address)
- **Basic Linux knowledge**
- **SSH access to your server

---

## Architecture: 100% Self-Hosted

```
┌─────────────────────────────────────────────────────────────┐
│                    Your Server                              │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   Nginx      │  │   Dashboard  │  │   PostgreSQL │      │
│  │   (SSL/TLS)  │  │   (FastAPI)  │  │   (Database) │      │
│  │   Port 443   │  │   Port 8000  │  │   Port 5432  │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│         │                 │                 │               │
│         └─────────────────┴─────────────────┘               │
│                           │                                 │
│                    ┌──────────────┐                        │
│                    │   Redis      │                        │
│                    │   (Cache)    │                        │
│                    │   Port 6379  │                        │
│                    └──────────────┘                        │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

**Zero external dependencies:**
- ❌ No AWS/Azure/GCP required
- ❌ No Twilio/SMS gateway API keys needed
- ❌ No paid monitoring services
- ❌ No external email services
- ❌ No cloud databases
- ❌ No API keys anywhere

---

## Step 1: Prepare Your Server

### 1.1 Get a Server

**Options:**
- **DigitalOcean** - $6/mo (2GB RAM, 1 CPU, 50GB SSD)
- **Linode** - $5/mo (2GB RAM, 1 CPU, 50GB SSD)  
- **Vultr** - $6/mo (2GB RAM, 1 CPU, 55GB SSD)
- **Home server** - Use your own hardware

### 1.2 Connect to Server

```bash
ssh root@your-server-ip
```

### 1.3 Update System

```bash
apt update && apt upgrade -y
apt install -y curl git docker docker-compose nginx certbot python3-certbot-nginx
```

---

## Step 2: Clone and Setup Repository

### 2.1 Clone Repository

```bash
cd /opt
git clone https://github.com/overandor/membra_db.git overmanifold
cd overmanifold
```

### 2.2 Create Self-Hosted Environment File

```bash
cat > .env << 'EOF'
# Self-Hosted Configuration (No API Keys Required)

# Server Configuration
ENVIRONMENT=production
LOG_LEVEL=INFO
DEBUG=false

# Database Configuration (Self-Hosted PostgreSQL)
DATABASE_URL=postgresql://overmanifold:changeme123@postgres:5432/overmanifold
DATABASE_POOL_SIZE=10
DATABASE_MAX_OVERFLOW=5

# Redis Configuration (Self-Hosted Redis)
REDIS_URL=redis://redis:6379
REDIS_PASSWORD=
REDIS_DB=0

# Membra Bridge Configuration (Local Mock)
MEMBRA_API_URL=http://localhost:8001
MEMBRA_NETWORK=testnet
MEMBRA_MOCK_MODE=true

# Security (Self-Generated Keys)
SECRET_KEY=$(openssl rand -hex 32)
JWT_SECRET_KEY=$(openssl rand -hex 32)
JWT_EXPIRATION_HOURS=24

# SMS Gateway (Mock Mode - No API Key)
SMS_GATEWAY_PROVIDER=mock
SMS_GATEWAY_API_KEY=
SMS_GATEWAY_API_SECRET=
SMS_GATEWAY_PHONE_NUMBER=+15550123456

# Email Configuration (Local SMTP or Mock)
SMTP_SERVER=localhost
SMTP_PORT=25
SMTP_USERNAME=
SMTP_PASSWORD=
SMTP_FROM=noreply@localhost

# Sponsorship Configuration (Self-Managed)
SPONSORSHIP_ENABLED=true
DEFAULT_DAILY_BUDGET=10000
MIN_SPONSOR_AMOUNT=1
MAX_SPONSOR_AMOUNT=1000

# Monitoring (Self-Hosted)
SENTRY_DSN=
ENABLE_METRICS=true
METRICS_PORT=9090

# Rate Limiting
RATE_LIMIT_ENABLED=true
RATE_LIMIT_PER_MINUTE=60
RATE_LIMIT_PER_HOUR=1000

# CORS Configuration
CORS_ORIGINS=*
CORS_ALLOW_CREDENTIALS=true

# Server Configuration
SERVER_HOST=0.0.0.0
SERVER_PORT=8000
EOF
```

### 2.3 Generate SSL Certificates (Self-Signed or Let's Encrypt)

**Option A: Self-Signed (for testing)**
```bash
mkdir -p ssl
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout ssl/key.pem \
  -out ssl/cert.pem \
  -subj "/C=US/ST=State/L=City/O=Organization/CN=localhost"
```

**Option B: Let's Encrypt (for production with domain)**
```bash
# First, set up your domain to point to your server IP
certbot certonly --standalone -d yourdomain.com
# Certificates will be in /etc/letsencrypt/live/yourdomain.com/
```

---

## Step 3: Create Self-Hosted Docker Compose

### 3.1 Create docker-compose file

```bash
cat > docker-compose.selfhosted.yml << 'EOF'
version: '3.8'

services:
  dashboard:
    build:
      context: .
      dockerfile: Dockerfile.dashboard
    container_name: overmanifold-dashboard
    ports:
      - "8000:8000"
    env_file:
      - .env
    volumes:
      - ./logs:/app/logs
      - ./ssl:/app/ssl:ro
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    restart: unless-stopped
    networks:
      - overmanifold-network
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/api/stats"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

  postgres:
    image: postgres:15-alpine
    container_name: overmanifold-postgres
    environment:
      POSTGRES_DB: overmanifold
      POSTGRES_USER: overmanifold
      POSTGRES_PASSWORD: changeme123
    volumes:
      - postgres-data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    restart: unless-stopped
    networks:
      - overmanifold-network
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U overmanifold"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    container_name: overmanifold-redis
    ports:
      - "6379:6379"
    volumes:
      - redis-data:/data
    restart: unless-stopped
    networks:
      - overmanifold-network
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  nginx:
    image: nginx:alpine
    container_name: overmanifold-nginx
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx-selfhosted.conf:/etc/nginx/nginx.conf:ro
      - ./ssl:/etc/nginx/ssl:ro
    depends_on:
      - dashboard
    restart: unless-stopped
    networks:
      - overmanifold-network

volumes:
  postgres-data:
  redis-data:

networks:
  overmanifold-network:
    driver: bridge
EOF
```

---

## Step 4: Create Self-Hosted Nginx Configuration

### 4.1 Create Nginx config

```bash
cat > nginx-selfhosted.conf << 'EOF'
events {
    worker_connections 1024;
}

http {
    upstream dashboard_backend {
        server dashboard:8000;
    }

    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api_limit:10m rate=10r/s;
    limit_req_zone $binary_remote_addr zone=general_limit:10m rate=30r/s;

    # HTTP redirect to HTTPS
    server {
        listen 80;
        server_name _;

        location / {
            return 301 https://$host$request_uri;
        }
    }

    # HTTPS server
    server {
        listen 443 ssl http2;
        server_name _;

        # SSL configuration
        ssl_certificate /etc/nginx/ssl/cert.pem;
        ssl_certificate_key /etc/nginx/ssl/key.pem;
        ssl_protocols TLSv1.2 TLSv1.3;
        ssl_ciphers HIGH:!aNULL:!MD5;

        # Security headers
        add_header X-Frame-Options "SAMEORIGIN" always;
        add_header X-Content-Type-Options "nosniff" always;
        add_header X-XSS-Protection "1; mode=block" always;

        # Logging
        access_log /var/log/nginx/dashboard_access.log;
        error_log /var/log/nginx/dashboard_error.log;

        # API endpoints with stricter rate limiting
        location /api/ {
            limit_req zone=api_limit burst=20 nodelay;
            
            proxy_pass http://dashboard_backend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            
            proxy_connect_timeout 60s;
            proxy_send_timeout 60s;
            proxy_read_timeout 60s;
        }

        # Dashboard endpoints
        location / {
            limit_req zone=general_limit burst=50 nodelay;
            
            proxy_pass http://dashboard_backend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            
            proxy_connect_timeout 30s;
            proxy_send_timeout 30s;
            proxy_read_timeout 30s;
        }

        # Health check
        location /health {
            proxy_pass http://dashboard_backend/api/stats;
            access_log off;
        }
    }
}
EOF
```

---

## Step 5: Create Auto-Deploy Script

### 5.1 Create deployment script

```bash
cat > deploy-selfhosted.sh << 'EOF'
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

# Create backup directory
mkdir -p "$BACKUP_DIR"

# Backup current deployment
if [ -d "$APP_DIR" ]; then
    log "Creating backup..."
    BACKUP_NAME="backup-$(date +%Y%m%d-%H%M%S)"
    cp -r "$APP_DIR" "$BACKUP_DIR/$BACKUP_NAME"
    success "Backup created: $BACKUP_NAME"
fi

# Navigate to app directory
cd "$APP_DIR"

# Pull latest changes
log "Pulling latest changes..."
git fetch origin
git reset --hard origin/main
success "Code updated"

# Build and start services
log "Building Docker containers..."
docker-compose -f docker-compose.selfhosted.yml build --no-cache
success "Docker images built"

log "Stopping existing containers..."
docker-compose -f docker-compose.selfhosted.yml down || true
success "Containers stopped"

log "Starting new containers..."
docker-compose -f docker-compose.selfhosted.yml up -d
success "Containers started"

# Wait for services to be healthy
log "Waiting for services to be healthy..."
sleep 10

MAX_ATTEMPTS=30
ATTEMPT=0

while [ $ATTEMPT -lt $MAX_ATTEMPTS ]; do
    if docker ps --filter name=dashboard --filter status=running | grep -q dashboard; then
        success "Dashboard is healthy!"
        break
    fi
    ATTEMPT=$((ATTEMPT+1))
    echo "Waiting for dashboard... ($ATTEMPT/$MAX_ATTEMPTS)"
    sleep 2
done

if [ $ATTEMPT -eq $MAX_ATTEMPTS ]; then
    error "Dashboard failed to start"
fi

# Clean up old backups (keep last 5)
log "Cleaning old backups..."
cd "$BACKUP_DIR"
ls -t | tail -n +6 | xargs -r rm -rf
success "Old backups cleaned"

# Show status
log "Deployment status:"
docker-compose -f "$APP_DIR/docker-compose.selfhosted.yml" ps

success "Deployment completed successfully!"
log "Dashboard available at: https://$(hostname -I | awk '{print $1}')"
EOF

chmod +x deploy-selfhosted.sh
```

---

## Step 6: Create Auto-Update System

### 6.1 Create update script

```bash
cat > auto-update.sh << 'EOF'
#!/bin/bash

# Auto-update script - runs every hour via cron
# Add to crontab: 0 * * * * /opt/overmanifold/auto-update.sh

set -e

LOG_FILE="/var/log/overmanifold-update.log"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> "$LOG_FILE"
}

cd /opt/overmanifold

# Check for updates
git fetch origin
LOCAL=$(git rev-parse HEAD)
REMOTE=$(git rev-parse origin/main)

if [ "$LOCAL" != "$REMOTE" ]; then
    log "Updates available, deploying..."
    ./deploy-selfhosted.sh
else
    log "No updates available"
fi
EOF

chmod +x auto-update.sh
```

### 6.2 Add to crontab

```bash
# Add to crontab for automatic updates every hour
(crontab -l 2>/dev/null; echo "0 * * * * /opt/overmanifold/auto-update.sh") | crontab -
```

---

## Step 7: Mock Services for Zero Dependencies

### 7.1 Create Mock Membra Bridge

```bash
cat > mock_membra_bridge.py << 'EOF'
#!/usr/bin/env python3
"""
Mock Membra Bridge Server
Provides mock responses without requiring real Membra bridge
"""

from fastapi import FastAPI
from fastapi.responses import JSONResponse
import random
import hashlib
from datetime import datetime
from typing import Dict, Any

app = FastAPI(title="Mock Membra Bridge")

# In-memory storage
mock_wallets: Dict[str, Dict] = {}
mock_transactions: Dict[str, Dict] = {}

def generate_wallet_address(phone: str) -> str:
    """Generate mock wallet address from phone number"""
    hash_input = f"membra_{phone}_{datetime.utcnow().isoformat()}"
    return "0x" + hashlib.sha256(hash_input.encode()).hexdigest()[:40]

@app.get("/oracle/phone_validation")
async def validate_phone(phone: str) -> Dict[str, Any]:
    """Mock phone validation"""
    return {
        "valid": len(phone) >= 10 and phone.startswith("+"),
        "phone": phone,
        "country": "US"
    }

@app.get("/oracle/wallet_balance")
async def get_wallet_balance(address: str) -> Dict[str, Any]:
    """Mock wallet balance"""
    return {
        "address": address,
        "balance": random.randint(1000, 10000),
        "premined_tokens": 1000,
        "currency": "USDC"
    }

@app.get("/oracle/network_status")
async def network_status() -> Dict[str, Any]:
    """Mock network status"""
    return {
        "status": "healthy",
        "block_height": random.randint(1000000, 2000000),
        "tps": random.randint(100, 1000),
        "timestamp": datetime.utcnow().isoformat()
    }

@app.post("/register_phone_wallet")
async def register_wallet(phone: str, email: str = None) -> Dict[str, Any]:
    """Mock phone wallet registration"""
    wallet_address = generate_wallet_address(phone)
    
    mock_wallets[phone] = {
        "phone_number": phone,
        "wallet_address": wallet_address,
        "public_key": "0x" + hashlib.sha256(phone.encode()).hexdigest()[:40],
        "balance": 1000,
        "premined_tokens": 1000,
        "merkle_root": hashlib.sha256(wallet_address.encode()).hexdigest(),
        "is_active": True,
        "email": email
    }
    
    return {
        "success": True,
        "wallet_address": wallet_address,
        "public_key": mock_wallets[phone]["public_key"],
        "balance": 1000,
        "premined_tokens": 1000
    }

@app.get("/phone_wallet/{phone}")
async def get_phone_wallet(phone: str) -> Dict[str, Any]:
    """Get phone wallet information"""
    if phone in mock_wallets:
        return mock_wallets[phone]
    else:
        # Auto-register
        return await register_wallet(phone)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
EOF

chmod +x mock_membra_bridge.py
```

### 7.2 Add mock bridge to docker-compose

```bash
cat >> docker-compose.selfhosted.yml << 'EOF'

  mock-membra-bridge:
    build:
      context: .
      dockerfile: Dockerfile.mock
    container_name: mock-membra-bridge
    ports:
      - "8001:8001"
    restart: unless-stopped
    networks:
      - overmanifold-network
EOF
```

### 7.3 Create mock bridge Dockerfile

```bash
cat > Dockerfile.mock << 'EOF'
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY mock_membra_bridge.py .

CMD ["python", "mock_membra_bridge.py"]
EOF
```

---

## Step 8: Deploy Everything

### 8.1 Run deployment

```bash
cd /opt/overmanifold
./deploy-selfhosted.sh
```

### 8.2 Verify deployment

```bash
# Check containers
docker-compose -f docker-compose.selfhosted.yml ps

# Check logs
docker-compose -f docker-compose.selfhosted.yml logs -f dashboard

# Test API
curl https://your-server-ip/api/stats
```

---

## Step 9: Access Your Dashboard

### 9.1 Access via IP

```
https://your-server-ip/
```

### 9.2 Access via domain (if configured)

```
https://yourdomain.com/
```

---

## Step 10: Maintenance

### 10.1 View logs

```bash
# Dashboard logs
docker logs -f overmanifold-dashboard

# Nginx logs
tail -f /var/log/nginx/dashboard_access.log

# Deployment logs
tail -f /var/log/overmanifold-deploy.log
```

### 10.2 Update deployment

```bash
cd /opt/overmanifold
git pull origin main
./deploy-selfhosted.sh
```

### 10.3 Backup data

```bash
# Backup PostgreSQL
docker exec overmanifold-postgres pg_dump -U overmanifold overmanifold > backup.sql

# Backup Redis
docker exec overmanifold-redis redis-cli SAVE
docker cp overmanifold-redis:/data/dump.rdb ./redis-backup.rdb
```

---

## Cost Breakdown

### Self-Hosted Costs (Monthly)
- **VPS**: $5-6 (DigitalOcean/Linode)
- **Domain**: $10-12/year (optional)
- **Electricity**: $0 (if using existing hardware)

### Total: $5-6/month OR FREE with own hardware

---

## Security Considerations

### ✅ What's Secure
- SSL/TLS encryption
- Docker container isolation
- Internal network communication
- No external API exposures
- Self-controlled data

### 🔒 Additional Security (Optional)
- Firewall configuration
- Fail2Ban for SSH protection  
- Regular security updates
- Intrusion detection
- Off-site backups

---

## Troubleshooting

### Dashboard won't start
```bash
# Check logs
docker logs overmanifold-dashboard

# Check port conflicts
netstat -tulpn | grep :8000

# Restart services
docker-compose -f docker-compose.selfhosted.yml restart
```

### Can't access via HTTPS
```bash
# Check SSL certificates
ls -la ssl/

# Check Nginx configuration
docker logs overmanifold-nginx

# Test Nginx config
docker exec overmanifold-nginx nginx -t
```

### Database connection issues
```bash
# Check PostgreSQL is running
docker ps | grep postgres

# Test database connection
docker exec -it overmanifold-postgres psql -U overmanifold -d overmanifold
```

---

## Benefits of Self-Hosted Approach

### ✅ **Zero Cost** (with own hardware)
### ✅ **Complete Control** over data and infrastructure
### ✅ **No API Keys** or external dependencies
### ✅ **Privacy** - all data stays on your server
### ✅ **Reliability** - no external service outages
### ✅ **Scalability** - upgrade hardware as needed
### ✅ **Learning** - gain DevOps skills

---

## Next Steps

1. **Deploy to your server** using the scripts above
2. **Test all functionality** with mock services
3. **Set up domain** (optional but recommended)
4. **Configure backups** for disaster recovery
5. **Monitor performance** and optimize as needed
6. **Share with community** for real-world testing

You now have a completely self-hosted deployment with zero external dependencies and no API keys required! 🚀