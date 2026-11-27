# User Guide (Membership module)

Short manual for the people who use the membership part of the Hunting Association portal: **members** (part A) and
**secretariat / administrator staff** (part B). It describes what the application does today. Technical details of every
URL are in [`api.md`](api.md); how to install and run it is in the [README](../README.md) and in
[`deployment-and-backup.md`](deployment-and-backup.md).

> **Demo notice.** This is an MVP. All data is synthetic, all fee amounts are *SAMPLE / PLACEHOLDER* values until the
> association approves them, and the consent and privacy wording is placeholder text that still needs legal review. In the
> demo setup no e-mail is ever delivered: messages such as password-reset links are printed in the server log
> (`docker compose logs web`).

## Roles at a glance

| Role | Who | What they can do |
|------|-----|------------------|
| Member | everybody who registers | apply, see own status, fees, card and data; download own data |
| Secretariat | association office staff | everything a member can, plus the back office: approve, set validity dates, record payments, quick-add, CSV export |
| Administrator | association IT contact | everything above plus the Django admin site (`/admin/`): roles, fee rules, content |
| Editor | web editors (public website) | edit news and regional representatives; not part of this guide |

A new account is always a *Member*. Only an administrator can change a role (see [B6](#b6-give-someone-a-role)).

---

## Part A: for members

### A1. Create an account and sign in

1. Open **Sign in → Register** (`/accounts/register/`). Enter a username, your e-mail address, first and last name and a
   password (twice). The password must not be too common, too short, purely numeric or similar to your name.
2. After registering you are signed in and see your **dashboard**.
3. Next time use `/accounts/login/` and type either your **e-mail address or your username** plus the password.
4. Too many wrong passwords block that sign-in name for about five minutes ("Too many failed login attempts"). Wait and
   try again.
5. **Forgot the password?** Use *Forgot your password?* on the sign-in page, enter your e-mail address and follow the link that
   is sent to you. The page looks the same whether or not the address is known, so nobody can probe which addresses exist.
6. Sign out from the account menu (your name in the top bar) or with *Sign Out* on the dashboard.

### A2. Check the fee first (no account needed)

Open **Fee calculator** (`/membership/calculator/`). Choose the category (*Hunter* or *Non-Hunter*), tick the insurance
add-on and/or the reduced rate if they apply, and press *Calculate Fee Breakdown*. The page shows the tariff version, base
fee, add-on, discount and the **indicative** total. Nothing is saved at this point.

### A3. Apply for membership

1. Sign in and press *Proceed to Membership Application* (or *Apply for membership* on the dashboard).
2. Fill in the form: first and last name, category, phone, street, city, postal code. The hunting licence number, licence
   and insurance expiry dates are optional; if you give a licence expiry date you must give the licence number as well.
   Optionally tick the insurance add-on and the reduced rate.
3. Tick the **consent** checkbox. Without it the application cannot be sent. The exact wording and its version are stored
   with your application.
4. Press submit. You land on **My membership** with a message such as "Application saved and frozen fee quote #1
   (85.00 EUR) generated". Your status is **Applicant**.

The application asks only for what the MVP uses; nothing else about you is collected.

### A4. Understand "My membership"

| Block | Meaning |
|-------|---------|
| Status | **Applicant**: waiting for the secretariat. **Active**: membership is valid. **Expired**: validity has ended. **Suspended**: paused by the secretariat |
| Member number | Appears (for example `HA-2026-0001`) once the secretariat approves you. Until then it reads "Pending secretariat approval" |
| Validity | The "from" and "until" dates set by the secretariat |
| Frozen fee quotes | Every time you submit the application a new quote is stored. A stored quote never changes, even if the association later changes its fees; the tariff version is shown next to each quote |
| Status history | A log of every status change with the date and a note |
| Consents | The consent you gave, its version and the exact text |

To change your details, press **Update Application / Generate New Quote**, correct the form and submit it again. This
creates a new quote and a new consent record and keeps the older ones.

### A5. Digital member card

Open **Digital member card** (`/membership/my-card/`). The card shows only the member number, your name, the status and the
valid-until date. Use *Download HTML Card* to save it as a file, or *Print / Save as PDF* to print it. Before approval the
card shows "PENDING-APPROVAL" instead of a number.

### A6. Download your own data

On **My membership** press **Download my data (JSON)**. You get one file containing your account details, membership
profile, quotes, consents, status history and payments, plus the description of how deletion requests are handled. You
see only your own data.

### A7. Ask for deletion or correction

There is no delete button. Deletion is handled by hand: write to the association secretariat. Staff check whether
accounting or legal retention rules apply, then deactivate your account and anonymise or delete your personal data (the
procedure is printed on *My membership* under "How Personal Data Deletion Requests Are Handled"). This is a documented MVP
procedure, not a statement of legal compliance.

### A8. Problems you may meet

| Message or situation | What it means |
|----------------------|---------------|
| "Invalid email/username or password" | Typing error or wrong password; use the password reset if needed |
| "Too many failed login attempts" | Wait about five minutes |
| *403 Forbidden* | The page is for secretariat staff or for another member, not for your account |
| Redirected to the application form when opening the card | You have not applied yet; submit the application first |

---

## Part B: for secretariat and administrator staff

You need an account with the role *Secretariat* or *Administrator* (a superuser also works). Staff see an extra entry
**Sekretariát (back office)** in the account menu; it opens `/membership/backoffice/`.

### B1. Find members

The **Member directory** shows three counters (total profiles, applicants waiting, active members) and a table with ten
members per page: member ID, name and account, category, status, valid-until date, latest payment status and actions.

- *Search* looks in name, member ID, e-mail, city and phone.
- *Status* and *Category* narrow the list; *Reset* clears all filters.
- *Manage* opens the member's detail page.

### B2. Approve an application and set validity

1. Open the applicant with *Manage*.
2. In **Approve / Update Lifecycle Status** choose *Active*, enter *Valid from* and *Valid until* and a short audit note
   (for example "Approved after document check"), then press *Save Status & Validity Dates*.
3. The system assigns the member number (`HA-<year>-<number>`) the first time a member becomes active and adds a line to
   the status history with your name and note.

Use the same form to set a member to *Expired* or *Suspended*. Check the dates: *Valid until* must not be earlier than
*Valid from*. Membership counts as active for the eligibility check only while the status is *Active* and today lies
between the two dates.

### B3. Record payments (manual only)

The portal does not take payments; the secretariat records what arrived on the bank account or in cash.

1. On the member's page fill in the payment form: status (*Pending*, *Paid*, *Overdue* or *Cancelled*), amount, currency,
   reference, optionally the quote it settles, the payment date and a note. The amount must be greater than zero and is
   pre-filled with the latest quote total.
2. Save. The row appears in the **Payment Audit Trail** with your username in *Recorded By*.
3. To change a payment later, pick the new status in the row and press its update button. Switching to *Paid* fills in
   today's date if none is set.

### B4. Add a member by hand and export the list

- **+ Quick-Add Member** creates a user, profile, status entry and fee quote in one go (username, e-mail, first and last
  name, category, initial status, phone and address are required). The new account has no usable password, so the person cannot
  sign in yet and the password-reset form skips such accounts. An administrator must set a password for the account in
  `/admin/` → *Users* if the member should use the portal. A member added this way has no consent record, so keep the
  paper or e-mail consent on file.
- **Export Filtered CSV** downloads `members_export.csv` containing exactly the members matching the current search and
  filters (14 columns: member number, username, names, e-mail, category, status, validity dates, phone, city, licence and
  insurance dates, latest payment status). The file contains personal data: store it safely, do not e-mail it
  unprotected, delete it when finished. Spreadsheet programs may treat text that starts with `=`, `+`, `-` or `@` as a
  formula, so check unusual cells before opening the file.

### B5. Fee rules and renewal reminders

- **Fee rules** are edited by an administrator in the Django admin (`/admin/` → *Fee rules*). A changed rule applies to
  **new** quotes only; stored quotes keep the amounts and tariff version they were created with.
- **Renewal reminders** are sent by running a command on the server: `docker compose exec web python manage.py
  send_renewal_reminders --days 60` (add `--dry-run` first to see who would be notified). It looks for active members
  whose validity ends within the next 60 days. There is no built-in scheduler yet: run it by hand or from the server's
  scheduler. The job does not remember who was already reminded, so running it every day repeats the reminder every day
  within the window. In the demo the e-mails are only printed, never delivered.

### B6. Give someone a role

Administrators open `/admin/` → *Users*, select the person and set **Role** in the "Role & Permissions" block (for
example *Secretariat*). The back office needs only the role. Access to `/admin/` itself additionally needs the *Staff
status* flag, which should be given only to administrators.

### B7. Handling personal data as staff

- Open member records only when your work requires it. Do not copy member data into chats, e-mails or AI tools.
- **Deletion requests:** follow the procedure printed on the member's *My membership* page. Prefer *deactivating* the
  account and anonymising the profile. Deleting a user in the Django admin also deletes the member's profile, quotes,
  consents and **payment records** (the accounting history), and removes your name from the audit trail of payments you
  recorded if your own account is deleted. Check retention rules before deleting anything.
- Backups contain the same personal data as the live database; see
  [`deployment-and-backup.md`](deployment-and-backup.md).

### B8. Quick reference of status values

| Membership status | Set by | Meaning |
|-------------------|--------|---------|
| Applicant | system (on application) | submitted, not yet approved |
| Active | secretariat | approved, valid between the validity dates |
| Expired | secretariat | validity ended |
| Suspended | secretariat | paused, not counted as active |

| Payment status | Meaning |
|----------------|---------|
| Pending | expected, not yet received |
| Paid | received (payment date set) |
| Overdue | expected earlier, not received |
| Cancelled | no longer expected |
