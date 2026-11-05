# Integration Contracts & APIs (Student A & Student B)

This document defines the shared technical contracts between **Student A** (Membership & Member Portal) and **Student B** (Public Website & Member Acquisition) as mandated by Section 6 of the MVP specification.

---

## 1. Eligibility Function / API Contract

Student A provides an eligibility function to verify whether a user's membership is active and whether their hunting licence and insurance are valid for a specific target date.

### Function Signature
- Function: `check_eligibility(user_or_email: str, target_date: date) -> dict`
- Module location: `membership.services.check_eligibility`

### Return Fields (as required by Section 5 Acceptance Criteria)
- `active` (boolean): `True` if member status is `active` and `valid_from <= target_date <= valid_until`.
- `licenceValid` (boolean): `True` if `hunting_licence_valid_until` is set and `>= target_date`.
- `insuranceValid` (boolean): `True` if `insurance_valid_until` is set and `>= target_date`.
- `validUntil` (string / ISO date or null): Membership expiration date (`YYYY-MM-DD`).

### Synthetic Example Responses
1. **Active hunter with valid licence and insurance (Target date: `2026-06-15`):**
   `{"active": true, "licenceValid": true, "insuranceValid": true, "validUntil": "2026-12-31"}`

2. **Active non-hunter without hunting licence (Target date: `2026-06-15`):**
   `{"active": true, "licenceValid": false, "insuranceValid": false, "validUntil": "2026-12-31"}`

3. **Applicant or expired member (Target date: `2026-06-15`):**
   `{"active": false, "licenceValid": false, "insuranceValid": false, "validUntil": null}`

---

## 2. Shared Notification Interface Stub

Student A owns the notification implementation/stub in `common/notifications.py`. Student B calls this shared function rather than creating a separate notification system.

### Function Signature
- Function: `send(channel: str, recipient: str, template: str, context: dict) -> bool`
- Supported channels: `"email"`, `"log"`
- Supported templates: `"application_received"`, `"renewal_reminder"`, `"enquiry_acknowledgement"`
- MVP Behaviour: Logs structured notification output to the application logger / console without sending live external emails to real addresses.

---

## 3. Membership Registration Handoff Configuration

Student B's public website ("Become a member" CTA and membership enquiry handoff) links to Student A's registration flow via a single configurable setting in `config/settings.py`:
- Setting name: `MEMBERSHIP_REGISTRATION_URL = "/membership/apply/"`
- Named URL route: `membership:apply`