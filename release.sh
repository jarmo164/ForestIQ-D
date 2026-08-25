#!/usr/bin/env sh
set -eu

if [ ! -f .env ]; then
  echo "Create .env from .env.example before releasing." >&2
  exit 1
fi

# Build the Django/PostGIS services and start Redis, the Celery worker and Beat.
docker compose -f docker-compose-full-stack.yml build api worker beat ui
docker compose -f docker-compose-full-stack.yml up -d db redis api worker beat ui

echo "ForestIQ API, PostGIS, Redis, Celery worker, Beat and UI have been started. Verify /api/services/status and worker logs."
