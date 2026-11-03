# ADR 0003: Public Site Data Model Boundaries and Privacy Controls

- **Status:** Accepted
- **Date:** 2026-11-03
- **Deciders:** Student B (Danylo Vinnytskyi), Student A

## Context
The MVP is developed in parallel by two students sharing a single Django repository and PostgreSQL database. Project rules strictly prohibit Student B from duplicating Student A's authentication (`accounts`) or membership lifecycle (`membership`) models. At the same time, Student B must deliver a complete public website (`public_site`) featuring news articles, a regional representatives directory, FAQs, and public enquiry forms, while ensuring privacy compliance (GDPR) for published contact details and visitor submissions.

## Decision
Isolate all public website entities within the `public_site` app (`Category`, `Article`, `RegionalRepresentative`, `VolunteerEnquiry`, `MembershipEnquiry`, `FAQ`) with strict architectural boundaries and privacy controls:
- **Decoupled Article Authorship:** Use a plain text field (`author_byline`) on the `Article` model for public display rather than a hard ForeignKey to `accounts.User`, avoiding cross-app migration dependencies during parallel development.
- **Lead-Capture Handoff for Membership:** Implement `MembershipEnquiry` strictly as a pre-registration question form for unauthenticated visitors. Direct membership registration CTAs will route visitors straight to Student A's registration view (`MEMBERSHIP_REGISTER_URL`)[cite: 4].
- **Explicit Privacy & Consent Flags:**
  - `RegionalRepresentative`: Include `is_active` and `consent_to_publish` boolean flags; public directory views will filter for records where both flags are `True`.
  - `VolunteerEnquiry` & `MembershipEnquiry`: Require explicit visitor consent (`consent_given = True`) on submission and restrict read/manage access strictly to authorised staff (`editor` and `admin` roles defined in ADR 0002).

## Consequences
- **Positive:** Complete separation of concerns between `public_site` and `membership`/`accounts`; zero risk of circular dependencies or migration conflicts between Student A and Student B; built-in privacy-by-design for personal data.
- **Negative:** Pre-registration enquiries submitted via `MembershipEnquiry` are not automatically converted into `accounts.User` records and require staff review or visitor follow-up via the main registration flow.