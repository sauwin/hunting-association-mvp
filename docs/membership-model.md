# Membership & Member Portal Data Model (Student A Scope)

This document defines the Entity-Relationship (ER) model and data dictionary for the `membership` module owned by **Student A**. It strictly follows **Section 2 (In scope — MUST deliver)** and **Section 6 (Coordination with Student B)** of the assignment specification, avoiding over-collection of personal data and maintaining a single unified authentication model (`accounts.User`).

---

## 1. Entity-Relationship Diagram (Mermaid)

```mermaid
erDiagram
    USER ||--o| MEMBER_PROFILE : "has"
    USER ||--o{ STATUS_HISTORY : "changed_by (staff)"
    USER ||--o{ PAYMENT : "recorded_by (staff)"

    MEMBER_PROFILE ||--o{ STATUS_HISTORY : "tracks"
    MEMBER_PROFILE ||--o{ FEE_QUOTE : "receives"
    MEMBER_PROFILE ||--o{ PAYMENT : "makes"
    MEMBER_PROFILE ||--o{ CONSENT_RECORD : "grants"

    FEE_RULE ||--o{ FEE_QUOTE : "calculates (frozen)"
    FEE_QUOTE ||--o{ PAYMENT : "settled_by"

    USER {
        bigint id PK
        string username UK
        string email UK
        string password
        string first_name
        string last_name
        string role "member | secretariat | editor | admin"
        boolean is_active
        datetime date_joined
    }

    MEMBER_PROFILE {
        bigint id PK
        bigint user_id FK, UK "Links to accounts.User"
        string member_number UK "Generated human-readable ID (e.g., HA-2026-0001)"
        string member_type "hunter | non_hunter"
        string phone
        text address
        string status "applicant | active | expired | suspended"
        date valid_from "Nullable until approved"
        date valid_until "Nullable until approved"
        date hunting_licence_valid_until "Optional, used in eligibility check"
        date insurance_valid_until "Optional, used in eligibility check"
        datetime created_at
        datetime updated_at
    }

    STATUS_HISTORY {
        bigint id PK
        bigint member_id FK "Links to MemberProfile"
        string old_status "applicant | active | expired | suspended | null"
        string new_status "applicant | active | expired | suspended"
        bigint changed_by_id FK "Nullable, links to accounts.User"
        text note "Reason or approval note"
        datetime changed_at
    }

    FEE_RULE {
        bigint id PK
        string version_code UK "e.g., 2026-v1"
        string name "Sample/Placeholder tariff name"
        string member_type "hunter | non_hunter"
        decimal base_fee "Sample amount in EUR"
        decimal insurance_addon_fee "Optional insurance add-on amount in EUR"
        decimal reduced_fee_discount "Optional discount amount in EUR"
        boolean is_active "Whether used for new quotes"
        date effective_from
        datetime created_at
    }

    FEE_QUOTE {
        bigint id PK
        bigint member_id FK "Links to MemberProfile"
        bigint fee_rule_id FK "Links to FeeRule version used"
        string rule_version_snapshot "Frozen version code (e.g., 2026-v1)"
        boolean includes_insurance_addon
        boolean applies_reduced_fee
        decimal frozen_base_amount "Frozen base fee at calculation time"
        decimal frozen_addon_amount "Frozen add-on fee at calculation time"
        decimal frozen_discount_amount "Frozen discount at calculation time"
        decimal total_amount "Final indicative fee (sample/placeholder)"
        datetime created_at
    }

    PAYMENT {
        bigint id PK
        bigint member_id FK "Links to MemberProfile"
        bigint quote_id FK "Nullable, links to FeeQuote"
        string status "pending | paid | overdue | cancelled"
        decimal amount "Amount in EUR"
        date payment_date "Nullable until paid"
        string reference "Manual bank/cash reference code"
        bigint recorded_by_id FK "Links to accounts.User (secretariat/admin)"
        text audit_note "Audit trail notes for manual recording"
        datetime created_at
        datetime updated_at
    }

    CONSENT_RECORD {
        bigint id PK
        bigint member_id FK "Links to MemberProfile"
        string consent_type "membership_terms | privacy_notice"
        string consent_version "e.g., v1.0-demo"
        text consent_text_snapshot "Exact placeholder text agreed to"
        boolean consented
        datetime consented_at
    }
```