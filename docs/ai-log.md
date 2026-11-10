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
