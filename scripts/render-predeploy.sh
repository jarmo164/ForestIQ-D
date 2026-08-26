#!/usr/bin/env sh
set -eu

# Render Postgres supports PostGIS, but the extension must be enabled per
# database before GeoDjango migrations create geometry columns.
python manage.py shell -c "from django.db import connection; connection.cursor().execute('CREATE EXTENSION IF NOT EXISTS postgis')"
python manage.py migrate --noinput
