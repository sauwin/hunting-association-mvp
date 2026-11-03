# User Journeys & Mobile-First Wireframes (Student B)

## 1. Core User Journeys

### Journey 1: First-Time Visitor -> Membership Registration (Max 2 Clicks)
1. **Landing (Homepage):** Visitor reads a clear explanation of the association, key benefits, and sees the primary `"Become a member"` CTA button in the hero section and header.
2. **Click 1:** Visitor clicks `"Become a member"` (or navigates to `"How to Join"` -> clicks `"Register Now"`).
3. **Click 2 / Handoff:** Visitor lands directly on Student A's registration route (configured via `MEMBERSHIP_REGISTER_URL`) or submits a quick Membership Interest Enquiry if they have questions first.

### Journey 2: Visitor -> Reading News & Sharing
1. Visitor opens `/news/` from the main navigation.
2. Filters articles by category (e.g., Conservation, Events, Announcements) or browses paginated list.
3. Opens `/news/<slug>/` to read the full article and uses static share links (Facebook, X/Twitter, Copy Link).

### Journey 3: Visitor -> Finding a Regional Representative / Volunteering
1. Visitor navigates to `/representatives/` to find an active contact in their county/region.
2. If their region needs volunteers, visitor clicks `"Volunteer with us"` (`/get-involved/`) and submits the Volunteer Recruitment Form with explicit privacy consent.
3. Authorised staff reviews the submission in Django Admin (`NEW` -> `CONTACTED` -> `ACCEPTED` / `DECLINED`).

---

## 2. Mobile-First Wireframes (ASCII Layout)

### 2.1 Mobile View (< 768px) — Homepage & Navigation
```text
+-----------------------------------+
| [Logo] Hunting Assoc.   [= Menu]  |
+-----------------------------------+
| HERO SECTION                      |
| Protecting wildlife & traditions  |
|                                   |
| [   Become a Member (CTA)   ]     |
| [   Ask a Question          ]     |
+-----------------------------------+
| WHY JOIN US? (Benefits Cards)     |
| +-------------------------------+ |
| | 1. Community & Mentorship     | |
| +-------------------------------+ |
| | 2. Training & Events          | |
| +-------------------------------+ |
| | 3. Regional Support           | |
| +-------------------------------+ |
+-----------------------------------+
| LATEST NEWS                       |
| +-------------------------------+ |
| | [Img] Autumn Conservation     | |
| | 02 Nov 2026 | Conservation    | |
| | Short summary text... [Read]  | |
| +-------------------------------+ |
| [ View All News -> ]              |
+-----------------------------------+
| FIND YOUR REGIONAL REP            |
| Connect with local coordinators   |
| [ Browse Directory -> ]           |
+-----------------------------------+
| FOOTER                            |
| Links: About | FAQ | Contact      |
| Social: [FB] [IG] [YouTube]       |
| Privacy Notice | Copyright        |
+-----------------------------------+