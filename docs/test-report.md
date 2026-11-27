# Automated Test Report (Student A: Membership module)

This report records the result of the automated test suite and shows which acceptance criteria of Assignment A are
covered by which tests. Behaviour that cannot be checked automatically is covered by the step-by-step
[manual test checklist](manual-test-checklist.md). Endpoint behaviour is described in [`api.md`](api.md).

## 1. How to run

From the repository root with the stack running (`docker compose up`):

```bash
# whole suite (separate throw-away test database, the demo database is not touched)
docker compose exec web python manage.py test

# one app, or one test class
docker compose exec web python manage.py test membership
docker compose exec web python manage.py test membership.tests.EligibilityContractTests

# verbose list of every test
docker compose exec web python manage.py test -v 2
```

Reproducibility from a clean state (what a reviewer should run):

```bash
docker compose down -v
docker compose up --build -d
docker compose exec web python manage.py test
```

## 2. Result

| Run | Environment | Tests | Result | Time |
|-----|-------------|-------|--------|------|
| 2026-11-26 | Docker Compose, PostgreSQL 16, Python 3.12 (recorded in `ai-log.md`, Entry 15) | 54 | OK | not recorded |
| 2026-11-27 | Python 3.13 with SQLite in memory (AI work session; same code, `config.settings` overridden for the database only) | 54 | OK, 0 failures, 0 errors | 12.7 s |

The suite contains **54 tests**: 32 for the Student A modules (`accounts`, `membership`, `common`) and 22 for Student B's
`public_site`. The Student A tests are listed in section 3.

### Code coverage (measured with `coverage.py`, 2026-11-27)

Statement coverage of the application code (migrations, test files and demo seed commands excluded): **94 %** overall
(1195 statements, 73 not executed). The Student A files:

| File | Coverage |
|------|----------|
| `membership/views.py` | 96 % |
| `membership/services.py` | 90 % |
| `membership/models.py` | 94 % |
| `membership/forms.py` | 91 % |
| `membership/management/commands/send_renewal_reminders.py` | 91 % |
| `accounts/views.py` | 94 % |
| `accounts/permissions.py` | 94 % |
| `accounts/forms.py` | 96 % |
| `common/notifications.py` | 100 % |

Coverage is a hint about which lines ran, not proof that the behaviour is right; the table in section 4 shows what is
actually asserted.

## 3. Student A tests

| Test class (file) | Tests | What it verifies |
|-------------------|-------|------------------|
| `accounts.tests.AuthenticationFlowTests` | 5 | registration creates a `member` and signs in; login with e-mail and with username; **login rate limiting** after repeated failures; dashboard needs sign-in; password reset request |
| `accounts.tests.RoleAndPermissionTests` | 5 | role helper properties; anonymous users are redirected to sign-in; members blocked from secretariat decorator/mixin; secretariat and admin allowed; editor isolated from member and secretariat areas |
| `common.tests.MigrationDriftTests` | 1 | models and migrations are in sync (`makemigrations --check`) |
| `membership.tests.MembershipModelsAndFeeCalculatorTests` | 4 | fee breakdown with add-ons and discount; **changing a fee rule does not rewrite stored quotes**; default lifecycle and versioned consent; demo seed command |
| `membership.tests.MembershipApplicationAndExportViewsTests` | 4 | calculator view shows the sample breakdown; application creates profile, consent, status history and frozen quote; application rejected without consent or without licence number; **GDPR JSON export** |
| `membership.tests.MembershipLifecycleAndCardTests` | 3 | status transition generates the member number and writes history; card shows only the MVP fields and can be downloaded; member cannot open another member's card, secretariat can |
| `membership.tests.SecretariatBackOfficeTests` | 5 | member blocked from back-office actions; directory search, filter and pagination; approve application and manage manual payments; quick-add; **filtered CSV export** |
| `membership.tests.EligibilityContractTests` | 3 | the three examples from `contracts.md`; expiry dates and identifier lookup (username, e-mail, member number); API authentication (401), date validation (400) and role rules (403) |
| `membership.tests.NotificationStubAndRenewalCommandTests` | 2 | shared notification stub (channels, validation); `send_renewal_reminders` dry run and dispatch |

## 4. Acceptance criteria traceability (Assignment A, section 5)

| Acceptance criterion | Automated evidence | Manual evidence (checklist section) |
|----------------------|--------------------|-------------------------------------|
| A new synthetic user can register/apply, receive a fee quote and later sign in to see their status | `test_registration_creates_member_role_and_logs_in`, `test_apply_membership_creates_profile_consent_status_history_and_quote` | 1, 2, 3 |
| Changing a fee rule affects new quotes but does not rewrite stored quotes | `test_changing_fee_rule_does_not_overwrite_existing_frozen_quotes` | 3 |
| A secretariat user can approve an application, set validity dates, record a manual payment and export a CSV | `test_secretariat_can_approve_application_and_manage_manual_payments`, `test_secretariat_can_export_filtered_csv` | 6, 7, 8 |
| A member cannot access another member's private data; secretariat-only actions are blocked for a member | `test_member_cannot_access_another_members_card_but_secretariat_can`, `test_member_cannot_access_secretariat_backoffice_actions`, `test_member_blocked_from_secretariat_decorator_and_mixin` | 6, 10 |
| The eligibility function returns `active`, `licenceValid`, `insuranceValid`, `validUntil` for a date, with contract tests | `EligibilityContractTests` (3 tests) | 9 |
| The member card shows only the MVP fields | `test_member_card_displays_only_mvp_fields_and_supports_download` | 4 |
| Core workflow tests pass from a clean Docker Compose setup | run in section 2 (clean-state commands in section 1) | 0 |
| Basic way for a member to view/export their own data | `test_export_my_data_returns_gdpr_json_bundle` | 5 |
| Rate-limited login, server-side role checks (minimum security) | `test_login_rate_limiting_blocks_brute_force`, `RoleAndPermissionTests` | 1, 10 |
| Renewal reminders (scheduled-job stub) | `test_send_renewal_reminders_command_dry_run_and_dispatch` | 11 |

## 5. Known gaps

These are not asserted by automated tests and are therefore checked manually (see the checklist):

- Page layout, navigation and the account menu in the shared header (visual check, desktop and mobile width; checklist section 12).
- The complete password-reset e-mail flow (only the request step is automated; checklist steps 1.7 and 1.8).
- The suite was also executed on SQLite; PostgreSQL-specific behaviour is covered only by the Docker run of 2026-11-26.
- No load, concurrency or penetration testing. The OWASP and GDPR checklists are handled in the security handover documents.
