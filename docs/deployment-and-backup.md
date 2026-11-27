# Deployment and Backup Guide

How the MVP is run, how its settings are changed, what must be done before it could ever face the internet, and how to
back up and restore the PostgreSQL database with `pg_dump` / `pg_restore`.

> **Scope.** Assignment A defers *production deployment* to a later project. What exists and has been tested is the
> **Docker Compose demo setup** (sections 1 and 2). Section 3 lists what has to change for a real server; those items
> are **not implemented and not tested**. Section 4 (backup and restore) works with the demo setup and was tested at the
> `pg_dump` / `pg_restore` level (see [How this was verified](#5-how-this-was-verified)).

## 1. What runs where

| Service | Image / command | Port | Data |
|---------|-----------------|------|------|
| `db` | `postgres:16-alpine` | `127.0.0.1:5432` on the host (not reachable from the network) | named volume `postgres_data` |
| `web` | built from the `Dockerfile` (`python:3.12-slim`), runs `python manage.py runserver 0.0.0.0:8000` | `8000` on all host interfaces | none; the code is bind-mounted from `./src` |

At every start the `web` container runs [`docker/entrypoint.sh`](../docker/entrypoint.sh): it waits for a healthy database,
applies migrations and, only if `SEED_DEMO_DATA=True`, loads the synthetic demo data. `runserver` is Django's development
server; it is fine for a demo and unsuitable for production (see section 3).

### Configuration (environment variables)

Settings come from environment variables, usually from a `.env` file next to `docker-compose.yml` (copy
[`.env.example`](../.env.example); `.env` is ignored by Git and never committed).

| Variable | Used by | Default | Meaning |
|----------|---------|---------|---------|
| `SECRET_KEY` | Django | `dev-insecure-placeholder-key` | signs sessions, CSRF tokens and password-reset links; **must be unique and secret** outside the demo |
| `DEBUG` | Django | `True` when unset; only the exact text `True` switches it on | detailed error pages; **must be `False` outside the demo** |
| `ALLOWED_HOSTS` | Django | `localhost,127.0.0.1` | comma-separated host names the site may be served under |
| `DB_NAME`, `DB_USER`, `DB_PASSWORD` | Django and the `db` container | `hunting_db`, `hunting_user`, `secret_password` | database credentials; the password is only applied when the volume is first created |
| `DB_HOST`, `DB_PORT` | Django | `db`, `5432` | Compose always overrides them for `web` |
| `WEB_PORT`, `DB_HOST_PORT` | Compose | `8000`, `5432` | host ports |
| `SEED_DEMO_DATA` | entrypoint | Compose: `True`; entrypoint alone: `False` | load synthetic demo data at start |
| `EMAIL_BACKEND`, `DEFAULT_FROM_EMAIL` | Django | console backend, `noreply@hunting-association-mvp.local` | the console backend only prints e-mails to the log |

Two things are **not** configurable through the environment today: the login rate limit (Django settings
`LOGIN_RATE_LIMIT_ATTEMPTS` = 5 and `LOGIN_RATE_LIMIT_TIMEOUT` = 300 seconds, defaults in `accounts/views.py`) and real
SMTP delivery (`EMAIL_HOST`, `EMAIL_PORT`, … are not read from the environment). Both need a small change in
`src/config/settings.py`.

## 2. Running the demo setup

```bash
cp .env.example .env            # Windows PowerShell: Copy-Item .env.example .env
docker compose up --build -d    # first start: pulls images, builds, migrates, loads demo data
docker compose ps               # db: healthy, web: running
docker compose logs -f web      # follow the application log (also shows e-mails)
```

| Task | Command |
|------|---------|
| Create an administrator | `docker compose exec web python manage.py createsuperuser` |
| Update to a new version | `git pull`, then `docker compose up --build -d` (migrations run automatically) |
| Stop, keep the data | `docker compose down` |
| Stop and **delete the database** | `docker compose down -v` |
| Run the test suite | `docker compose exec web python manage.py test` |
| Open a database shell | `docker compose exec db psql -U hunting_user -d hunting_db` |

Notes:

- With `SEED_DEMO_DATA=True` the seed commands run at **every** start and *update* the sample fee rule `2026-v1-sample`
  and the sample articles and representatives back to their seeded values. Do not leave it on if staff have edited those
  records; use `SEED_DEMO_DATA=False`.
- Changing `DB_PASSWORD` after the volume exists has no effect on the stored password; reset the volume or change the
  password inside PostgreSQL.

## 3. Before this could run on a real server (not implemented)

Use this as the starting list for the production project. `python manage.py check --deploy` run on the 2026-11-27 code
reports 6 warnings with the values from `.env.example` and still 4 after `DEBUG=False` and a long random `SECRET_KEY`
(HSTS, SSL redirect, secure session cookie, secure CSRF cookie), because the settings file has no switches for them yet.

| # | Item | What to do |
|---|------|-----------|
| 1 | Secrets | new random `SECRET_KEY` (`python -c "import secrets; print(secrets.token_urlsafe(50))"`), strong `DB_PASSWORD`, `.env` readable only by the deploying user |
| 2 | Debug off | `DEBUG=False`; set `ALLOWED_HOSTS` to the real host name |
| 3 | Application server | replace `runserver` by a WSGI server such as gunicorn (`config.wsgi:application`; gunicorn is not in `requirements.txt` yet) behind a reverse proxy |
| 4 | HTTPS | terminate TLS at the proxy; then add settings `SECURE_PROXY_SSL_HEADER`, `CSRF_TRUSTED_ORIGINS`, `SESSION_COOKIE_SECURE=True`, `CSRF_COOKIE_SECURE=True`, `SECURE_SSL_REDIRECT=True` and, after testing, `SECURE_HSTS_SECONDS` |
| 5 | Static files | with `DEBUG=False` the development server no longer serves static files (the Django admin needs them): set `STATIC_ROOT`, run `collectstatic`, serve the folder from the proxy |
| 6 | Compose file | remove the `./src:/app` bind mount and the `runserver` command, add `restart: unless-stopped`, publish no database port, run the container as a non-root user (`USER` in the `Dockerfile`) |
| 7 | Demo data off | `SEED_DEMO_DATA=False`; create real accounts only |
| 8 | Real e-mail | add SMTP settings (host, port, user, password from the environment) and set `EMAIL_BACKEND` to the SMTP backend |
| 9 | Login rate limit | the limit counts in Django's per-process memory cache keyed by client IP: behind a proxy every user then shares the proxy's IP, and several worker processes each count separately. Use a shared cache and take the client IP from the trusted proxy header |
| 10 | Django version | `requirements.txt` limits Django to `<5.2`, but 5.1 no longer receives security fixes. Move to the 5.2 LTS line (`Django>=5.2,<5.3`); the 54 tests pass on 5.2.19 (see [`owasp-checklist.md`](owasp-checklist.md), A03) |
| 11 | Logging | configure `LOGGING` to write to standard output and let Docker rotate it; the notification log line contains the recipient e-mail address (it only appears once INFO logging is configured), so review what is logged before real data is used |
| 12 | Backups | run section 4 on a schedule and test a restore regularly |
| 13 | Legal | final consent text, retention rules and a privacy notice are decisions of the association (see [`gdpr-checklist.md`](gdpr-checklist.md)) |

## 4. Backup and restore with `pg_dump` / `pg_restore`

### What to back up

| What | How | Note |
|------|-----|------|
| The PostgreSQL database (all members, quotes, payments, consents, content, accounts, sessions) | `pg_dump` in custom format (`-Fc`) | this is the only application data; there are no uploaded files in the MVP |
| `.env` (secrets) | copy separately to a safe place | never store it in Git or next to the database dump |
| The code | Git | nothing to back up on the server |

The custom format is compressed and lets `pg_restore` restore everything, or only selected tables.

**A backup contains personal data**, exactly like the live database. Store it outside the repository (the repository's
`.gitignore` excludes `backups/` and `*.dump`), restrict who can read it, encrypt it when it leaves the server, and delete
old copies according to the retention rule the association decides.

### Create a backup

The commands use the tools inside the `db` container, so the `pg_dump` version always matches the server. Create the
target folder once: `mkdir backups` (PowerShell: `New-Item -ItemType Directory -Force backups`).

```bash
# 1. dump inside the container (user and database name come from the container's own environment)
docker compose exec db sh -c 'pg_dump -U $POSTGRES_USER -d $POSTGRES_DB -Fc -f /tmp/backup.dump'
# 2. check that the archive can be read (prints the first lines of its table of contents)
docker compose exec db sh -c 'pg_restore -l /tmp/backup.dump | head -5'
# 3. copy it to the host, with the date in the name
docker compose cp db:/tmp/backup.dump ./backups/hunting_db_2026-11-27.dump
# 4. remove the temporary copy in the container
docker compose exec db rm /tmp/backup.dump
```

These lines work unchanged in PowerShell. Do **not** write `docker compose exec db pg_dump … > file.dump` in Windows
PowerShell 5.1: the `>` operator re-encodes the binary output as text and corrupts the dump. On Linux and macOS the
shortcut is safe (default user and database names shown; use your `.env` values if you changed them):

```bash
docker compose exec -T db pg_dump -U hunting_user -d hunting_db -Fc > backups/hunting_db_$(date +%F).dump
```

A healthy dump of the demo database is tens of kilobytes (about 75 KB in the test below); a file of a few bytes means the
command failed.

### Restore a backup

Stop the web container first so that nothing writes while the data is replaced.

```bash
docker compose cp ./backups/hunting_db_2026-11-27.dump db:/tmp/restore.dump
docker compose stop web
docker compose exec db sh -c 'pg_restore -U $POSTGRES_USER -d $POSTGRES_DB --clean --if-exists --no-owner /tmp/restore.dump'
docker compose exec db rm /tmp/restore.dump
docker compose start web
```

`--clean --if-exists` drops the existing tables and recreates them from the dump; `--no-owner` avoids ownership errors
when the database user differs. The entrypoint runs the migrations again when `web` starts, which does nothing if the
dump already contains them. Keep `SEED_DEMO_DATA=False` for a restored real database (section 2).

To restore into a completely **empty database** (for example after losing the volume), start only the database, then
`pg_restore` as above; if the database object itself is missing, first run
`docker compose exec db sh -c 'createdb -U $POSTGRES_USER $POSTGRES_DB'`.

### Prove that a backup works (do this regularly)

Restore into a scratch database and compare, without touching the live data:

```bash
docker compose cp ./backups/hunting_db_2026-11-27.dump db:/tmp/restore.dump
docker compose exec db sh -c 'createdb -U $POSTGRES_USER restore_test'
docker compose exec db sh -c 'pg_restore -U $POSTGRES_USER -d restore_test --no-owner --exit-on-error /tmp/restore.dump'
docker compose exec db psql -U hunting_user -d restore_test -c "SELECT count(*) FROM membership_memberprofile;"
docker compose exec db psql -U hunting_user -d hunting_db   -c "SELECT count(*) FROM membership_memberprofile;"
docker compose exec db sh -c 'dropdb -U $POSTGRES_USER restore_test'
docker compose exec db rm /tmp/restore.dump
```

The two counts must match (compare other tables, for example `accounts_user` and `membership_paymentrecord`, the same
way). After a real restore also open the site, sign in as a secretariat user and open the member directory.

### Schedule and retention (suggestion)

On a Linux server run the backup command daily from `cron` (use `docker compose exec -T …` there, because cron has no
terminal), for example at 02:30, and keep the last 7 daily and 4 weekly files. These numbers are a suggestion; the
association must decide the real retention. Remember that **deleted personal data survives in older backups**: when a
deletion request has been carried out, old backups must expire on schedule, and after a restore the deletion has to be
repeated.

### Troubleshooting

| Symptom | Cause and fix |
|---------|---------------|
| The restore hangs or stops with lock errors while dropping tables | `web` (or another client) still holds database connections: `docker compose stop web` and retry |
| Many `role "…" does not exist` or ownership errors | add `--no-owner` (already in the commands above) |
| `pg_restore: error: input file does not appear to be a valid archive` | the dump was created with a PowerShell `>` redirect, or is truncated; create it again with the method above |
| `password authentication failed` from the app after a restore | the database password in `.env` differs from the one stored in the volume; align them |

## 5. How this was verified

| Check | Result |
|-------|--------|
| `pg_dump -Fc` of a migrated and seeded application database on PostgreSQL 16.15 (2026-11-27, AI session, no Docker daemon) | dump created and readable by `pg_restore -l` |
| Delete payments and consents, `pg_restore --clean --if-exists --no-owner` into the same database | all rows back (2 users, 1 profile, 1 quote, 1 payment, 1 consent, 7 articles) |
| Restore into a scratch database with `--exit-on-error`, then drop it | succeeded, row counts equal |
| Drop the database, create it empty, restore | succeeded; `migrate --check` reports no pending migrations; sign-in, the back office and the eligibility API work |
| `docker compose` wrappers (`exec`, `cp`, `stop`, `start`) | **not run by the AI** (no Docker daemon in its sandbox); the team must rehearse sections 2 and 4 once on a clean machine and record the date here: ____ |
| `python manage.py check --deploy` | run, results quoted in section 3 |
