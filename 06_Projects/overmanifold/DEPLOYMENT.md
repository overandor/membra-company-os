# Overmanifold Protocol - Deployment Guide

## Overview

This guide covers deploying the Overmanifold Protocol to production environments using Docker, Kubernetes, and CI/CD pipelines.

## Prerequisites

- Docker 20.10+
- Docker Compose 2.0+
- Kubernetes 1.25+ (for K8s deployment)
- kubectl configured for your cluster
- Python 3.11+
- PostgreSQL 15+
- Redis 7+

## Quick Start (Local Development)

### 1. Clone and Setup

```bash
git clone https://github.com/overmanifold/protocol.git
cd protocol
cp .env.example .env
# Edit .env with your configuration
```

### 2. Start Services

```bash
docker-compose up -d
```

This starts:
- Overmanifold API (port 8000)
- PostgreSQL (port 5432)
- Redis (port 6379)
- Prometheus (port 9090)
- Grafana (port 3000)
- Redis Commander (port 8081)

### 3. Verify Deployment

```bash
# Health check
curl http://localhost:8000/health

# API documentation
curl http://localhost:8000/docs
```

## Production Deployment

### Docker Deployment

#### Build Image

```bash
docker build -t overmanifold/protocol:latest .
```

#### Run Container

```bash
docker run -d \
  --name overmanifold-api \
  -p 8000:8000 \
  --env-file .env \
  -v $(pwd)/logs:/var/log/overmanifold \
  overmanifold/protocol:latest
```

### Kubernetes Deployment

#### 1. Create Namespace

```bash
kubectl create namespace overmanifold
```

#### 2. Create Secrets

```bash
kubectl create secret generic overmanifold-secrets \
  --from-literal=db-password=your_password \
  --from-literal=secret-key=your_secret_key \
  -n overmanifold
```

#### 3. Deploy Services

```bash
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/secrets.yaml
kubectl apply -f k8s/postgres.yaml
kubectl apply -f k8s/redis.yaml
kubectl apply -f k8s/api.yaml
kubectl apply -f k8s/ingress.yaml
kubectl apply -f k8s/monitoring/
```

#### 4. Verify Deployment

```bash
kubectl get pods -n overmanifold
kubectl get services -n overmanifold
kubectl logs -f deployment/overmanifold-api -n overmanifold
```

### CI/CD Pipeline

The GitHub Actions workflow (`.github/workflows/ci.yml`) automatically:

1. **Security Scanning**: Trivy vulnerability scanner, Bandit security linter
2. **Code Quality**: Black formatter, Flake8 linter, mypy type checking
3. **Testing**: Unit and integration tests with coverage reporting
4. **Building**: Docker image build and push
5. **Deployment**: Automatic deployment to staging/production

#### Manual Trigger

```bash
gh workflow run ci.yml
```

## Configuration

### Environment Variables

Key environment variables (see `.env.example`):

- `ENVIRONMENT`: development, staging, production
- `DEBUG`: true/false
- `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`
- `REDIS_HOST`, `REDIS_PORT`, `REDIS_PASSWORD`
- `SECRET_KEY`: Generate with `python -c "import secrets; print(secrets.token_urlsafe(32))"`
- `JWT_ALGORITHM`, `JWT_EXPIRATION_HOURS`
- `API_HOST`, `API_PORT`, `API_WORKERS`

### Feature Flags

Enable/disable features via `FEATURE_FLAGS`:

```json
{
  "transaction_workers": true,
  "repo_tokenization": true,
  "browser_validators": true,
  "sms_transport": false,
  "phone_did": false
}
```

## Monitoring

### Prometheus Metrics

Access Prometheus at `http://your-server:9090`

Key metrics:
- `overmanifold_request_duration_seconds`
- `overmanifold_requests_total`
- `overmanifold_errors_total`
- `overmanifold_active_connections`

### Grafana Dashboards

Access Grafana at `http://your-server:3000` (default admin/admin)

Import dashboards from `monitoring/grafana/dashboards/`

### Health Checks

- `/health` - Basic health check
- `/health/ready` - Readiness probe
- `/health/live` - Liveness probe
- `/health/detailed` - Detailed component status

## Scaling

### Horizontal Pod Autoscaler

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: overmanifold-api-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: overmanifold-api
  minReplicas: 3
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
```

### Database Scaling

- Use managed PostgreSQL (RDS, Cloud SQL)
- Enable read replicas
- Configure connection pooling
- Regular vacuum and analyze

### Redis Scaling

- Use Redis Cluster for large datasets
- Enable persistence (AOF + RDB)
- Configure max memory policy
- Monitor memory usage

## Security

### Secrets Management

Never commit secrets to git. Use:

- Kubernetes Secrets
- AWS Secrets Manager / HashiCorp Vault
- Environment variables in production
- `.env` files (gitignored)

### Network Security

- Use TLS/SSL for all communications
- Configure network policies
- Enable firewall rules
- Use private networks for database connections

### API Security

- Enable rate limiting
- Use API keys or JWT authentication
- Validate all inputs
- Implement CORS properly
- Regular security audits

## Backup and Recovery

### Database Backups

```bash
# Backup
kubectl exec -it postgres-0 -n overmanifold -- pg_dump -U overmanifold overmanifold > backup.sql

# Restore
kubectl exec -i postgres-0 -n overmanifold -- psql -U overmanifold overmanifold < backup.sql
```

### Redis Backups

```bash
# Backup RDB file
kubectl cp redis-0:/data/dump.rdb ./redis-backup.rdb

# Restore
kubectl cp ./redis-backup.rdb redis-0:/data/dump.rdb
```

### Disaster Recovery

1. Restore from latest backup
2. Verify data integrity
3. Update DNS if needed
4. Monitor system health
5. Communicate with stakeholders

## Troubleshooting

### Common Issues

**API not responding**
```bash
kubectl logs -f deployment/overmanifold-api -n overmanifold
kubectl describe pod -l app=overmanifold-api -n overmanifold
```

**Database connection issues**
```bash
kubectl exec -it postgres-0 -n overmanifold -- psql -U overmanifold -d overmanifold
kubectl get services -n overmanifold
```

**High memory usage**
```bash
kubectl top pods -n overmanifold
kubectl exec -it overmanifold-api-xxx -n overmanifold -- python -m memory_profiler
```

### Logs

```bash
# Application logs
kubectl logs -f deployment/overmanifold-api -n overmanifold

# All logs
kubectl logs -l app=overmanifold -n overmanifold --all-containers=true

# Previous logs
kubectl logs --previous deployment/overmanifold-api -n overmanifold
```

## Performance Tuning

### Database Optimization

- Add appropriate indexes
- Optimize queries
- Configure work_mem and maintenance_work_mem
- Regular vacuum and analyze

### Application Optimization

- Enable caching (Redis)
- Use connection pooling
- Optimize Python code
- Profile and optimize hot paths

### Network Optimization

- Enable HTTP/2
- Use CDN for static assets
- Optimize TLS configuration
- Enable compression

## Maintenance

### Rolling Updates

```bash
kubectl set image deployment/overmanifold-api \
  overmanifold-api=overmanifold/protocol:v1.0.1 \
  -n overmanifold
```

### Database Migrations

```bash
# Run migrations
kubectl exec -it deployment/overmanifold-api -n overmanifold -- \
  python -m alembic upgrade head
```

### Certificate Renewal

- Monitor certificate expiration
- Automate renewal with Let's Encrypt
- Test renewal process

## Support

For issues and questions:
- GitHub Issues: https://github.com/overmanifold/protocol/issues
- Documentation: https://docs.overmanifold.io
- Email: support@overmanifold.io