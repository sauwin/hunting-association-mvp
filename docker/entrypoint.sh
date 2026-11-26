#!/bin/sh
# Entrypoint of the `web` container.
#
# Why this exists: a fresh `docker compose up` must give a working application
# without manual steps (Assignment A, section 5: README setup reproducible in
# under 15 minutes). docker-compose.yml already waits until PostgreSQL passes
# its healthcheck, so this script only has to
#   1. apply database migrations, and
#   2. optionally load the synthetic demo data (all seed commands are idempotent).
# Afterwards it hands over to the container command (runserver, tests, shell...).
set -eu

echo "[entrypoint] Applying database migrations..."
python manage.py migrate --noinput

# Opt-in by design: outside the local demo setup (e.g. a real deployment) demo
# data must never be loaded by accident. docker-compose.yml turns it on for the
# demo; here, an unset variable means "do not seed".
if [ "${SEED_DEMO_DATA:-False}" = "True" ]; then
    echo "[entrypoint] Loading synthetic demo data (idempotent)..."
    python manage.py seed_membership_demo
    python manage.py seed_articles
    python manage.py seed_representatives
else
    echo "[entrypoint] SEED_DEMO_DATA is not 'True' - skipping demo data."
fi

exec "$@"
