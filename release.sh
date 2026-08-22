#!/usr/bin/env sh
set -eu

if [ ! -f .env ]; then
  echo "Create .env from .env.example before releasing." >&2
  exit 1
fi

# Build the Django/PostgreSQL service and apply database migrations via Compose.
docker compose -f docker-compose-full-stack.yml build api
docker compose -f docker-compose-full-stack.yml up -d db api

echo "ForestIQ Django API has been built and started. Verify /api/services/status before deploying the UI."
