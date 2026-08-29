#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENV_FILE="${ROOT_DIR}/.env"
ENV_EXAMPLE="${ROOT_DIR}/.env.example"

echo "============================================"
echo "CommercePulse Development Environment Setup"
echo "============================================"
echo ""

if [ ! -f "${ENV_FILE}" ]; then
    echo "[1/4] Creating .env from .env.example..."
    cp "${ENV_EXAMPLE}" "${ENV_FILE}"
    echo "  Created: ${ENV_FILE}"
    echo "  IMPORTANT: Edit .env and set real values before starting services!"
    echo ""
else
    echo "[1/4] .env already exists, skipping copy."
    echo ""
fi

echo "[2/4] Creating Docker volumes..."

VOLUMES=(
    "commercepulse_postgres_data"
    "commercepulse_redis_data"
    "commercepulse_backend_venv"
    "commercepulse_nginx_certs"
    "commercepulse_nginx_cache"
    "commercepulse_nginx_logs"
)

for VOLUME in "${VOLUMES[@]}"; do
    if docker volume inspect "${VOLUME}" > /dev/null 2>&1; then
        echo "  Volume exists: ${VOLUME}"
    else
        docker volume create "${VOLUME}" > /dev/null
        echo "  Created volume: ${VOLUME}"
    fi
done
echo ""

echo "[3/4] Verifying Docker and Docker Compose..."

if ! command -v docker &> /dev/null; then
    echo "  ERROR: Docker is not installed. Please install Docker first."
    exit 1
fi
echo "  Docker: $(docker --version)"

if docker compose version &> /dev/null; then
    echo "  Docker Compose: $(docker compose version)"
elif command -v docker-compose &> /dev/null; then
    echo "  Docker Compose (legacy): $(docker-compose --version)"
else
    echo "  WARNING: Docker Compose not found. Install Docker Compose plugin."
fi
echo ""

echo "[4/4] Setup complete!"
echo ""
echo "============================================"
echo "Next Steps:"
echo "============================================"
echo ""
echo "1. Edit the .env file with your configuration:"
echo "     nano ${ENV_FILE}"
echo ""
echo "2. Start development services:"
echo "     cd ${ROOT_DIR}"
echo "     docker compose up --build"
echo ""
echo "3. Or start specific services only:"
echo "     docker compose up postgres redis"
echo "     docker compose up backend worker"
echo "     docker compose up frontend"
echo ""
echo "4. Include nginx in production mode:"
echo "     docker compose --profile production up --build"
echo ""
echo "5. Run tests:"
echo "     ${ROOT_DIR}/scripts/run-tests.sh"
echo ""
echo "6. View service URLs:"
echo "     Frontend:  http://localhost:3000"
echo "     Backend:   http://localhost:8000/api/v1"
echo "     API Docs:  http://localhost:8000/docs"
echo "     Postgres:  localhost:${POSTGRES_PORT:-5432}"
echo "     Redis:     localhost:${REDIS_PORT:-6379}"
echo "     Nginx:     http://localhost (prod profile)"
echo ""
echo "============================================"
