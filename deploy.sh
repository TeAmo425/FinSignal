#!/bin/bash
set -e

echo "=== FinAgent Deploy ==="

# Check .env exists
if [ ! -f ".env" ]; then
  echo "ERROR: .env not found. Create it with REDIS_PASSWORD=<your-password>"
  exit 1
fi

if [ ! -f "backend/.env" ]; then
  echo "ERROR: backend/.env not found."
  exit 1
fi

# Create uploads directory if missing
mkdir -p backend/uploads

# Stop old containers (if any)
docker compose down 2>/dev/null || true

# Build and start
docker compose up -d --build

echo ""
echo "=== Deploy complete ==="
echo "Site: http://$(curl -s ifconfig.me 2>/dev/null || echo '<server-ip>')"
docker compose ps
