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

  ## Entry 2 — Initial Discovery, Content Model & ADR Structuring
* **Date:** 2026-11-02
* **Task / Issue:** Initial project discovery, database schema design for Student B scope, and ADR templates.
* **Prompt Summary:** Asked AI to help structure the database models (`Category`, `Article`, `RegionalRepresentative`, `VolunteerEnquiry`, `MembershipEnquiry`, `FAQ`) based on the MVP requirements, ensuring no overlap with Student A's User/Membership models.
* **AI Output:** Suggested Django model fields, data types, status enums, and Mermaid ER diagram syntax.
* **Verification & Human Changes:** 
  - Verified every field against Section 2 ("In scope — MUST deliver") and Section 6 ("Coordination with Student A").
  - Confirmed that `Article.author` uses a simple `CharField` (`author_byline`) rather than creating a separate `User` model, avoiding conflict with Student A's authentication system.
  - Added explicit `consent_given` and `consent_timestamp` fields on enquiry models to meet privacy/GDPR requirements.