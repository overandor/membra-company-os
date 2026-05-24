#!/bin/bash
# Docker Compose validation script for Membra Money
# Run this locally after installing Docker Desktop / docker-compose.

set -e

echo "=== Docker Compose Validation ==="
echo ""

# Validate compose files
echo "[1/3] Validating docker-compose.yml..."
docker compose -f docker-compose.yml config > /dev/null
echo "      OK"

echo ""
echo "[2/3] Validating docker-compose.prod.yml..."
docker compose -f docker-compose.prod.yml config > /dev/null
echo "      OK"

# Optional: start services and health-check
echo ""
echo "[3/3] Starting services (dev mode)..."
docker compose up --build -d
echo "      Services started"

echo ""
echo "Waiting for API to be ready (15s)..."
sleep 15

echo ""
echo "Health check:"
if curl -sf http://localhost:8000/api/v1/health; then
    echo "      OK — API is healthy"
else
    echo "      WARNING — API not responding yet (may need more time)"
fi

echo ""
echo "To stop: docker compose down"
echo "=== Docker Validation Complete ==="
