# ADR 0005: Session Authentication, Login Rate Limiting, and Server-Side RBAC

## Status
Accepted

## Context
Both Student A (Membership Portal & Secretariat Back Office) and Student B (Public Website & Editorial Administration) require reliable authentication, password hashing, CSRF protection, login rate limiting, and server-side role enforcement without external identity providers.

## Decision
1. **Framework Authentication & Password Hashing:** We use Django's built-in session authentication (`django.contrib.auth`) and PBKDF2 password hashing, supporting both email and username login via `EmailOrUsernameLoginForm`.
2. **Cache-Based Login Rate Limiting:** To mitigate credential brute-force attacks without adding external infrastructure dependencies, `login_view` tracks failed attempts per `(client IP, normalized identifier)` SHA-256 key in Django's cache and returns `HTTP 429 Too Many Requests` once `LOGIN_RATE_LIMIT_ATTEMPTS` is reached.
3. **Server-Side RBAC Enforcement:** Every protected view validates user roles on the server via `role_required` decorators or `RoleRequiredMixin` subclasses (`MemberRequiredMixin`, `SecretariatRequiredMixin`, `EditorRequiredMixin`), raising `PermissionDenied` (`HTTP 403`) for unauthorized roles.

## Consequences
- **Positive:** Zero third-party auth dependencies; satisfies OWASP Top 10 baseline (broken access control, identification/authentication failures); shared seamlessly between Student A and Student B modules.
- **Negative / Limitations:** Default local memory cache resets on container restart, which is acceptable for the single-container MVP demo environment.