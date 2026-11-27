# Demo Script and Defence Preparation (Student A: Membership module)

Preparation notes for the 5-minute demo video and for the individual defence of the membership module. Assignment A
describes the defence as 45 to 60 minutes: a **15-minute demo**, a **20-minute code walkthrough** of three areas chosen by
the examiners, a **15-minute small live change without AI**, and **questions on security, GDPR and design decisions**.
Understanding matters more than code volume, so every answer below should be re-told in your own words.

Contents: [1. Preparation](#1-preparation) · [2. The 5-minute demo](#2-the-5-minute-demo) ·
[3. Code walkthrough map](#3-code-walkthrough-map-20-minutes) · [4. Live change rehearsal](#4-live-change-without-ai-15-minutes) ·
[5. Questions and short answers](#5-questions-and-short-answers) · [6. Final checklist](#6-final-checklist)

## 1. Preparation

### Start from a clean state (about 5 minutes, do it the day before and again an hour before)

```bash
docker compose down -v
docker compose up --build -d
docker compose exec web python manage.py createsuperuser      # username: admin1
docker compose exec web python manage.py test                 # expect: Ran 54 tests ... OK
```

### Windows and data to prepare

| Item | Content |
|------|---------|
| Browser window A (normal) | signed out, at `http://localhost:8000/membership/calculator/` |
| Browser window B (private) | signed in as `admin1` later in the demo, at `http://localhost:8000/admin/` |
| Terminal | in the repository folder, Docker running, font large |
| Text file with the form values | username `member.demo`, e-mail `member.demo@example.test`, names `Mia` / `Demo`, password `Demo-Pass-2026!x`; Hunter, phone `+421900111222`, street `Lesna 1`, city `Nitra`, postal code `94901`, licence number `SK-DEMO-1`, licence until `2027-03-31`, insurance until `2026-12-31`, insurance add-on ticked, consent ticked |
| Open in tabs | `docs/api.md`, `docs/adr/0004-fee-versioning-and-frozen-quotes.md`, the repository on the files you will show |

Do not use real names, e-mail addresses or documents anywhere in the demo or the video.

### Fall-backs

| Problem | Plan B |
|---------|--------|
| Docker or the stack does not start | show the pre-recorded demo video, then walk through the code and the test run output from the day before |
| Port 8000 or 5432 busy | `WEB_PORT=8080` / `DB_HOST_PORT=5433` in `.env`, restart (README troubleshooting) |
| Typing mistakes in the form | keep the values in the text file and paste them |
| Time is running out | use the cut list at the end of section 2 |

## 2. The 5-minute demo

The same script serves the live demo and the video. Times are cumulative.

| Time | What you do (URL or command) | What you say |
|------|------------------------------|--------------|
| 0:00 | Slide or README: modules and the stack | "One Django project with PostgreSQL in Docker Compose. I own accounts, membership and the shared notification interface; Student B owns the public site. All data is synthetic and all fees are sample values." |
| 0:30 | `/membership/calculator/`: pick Hunter, tick insurance and reduced rate, calculate | "The fee comes from database rules, not from code: base 60, insurance +25, reduced −15, total 70 EUR, labelled sample." |
| 1:00 | `/accounts/register/`, register `member.demo`; then `/membership/apply/`, paste the values, tick consent, submit | "Registration always creates a member. The application stores the profile, an explicit versioned consent and a frozen fee quote." |
| 1:45 | On *My membership*: point at status Applicant, quote #1 (85.00 EUR, tariff `2026-v1-sample`), consent version | "The quote is a copy of the amounts with the tariff version. The member number appears only after approval." |
| 2:00 | Window B: `/admin/membership/feerule/`, change the hunter fee 60 → 65, save; back in window A press *Update Application / Generate New Quote* and submit | "I changed the rule. The old quote is untouched; the new quote uses 65. That is the frozen-quote acceptance criterion." |
| 2:40 | Window B: `/membership/backoffice/` → *Manage* `member.demo`: status *Active*, valid `2026-01-01` to `2026-12-31`, save. Record a payment: status Paid, the amount is pre-filled from the latest quote (90.00 EUR), reference `REF-1` | "Secretariat approves and sets validity. The system issues the member number and writes the status history with my name. Payments are recorded manually with an audit trail; there is no payment gateway." |
| 3:30 | *View Digital Card*, then back to the directory and *Export Filtered CSV* | "The card shows only four fields. The CSV contains exactly what the filter shows." |
| 4:00 | Window A (signed in as the member): `/membership/api/eligibility/?user=member.demo&date=2026-06-15`, then `date=2027-02-01`. Terminal: `docker compose exec web python manage.py send_renewal_reminders --days 60 --date 2026-12-01 --dry-run` | "This is the contract for Student B: active, licenceValid, insuranceValid, validUntil for a date. After the membership ends, `active` and `insuranceValid` are false. The reminder job runs as a command; the dry run shows who would be reminded." |
| 4:30 | Window A, same member: `/membership/backoffice/` shows 403; *Download my data (JSON)*; terminal: `docker compose exec web python manage.py test` (show the last lines) | "Members cannot open staff pages, the check is on the server. Members can export their own data. 54 automated tests pass." |
| 5:00 | stop | |

**Cut list if you run over:** drop the fee-rule change (2:00) first, then the reminder command, then the CSV.
**Add if you have time:** the 403 on another member's card (`/membership/cards/<id>/`).

## 3. Code walkthrough map (20 minutes)

The examiners choose three areas. Be able to open the file, say what each function does, name the test that proves it, and
say one limitation. All paths are under `src/`.

| Area | Where to look | Be ready to explain | Tests and documents |
|------|---------------|---------------------|---------------------|
| **Fee rules and frozen quotes** | `membership/models.py` (`FeeRule`, `FeeQuote`), `membership/services.py` (`get_active_fee_rule`, `calculate_fee_breakdown`, `create_frozen_fee_quote`), `membership/views.py` (`apply_membership`) | the calculation (`max(0, base + insurance − discount)`); that the quote **copies** amounts, version and label instead of pointing at the rule; `PROTECT` on `fee_rule`; why the application, consent and quote are saved in one `transaction.atomic()` block. Limitation: a rule edited in place keeps its version code, so the copy in the quote is what preserves history | `test_changing_fee_rule_does_not_overwrite_existing_frozen_quotes`, `test_calculate_fee_breakdown_with_addons_and_discounts`; ADR 0004 and 0006 |
| **Authentication and permissions** | `accounts/models.py` (roles, `can_manage_members`), `accounts/permissions.py` (`role_required`, `RoleRequiredMixin`), `accounts/views.py` (`login_view` and the rate limit, `register_view`), `accounts/forms.py`, `config/settings.py` (middleware, password validators) | anonymous users are redirected (302), wrong role gets 403; superuser and admin pass every check; registration cannot set a role; the rate-limit key is a hash of client IP and identifier, 5 failures per 300 s, then HTTP 429; the object-level check in `member_card_view`. Limitation: the counter is in process memory | `RoleAndPermissionTests`, `test_login_rate_limiting_blocks_brute_force`, `test_member_cannot_access_another_members_card_but_secretariat_can`; ADR 0002 and 0005; OWASP checklist |
| **Personal data handling** | `membership/models.py` (`ConsentRecord`), `membership/services.py` (`DEFAULT_CONSENT_TEXT`, `DEFAULT_CONSENT_VERSION`, `DELETION_REQUEST_PROCEDURE_TEXT`), `membership/views.py` (`export_my_data`), `membership/forms.py` | what is stored and why (minimisation); how consent is versioned and keeps the exact text; what the export contains; why deletion is a manual procedure and why deleting a user in the admin cascades to payments. No compliance claim: the wording is placeholder | `test_export_my_data_returns_gdpr_json_bundle`, `test_member_profile_default_lifecycle_and_versioned_consent`; GDPR checklist; `membership-model.md` |
| **Eligibility logic and the contract with B** | `membership/services.py` (`check_eligibility`, `_resolve_member_profile`), `membership/views.py` (`eligibility_api_view`), `docs/contracts.md` | `active` needs status *Active*, a `valid_until` and the date inside the validity window; licence and insurance are checked independently with `>= date`; unknown identifiers give four "false/null" values with status 200; who may query whom (401/403); the same function is used in-process and over HTTP. Contract changes need both students and the supervisor | `EligibilityContractTests` (3 tests); ADR 0007; `docs/api.md` |
| **Lifecycle, payments and back office** | `membership/services.py` (`transition_member_status`, `generate_member_number`), `membership/views.py` (`backoffice_member_list`, `backoffice_member_detail`, `backoffice_update_payment_status`, `backoffice_quick_add_member`, `backoffice_export_csv`) | status change plus history in one transaction; member number `HA-<year>-<id>`; the `action` field that selects the status or payment form; manual payment statuses and who recorded them; search, filters and pagination (10 per page); CSV of the filtered list. Limitation: a payment status change overwrites the previous value | `SecretariatBackOfficeTests` (5), `MembershipLifecycleAndCardTests` (3) |
| **Notification stub and renewal reminders** | `common/notifications.py` (`send`, `render_notification`), `membership/management/commands/send_renewal_reminders.py` | the shared `send(channel, recipient, template, context)` interface that B also uses; the reminder window (`--days`, `--date`, `--dry-run`); console e-mail backend. Limitation: no memory of reminders already sent | `NotificationStubAndRenewalCommandTests` (2); ADR 0007 |
| **Reproducible setup** | `Dockerfile`, `docker-compose.yml`, `docker/entrypoint.sh`, `.env.example`, `config/settings.py` | what happens at container start (wait for DB, migrate, optional seed); why secrets come from the environment; what is dev-only (runserver, `DEBUG`) | `MigrationDriftTests`; README; deployment guide |

## 4. Live change without AI (15 minutes)

Typical tasks are small: change behaviour in one or two places, keep the tests green, and explain what you did. Practise
with a timer and without AI. Useful commands:

```bash
docker compose exec web python manage.py test                                   # all tests
docker compose exec web python manage.py test membership.tests.SecretariatBackOfficeTests   # one class
git diff                                                                        # review before committing
```

The six exercises below were tried on 2026-11-27 and behave as described.

| # | Change | Where | What happens and what to do |
|---|--------|-------|-----------------------------|
| 1 | Make the CSV export safe for spreadsheets: prefix text that starts with `=`, `+`, `-` or `@` with `'` | `backoffice_export_csv` in `membership/views.py` (add a small helper and use it for the name columns) | existing tests stay green; add an assertion to `test_secretariat_can_export_filtered_csv` that a name such as `=1+1` is exported as `'=1+1`. This is open item A05 in the OWASP checklist |
| 2 | Add a payment status *Refunded* | `PaymentRecord.Status` in `membership/models.py` | `MigrationDriftTests` **fails** because the choices changed; run `python manage.py makemigrations membership`, commit the new migration, tests pass. Shows why the drift test exists |
| 3 | Allow logout only with POST | `logout_view` in `accounts/views.py`: `@require_http_methods(["POST"])` | all tests pass because the app already logs out with POST forms; open item A01 in the OWASP checklist |
| 4 | Show 20 members per page in the back office | `Paginator(queryset, 10)` in `backoffice_member_list` | `test_backoffice_member_list_search_filter_and_pagination` **fails** (expects 10 per page and 2 pages); update the expected numbers in the test and explain why |
| 5 | Lock the login after 3 failures instead of 5 | the default in `login_view` (`getattr(settings, "LOGIN_RATE_LIMIT_ATTEMPTS", 5)`) or a setting in `config/settings.py` | the existing test uses `override_settings` with 3 attempts, so it stays green; say what you would add to prove the new default |
| 6 | Require passwords of at least 10 characters | `AUTH_PASSWORD_VALIDATORS` in `config/settings.py`: `'OPTIONS': {'min_length': 10}` on `MinimumLengthValidator` | all 31 tests of `accounts` and `membership` pass (the test passwords are longer); add a test that a 9-character password is rejected on registration |

Rules of thumb: read the failing test first, change as little as possible, run the tests, write a commit message that says
**why**, and be ready to explain every line you typed.

## 5. Questions and short answers

Re-tell these in your own words and know where the code or the document is.

### Security

| Question | Short answer |
|----------|--------------|
| How are passwords stored? | Django's PBKDF2-SHA256 hasher, salted, 870,000 iterations. I wrote no cryptography myself. |
| How do you stop password guessing? | Failed logins are counted per client address and sign-in name; after 5 failures in 300 seconds the next attempt gets HTTP 429. The counter is in process memory, so production would need a shared cache. |
| How is access controlled? | On the server, in every protected view: `login_required` for member pages, `role_required` for the back office, plus an ownership check for cards. Anonymous users are redirected to sign-in, wrong roles get 403. |
| Why 302 for anonymous but 403 for a member? | Not signed in: you can fix it by signing in. Signed in with the wrong role: signing in again will not help, so the answer is "forbidden". |
| CSRF, XSS, SQL injection? | CSRF middleware and a token in every form; templates escape output and never use `\|safe`; all queries go through the ORM. |
| What is still weak? | See the OWASP checklist: Django 5.1 is out of support and needs the move to 5.2 LTS, the CSV export does not neutralise formulas, logout works with GET, no MFA (deferred), no HTTPS in the demo setup, security events are not logged. |

### GDPR

| Question | Short answer |
|----------|--------------|
| What personal data do you keep and why? | Account (name, e-mail), profile (phone, address, licence and insurance dates) and payments; only what the application, card and eligibility check need. The inventory is in the GDPR checklist. |
| How is consent handled? | A mandatory checkbox; the record stores purpose, version, the exact text and the time. The wording is a placeholder, and the lawful basis is for the association and a lawyer to decide. I make no compliance claim. |
| How does a member see or export their data? | *My membership* shows it and *Download my data (JSON)* exports account, profile, quotes, consents, history and payments. |
| How is deletion handled? | By hand, following the printed procedure: check retention duties, then anonymise the account and profile; deleting a user in the admin would also delete payments. Data stays in old backups until they expire. |
| Is any real data used? | No. All data is synthetic, in the demo, the tests and the AI prompts. |

### Design decisions

| Question | Short answer |
|----------|--------------|
| Why a custom `User` model? | Roles and a unique e-mail are needed from the first migration, and B must not create a competing user model (ADR 0002). |
| Why do quotes copy the amounts? | The acceptance criterion says changing a rule must not rewrite old quotes; a copy with the tariff version guarantees that, and `PROTECT` keeps referenced rules from being deleted. |
| Why a `services.py` layer? | The same logic is used by views, the JSON API, the management command, B's in-process calls and the tests, so it exists once. |
| Why does an unknown member get `200` with all false? | Answering 404 would reveal which identifiers exist; the contract with B stays simple (ADR 0007). |
| Why the Django admin and a separate back office? | The back office has the secretariat workflows with role checks; the admin is for maintenance such as fee rules. |
| Why manual payments? | Assignment A defers payment gateways and reconciliation; manual status records with the acting user are the MVP. |
| What would you do with 50 more hours? | The open actions in the OWASP checklist: Django 5.2, production settings and HTTPS, security logging, e-mail verification, a complete payment history, retention and erasure support. |

## 6. Final checklist

**Before the defence**

- [ ] Clean clone, `docker compose up --build` works in under 15 minutes; tests show 54 OK
- [ ] Demo accounts and tabs ready (section 1); the video of the 5-minute demo exists
- [ ] Handover set is complete: README, `docs/api.md`, `docs/test-report.md`, `docs/manual-test-checklist.md`, `docs/user-guide.md`, `docs/deployment-and-backup.md`, `docs/owasp-checklist.md`, `docs/gdpr-checklist.md`, `docs/ai-log.md`, ADRs, `THIRD_PARTY_LICENSES.md`
- [ ] I have walked through the manual checklist at least once and written the date in its sign-off block
- [ ] I have rehearsed the backup and restore commands once on my machine

**Numbers to know without looking**

54 automated tests (32 in Student A's scope) · 94 % coverage · 12 endpoints · statuses applicant / active / expired /
suspended · payment statuses pending / paid / overdue / cancelled · sample fees 60 / 35 / +25 / −15 EUR · member number
`HA-<year>-<id>` · login limit 5 failures per 300 s · 10 members per page.

**During the live change**

- [ ] No AI, no copying from the documents; reading the code and the tests is allowed
- [ ] Run the tests before and after; explain every line; commit message says why
