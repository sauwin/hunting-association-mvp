# Manual Test Checklist (Student A: Membership module)

Step-by-step checks for everything that the [automated tests](test-report.md) cannot fully prove: the real browser flow,
the shared layout and navigation, file downloads and the management command. The expected behaviour of every endpoint is
described in [`api.md`](api.md). All data is synthetic; never type real personal data.

**How to use:** work through the sections in order (later sections reuse data created earlier). Mark each step in the last
column (`[x]` = passed, `[!]` = failed, with a note) and fill in the sign-off block at the end. The expected values below
were replayed against the application code with the Django test client on 2026-11-27 (see the test report); the
browser-only parts (layout, downloads, print preview, mobile view) are checked by hand and have not been automated.

**Test accounts used below (they are created in the steps):**

| Account | Role | Created in |
|---------|------|------------|
| `admin1` / any strong password | superuser; acts as the secretariat (`can_manage_members` is true for superusers) | step 0.3 |
| `member.demo`, e-mail `member.demo@example.test`, password `Demo-Pass-2026!x` | member | step 1.2 |
| `friend.demo`, e-mail `friend.demo@example.test` | member without an application (second person, for the access-control checks) | step 10.1 |

**Good to know before you start**

- Member numbers look like `HA-<current year>-<database id of the member, 4 digits>`. After a clean start the first
  approved member gets `HA-2026-0001` in 2026 (the year part follows the date you run the test). Wherever this checklist
  writes `HA-2026-0001`, use the number the application actually shows.
- A superuser created with `createsuperuser` keeps the role label *Member* in the account menu; the back-office entry is
  still shown and the back office works because the superuser flag grants access.
- `docker compose exec` prints e-mails straight into your terminal (console e-mail backend); e-mails produced by the web
  server (password reset) appear in `docker compose logs web`. Nothing is ever sent to a real mailbox.

---

## 0. Clean start

| # | Step | Expected result | Result |
|---|------|-----------------|--------|
| 0.1 | `docker compose down -v`, then `docker compose up --build -d`, then `docker compose logs web` | the log contains `[entrypoint] Applying database migrations...`, `[entrypoint] Loading synthetic demo data (idempotent)...` and the Django development server start | [ ] |
| 0.2 | Open <http://localhost:8000/> | public home page (Student B's site) loads | [ ] |
| 0.3 | `docker compose exec web python manage.py createsuperuser` (username `admin1`, e-mail `admin1@example.test`) | superuser created | [ ] |
| 0.4 | `docker compose exec web python manage.py test` | `Ran 54 tests …` and `OK` | [ ] |

## 1. Registration and sign-in

| # | Step | Expected result | Result |
|---|------|-----------------|--------|
| 1.1 | Open `/accounts/login/` | sign-in form (e-mail or username + password); links to registration and to password reset | [ ] |
| 1.2 | Register at `/accounts/register/`: username `member.demo`, e-mail `member.demo@example.test`, first name `Mia`, last name `Demo`, password `Demo-Pass-2026!x` (twice) | message "Account registered successfully."; you are signed in and the dashboard says "Welcome, Mia" | [ ] |
| 1.3 | Sign out, open the registration form again and submit it with an invalid e-mail and two different passwords | form shown again with field errors; no account created | [ ] |
| 1.4 | Register again with the already used e-mail `member.demo@example.test` (new username) | error "A user with this email address already exists." | [ ] |
| 1.5 | Sign in with the **e-mail** address, sign out, then sign in with the **username** | both sign-ins work | [ ] |
| 1.6 | On the sign-in page enter a wrong password 6 times for the identifier `locktest` (it does not have to exist) | attempts 1–5 show the normal error; attempt 6 returns the page with "Too many failed login attempts. Please wait a few minutes and try again." (HTTP 429). The counter is per identifier, so `member.demo` is not locked. It resets after 5 minutes or after `docker compose restart web` | [ ] |
| 1.7 | Open `/accounts/password-reset/`, enter `member.demo@example.test`, press *Send Reset Link* | the "Reset Email Sent" page appears; the reset e-mail with a link `/accounts/reset/<uid>/<token>/` is printed in `docker compose logs web` | [ ] |
| 1.8 | Open that link in the browser and set a new password, then sign in with it | the confirmation page appears and the new password works (use it from here on) | [ ] |

## 2. Fee calculator (no sign-in needed)

| # | Step | Expected result | Result |
|---|------|-----------------|--------|
| 2.1 | Signed out, open `/membership/calculator/` | page loads; amber label "SAMPLE / PLACEHOLDER FEE QUOTE — Subject to association approval"; Tariff Rule Version `2026-v1-sample`; Base Annual Fee 60.00 EUR; Total Indicative Amount 60.00 EUR | [ ] |
| 2.2 | Choose *Non-Hunter*, press *Calculate Fee Breakdown* | Base Annual Fee 35.00 EUR, total 35.00 EUR | [ ] |
| 2.3 | *Hunter* + the insurance add-on checkbox, calculate | Insurance Add-On 25.00 EUR, total **85.00 EUR** | [ ] |
| 2.4 | *Hunter* + insurance + the reduced-fee checkbox, calculate | Reduced-Rate Discount − 15.00 EUR, total **70.00 EUR** | [ ] |
| 2.5 | Click *Proceed to Membership Application* while signed out | redirected to the sign-in page; after signing in you arrive at the application form | [ ] |

## 3. Application and frozen quotes

| # | Step | Expected result | Result |
|---|------|-----------------|--------|
| 3.1 | Signed in as `member.demo`, open `/membership/apply/` | form with first/last name, category, phone, address, licence number and dates, insurance date, the two add-on checkboxes and the consent checkbox | [ ] |
| 3.2 | Fill in the form but leave the consent checkbox empty, submit | form shown again with "This field is required." at the consent; nothing saved | [ ] |
| 3.3 | Enter a licence expiry date but leave the licence number empty (consent ticked), submit | error "Please provide a hunting licence number when specifying a licence expiry date." | [ ] |
| 3.4 | Fill in: Hunter, phone `+421900111222`, street `Lesna 1`, city `Nitra`, postal code `94901`, licence number `SK-DEMO-1`, licence valid until `2027-03-31`, insurance valid until `2026-12-31`, insurance add-on ticked, consent ticked; submit | redirect to *My membership* with the message "Application saved and frozen fee quote #1 (85.00 EUR) generated."; status **Applicant**; member number "Pending secretariat approval" | [ ] |
| 3.5 | On *My membership* look at "Frozen Fee Quotes", the consent block and the status history | one frozen quote: rule version `2026-v1-sample`, base 60.00, insurance 25.00, total 85.00 EUR, "SAMPLE / PLACEHOLDER" label; one consent with version `2026-v1-demo`; history entry "Initial membership application submitted." | [ ] |
| 3.6 | As `admin1` (private window) open `/admin/membership/feerule/`, edit `2026-v1-sample`: hunter base fee 60.00 → 65.00, save | saved | [ ] |
| 3.7 | As `member.demo` reload *My membership* | the existing quote is **unchanged** (base 60.00, total 85.00 EUR) | [ ] |
| 3.8 | As `member.demo` submit the application form again with the same data | message "… frozen fee quote #2 (90.00 EUR) generated."; the second quote has base 65.00 and total 90.00 EUR; quote #1 is still 60.00 / 85.00; there are now two consent records | [ ] |
| 3.9 | In the admin set the hunter base fee back to 60.00 (or run `docker compose restart web`, the seed command resets the sample rule) | tariff back to the sample value | [ ] |

## 4. Digital member card

| # | Step | Expected result | Result |
|---|------|-----------------|--------|
| 4.1 | As `member.demo` click *View / Print Digital Member Card* on *My membership* (or open `/membership/my-card/`) | card shows only: member ID ("PENDING-APPROVAL" until approved), full name, membership status, valid until; "SAMPLE / MVP" tag; no address, phone or licence data | [ ] |
| 4.2 | Click *Download HTML Card* | file `member_card_member.demo.html` is downloaded and opens offline with the same four fields | [ ] |
| 4.3 | Click *Print / Save as PDF* | the print preview shows the card without the buttons | [ ] |
| 4.4 | Sign in as a user **without** an application and open `/membership/my-card/` (done in step 10.1 with `friend.demo`) | redirected to the application form with the message "Please submit a membership application before accessing your digital member card." | [ ] |

## 5. GDPR data export and deletion procedure

| # | Step | Expected result | Result |
|---|------|-----------------|--------|
| 5.1 | As `member.demo` click *Download my data (JSON)* on *My membership* | file `membership_data_member.demo.json` is downloaded | [ ] |
| 5.2 | Open the file | top-level keys `exported_at`, `notice`, `deletion_request_procedure`, `account`, `member_profile`, `fee_quotes` (2 entries), `consents` (2 entries), `status_history`, `payments`; only this member's data, no password | [ ] |
| 5.3 | On *My membership* read the block "How Personal Data Deletion Requests Are Handled (MVP Documentation)" | the procedure is described and is marked as sample text, with no claim of legal compliance | [ ] |

## 6. Secretariat back office: approval and validity

| # | Step | Expected result | Result |
|---|------|-----------------|--------|
| 6.1 | Sign in as `admin1`, open `/membership/backoffice/` | member directory (columns Member ID, Name & Account, Category, Status, Valid Until, Latest Payment, Actions); `member.demo` is listed as *Applicant* | [ ] |
| 6.2 | Search for `member.demo`, then filter by status *Applicant* and category *Hunter*; press *Reset* | the list narrows to that member; *Reset* clears the filters | [ ] |
| 6.3 | Click the member's *Manage* action | detail page with profile data, the status form, the payment form, payments, frozen quotes and status history | [ ] |
| 6.4 | In "Approve / Update Lifecycle Status" choose *Active*, valid from `2026-01-01`, valid until `2026-12-31`, note `Approved after document check`, press *Save Status & Validity Dates* | message "Membership status updated to 'Active' (Member ID: HA-2026-0001)."; status Active; the history shows "applicant → active" with your note | [ ] |
| 6.5 | Click *View Digital Card* | the card shows the member number and status Active; the back link is "Back to member detail" and returns to the detail page | [ ] |
| 6.6 | Click *+ Quick-Add Member* and create `quick.demo`: e-mail `quick.demo@example.test`, first name `Quick`, last name `Demo`, *Non-Hunter*, status *Applicant*, phone `+421900333444`, street `Hlavna 2`, city `Zilina`, postal code `01001` (the other fields stay empty) | message "Member 'quick.demo' created with status 'Applicant'."; redirect to the new member's detail page; history entry "Quick-added by secretariat." and a frozen quote of 35.00 EUR exist. The account has no usable password (it cannot sign in) | [ ] |
| 6.7 | Submit the quick-add form again with the same username and e-mail | errors "A user with this username already exists." and "A user with this email address already exists."; no duplicate created | [ ] |

## 7. Manual payments

Use the detail page of `member.demo`.

| # | Step | Expected result | Result |
|---|------|-----------------|--------|
| 7.1 | In the payment form choose status *Pending*, amount `70.00` (the form pre-fills the latest quote total, overwrite it), currency `EUR`, reference `REF-1`, press the save button | message "Recorded pending payment of 70.00 EUR (Ref: REF-1)."; the "Payment Audit Trail" shows the row with *Recorded By* `admin1` | [ ] |
| 7.2 | Change that row's status to *Paid* with the select and press its update button | message "Payment #1 updated to Paid."; the payment date shows today's date | [ ] |
| 7.3 | Change it to *Overdue*, then to *Cancelled* | each change is accepted ("Payment #1 updated to Overdue." / "… to Cancelled.") | [ ] |
| 7.4 | Submit the payment form with amount `0` | error "Payment amount must be greater than zero."; nothing recorded | [ ] |
| 7.5 | Open the directory again | the *Latest Payment* column of `member.demo` shows the newest payment status | [ ] |
| 7.6 | Look for any card form, payment gateway or redirect to an external payment provider | none exists (payments are recorded manually only) | [ ] |

## 8. CSV export

| # | Step | Expected result | Result |
|---|------|-----------------|--------|
| 8.1 | In the directory click *Export Filtered CSV* with no filter | file `members_export.csv` downloads with a header row and one row per member (`member.demo` and `quick.demo`) | [ ] |
| 8.2 | Filter by status *Active*, then export again | only active members (`member.demo`) are in the file | [ ] |
| 8.3 | Open the file | 14 columns: `member_number, username, first_name, last_name, email, member_type, status, valid_from, valid_until, phone, city, licence_valid_until, insurance_valid_until, latest_payment_status`; for `member.demo` the member number is `HA-2026-0001` and `latest_payment_status` is `cancelled` (after step 7.3). The file is UTF-8; if diacritics look wrong in Excel, import it via *Data → From Text/CSV* and pick UTF-8 | [ ] |

## 9. Eligibility check

Stay signed in as `admin1` and open these URLs in the same browser (the JSON is shown in the page).

| # | URL (after `http://localhost:8000`) | Expected result | Result |
|---|-------------------------------------|-----------------|--------|
| 9.1 | `/membership/api/eligibility/?user=member.demo&date=2026-06-15` | 200 `{"active": true, "licenceValid": true, "insuranceValid": true, "validUntil": "2026-12-31"}` | [ ] |
| 9.2 | `/membership/api/eligibility/?user=member.demo&date=2027-02-01` | 200 `{"active": false, "licenceValid": true, "insuranceValid": false, "validUntil": "2026-12-31"}` | [ ] |
| 9.3 | `/membership/api/eligibility/?email=member.demo@example.test&date=2026-06-15` | same as 9.1 (lookup by e-mail) | [ ] |
| 9.4 | `/membership/api/eligibility/?user=HA-2026-0001&date=2026-06-15` | same as 9.1 (lookup by member number; use the number from step 6.4) | [ ] |
| 9.5 | `/membership/api/eligibility/?user=quick.demo&date=2026-06-15` | 200 all three flags `false`, `validUntil: null` (applicant without validity dates) | [ ] |
| 9.6 | `/membership/api/eligibility/?user=nobody&date=2026-06-15` | 200 all three flags `false`, `validUntil: null` (unknown member, no 404 by contract) | [ ] |
| 9.7 | `/membership/api/eligibility/?date=15-06-2026` | 400 `{"error": "Invalid date format. Expected YYYY-MM-DD."}` | [ ] |
| 9.8 | In a private window that is not signed in, open `/membership/api/eligibility/` | 401 `{"error": "Authentication required."}` | [ ] |
| 9.9 | As `member.demo` (sign in in the private window) open `/membership/api/eligibility/?date=2026-06-15` without `user` | 200 with the member's own result (same as 9.1) | [ ] |

## 10. Access control (negative tests)

| # | Step | Expected result | Result |
|---|------|-----------------|--------|
| 10.1 | In a private window register `friend.demo` (e-mail `friend.demo@example.test`, any names) and open `/membership/my-card/` | the dashboard shows no back-office entry in the account menu; `/membership/my-card/` redirects to the application form with an information message (step 4.4) | [ ] |
| 10.2 | As `friend.demo` open `/membership/backoffice/` | **403 Forbidden** | [ ] |
| 10.3 | As `friend.demo` open `/membership/backoffice/export-csv/` | **403 Forbidden** | [ ] |
| 10.4 | As `friend.demo` open `/membership/cards/1/` (`member.demo`'s card; use the id from the member's *Manage* URL) | **403 Forbidden** | [ ] |
| 10.5 | As `friend.demo` open `/membership/api/eligibility/?user=member.demo` | 403 `{"error": "You do not have permission to check another member's eligibility."}` | [ ] |
| 10.6 | As `friend.demo` open `/membership/export-data/` | downloads only `friend.demo`'s own data: `member_profile` is `null`, no quotes or payments | [ ] |
| 10.7 | Signed out, open `/membership/my-application/` | redirected to `/accounts/login/?next=/membership/my-application/` | [ ] |
| 10.8 | As `admin1` open `/membership/cards/999/` and `/membership/backoffice/members/999/` | **404 Not Found** for both | [ ] |

## 11. Renewal reminders

The command takes a fixed `--date`, so the result does not depend on today's date. `member.demo` is active until
`2026-12-31`.

| # | Step | Expected result | Result |
|---|------|-----------------|--------|
| 11.1 | `docker compose exec web python manage.py send_renewal_reminders --days 60 --date 2026-12-01 --dry-run` | `[DRY-RUN] Would notify member.demo@example.test (member=HA-2026-0001, valid_until=2026-12-31, days_remaining=30)` and `DRY-RUN complete: processed=1, skipped=0, window=2026-12-01..2027-01-30.`; no e-mail text is printed | [ ] |
| 11.2 | The same command without `--dry-run` | `Sent renewal reminder via 'email' to member.demo@example.test (valid_until=2026-12-31)` and `Renewal reminder job complete: processed=1, skipped=0, window=2026-12-01..2027-01-30.`; the e-mail with the subject "[Hunting Association MVP] Membership Renewal Reminder (Sample)" is printed in the terminal; nothing is really sent | [ ] |
| 11.3 | `… send_renewal_reminders --days 10 --date 2026-12-01 --dry-run` | `DRY-RUN complete: processed=0, skipped=0, window=2026-12-01..2026-12-11.` (the member expires outside the 10-day window) | [ ] |
| 11.4 | `… send_renewal_reminders --days -1` | error `--days must be a non-negative integer.` | [ ] |

## 12. Shared layout, navigation and responsive check

| # | Step | Expected result | Result |
|---|------|-----------------|--------|
| 12.1 | Signed out: compare the header and footer on `/`, `/membership/calculator/` and `/accounts/login/` | the same header and footer everywhere; a *Prihlásiť sa* link is visible | [ ] |
| 12.2 | Signed in as `member.demo`: open the account menu in the header | shows full name, e-mail and role badge; entries *Môj účet*, *Moje členstvo*, *Členská karta*, *Odhlásiť sa*; **no** *Sekretariát* entry | [ ] |
| 12.3 | Click outside the open menu, then open it again and press `Esc` | the menu closes both times | [ ] |
| 12.4 | Sign in as `admin1` and open the account menu | the menu additionally shows *Sekretariát (back office)* (the role badge reads *Member*, see "Good to know") | [ ] |
| 12.5 | Visit the dashboard, calculator, application form, *My membership*, card, directory, member detail and quick-add pages | every page has a "Back to …" link with a left-arrow icon at the top and the same dark-green banner with the page title; each flash message appears once | [ ] |
| 12.6 | On the dashboard use *Sign Out* | you are sent to the sign-in page with the message "You have been signed out." | [ ] |
| 12.7 | Browser window about 390 px wide (or phone emulation): open the hamburger menu while signed in | the list contains the account entries and *Odhlásiť sa*; wide tables scroll horizontally instead of breaking the page | [ ] |
| 12.8 | Tab through the sign-in form with the keyboard | focus is visible on every field and button; every field has a label | [ ] |

---

## Sign-off

| Field | Value |
|-------|-------|
| Tester | |
| Date | |
| Environment (OS, browser, Docker version) | |
| Commit / branch tested | |
| Steps passed / total | / 78 |
| Failed steps and notes | |
