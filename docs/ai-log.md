# AI Usage Log

## Entry 1 — Repository Initialization, Docker Setup & Custom User Model
- **Date:** 2026-11-02
- **Task / Issue:** Project initialization, Git/SSH setup, Docker Compose configuration with PostgreSQL, and Django custom User model implementation (Student A scope, Issue #1).
- **Prompt Summary:** Asked AI for a step-by-step guide to initialize a Git repository, structure a Django/PostgreSQL/Docker environment reproducible under 15 minutes, and implement a custom `User` model with roles (`member`, `secretariat`, `editor`, `admin`).
- **AI Output:** Provided Git/SSH initialization commands, `Dockerfile`, `docker-compose.yml`, `requirements.txt`, and code for `accounts.User` and `settings.py`.
- **Verification & Human Changes:**
  - Verified that the repository layout follows the required modular structure (`accounts`, `membership`, `public_site`, `common`, `config`) to avoid conflicts with Student B.
  - Resolved Docker Buildx case-sensitivity path issue on Windows and tested the environment with PostgreSQL 16, applying initial migrations and creating a superuser.
  - Confirmed that the custom `User` model includes the `editor` role required by Student B alongside `member`, `secretariat`, and `admin`.

  ## Entry 2 — Initial Discovery, Content Model
* **Date:** 2026-11-02
* **Task / Issue:** Initial project discovery, database schema design for Student B scope, and ADR templates.
* **Prompt Summary:** Asked AI to help structure the database models (`Category`, `Article`, `RegionalRepresentative`, `VolunteerEnquiry`, `MembershipEnquiry`, `FAQ`) based on the MVP requirements, ensuring no overlap with Student A's User/Membership models.
* **AI Output:** Suggested Django model fields, data types, status enums, and Mermaid ER diagram syntax.
* **Verification & Human Changes:** 
  - Verified every field against Section 2 ("In scope — MUST deliver") and Section 6 ("Coordination with Student A").
  - Confirmed that `Article.author` uses a simple `CharField` (`author_byline`) rather than creating a separate `User` model, avoiding conflict with Student A's authentication system.
  - Added explicit `consent_given` and `consent_timestamp` fields on enquiry models to meet privacy/GDPR requirements.

## Entry 3 — Initial Discovery, Membership ER Model, Contracts
- **Date:** 2026-11-05
- **Task / Issue:** Initial discovery, database schema design for Student A scope (`docs/membership-model.md`), shared integration contracts (`docs/contracts.md`), and fee versioning ADR (`docs/adr/0004-fee-versioning-and-frozen-quotes.md`) (Student A scope, Issue #6).
- **Prompt Summary:** Asked AI to help design the Mermaid ER diagram and data dictionary (`MemberProfile`, `StatusHistory`, `FeeRule`, `FeeQuote`, `Payment`, `ConsentRecord`), define the eligibility function and notification stub contracts for Student B, and draft ADR-0004 for immutable fee quotes.
- **AI Output:** Suggested entity relationships, field definitions, Mermaid ER syntax, JSON response examples for `check_eligibility`, notification stub signature, and ADR-0004 structure.
- **Verification & Human Changes:**
  - Verified every field against Section 2 ("In scope — MUST deliver") and Section 6 ("Coordination with Student B") to ensure strict data minimisation and reuse of `accounts.User`.
  - Confirmed that `check_eligibility` returns the exact fields required by Section 5 Acceptance Criteria (`active`, `licenceValid`, `insuranceValid`, `validUntil`).
  - Separated `FeeRule` and `FeeQuote` with frozen monetary snapshots (`on_delete=models.PROTECT`) so changing fee rules affects new quotes without rewriting historical quotes.


## Entry 4 — Public Site Core Pages, FAQ Module, and Slovak Localization
- **Date:** 2026-11-10
- **Task / Issue:** Implementation of homepage, core public pages (`about`, `how_to_join`, `faq`), `FAQ` model/admin, and unit tests (`public_site` app, Student B scope, Issue #8).
- **Prompt Summary:** Asked AI to assist with responsive Tailwind CSS layout snippets for the public templates, Slovak translation phrasing for hunting terminology, and boilerplate structure for the FAQ view tests.
- **AI Output:** Suggested HTML/Tailwind grid structures for the 5 templates, SVG icon options, Slovak text drafts, and basic `TestCase` examples.
- **Verification & Human Changes:**
  - Implemented the `FAQ` model, admin configuration, URL routing, and view logic (`MEMBERSHIP_REGISTER_URL` handoff to `/membership/apply/`), verifying compliance with Student A's integration contract.
  - Researched *Deutscher Jagdverband* to structure and add custom domain content: association statistics (*Fakty a čísla*), hunting ethics (*Waidgerechtigkeit*), 4 specialized commissions, membership categories, and document checklists.
  - Fixed a `NoReverseMatch` URL tag issue in the footer (`{% url 'public_site:about' %}`) and corrected a typo in the navigation bar (`Ako vstúpiť`).
  - Populated the database with Slovak FAQ records and ran the unit test suite in Docker (`Ran 3 tests in 0.102s — OK`).
  ## Entry 4 — Server-Side RBAC Permissions, Role Mixins & Access Control Tests
- **Date:** 2026-11-09
- **Task / Issue:** Implement server-side role-based access control utilities (`permissions.py`), `User` role helper properties, and automated access control tests (Student A scope, Issue #9).
- **Prompt Summary:** Asked AI to generate role helper properties on `accounts.User`, function decorators (`role_required`), class-based view mixins (`SecretariatRequiredMixin`, `MemberRequiredMixin`, `EditorRequiredMixin`), and unit tests verifying HTTP 403 responses for unauthorised roles.
- **AI Output:** Provided implementation for `src/accounts/models.py`, `src/accounts/permissions.py`, and `RequestFactory`-based unit tests in `src/accounts/tests.py`.
- **Verification & Human Changes:**
  - Verified that unauthenticated users are redirected to the login page (`HTTP 302`) while authenticated users lacking required roles raise `PermissionDenied` (`HTTP 403`).
  - Confirmed that `member` accounts are strictly blocked from `secretariat` and `editor` views, satisfying Section 5 Acceptance Criteria.
  - Executed `docker compose exec web python manage.py test accounts` and verified all 5 unit tests pass.

## Entry 5 — Authentication Flow, Rate-Limited Login & ADR-0005
- **Date:** 2026-11-11
- **Task / Issue:** Implement registration, email/username login with brute-force rate limiting, logout, password reset flow, templates, unit tests, and ADR-0005 (Student A scope, Issue #10).
- **Prompt Summary:** Asked AI to create `RegistrationForm` and `EmailOrUsernameLoginForm`, implement rate-limited login and auth views, wire URLs and styled templates extending `public_site/base.html`, and write integration tests.
- **AI Output:** Generated `forms.py`, `views.py`, `urls.py`, templates in `src/accounts/templates/accounts/`, `AuthenticationFlowTests` in `src/accounts/tests.py`, and `docs/adr/0005-authentication-and-rbac-security.md`.
- **Verification & Human Changes:**
  - Verified login, registration, and styled form layout in browser at `http://localhost:8000/accounts/login/`.
  - Caught an `AttributeError` (`cleaned_data` missing on unvalidated form when `form.add_error` was called during HTTP 429 lockout) via `test_login_rate_limiting_blocks_brute_force` and fixed it by initializing `form.cleaned_data = {}` in `login_view` without hitting the database.
  - Re-ran `docker compose exec web python manage.py test accounts` and confirmed all 10 unit/integration tests pass.

  ## Entry 6 — Membership Domain Models, Fee Calculator & Frozen Quotes
- **Date:** 2026-11-13
- **Task / Issue:** Implement `membership` models, database-configured placeholder fee rules, frozen quote calculation service, demo seed command, and unit tests (Student A scope, Issue #11).
- **Prompt Summary:** Asked AI to design PostgreSQL models for member profiles, status history, versioned fee rules, frozen quotes, consents, and payments, implement the fee calculator service and `seed_membership_demo` command, and explain Django ORM syntax alongside unit tests.
- **AI Output:** Generated `src/membership/models.py`, `src/membership/admin.py`, `src/membership/services.py`, `seed_membership_demo.py`, and `MembershipModelsAndFeeCalculatorTests` in `src/membership/tests.py`.
- **Verification & Human Changes:**
  - Applied `0001_initial` migration and verified `python manage.py seed_membership_demo` in Docker container.
  - Reviewed ORM model fields, `TextChoices` enums, and foreign key protection rules (`on_delete=models.PROTECT` for `FeeQuote.fee_rule`).
  - Ran `docker compose exec web python manage.py test membership` and verified all 4 unit tests pass, confirming that updating a `FeeRule` does not alter previously stored `FeeQuote` records.



  ## Entry 7 — Articles & News Module
- **Date:** 2026-11-14
- **Context:** Implementing Block 3 (`Category` and `Article` models, public listing with category filtering and pagination, detail view with server-side draft preview protection, and Slovak seed data).
- **Key Prompts & AI Assistance:**
  - Consulted on the optimal database schema structure and field choices for `Category` and `Article` to ensure strict alignment with the project's ER diagram and Student B boundaries.
  - Used AI assistance to draft boilerplate code for Django Admin bulk actions, pagination logic, and Tailwind CSS responsive card layouts (`article_list.html`, `article_detail.html`).
- **Verification, Human Decisions & Independent Work:**
  - Independently designed and structured the database migration workflow, resolved container execution environments, and managed Git branching strategy (`feat/17-articles-and-news`).
  - Personally verified and fine-tuned server-side role-based access control (RBAC) in `article_detail_view` to guarantee that anonymous visitors receive a secure HTTP 404 on drafts, while authorised staff/editors can safely preview them via a distinct warning banner.
  - Hand-crafted realistic Slovak seed data and tailored category descriptions reflecting the authentic domain terminology of the Slovak Hunting Association (Slovenská poľovnícka komora).
  - Wrote, executed, and successfully passed all unit tests (`Ran 8 tests - OK`) covering article visibility, draft security, and category filtering.

  ## Entry 8 — Membership Application Form, Fee Preview, Consent Capture & GDPR Export
- **Date:** 2026-11-16
- **Task / Issue:** Implement web forms, controller views, HTML templates, and integration tests for membership application, fee calculator preview, versioned consent capture, and personal data JSON export (Student A scope, Issue #12).
- **Prompt Summary:** Asked AI to create `FeeCalculatorPreviewForm` and `MembershipApplicationForm` in `forms.py`, implement `views.py` and `urls.py` with atomic transaction handling, build templates under `src/membership/templates/membership/`, troubleshoot `TemplateDoesNotExist` after container restart, and write integration tests.
- **AI Output:** Generated `src/membership/forms.py`, `src/membership/views.py`, `src/membership/urls.py`, 4 HTML templates, and `MembershipApplicationAndExportViewsTests` in `src/membership/tests.py`.
- **Verification & Human Changes:**
  - Restarted Docker `web` service so Django template loader detected the new `src/membership/templates/` directory and manually tested `/membership/calculator/`, `/membership/apply/`, and `/membership/my-application/` in the browser.
  - Ran `docker compose exec web python manage.py test membership` and verified all 8 tests pass (covering licence validation, explicit consent requirement, frozen quote snapshot creation, and JSON data export).

## Entry 9 — Membership Lifecycle Service, Digital Member Card & GDPR Deletion Procedure
- **Date:** 2026-11-17
- **Task / Issue:** Implement membership lifecycle transition service (`applicant`, `active`, `expired`, `suspended`), automatic member ID generator, printable/downloadable HTML digital member card with strictly MVP fields, GDPR deletion procedure notice, and access-control tests (Student A scope, Issue #13).
- **Prompt Summary:** Asked AI to implement `transition_member_status` and `generate_member_number` in `services.py`, create `member_card_view` with owner/secretariat authorization checks and `?download=1` support, build `member_card.html` with print CSS, and write unit/security tests.
- **AI Output:** Updated `src/membership/services.py`, `src/membership/views.py`, `src/membership/urls.py`, `src/membership/templates/membership/`, and added `MembershipLifecycleAndCardTests` in `src/membership/tests.py`.
- **Verification & Human Changes:**
  - Verified `/membership/my-card/` and `/membership/my-application/` in the browser, confirming print styles and HTML download header.
  - Ran `docker compose exec web python manage.py test membership` and confirmed all 11 tests pass, including verification that the digital card excludes private fields (phone, address, licence number) and blocks cross-member access with HTTP 403.
