# ADR-0007: Eligibility Verification Contract and Shared Notification Stub

- **Status:** Accepted
- **Date:** 2026-11-23
- **Deciders:** Student A (Membership & Member Portal), coordinated with Student B (Public Website)

## Context
Section 6 of the MVP specification requires two clean integration boundaries between Student A and Student B:
1. An eligibility contract owned by Student A that checks whether a member is active and whether their hunting licence and insurance are valid on a supplied date (`active`, `licenceValid`, `insuranceValid`, `validUntil`), usable both in-process by Django modules and over HTTP.
2. A single shared notification interface (`send(channel, recipient, template, context)`) owned by Student A so Student B does not create a competing notification mechanism, plus a tested renewal reminder job stub without requiring live SMTP or real personal data.

## Decision
1. **In-Process Service + Protected JSON Endpoint for Eligibility:**
   - Implemented `membership.services.check_eligibility(user_or_email, target_date)` accepting a `User`, `MemberProfile`, email, username, or `member_number` and returning the exact JSON schema defined in `docs/contracts.md`.
   - Exposed `GET /membership/api/eligibility/` with server-side authentication (`401` for anonymous requests) and RBAC (`403` when a regular `member` queries another member's identifier; `secretariat`/`admin` may query any member).
   - Unknown or incomplete profiles safely evaluate to `active: false, licenceValid: false, insuranceValid: false, validUntil: null` rather than raising errors or leaking account existence.
2. **Centralised Notification Stub in `common/notifications.py`:**
   - Implemented `common.notifications.send(channel, recipient, template, context)` supporting `"email"` and `"log"` channels and versioned plain-text templates under `src/common/templates/notifications/`.
   - Configured Django's `EMAIL_BACKEND` to default to `console.EmailBackend` so development/demo runs never send external emails to real addresses, while automated tests capture dispatches via `django.core.mail.outbox`.
3. **Renewal Reminder Management Command Stub:**
   - Added `python manage.py send_renewal_reminders` with `--days`, `--date`, `--channel`, and `--dry-run` flags so scheduled-job behaviour can be deterministically tested and later triggered by cron/systemd without changing domain code.

## Consequences
- **Positive:** Both modules share one authoritative source of truth for member eligibility and outbound notifications, eliminating duplicate logic.
- **Positive:** Automated contract tests verify all synthetic scenarios from `docs/contracts.md` and guard against accidental schema regressions.
- **Trade-off:** Replacing the MVP notification stub with a live SMTP provider or background task queue (e.g., Celery) is deferred to post-MVP production rollout, but the `send(...)` interface stays unchanged.