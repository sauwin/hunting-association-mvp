# OWASP Top 10 Checklist (Membership module and shared platform)

Review of the Hunting Association MVP against the **OWASP Top 10:2025** categories, written for the Assignment A handover.
It states what the code does today, where the evidence is, and what is still open. It is a developer self-review of an
MVP, **not** a penetration test and not a production security sign-off (both are outside the MVP scope).

- **Reviewed:** 2026-11-27, repository state after issue #34. Scope: `accounts`, `membership`, `common`, and the shared
  settings and Docker files. Student B's `public_site` is covered where it shares the platform (forms, headers, data).
- **Status words:** **Done** = implemented and evidenced; **Partial** = implemented for the MVP with a known gap;
  **Open** = not implemented yet; **N/A** = does not apply to the MVP.
- **Evidence:** code location, automated test, or a check run during this review. The checks were run with the Django test
  client on the real code (CSRF, headers, output encoding, redirects, role escalation, CSV), with `pip-audit` on the
  resolved dependencies, and with `python manage.py check --deploy`. Everything is reproducible with the commands in
  [section 4](#4-how-to-reproduce-the-checks).

## 1. Summary

| ID | Category (2025) | Status | One-line result |
|----|-----------------|--------|-----------------|
| A01 | Broken Access Control | **Done** | server-side role and object checks everywhere; one low-risk item (logout via GET) |
| A02 | Security Misconfiguration | **Partial** | safe headers and secrets handling, but dev defaults (`DEBUG`, `SECRET_KEY`) and no HTTPS/cookie switches yet |
| A03 | Software Supply Chain Failures | **Open** | Django 5.1.15 is out of support and `pip-audit` reports 8 advisories; fix tested (Django 5.2 LTS) but not applied |
| A04 | Cryptographic Failures | **Partial** | strong password hashing; no TLS or encryption at rest in the demo setup |
| A05 | Injection | **Partial** | ORM and auto-escaping everywhere; CSV export does not neutralise spreadsheet formulas |
| A06 | Insecure Design | **Partial** | frozen quotes, consent versions, data minimisation by design; no e-mail verification, no registration throttling |
| A07 | Authentication Failures | **Partial** | hashing, validators, rate-limited login; no MFA (deferred) and in-memory rate-limit counter |
| A08 | Software or Data Integrity Failures | **Partial** | migrations checked by a test; CDN script without integrity check, admins can edit audit rows |
| A09 | Security Logging & Alerting Failures | **Open** | business audit trail exists; security events are not logged or alerted |
| A10 | Mishandling of Exceptional Conditions | **Partial** | validation and JSON errors handled, transactions used; default error pages, no central handling |

The assignment's minimum security baseline is covered as follows:

| Baseline item (Assignment A, rules for both students) | Status | Where |
|-------------------------------------------------------|--------|-------|
| Framework password hashing | Done | Django PBKDF2-SHA256, 870,000 iterations (A04) |
| CSRF protection | Done | `CsrfViewMiddleware`, token in every form (A01) |
| Input validation | Done | Django forms and model fields (A05) |
| Rate-limited login | Done | `accounts/views.py`, 5 failures per 300 s (A07) |
| Server-side role checks for every protected action | Done | `accounts/permissions.py` and view decorators (A01) |
| Private storage for member photos/documents | N/A | the MVP has no uploads at all |
| OWASP Top 10 checklist | Done | this file |

## 2. Category by category

### A01 Broken Access Control: Done

| Control | Evidence | Status |
|---------|----------|--------|
| Every protected view enforces a role or login on the server: `login_required` for member pages, `role_required(SECRETARIAT, ADMIN)` for the five back-office views; anonymous users are redirected to sign-in, wrong roles get 403 | `membership/views.py`, `accounts/permissions.py`; tests `RoleAndPermissionTests`, `test_member_cannot_access_secretariat_backoffice_actions`, `test_member_blocked_from_secretariat_decorator_and_mixin` | Done |
| Object-level checks: a member can open only their own card; the data export and the status page use `request.user` and never a URL id | `member_card_view`; test `test_member_cannot_access_another_members_card_but_secretariat_can`; manual checklist 10.4 and 10.6 | Done |
| Eligibility API: authentication required, a member may query only themselves, 401/403/405 for violations | test `test_eligibility_api_enforces_auth_validation_and_rbac` | Done |
| The registration form cannot set privileges: posting `role=admin`, `is_staff` and `is_superuser` created a normal member | check on 2026-11-27 (form fields are an explicit list; `RegistrationForm.save` fixes the role) | Done |
| CSRF: all state-changing forms carry a token; POSTs without a token were rejected with 403 on sign-in, registration, back-office status change and payment status | check on 2026-11-27 with `enforce_csrf_checks`; the test client skips CSRF, so there is no automated test for this | Done |
| No server-side requests to user-supplied URLs (the former SSRF category is part of A01 in 2025); the article `cover_image` URL is only placed in an `<img>` tag for the browser | grep: no `requests`, `urllib`, `httpx` in the code | Done |
| `GET /accounts/logout/` signs the user out (the logout view accepts GET and POST), so another site could log a user out with an image tag | `accounts/views.py` `logout_view`; check on 2026-11-27 | Open, low risk |
| Staff can see every member (no per-region or per-case limits); a superuser passes all role checks | design decision, documented in the user guide | Accepted |
| Django admin (`/admin/`) needs the *staff* flag; the `role` field alone does not open it | `UserAdmin`; check: anonymous and member requests are redirected to the admin sign-in | Done |

### A02 Security Misconfiguration: Partial

| Control | Evidence | Status |
|---------|----------|--------|
| Secrets only in environment variables; `.env` ignored by Git and excluded from the Docker build context; `.env.example` holds placeholders | `.gitignore`, `.dockerignore`, `.env.example` | Done |
| Browser-side headers from Django: `X-Frame-Options: DENY`, `X-Content-Type-Options: nosniff`, `Referrer-Policy: same-origin`, `Cross-Origin-Opener-Policy: same-origin`; session cookie `HttpOnly` and `SameSite=Lax` | response headers checked on 2026-11-27 | Done |
| Database port published on `127.0.0.1` only | `docker-compose.yml` | Done |
| `DEBUG` is **on** when the variable is unset, `SECRET_KEY` and the database password have placeholder defaults, and nothing stops the application from starting that way | `src/config/settings.py` | Open: demo defaults, see deployment guide section 3 |
| `check --deploy` reports 6 warnings with the `.env.example` values (HSTS, SSL redirect, secret key, secure session cookie, secure CSRF cookie, debug) and 4 with `DEBUG=False` and a strong key; the settings file has no switches for HTTPS-related options | `python manage.py check --deploy` on 2026-11-27 | Open |
| No `Content-Security-Policy` header (the pages use the Tailwind CDN script and inline scripts) | response headers | Open: needs a compiled stylesheet first |
| Development server, root user in the container, source bind-mounted, web port open on all interfaces | `Dockerfile`, `docker-compose.yml` | Open: the demo setup, see deployment guide section 3 |
| Default Django error pages (no custom 403, 404 or 500 templates) | no `handler*` in `config/urls.py` | Open, low |

### A03 Software Supply Chain Failures: Open

| Control | Evidence | Status |
|---------|----------|--------|
| Dependencies and licences are inventoried | [`THIRD_PARTY_LICENSES.md`](../THIRD_PARTY_LICENSES.md) | Done |
| Vulnerability scan: `pip-audit` on the packages resolved from `requirements.txt` on 2026-11-27 reports **8 distinct advisories for Django 5.1.15** (GeoDjango, cache middleware, `get_signed_cookie`, `DomainNameValidator` and similar; none of these features are used by the MVP) and **1 for pytest 8.4.2** (11 findings in total because `pip-audit` lists some advisories twice; the pytest one is a local temp-directory issue in a tool that is declared but unused) | `pip-audit` output; Django 5.1 received its last security release (5.1.15) in December 2025 and is out of support, while Django 5.2 LTS is supported until April 2028 | Open |
| Cause and fix: `requirements.txt` says `Django>=5.0,<5.2`, so the supported 5.2 line cannot be installed. With Django 5.2.19 all 54 tests passed and `pip-audit` found nothing | check on 2026-11-27 in a separate virtual environment | Fix identified, **not applied**: change to `Django>=5.2,<5.3` in a separate issue and re-run the tests |
| Versions are ranges, there is no lock file and no automated update or scan job | `requirements.txt` | Open |
| Unused packages inflate the attack surface (`python-dotenv`, `pytest`, `pytest-django` are declared but never imported or configured) | [`THIRD_PARTY_LICENSES.md`](../THIRD_PARTY_LICENSES.md) section 5 | Open, optional clean-up |
| Tailwind is loaded as a script from a public CDN at run time and Docker images are referenced by tag, not by digest | `public_site/base.html`, `Dockerfile` | Open: compile Tailwind and pin images for production |

### A04 Cryptographic Failures: Partial

| Control | Evidence | Status |
|---------|----------|--------|
| Passwords stored with Django's default hasher PBKDF2-SHA256 (870,000 iterations, salted) | check on 2026-11-27: stored values start with `pbkdf2_sha256$870000$` | Done |
| Sessions, CSRF tokens and password-reset links signed with the `SECRET_KEY` | Django defaults | Done (depends on A02: a real key) |
| No card or bank data stored; payments are manual status records only | `PaymentRecord` model | Done |
| No HTTPS in the demo; cookies are not marked `Secure` until HTTPS settings are added | A02 | Open, deployment step |
| Database traffic inside the Docker network and the volume are unencrypted; backups are plain dump files | deployment guide section 4 | Open: use disk encryption and encrypt backups that leave the server |
| Phone, address and licence number are stored as plain columns (no field-level encryption) | `MemberProfile` | Accepted for the MVP |

### A05 Injection: Partial

| Control | Evidence | Status |
|---------|----------|--------|
| All database access through the Django ORM; no `raw()`, `extra()` or cursor use; a search string such as `' OR 1=1 --` returned an ordinary result page | grep of `src/`; check on 2026-11-27 | Done |
| HTML output is auto-escaped; no `\|safe`, `mark_safe` or `autoescape off`. A first name of `<script>alert(1)</script>` appeared escaped on the dashboard | grep; check on 2026-11-27 | Done |
| Input validation with Django forms (types, lengths, required fields, choices, date fields), server-side | `membership/forms.py`, `accounts/forms.py`; test `test_apply_membership_rejects_missing_consent_or_missing_licence_number` | Done |
| No shell, `eval` or `exec` calls | grep | Done |
| **CSV injection:** the member export writes names and other text as they are; a last name of `=1+1` appears unchanged in `members_export.csv`, and a spreadsheet program may run it as a formula | check on 2026-11-27; `backoffice_export_csv` | Open: prefix cells that start with `=`, `+`, `-` or `@` with an apostrophe |
| Rejected or never built: SQL built from strings, HTML built from user input | design | Done |

### A06 Insecure Design: Partial

| Control | Evidence | Status |
|---------|----------|--------|
| Data minimisation: the application form collects only fields the MVP uses; the member card shows four fields; the eligibility API returns four flags and gives the same answer for unknown and non-member identifiers | `docs/membership-model.md`, `docs/contracts.md`, test `test_member_card_displays_only_mvp_fields_and_supports_download` | Done |
| Integrity by design: fee quotes are frozen copies with the rule version, fee rules referenced by quotes cannot be deleted (`PROTECT`), consent is stored with a version and the exact text, status changes and payments carry the acting staff user | ADR 0004, ADR 0006; tests `test_changing_fee_rule_does_not_overwrite_existing_frozen_quotes`, `test_member_profile_default_lifecycle_and_versioned_consent` | Done |
| Payments are manual records; no payment gateway, so no payment-fraud surface | assignment scope | Done |
| No e-mail verification: anyone can register with an address they do not control (the assignment asks for it "where practical") | `RegistrationForm` | Open |
| No throttling on registration, password reset or the public enquiry forms (the enquiry forms have a honeypot field only) | `accounts/views.py`, `public_site/forms.py` | Open |
| No formal threat model beyond the ADRs; no abuse-case tests | `docs/adr/` | Open |
| Renewal reminders do not remember who was reminded, so a daily run repeats messages | `send_renewal_reminders` | Open, low |

### A07 Authentication Failures: Partial

| Control | Evidence | Status |
|---------|----------|--------|
| Framework authentication; four password validators (similarity, minimum length, common passwords, numeric only) | `AUTH_PASSWORD_VALIDATORS` | Done |
| Login rate limit: after 5 failures per client address and sign-in name within 300 seconds the next attempt returns HTTP 429 | `accounts/views.py`; test `test_login_rate_limiting_blocks_brute_force`; manual checklist 1.6 | Done |
| The rate-limit counter lives in each process's memory: it resets on restart, is counted per worker, and behind a reverse proxy all clients share one address | ADR 0005 (limitation noted); deployment guide section 3, item 9 | Open for production |
| Generic error on failed sign-in; the password-reset form answers identically for known and unknown e-mail addresses | check on 2026-11-27 | Done |
| Registration reports "A user with this email address already exists", which reveals that the address is registered | `RegistrationForm.clean_email` | Accepted (usability trade-off) |
| Session id is renewed at sign-in (Django default); the open-redirect target `next` is validated (an external `next` URL led to the dashboard) | Django `login()`; `login_view`; redirect check on 2026-11-27 | Done |
| Sessions last two weeks with no idle timeout | Django default | Open, low |
| No multi-factor authentication | explicitly deferred by Assignment A | Out of MVP scope |
| Staff-created accounts (quick-add) have no usable password and cannot sign in or use password reset until an administrator sets a password | `backoffice_quick_add_member`; user guide B4 | Known limitation |

### A08 Software or Data Integrity Failures: Partial

| Control | Evidence | Status |
|---------|----------|--------|
| Schema changes only through versioned migrations; a test fails when models and migrations drift apart | `common/tests.py` `MigrationDriftTests` | Done |
| Session data uses Django's JSON serializer; no `pickle` in the code | grep | Done |
| Fee quotes and the status history are never edited by the application, only appended. Payment rows are different: a status change updates the row in place (status, date and `recorded_by`), so only the last change is kept, not the full history | `membership/services.py`, `backoffice_update_payment_status` | Partial: add a payment history table or log entries to make the payment audit trail complete |
| The Django admin lets an administrator edit or delete status-history, consent and payment rows, so the audit trail is not tamper-proof against administrators | `membership/admin.py` | Open: make those admin models read-only for production |
| The Tailwind script is fetched from a CDN with no integrity check; no CI pipeline runs the tests on every push | `base.html`; repository | Open |

### A09 Security Logging & Alerting Failures: Open

| Control | Evidence | Status |
|---------|----------|--------|
| Business audit trail: status history with the acting user, payments with the last acting user (`recorded_by`) and `updated_at`, consent records with timestamps, Django admin log | models, `django_admin_log` | Done |
| Public enquiries are logged by id, type and region only, without personal data | `public_site/views.py` | Done |
| Failed sign-ins, rate-limit hits, 403 responses and data exports (CSV, JSON) are not logged; there is no `LOGGING` configuration, no log retention rule and no alerting | `src/config/settings.py` | Open |
| The notification log line contains the recipient e-mail address (personal data in a log); it is hidden by Django's default logging but appears as soon as INFO logging is configured | `common/notifications.py` | Open: mask or drop before real data is used |

### A10 Mishandling of Exceptional Conditions: Partial

| Control | Evidence | Status |
|---------|----------|--------|
| Invalid input is rejected with a message instead of an error: bad forms, an invalid payment status, an invalid date | forms; `backoffice_update_payment_status`; manual checklist 3.2, 3.3, 7.4 | Done |
| The eligibility API answers with JSON status codes 400, 401, 403 and 405 and never with a stack trace; an unknown member is a normal "all false" answer | test `test_eligibility_api_enforces_auth_validation_and_rbac` | Done |
| Multi-step writes (application, status change, quick-add) run inside `transaction.atomic()` so a failure leaves no half-saved member | `membership/views.py`, `services.py` | Done |
| The management command reports bad arguments as clear errors | `send_renewal_reminders` (manual checklist 11.4) | Done |
| Default Django error pages; no central exception handling or alert; with `DEBUG=True` an error shows internals | A02 | Open |

## 3. MVP scope boundaries and open actions

**Deliberately outside the MVP** (Assignment A, section 3, and the rules): production deployment and operations, two-factor
authentication, production payment gateway, full legal GDPR workflow and final consent wording, production security and
legal sign-off, penetration testing, WAF and denial-of-service protection.

**Open actions, in the order that would be tackled first:**

| Priority | Action | Effort |
|----------|--------|--------|
| 1 | Move Django to 5.2 LTS (`Django>=5.2,<5.3`), run the tests, re-run `pip-audit` (A03) | small, tested in this review |
| 1 | Production settings: `DEBUG` off by default, refuse to start with the placeholder `SECRET_KEY`, switches for HTTPS, secure cookies and HSTS (A02, A04) | small |
| 2 | Neutralise formulas in the CSV export (A05) | small |
| 2 | Log failed logins, rate-limit hits, 403s and exports without personal data (A09) | small |
| 2 | Make logout POST-only (A01) | small |
| 3 | Shared cache and trusted proxy address for the rate limit (A07) | medium |
| 3 | E-mail verification and throttling of registration, reset and enquiry forms (A06, A07) | medium |
| 3 | Read-only audit models in the admin, custom error pages, compiled Tailwind and a CSP header, CI with `pip-audit` (A02, A08, A10) | medium |
| 3 | Remove the unused packages (`python-dotenv`, `pytest`, `pytest-django`) or start using them (A03) | small |

## 4. How to reproduce the checks

```bash
# automated tests that cover access control, rate limiting, validation, migrations, eligibility API
docker compose exec web python manage.py test

# deployment warnings (use your real environment values to see the production view)
docker compose exec web python manage.py check --deploy

# known vulnerabilities in the installed packages (pip-audit is not a project dependency)
docker compose exec web sh -c "pip install pip-audit && pip-audit"
```

The manual checks listed as "check on 2026-11-27" can be repeated in a browser or with the Django test client:
POST without a CSRF token (expect 403), register with `role=admin` (expect a plain member), a first name of
`<script>alert(1)</script>` (expect escaped output), sign in with `?next=https://example.org/` (expect the dashboard),
export the CSV with a last name of `=1+1` (currently unchanged, see A05).

## 5. References

- OWASP Top 10:2025: <https://owasp.org/Top10/2025/>
- Django release and support status: <https://www.djangoproject.com/download/>
- Project documents: [`api.md`](api.md), [`test-report.md`](test-report.md), [`manual-test-checklist.md`](manual-test-checklist.md),
  [`deployment-and-backup.md`](deployment-and-backup.md), [`gdpr-checklist.md`](gdpr-checklist.md), ADRs 0002 and 0005.
