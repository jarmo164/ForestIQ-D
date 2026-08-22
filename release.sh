#!/usr/bin/env sh
set -eu

if [ ! -f .env ]; then
  echo "Create .env from .env.example before releasing." >&2
  exit 1
fi

# Build the Django/PostgreSQL services and start the durable Django Q worker.
docker compose -f docker-compose-full-stack.yml build api worker
docker compose -f docker-compose-full-stack.yml up -d db api worker

echo "ForestIQ API and Django Q worker have been started. Verify /api/services/status and worker logs before deploying the UI."
