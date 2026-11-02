# ADR 0001: Technology Stack, Containerization, and Modular App Structure

- **Status:** Accepted
- **Date:** 2026-11-02
- **Deciders:** Student A (Maksym Druziuk), Student B

## Context
Both students are building a shared MVP for the Hunting Association within a 150-hour limit per student: Student A owns the Membership & Member Portal, and Student B owns the Public Website & Member Acquisition module. Both modules must run in a single repository with PostgreSQL, avoid code conflicts between students, and start cleanly in under 15 minutes.

## Decision
1. **Backend & Database:** Use Python 3.12 with Django 5.x and PostgreSQL 16 as the primary relational database.
2. **Containerization:** Use Docker and Docker Compose (`web` and `db` services with healthchecks) and manage all secrets via environment variables (`.env`).
3. **Modular Django Apps:** Split the codebase inside `src/` into isolated Django apps:
   - `accounts`: Custom User model and authentication (owned by Student A).
   - `membership`: Member profiles, applications, fee calculator, payments, and eligibility API (owned by Student A).
   - `public_site`: Public pages, articles, regional representatives, and enquiry forms (owned by Student B).
   - `common`: Shared templates, navigation, and notification interface stub.

## Consequences
- **Positive:** Identical environment on Windows/Linux/macOS; reproducible setup via `docker compose up` in under 15 minutes; strict module boundaries prevent merge conflicts between Student A and Student B.
- **Negative:** Requires Docker Desktop running locally and minor overhead managing container builds.