# ADR 0002: Custom User Model and Unified Role-Based Access Control

- **Status:** Accepted
- **Date:** 2026-11-02
- **Deciders:** Student A (Maksym Druziuk), Student B

## Context
The project rules prohibit Student B from creating a competing User or membership model. Meanwhile, the system requires distinct server-side permissions across both modules: prospective/active members accessing their portal, secretariat staff managing applications and payments, editors publishing news and managing regional representatives, and administrators overseeing the system.

## Decision
Implement a custom `User` model (`accounts.User` inheriting from `AbstractUser`) prior to the initial database migration, configured via `AUTH_USER_MODEL = 'accounts.User'`:
- Enforce unique email addresses (`email = models.EmailField(unique=True)`).
- Define an explicit `role` field using `TextChoices` with four unified roles:
  - `member`: Default role for registered applicants and members (Student A scope).
  - `secretariat`: Staff role for reviewing applications, recording manual payments, and exporting CSVs (Student A scope).
  - `editor`: Staff role for managing public articles, representatives, and enquiries (Student B scope).
  - `admin`: Full administrative access across both modules.

## Consequences
- **Positive:** Single source of truth for authentication; prevents duplicate user tables; simplifies server-side role checks across both students' views.
- **Negative:** Requires all authentication forms and admin configurations to reference `AUTH_USER_MODEL` (`get_user_model()`) instead of Django's default `User`.