# GDPR Checklist (Membership module and shared platform)

A practical checklist of how the Hunting Association MVP handles personal data, what the MVP supports, and what the
association still has to decide. It follows the structure of the General Data Protection Regulation (GDPR) so that a
lawyer or data-protection contact can review it quickly.

> **Important.** This document describes technical and organisational facts about the MVP. It is **not legal advice and
> makes no claim of GDPR compliance.** Assignment A leaves the full legal workflow, the retention policy, the final
> consent wording and the legal sign-off to the association. Until then the application runs on **synthetic demo data
> only**, and every consent and privacy text in it is labelled *SAMPLE / PLACEHOLDER*.

- **Reviewed:** 2026-11-27, repository state after issue #34.
- **Status words:** **Supported** = implemented in the MVP; **Manual** = possible only by staff following a procedure;
  **Open** = not built; **Decision** = needs the association or legal advice.
- Related documents: [`membership-model.md`](membership-model.md) (data dictionary), [`api.md`](api.md) (export endpoint),
  [`owasp-checklist.md`](owasp-checklist.md) (security measures), [`deployment-and-backup.md`](deployment-and-backup.md),
  [`user-guide.md`](user-guide.md), [`adr/0003-public-site-data-boundaries.md`](adr/0003-public-site-data-boundaries.md).

## 1. Personal-data inventory

| Area | Data | Purpose in the MVP | Who can see it | Retention today |
|------|------|--------------------|----------------|-----------------|
| Account (`accounts_user`) | username, e-mail, first and last name, password hash (PBKDF2), role, join and last-login dates | sign-in and identification | the person; secretariat and administrators; Django admin | until the account is deleted or anonymised |
| Membership profile (`membership_memberprofile`) | category, phone, street, city, postal code, hunting-licence number, licence and insurance expiry dates, status, validity dates, member number | application, approval, card, eligibility check | the person (own page and export); secretariat and administrators | same |
| Fee quotes (`membership_feequote`) | amounts, tariff version, add-on choices, linked to the member | transparent fee, frozen history | the person; secretariat and administrators | same; deleting the member deletes quotes |
| Consent records (`membership_consentrecord`) | purpose, consent version, exact text, accepted, timestamp | proof of the consent given | the person (own page and export); administrators | same |
| Payments (`membership_paymentrecord`) | status, amount, currency, reference, date, free-text note, acting staff user | manual payment tracking | secretariat and administrators; the person sees them in the export | same; **deleting a member in the Django admin deletes the payments too** |
| Status history (`membership_membershipstatushistory`) | status changes, free-text note, acting staff user, time | audit trail | secretariat and administrators; the person sees it on *My membership* | same |
| Sessions (`django_session`) | session key and data, expiry | keep users signed in | nobody (technical) | 2 weeks, then unused rows remain until cleared with `clearsessions` |
| Volunteer enquiries (`public_site_volunteerenquiry`) | full name, region, e-mail, phone, interests, message, consent flag, status, internal staff note | answer volunteer interest (Student B) | editors and administrators via the Django admin | no rule |
| Membership enquiries (`public_site_membershipenquiry`) | full name, e-mail, phone, region, preferred category, licence yes/no, message, consent flag, status, staff note | answer questions before registration (Student B) | editors and administrators via the Django admin | no rule |
| Regional representatives (`public_site_representative`) | display name, role, public contact, short biography, areas | public contact directory (Student B) | public, when the entry is active | no rule |
| Server log and e-mail output | the web server's request log (a production reverse proxy normally records client IP addresses); the console e-mail backend prints whole e-mails; the notification code has a log line with the recipient e-mail that is hidden unless INFO logging is switched on | operation | whoever can read the container logs | Docker log default, no rule |
| Backups | a full copy of everything above | disaster recovery | whoever can read the backup files | no rule; see section 5 |

Notes:

- **No special-category data (Art. 9)** is collected: no health, biometric, political or similar data, and no
  government identification numbers. The hunting-licence number and licence and insurance dates are administrative data;
  the association should confirm with legal advice that they need no extra treatment.
- **No photos, documents or other uploads** exist in the MVP.
- **Third-party requests from the visitor's browser:** every page loads the Tailwind script from a public CDN, and the demo
  articles load photos from Unsplash. The visitor's IP address therefore reaches those providers. Compile Tailwind into
  the project and host images yourself before real use.
- The staff-only *internal notes* and the free-text notes of payments and status changes can contain personal data;
  staff should keep them factual and short.

## 2. Principles (Art. 5 and 25) as implemented

| Principle | What the MVP does | Status |
|-----------|-------------------|--------|
| Data minimisation | the application form collects only fields used by the MVP (no date of birth, no ID numbers, no photos); the member card shows four fields; the eligibility API returns four flags | Supported |
| Purpose limitation | consent is recorded for one purpose, membership processing; the card, export and eligibility check each use only the fields they need | Supported |
| Privacy by default | self-service export shows only the member's own data; the back office requires a staff role; demo data is synthetic and loaded only on request | Supported |
| Accuracy | the member can correct their details by submitting the application form again; staff can correct records in the back office or admin | Supported (limited fields) |
| Storage limitation | no retention periods, no automatic deletion or anonymisation job, no clean-up of old enquiries, sessions or logs | Open / Decision |
| Integrity and confidentiality | roles, CSRF, password hashing, rate-limited login; see the OWASP checklist for gaps (no HTTPS and no encryption at rest in the demo setup) | Partial |
| Accountability | ADRs, AI log, test report; no record of processing activities, no data-protection impact assessment | Open / Decision |

## 3. Lawful basis, consent and information (Art. 6, 7, 13)

| Item | MVP behaviour | Status |
|------|---------------|--------|
| Consent at application | a mandatory checkbox with the wording shown next to it; the stored record holds the purpose, version (`2026-v1-demo`), the exact text shown, `accepted` and a timestamp; each submission of the form adds a new record | Supported |
| Versioned wording | the text and its version live in `membership/services.py` (`DEFAULT_CONSENT_TEXT`, `DEFAULT_CONSENT_VERSION`); old records keep the text that was shown | Supported |
| Consent wording | placeholder text, explicitly "not legal compliance wording" | Decision: final wording and the lawful basis for membership administration (consent, contract or legitimate interest) |
| Consent on the public enquiry forms | mandatory checkbox, stored as a yes/no flag only (no version, no text snapshot, no timestamp other than the record's creation time) | Partial (Student B) |
| Staff-created members (quick-add) | no consent record is created, because the member did not use the form | Decision: keep the paper or e-mail consent outside the system, or add a consent record at quick-add |
| Withdrawal of consent | no button and no `withdrawn` state; records are only added | Open: handle through the manual procedure (section 4) |
| Privacy notice (Art. 13) | no privacy-notice page exists, only the consent sentence at the forms | Open / Decision |
| Minors | no age field and no age check | Decision |
| Directory consent | ADR 0003 describes a `consent_to_publish` flag for representatives, but the `Representative` model only has `is_active`; the public directory shows entries where `is_active` is true | To be confirmed by Student B |

## 4. Rights of the data subject (Art. 15 to 22)

| Right | How it is handled today | Status |
|-------|-------------------------|--------|
| Access (Art. 15) and portability (Art. 20) | the member downloads a JSON file with account, profile, quotes, consents, status history and payments (`/membership/export-data/`); test `test_export_my_data_returns_gdpr_json_bundle`; manual checklist section 5 | Supported (membership data only) |
| Access to public-site enquiry data | not part of the member export; editors can look the person up in the Django admin | Manual |
| Rectification (Art. 16) | the member edits profile fields by submitting the application form again (this also creates a new quote and consent record); name changes work the same way; e-mail and username changes go through staff | Supported / Manual |
| Erasure (Art. 17) | **manual procedure**, described below and printed on the member's page; no delete button | Manual |
| Restriction (Art. 18) and objection (Art. 21) | staff set the status to *Suspended* or deactivate the account; no dedicated flag | Manual |
| Withdraw consent (Art. 7) | see section 3 | Manual |
| Automated decisions (Art. 22) | none; approval is a staff decision, and the eligibility flags are informational for the public site | N/A |
| Response deadline and request register | not tracked by the system | Decision: the association keeps a register outside the application |

### Procedure for an erasure request (MVP, manual)

The text shown to members (`DELETION_REQUEST_PROCEDURE_TEXT`) promises exactly this and is placeholder wording. The steps
below describe how staff can carry it out with the tools that exist.

1. **Verify identity.** Confirm that the request really comes from the account holder.
2. **Check retention duties.** Payment records and fee quotes may have to be kept for accounting. The association decides
   which rules apply; the MVP has no rule built in.
3. **Do not simply delete the user in the Django admin.** Deleting the user also deletes the profile, quotes, consents,
   status history and **all payment records** (cascade). Prefer anonymising.
4. **Anonymise the account and profile.** An administrator opens the shell (`docker compose exec web python manage.py
   shell`) and runs the following for the person's username. It was run against the demo database on 2026-11-27: the
   account could no longer sign in, the CSV export showed blank personal columns, and quotes, payments and consents
   stayed attached to the member number.

   ```python
   from django.contrib.auth import get_user_model
   from django.db import transaction
   from membership.models import MemberProfile

   User = get_user_model()
   with transaction.atomic():
       user = User.objects.get(username="THE-USERNAME")
       pk = user.pk
       user.username = f"deleted-user-{pk}"
       user.email = f"deleted-{pk}@invalid.example"
       user.first_name = ""
       user.last_name = ""
       user.is_active = False
       user.set_unusable_password()
       user.save()

       profile = MemberProfile.objects.get(user=user)   # skip these lines if there is no profile
       profile.phone = ""
       profile.street_address = ""
       profile.city = ""
       profile.postal_code = ""
       profile.hunting_licence_number = ""
       profile.licence_valid_until = None
       profile.insurance_valid_until = None
       profile.status = MemberProfile.Status.EXPIRED
       profile.save()
   ```
5. **Clean free text by hand.** Read the notes of the status history and of the payments in the back office or admin and
   remove personal details. Decide, with the association, whether the consent records are kept as proof or deleted.
6. **Remove public-site records.** Delete the person's volunteer and membership enquiries (Django admin).
7. **Backups and logs.** The data stays in older backups and logs until they expire (section 5); if a backup is restored,
   repeat the erasure.
8. **Record the request** (date received, date handled, who, what was done) in the association's own register.
9. **Confirm** to the person in writing.

## 5. Security and organisational measures (Art. 32)

| Measure | Status | Evidence |
|---------|--------|----------|
| Access control by role, server-side; members see only their own data | Supported | OWASP A01; tests listed there |
| Password hashing, CSRF protection, rate-limited login, input validation | Supported | OWASP A04, A05, A07 |
| Synthetic data only in development, tests, demos and AI prompts; no real personal data in the repository | Supported | README security notes; ai-log |
| Secrets in environment variables, never in Git | Supported | `.gitignore`, `.env.example` |
| Encrypted connections (HTTPS) and encryption at rest | Open | demo runs on plain HTTP; deployment guide section 3 |
| Backups protected, access restricted, retention defined | Open / Decision | deployment guide section 4: backups are plain files that contain personal data; the repository ignores them (`backups/`, `*.dump`) |
| Logs free of personal data | Partial | the notification log line contains the recipient e-mail (hidden unless INFO logging is on) and the console e-mail backend prints whole e-mails; the public enquiry logs contain no personal data |
| Audit trail of staff actions | Partial | status changes and payments record the acting user; payment rows keep only the last change; exports and reads are not logged |
| Staff awareness: handle member data only when needed, no copies into chats, e-mails or AI tools | Supported (documented) | user guide B7 |
| Breach detection and notification procedure (Art. 33, 34) | Open / Decision | nothing built; needs an owner and a process |

## 6. Roles, processors and transfers

| Question | Answer for the MVP | Status |
|----------|--------------------|--------|
| Controller | the hunting association (to be confirmed) | Decision |
| Processors | none in the demo setup. A real deployment adds a hosting provider and a mail provider, each needing a data-processing agreement | Decision |
| Recipients outside the association | Tailwind CDN and Unsplash receive the visitor's IP address when pages load (section 1); no member data is sent to anyone | Open |
| Transfers outside the EU | not assessed; depends on hosting and mail providers | Decision |
| Data-protection officer, records of processing (Art. 30), impact assessment (Art. 35) | not prepared | Decision |

## 7. What the association must decide before real data is used

1. The controller, the lawful basis for each purpose, and the final consent and privacy-notice wording.
2. Retention periods for members, payments, quotes, consents, enquiries, logs and backups, and who deletes what and when.
3. The handling of erasure, restriction and objection requests, including accounting duties and the request register.
4. Hosting, mail provider and the agreements with them; HTTPS; backup protection.
5. Whether quick-added members need a consent record, how consent is withdrawn, and whether minors may join.
6. A breach procedure, and who answers data-protection questions.
