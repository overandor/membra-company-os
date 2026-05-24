# MEMBRA Bridge Ecosystem - Deployment Guide

Complete deployment guide for the MEMBRA Bridge Ecosystem with hierarchical merkle root taxonomy, IPFS backup, phone-based wallet addresses, SMS mining, and oracle integration.

## Prerequisites

- Python 3.11+
- Docker & Docker Compose
- Git
- 8GB+ RAM
- 50GB+ available disk space
- Solana CLI (optional, for wallet operations)

## Quick Start

### 1. Clone and Setup

```bash
# Clone the repository
git clone https://github.com/your-repo/membra-bridge-ecosystem
cd membra-bridge-ecosystem

# Run setup script
chmod +x setup.sh
./setup.sh
```

### 2. Configure Environment

```bash
# Copy environment template
cp .env.example .env

# Edit configuration
nano .env
```

### 3. Start Services

```bash
# Start all services
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f
```

### 4. Access Services

- **API Gateway**: http://localhost:8080
- **API Documentation**: http://localhost:8080/docs
- **Grafana Dashboard**: http://localhost:3000 (admin/admin)
- **Prometheus**: http://localhost:9090
- **IPFS Gateway**: http://localhost:8080

## Architecture Overview

### Core Components

1. **File Tokenization Service** (`file-tokenizer:8001`)
   - Hierarchical merkle tree construction
   - File system scanning and hashing
   - Mathematical proof generation

2. **Oracle System** (`oracle-system:8002`)
   - 30+ endpoint integration
   - Real-time price discovery
   - KPI tracking and signals

3. **Phone Wallet Service** (`phone-wallet:8003`)
   - Phone-to-wallet mapping
   - SMS mining rewards
   - Premined token distribution

4. **KPI Tracker** (`kpi-tracker:8004`)
   - Advanced KPI calculation
   - Arbitrage signal generation
   - Market analysis

5. **ZK Verifier** (`zk-verifier:8005`)
   - Zero-knowledge proof generation
   - M5 Pro MacBook validation
   - Resource staking coordination

6. **LLM Validator** (`llm-validator:8006`)
   - LLM inference validation
   - Oracle decision making
   - Network coordination

7. **Liquidity Layer** (`liquidity-layer:8007`)
   - Cross-chain liquidity pools
   - Automated market making
   - Arbitrage execution

8. **API Gateway** (`api-gateway:8080`)
   - Unified API endpoint
   - Request routing
   - Load balancing

## Detailed Configuration

### Database Setup

```bash
# PostgreSQL is automatically started by docker-compose
# Access database:
docker exec -it membra-postgres psql -U membra_user -d membra_bridge
```

### IPFS Setup

```bash
# IPFS runs in Docker container
# Check IPFS status:
docker exec -it membra-ipfs ipfs id

# Add file to IPFS:
docker exec -it membra-ipfs ipfs add /path/to/file

# Pin file:
docker exec -it membra-ipfs ipfs pin add <cid>
```

### Solana Wallet Setup

```bash
# Create new wallet
solana-keygen new

# Get wallet address
solana address

# Airdrop SOL (devnet)
solana airdrop 2
```

## API Usage Examples

### File Tokenization

```bash
# Tokenize a directory
curl -X POST http://localhost:8080/api/tokenize \
  -H "Content-Type: application/json" \
  -d '{
    "path": "/app/data",
    "pattern": "*"
  }'
```

### Phone Wallet Registration

```bash
# Register phone number
curl -X POST http://localhost:8080/api/wallet/register \
  -H "Content-Type: application/json" \
  -d '{
    "phone_number": "+14155552671",
    "custom_premined": 1500
  }'
```

### SMS Mining

```bash
# Process SMS for rewards
curl -X POST http://localhost:8080/api/sms/process \
  -H "Content-Type: application/json" \
  -d '{
    "phone_number": "+14155552671",
    "sms_type": "sent",
    "content": "Hello from membra!",
    "sponsor_address": "0x1234567890"
  }'
```

### Oracle Prices

```bash
# Get oracle prices
curl http://localhost:8080/api/oracle/prices
```

### LLM Inference

```bash
# Submit LLM inference request
curl -X POST http://localhost:8080/api/llm/inference \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Analyze current market conditions",
    "model_id": "mock-gpt",
    "temperature": 0.7
  }'
```

### Liquidity Operations

```bash
# Get liquidity pools
curl http://localhost:8080/api/liquidity/pools

# Get arbitrage opportunities
curl http://localhost:8080/api/liquidity/arbitrage
```

## Monitoring and Maintenance

### Health Checks

```bash
# Check all services health
curl http://localhost:8080/health

# Check system status
curl http://localhost:8080/api/status
```

### Logs

```bash
# View all logs
docker-compose logs -f

# View specific service logs
docker-compose logs -f file-tokenizer
docker-compose logs -f oracle-system
```

### Backup and Restore

```bash
# Backup PostgreSQL
docker exec membra-postgres pg_dump -U membra_user membra_bridge > backup.sql

# Restore PostgreSQL
cat backup.sql | docker exec -i membra-postgres psql -U membra_user -d membra_bridge

# Backup IPFS data
docker cp membra-ipfs:/data/ipfs ./ipfs_backup
```

## Scaling and Production Deployment

### Horizontal Scaling

```bash
# Scale specific services
docker-compose up -d --scale file-tokenizer=3
docker-compose up -d --scale oracle-system=2
```

### Kubernetes Deployment

```bash
# Apply Kubernetes manifests
kubectl apply -f k8s/

# Check deployment
kubectl get pods -n membra-bridge
```

### Load Balancing

```bash
# Configure Nginx as load balancer
# See nginx.conf.example for configuration
```

## Security Considerations

### Environment Variables

- Never commit `.env` file to version control
- Use strong secrets in production
- Rotate keys regularly
- Use different keys for different environments

### Network Security

- Configure firewall rules
- Use VPN for private network access
- Enable HTTPS/TLS for all endpoints
- Implement rate limiting

### Wallet Security

- Never share private keys
- Use hardware wallets for large amounts
- Enable multi-signature for critical operations
- Regular security audits

## Troubleshooting

### Common Issues

**Services won't start**
```bash
# Check logs
docker-compose logs

# Restart services
docker-compose restart
```

**Database connection issues**
```bash
# Check PostgreSQL status
docker-compose ps postgres

# Restart PostgreSQL
docker-compose restart postgres
```

**IPFS connection issues**
```bash
# Check IPFS status
docker exec -it membra-ipfs ipfs id

# Restart IPFS
docker-compose restart ipfs
```

**Out of memory errors**
```bash
# Increase Docker memory limit
# In Docker Desktop settings
```

## Performance Optimization

### Database Optimization

```sql
-- Create indexes
CREATE INDEX idx_phone_wallets_phone ON phone_wallets(phone_number);
CREATE INDEX idx_transactions_timestamp ON transactions(timestamp);
```

### Caching Strategy

- Redis is configured for caching
- Adjust TTL values in `.env`
- Monitor cache hit rates

### Resource Allocation

```yaml
# In docker-compose.yml, adjust resource limits:
services:
  file-tokenizer:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 4G
```

## Updates and Maintenance

### Updating the System

```bash
# Pull latest changes
git pull origin main

# Rebuild images
docker-compose build

# Restart services
docker-compose up -d
```

### Regular Maintenance

```bash
# Clean up unused Docker resources
docker system prune -a

# Backup data
./backup.sh

# Update dependencies
pip install --upgrade -r requirements.txt
```

## Support and Community

- **Documentation**: https://docs.membra.network
- **GitHub Issues**: https://github.com/your-repo/membra-bridge-ecosystem/issues
- **Discord**: https://discord.gg/membra
- **Email**: support@membra.network

## License

MIT License - See LICENSE file for details