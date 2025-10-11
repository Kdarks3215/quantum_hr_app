#!/bin/sh
set -e

if [ -n "$DATABASE_URL" ]; then
  alembic upgrade head
else
  echo "DATABASE_URL not set; skipping alembic migrations."
fi

if [ "${SEED_DEFAULT_DATA:-false}" = "true" ]; then
  python -c "from app import create_app, db; from app.seed import seed_defaults; app = create_app({'SEED_DEFAULT_DATA': False});\nwith app.app_context():\n    seed_defaults()"
fi

exec "$@"

