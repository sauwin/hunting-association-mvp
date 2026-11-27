# API and Endpoint Documentation (Student A: Membership module)

This document describes every HTTP endpoint of the membership module (`src/membership/urls.py`, mounted at
`/membership/`): its parameters, who may call it, and the status codes it returns. The only real JSON API is
the **eligibility API** that Student B's public site consumes; the other endpoints are server-rendered HTML pages
plus two downloads (a JSON export of the member's own data and a CSV member list).

All example responses below were captured from the running application with synthetic demo data
(see [`test-report.md`](test-report.md) for how the behaviour is verified). The shared contract with Student B is
defined in [`contracts.md`](contracts.md); this document must stay consistent with it.

- Base URL in the Docker demo: `http://localhost:8000` (change `WEB_PORT` in `.env` to use another port).
- All data is synthetic and all fee amounts are sample/placeholder values.

---

## 1. Conventions

### 1.1 Authentication

There are no API tokens. Authentication is the normal Django **session cookie** obtained by signing in at
`/accounts/login/`. Every endpoint except `/membership/calculator/` requires a signed-in user.

### 1.2 Roles

Roles are defined in `accounts.User.role` (`member`, `secretariat`, `editor`, `admin`). Role checks run on the server
for every protected action (`accounts/permissions.py`). Administrators and superusers pass every role check.

| Abbreviation used below | Who |
|-------------------------|-----|
| anonymous | not signed in |
| member | any signed-in user (also secretariat/admin) |
| secretariat | role `secretariat` or `admin` (property `can_manage_members`) |

### 1.3 Error behaviour (important difference between JSON and HTML endpoints)

| Situation | JSON API (`/membership/api/eligibility/`) | HTML pages and downloads |
|-----------|-------------------------------------------|--------------------------|
| Not signed in | `401` + `{"error": "Authentication required."}` | `302` redirect to `/accounts/login/?next=<original path>` |
| Signed in, role not sufficient | `403` + `{"error": "..."}` | `403` Forbidden page |
| Unknown object id | n/a | `404` Not Found page |
| Wrong HTTP method | `405` + `{"error": "Method not allowed."}` | `405` (only on POST-only endpoints) |
| Invalid input | `400` + `{"error": "..."}` | form pages are shown again with status `200` and field errors (no `400`) |

### 1.4 Status codes used by the module

| Code | Meaning in this module |
|------|------------------------|
| `200` | Request succeeded (also: a form page re-rendered with validation errors) |
| `302` | Redirect after a successful form submission, or anonymous user sent to the sign-in page |
| `400` | Eligibility API only: `date` is not a valid `YYYY-MM-DD` date |
| `401` | Eligibility API only: no signed-in user |
| `403` | Signed in, but the role or ownership check failed |
| `404` | Member profile or payment record with the given id does not exist |
| `405` | Method not allowed (non-GET on the eligibility API; non-POST on the payment status endpoint) |

---

## 2. Endpoint overview

| Method | Path | Name (`membership:`) | Access | Response |
|--------|------|----------------------|--------|----------|
| GET | `/membership/calculator/` | `fee_calculator` | everyone | HTML |
| GET, POST | `/membership/apply/` | `apply` | member | HTML (POST: `302` to my-application) |
| GET | `/membership/my-application/` | `application_overview` | member | HTML |
| GET | `/membership/my-card/` | `my_card` | member | HTML card |
| GET | `/membership/cards/<member_id>/` | `member_card_detail` | owner or secretariat | HTML card |
| GET | `/membership/export-data/` | `export_my_data` | member (own data only) | JSON download |
| GET | `/membership/api/eligibility/` | `eligibility_api` | member (secretariat for other members) | JSON |
| GET | `/membership/backoffice/` | `backoffice_member_list` | secretariat | HTML |
| GET, POST | `/membership/backoffice/members/quick-add/` | `backoffice_quick_add` | secretariat | HTML (POST: `302` to member detail) |
| GET, POST | `/membership/backoffice/members/<member_id>/` | `backoffice_member_detail` | secretariat | HTML (POST: `302` back) |
| POST | `/membership/backoffice/payments/<payment_id>/status/` | `backoffice_update_payment_status` | secretariat | `302` to member detail |
| GET | `/membership/backoffice/export-csv/` | `backoffice_export_csv` | secretariat | CSV download |

---

## 3. Eligibility API (contract with Student B)

`GET /membership/api/eligibility/`

Tells whether a member is active on a given date and whether their hunting licence and insurance are valid on that date.
The same logic is available in-process as `membership.services.check_eligibility(user_or_email, target_date)`;
the endpoint is a thin wrapper around it.

### 3.1 Query parameters

| Parameter | Required | Format | Meaning |
|-----------|----------|--------|---------|
| `date` | no | `YYYY-MM-DD` | Target date. Defaults to today (server local date). |
| `user` | no | username, e-mail address or member number | Member to check. Case-insensitive. |
| `email` | no | same as `user` | Alias of `user`. If both are sent, `user` wins. |

Without `user`/`email` the signed-in user is checked.

### 3.2 Who may check whom

| Caller | May check |
|--------|-----------|
| member | only themselves: no identifier, or an identifier equal to their own username, e-mail or member number |
| secretariat / admin | any member |

### 3.3 Response body (`200`, `application/json`)

| Field | Type | Rule |
|-------|------|------|
| `active` | boolean | `true` if status is `active` and `valid_from <= date <= valid_until` (a missing `valid_from` counts as "from the beginning") |
| `licenceValid` | boolean | `true` if the profile's `licence_valid_until` is set and `>= date` |
| `insuranceValid` | boolean | `true` if `insurance_valid_until` is set and `>= date` |
| `validUntil` | string or `null` | Membership expiry as `YYYY-MM-DD`; `null` if the profile has none or does not exist |

An unknown identifier, or a user without a membership profile, returns `200` with `active`, `licenceValid` and
`insuranceValid` set to `false` and `validUntil` set to `null`. This is deliberate: the endpoint does not reveal
whether a member exists. The `licenceValid`/`insuranceValid` flags are independent of `active`: an applicant who
entered a valid licence gets `licenceValid: true` with `active: false`.

> Naming note: `contracts.md` calls the licence field `hunting_licence_valid_until`; the model field is
> `licence_valid_until`. The JSON field names of the API (`active`, `licenceValid`, `insuranceValid`, `validUntil`)
> are exactly the ones in the contract.

### 3.4 Status codes

| Code | When | Body |
|------|------|------|
| `200` | Check performed | the four fields above |
| `400` | `date` present but not an ISO date (e.g. `15-06-2026`) | `{"error": "Invalid date format. Expected YYYY-MM-DD."}` |
| `401` | not signed in | `{"error": "Authentication required."}` |
| `403` | a member asks about someone else | `{"error": "You do not have permission to check another member's eligibility."}` |
| `405` | any method other than `GET` | `{"error": "Method not allowed."}` |

There is no `404`: an unknown member is a normal `200` answer (see above).

### 3.5 Examples

Synthetic data used: `hunter1` (hunter, status `active`, valid `2026-01-01` to `2026-12-31`, licence valid until
`2027-03-31`, insurance valid until `2026-12-31`, member number `HA-2026-0001`), `friend1` (non-hunter, active, no licence),
`applicant1` (status `applicant`, licence valid until `2027-03-31`).

Sign in first and keep the session cookie (shown here with `curl`; the sign-in form needs a CSRF token, so in practice
use a browser or the Django test client; the examples show requests with an already authenticated session):

```bash
curl -s -b cookies.txt "http://localhost:8000/membership/api/eligibility/?date=2026-06-15"
```

| # | Caller | Request (query string) | Status | Response body |
|---|--------|------------------------|--------|---------------|
| 1 | hunter1 | `?date=2026-06-15` | 200 | `{"active": true, "licenceValid": true, "insuranceValid": true, "validUntil": "2026-12-31"}` |
| 2 | hunter1 | `?date=2027-02-01` (after expiry) | 200 | `{"active": false, "licenceValid": true, "insuranceValid": false, "validUntil": "2026-12-31"}` |
| 3 | hunter1 | `?user=hunter1&date=2026-06-15` (own username) | 200 | same as #1 |
| 4 | secretariat | `?email=friend1@example.test&date=2026-06-15` | 200 | `{"active": true, "licenceValid": false, "insuranceValid": false, "validUntil": "2026-12-31"}` |
| 5 | secretariat | `?user=applicant1&date=2026-06-15` | 200 | `{"active": false, "licenceValid": true, "insuranceValid": false, "validUntil": null}` |
| 6 | secretariat | `?user=HA-2026-0001&date=2026-06-15` (member number) | 200 | same as #1 |
| 7 | secretariat | `?user=nobody&date=2026-06-15` | 200 | `{"active": false, "licenceValid": false, "insuranceValid": false, "validUntil": null}` |
| 8 | hunter1 | `?user=friend1` (someone else) | 403 | `{"error": "You do not have permission to check another member's eligibility."}` |
| 9 | hunter1 | `?date=15-06-2026` | 400 | `{"error": "Invalid date format. Expected YYYY-MM-DD."}` |
| 10 | anonymous | (any) | 401 | `{"error": "Authentication required."}` |
| 11 | hunter1 | `POST` (any) | 405 | `{"error": "Method not allowed."}` |

Examples 1, 5 and 7 correspond to the three synthetic examples in `contracts.md`; they are covered by the contract
tests in `membership.tests.EligibilityContractTests`.

---

## 4. Member self-service endpoints

### 4.1 `GET /membership/calculator/` (everyone)

Indicative fee calculator, no sign-in needed. It never stores anything.

| Query parameter | Values | Default |
|-----------------|--------|---------|
| `member_type` | `hunter`, `non_hunter` | `hunter` |
| `include_insurance` | `on` (checkbox) | off |
| `apply_reduced_rate` | `on` (checkbox) | off |

Returns `200` HTML with the breakdown for the active fee rule (sample tariff `2026-v1-sample`: hunter 60.00, non-hunter
35.00, insurance add-on 25.00, reduced-rate discount 15.00, EUR). Invalid parameters give `200` with form errors and the
default breakdown. Example: `?member_type=hunter&include_insurance=on&apply_reduced_rate=on` shows a total of `70.00 EUR`.

### 4.2 `GET`/`POST /membership/apply/` (signed-in)

Membership application. `POST` fields:

| Field | Required | Notes |
|-------|----------|-------|
| `first_name`, `last_name` | yes | copied to the user account |
| `member_type` | yes | `hunter` or `non_hunter` |
| `phone`, `street_address`, `city`, `postal_code` | yes | |
| `hunting_licence_number` | when a licence expiry date is given | |
| `licence_valid_until`, `insurance_valid_until` | no | `YYYY-MM-DD` |
| `include_insurance`, `apply_reduced_rate` | no | checkboxes that feed the fee quote |
| `consent_accepted` | yes | explicit, versioned consent |

| Result | Status |
|--------|--------|
| Valid: profile (status `applicant`), consent record, status-history entry and a **frozen fee quote** are created | `302` to `/membership/my-application/` |
| Missing consent, missing licence number, etc. | `200`, form shown again with errors, nothing saved |
| Not signed in | `302` to sign-in |

Submitting the form again (for an existing profile) updates the profile and creates one more consent record and one more frozen quote; earlier quotes are never changed.

### 4.3 `GET /membership/my-application/` (signed-in)

Own status, member number, validity, frozen quotes, status history, consents and the data-deletion procedure.
`200` HTML. Without an application the page shows a link to the application form instead.

### 4.4 `GET /membership/my-card/` and `GET /membership/cards/<member_id>/`

Digital member card with only the MVP fields (member ID, name, status, valid until).

| Request | Result |
|---------|--------|
| `/my-card/` with a profile | `200` HTML |
| `/my-card/` without a profile | `302` to `/membership/apply/` with an info message |
| `/cards/<id>/` own profile, or secretariat | `200` HTML |
| `/cards/<id>/` another member's profile, as a member | `403` |
| `/cards/<id>/` unknown id | `404` |
| not signed in | `302` to sign-in |

Add `?download=1` to receive the card as a downloadable HTML file (`member_card_<username>.html`).

### 4.5 `GET /membership/export-data/` (signed-in; GDPR self-service)

Downloads all data stored about the signed-in user as JSON (`Content-Disposition: attachment;
filename="membership_data_<username>.json"`). Always `200` for a signed-in user, even without a profile
(then `member_profile` is `null`). Anonymous: `302` to sign-in.

Top-level keys of the JSON object:

```json
{
  "exported_at": "2026-11-27T13:05:11.123456+00:00",
  "notice": "SYNTHETIC DEMO DATA EXPORT — Hunting Association MVP",
  "deletion_request_procedure": "…text of the documented deletion procedure…",
  "account": {"username": "…", "email": "…", "first_name": "…", "last_name": "…", "role": "member", "date_joined": "…"},
  "member_profile": {"member_number": "HA-2026-0001", "member_type": "hunter", "status": "active", "phone": "…",
                     "street_address": "…", "city": "…", "postal_code": "…", "hunting_licence_number": "…",
                     "licence_valid_until": "2027-03-31", "insurance_valid_until": "2026-12-31",
                     "valid_from": "2026-01-01", "valid_until": "2026-12-31"},
  "fee_quotes": [],
  "consents": [],
  "status_history": [],
  "payments": []
}
```

The user can only ever export their own data; there is no id parameter.

---

## 5. Secretariat back office

All endpoints below need role `secretariat` or `admin`. Anonymous users get `302` to sign-in, a signed-in member gets `403`.

### 5.1 `GET /membership/backoffice/`: member directory

| Query parameter | Values | Meaning |
|-----------------|--------|---------|
| `q` | text | case-insensitive search in member number, username, e-mail, first/last name, city, phone |
| `status` | `applicant`, `active`, `expired`, `suspended` | filter by lifecycle status (unknown values are ignored) |
| `member_type` | `hunter`, `non_hunter` | filter by category (unknown values are ignored) |
| `page` | integer | pagination |

### 5.2 `GET`/`POST /membership/backoffice/members/quick-add/`

Creates a synthetic member (account with an unusable password, profile, initial status history and a frozen quote) in one step.
Required `POST` fields: `username`, `email`, `first_name`, `last_name`, `member_type`, `status`, `phone`, `street_address`,
`city`, `postal_code`. Optional: `hunting_licence_number`, `licence_valid_until`, `insurance_valid_until`, `valid_from`,
`valid_until`, `include_insurance`, `apply_reduced_rate`. Success: `302` to the member's detail page; invalid input: `200` with errors.

### 5.3 `GET`/`POST /membership/backoffice/members/<member_id>/`

Member detail. Unknown id: `404`. `POST` needs a hidden field `action`:

| `action` | Other fields | Effect |
|----------|--------------|--------|
| `update_status` | `status`, `valid_from`, `valid_until`, `note` | lifecycle transition; a member number is generated on first approval; history entry written |
| `record_payment` | `status`, `amount`, `currency`, `reference`, `payment_date`, `quote`, `notes` | creates a manual payment record attributed to the staff user |

Both return `302` back to the detail page on success and `200` with form errors otherwise.
Payment `status` values: `pending`, `paid`, `overdue`, `cancelled`. There is **no live payment provider**.

### 5.4 `POST /membership/backoffice/payments/<payment_id>/status/`

Changes the status of an existing payment (`status` = one of the four values). Only `POST` is accepted (`GET` gives `405`).
Setting `paid` fills an empty payment date. Always `302` to the member's detail page; an invalid status value does not change
anything and shows the message "Invalid payment status selected." Unknown payment id: `404`.

### 5.5 `GET /membership/backoffice/export-csv/`

Exports the member list as CSV, honouring the same `q`, `status` and `member_type` filters as the directory
(`Content-Type: text/csv; charset=utf-8`, `Content-Disposition: attachment; filename="members_export.csv"`).

Columns: `member_number, username, first_name, last_name, email, member_type, status, valid_from, valid_until, phone, city,
licence_valid_until, insurance_valid_until, latest_payment_status`.

Example for `?status=active&q=hunter`:

```csv
member_number,username,first_name,last_name,email,member_type,status,valid_from,valid_until,phone,city,licence_valid_until,insurance_valid_until,latest_payment_status
HA-2026-0001,hunter1,Hunter1,Demo,hunter1@example.test,hunter,active,2026-01-01,2026-12-31,+421900000000,Nitra,2027-03-31,2026-12-31,
```

---

## 6. Sample flows

### 6.1 Applicant becomes an eligible member

1. Visitor opens `/membership/calculator/` → `200` (indicative fee).
2. Visitor registers at `/accounts/register/` (`302`, now signed in) and submits `/membership/apply/` → `302` to
   `/membership/my-application/`; status **Applicant**, a frozen quote is shown.
3. Eligibility for this user now returns `{"active": false, …, "validUntil": null}` (applicant).
4. Secretariat opens the member in `/membership/backoffice/members/<id>/`, posts `update_status` with
   status `active`, `valid_from=2026-01-01`, `valid_until=2026-12-31` → `302`; a member number such as `HA-2026-0001` is assigned.
5. Secretariat records a payment (`record_payment`, status `paid`) → `302`.
6. Eligibility for `2026-06-15` now returns `{"active": true, …, "validUntil": "2026-12-31"}`; the member card shows status **Active**.

### 6.2 Secretariat handles a payment and exports the list

1. `GET /membership/backoffice/?status=active` → `200`, list of active members.
2. Open a member, `record_payment` with status `pending`, amount `70.00`, currency `EUR`, reference `REF-1` → `302`.
3. `POST /membership/backoffice/payments/<id>/status/` with `status=paid` → `302`; message "Payment #<id> updated to Paid."
4. `GET /membership/backoffice/export-csv/?status=active` → `200`, CSV file with the latest payment status in the last column.

### 6.3 A member tries to reach staff functions (must fail)

| Request as a member | Result |
|---------------------|--------|
| `GET /membership/backoffice/` | `403` |
| `GET /membership/backoffice/export-csv/` | `403` |
| `POST /membership/backoffice/payments/1/status/` | `403` |
| `GET /membership/cards/<someone else's id>/` | `403` |
| `GET /membership/api/eligibility/?user=<someone else>` | `403` JSON |

---

## 7. Not covered / limits of this MVP

- No OpenAPI schema file: this Markdown document is the API documentation ("OpenAPI or equivalent" in the assignment).
- No API tokens, CORS, rate limiting or pagination on the JSON API; the eligibility endpoint relies on the session cookie.
  Login attempts are rate-limited (by default 5 failed attempts per 5 minutes per IP and account identifier; settings `LOGIN_RATE_LIMIT_ATTEMPTS` / `LOGIN_RATE_LIMIT_TIMEOUT`).
- Notifications (`common.notifications.send`) are a shared in-process function, not an HTTP endpoint; see `contracts.md`.
- Student B's public-site endpoints are documented by Student B.
