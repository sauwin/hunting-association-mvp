# Hunting Association Portal (MVP)

Membership management and member portal plus a public website for a hunting
association. Built with Python / Django, PostgreSQL and Docker Compose.
**All data in this repository is synthetic** and all fee amounts are
sample/placeholder values until the association approves them.

| Module (`src/…`) | Responsibility | Owner |
|------------------|----------------|-------|
| `accounts/`      | Custom `User`, roles (member, secretariat, editor, admin), login, password reset, server-side permissions | Student A |
| `membership/`    | Applications, fee rules and frozen quotes, consents, lifecycle, member card, payments, secretariat back office, eligibility API | Student A |
| `common/`        | Shared notification interface (`send(channel, recipient, template, context)`) | Student A |
| `public_site/`   | Public pages, news/articles, regional representatives, volunteer and membership enquiries | Student B |

## Quick start

**Prerequisites:** Git and Docker with Compose **v2.24 or newer**
(`docker compose version`). Ports `8000` (web) and `5432` (PostgreSQL) must be
free on your machine, or change them as described in
[Troubleshooting](#troubleshooting).

```bash
git clone <repository-url> hunting-association-mvp
cd hunting-association-mvp
cp .env.example .env        # Windows PowerShell: Copy-Item .env.example .env
docker compose up --build
```

The `.env` step is optional (sensible defaults are built in), but recommended
because it is the one place to change ports and settings. The first start takes
a few minutes, mostly for pulling images and building the web image.

On the first start the `web` container automatically
(see [`docker/entrypoint.sh`](docker/entrypoint.sh)):

1. waits until PostgreSQL is healthy (Compose healthcheck),
2. applies all database migrations,
3. loads the synthetic demo data (safe to repeat, nothing is duplicated),
4. starts the development server.

When the log shows `Starting development server at http://0.0.0.0:8000/`,
open <http://localhost:8000/>.

### What is loaded as demo data

- one sample fee rule (`2026-v1-sample`, marked *SAMPLE / PLACEHOLDER*),
- 3 article categories, 6 published articles and 1 draft article (Slovak sample content),
- 5 sample regional representatives and 2 sample volunteer enquiries.

There are no user accounts yet. Create an administrator (this account may use
the secretariat back office, because superusers pass every role check):

```bash
docker compose exec web python manage.py createsuperuser
```

Sign in at <http://localhost:8000/accounts/login/> with the e-mail address or
the username you chose.

### Useful addresses

| URL | What it is | Who may open it |
|-----|------------|-----------------|
| `/` | Public home page, news at `/news/`, contacts at `/representatives/` | everyone |
| `/accounts/register/`, `/accounts/login/` | Account registration and sign-in | everyone |
| `/membership/calculator/` | Indicative fee calculator (sample amounts) | everyone |
| `/membership/apply/` | Membership application with consent and frozen fee quote | signed-in users |
| `/membership/my-application/`, `/membership/my-card/`, `/membership/export-data/` | Own status, digital card, JSON export of own data | the member |
| `/membership/backoffice/` | Searchable member list, approvals, manual payments, CSV export | secretariat, admin |
| `/membership/api/eligibility/` | Eligibility JSON API for the public site | signed-in users (see `docs/contracts.md`) |
| `/admin/` | Django admin (content and data maintenance) | staff users |

## Everyday commands

Run these from the repository root while the stack is up (`docker compose up`).

```bash
# Run the whole automated test suite (uses a separate throw-away test database)
docker compose exec web python manage.py test

# Run only one app
docker compose exec web python manage.py test membership

# Renewal reminders: preview, then send through the console e-mail backend
docker compose exec web python manage.py send_renewal_reminders --days 60 --dry-run
docker compose exec web python manage.py send_renewal_reminders --days 60

# Django shell / new migrations after changing a model
docker compose exec web python manage.py shell
docker compose exec web python manage.py makemigrations

# Stop (data is kept) / stop and DELETE the database volume for a clean start
docker compose down
docker compose down -v
```

E-mails are never sent: the default `console` backend prints them to the
container log (`docker compose logs -f web`).

### Test from a completely clean state

This is what a reviewer should run to confirm the setup is reproducible:

```bash
docker compose down -v
docker compose up --build -d
docker compose exec web python manage.py test
```

## Troubleshooting

| Symptom | Cause and fix |
|---------|---------------|
| `port is already allocated` / `address already in use` | Another program uses 8000 or 5432. Set `WEB_PORT` and/or `DB_HOST_PORT` in `.env` (for example `WEB_PORT=8080`) and run `docker compose up` again. |
| `password authentication failed for user …` after editing `DB_PASSWORD` | PostgreSQL stores the password in its volume when it is first created. Run `docker compose down -v` (this deletes the demo database) and start again. |
| `exec /usr/local/bin/entrypoint.sh: no such file or directory` | The image was built from an older version of the repository. Rebuild it: `docker compose build --no-cache` (the Dockerfile normalises Windows line endings and sets the executable bit). |
| `TemplateDoesNotExist` right after adding a new `templates/` folder | The development server only discovers new template directories on start: `docker compose restart web`. |
| Compose reports an error about the `env_file` block | Compose is older than v2.24 and does not know `required: false`. Update Docker, or create `.env` and replace the block in `docker-compose.yml` with `- .env`. |
| You want the demo data gone | Set `SEED_DEMO_DATA=False` in `.env` and run `docker compose down -v && docker compose up`. |

## Documentation

| Document | Content |
|----------|---------|
| [`docs/contracts.md`](docs/contracts.md) | Contracts between the membership module and the public site (eligibility, notifications, registration link) |
| [`docs/api.md`](docs/api.md) | API reference: endpoints, query parameters, status codes (`200`, `400`, `401`, `403`, `404`) and sample JSON/HTML flows, including `/membership/api/eligibility/` |
| [`docs/test-report.md`](docs/test-report.md) | Automated test results (54 tests, coverage) and traceability to the acceptance criteria |
| [`docs/manual-test-checklist.md`](docs/manual-test-checklist.md) | Step-by-step manual checks: registration, application, quotes, card, GDPR export, back office, payments, CSV, eligibility, reminders |
| [`THIRD_PARTY_LICENSES.md`](THIRD_PARTY_LICENSES.md) | Third-party libraries, front-end resources and container images with their licences |
| [`docs/user-guide.md`](docs/user-guide.md) | Short user guide: members (register, apply, card, data export) and secretariat/admin staff (approvals, payments, CSV, fee rules, reminders) |
| [`docs/deployment-and-backup.md`](docs/deployment-and-backup.md) | Running the stack, environment variables, production hardening list, PostgreSQL backup and restore with `pg_dump` / `pg_restore` |
| [`docs/owasp-checklist.md`](docs/owasp-checklist.md) | OWASP Top 10:2025 review of the MVP with status, evidence and open actions |
| [`docs/gdpr-checklist.md`](docs/gdpr-checklist.md) | GDPR checklist: personal-data inventory, consent, data subject rights, manual deletion procedure, open decisions (not legal advice) |
| [`docs/demo-and-defence.md`](docs/demo-and-defence.md) | 5-minute demo script, code walkthrough map, live-change rehearsal and defence checklist |
| [`docs/membership-model.md`](docs/membership-model.md) | Membership data model and privacy notes |
| [`docs/content-model.md`](docs/content-model.md) | Public-site content model |
| [`docs/wireframes.md`](docs/wireframes.md) | Public-site user flow and wireframes |
| [`docs/adr/`](docs/adr/) | Architecture decision records |
| [`docs/ai-log.md`](docs/ai-log.md) | Log of AI-assisted work sessions |

## Security notes for developers

- Secrets live only in environment variables / `.env` (ignored by Git); `.env.example` contains placeholders only.
- Never put real personal data into the repository, prompts or screenshots - use the synthetic demo data.
- `DEBUG=True` and the placeholder `SECRET_KEY` are for local development only.
