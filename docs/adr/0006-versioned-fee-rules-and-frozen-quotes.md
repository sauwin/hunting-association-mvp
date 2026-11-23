# ADR-0006: Versioned Fee Rules, Frozen Quote Snapshots, and Consent Records

- **Status:** Accepted
- **Date:** 2026-11-13
- **Deciders:** Student A (Membership & Back-Office Module)

## Context
The hunting association MVP requires a transparent membership fee calculator (hunter vs. non-hunter base fee, optional insurance add-on, optional reduced-rate discount) and explicit GDPR-style consent capture during application. A core acceptance criterion states that updating a fee rule in the database must affect new quotes without rewriting previously stored quotes. Additionally, all MVP monetary amounts must be clearly marked as sample/placeholder values.

## Decision
1. **Database-Configured Versioned Rules (`FeeRule`):** Store fee schedules in PostgreSQL with an immutable `version` code (e.g., `2026-v1-sample`) and an `is_placeholder=True` flag rather than hardcoding prices in Python code.
2. **Frozen Quote Snapshots (`FeeQuote`):** When a quote is generated for a member, copy all calculated monetary components (`base_amount`, `insurance_amount`, `discount_amount`, `total_amount`, `currency`), the `rule_version_snapshot`, and the sample/placeholder warning label directly into the `FeeQuote` row. Link `FeeQuote.fee_rule` with `on_delete=models.PROTECT` so historical rules referenced by quotes cannot be deleted.
3. **Immutable Consent Snapshots (`ConsentRecord`):** Record both the `consent_version` and the exact `consent_text_snapshot` accepted by the user alongside the timestamp.

## Consequences
- **Positive:** Historical quotes and audit trails remain 100% immutable even if administrators modify existing `FeeRule` rows or introduce new tariff versions.
- **Positive:** Storing exact snapshots simplifies oral defense verification and satisfies the requirement that fee changes never retroactively alter stored member calculations.
- **Trade-off:** Slight data denormalization between `FeeRule` and `FeeQuote`, which is intentional and standard practice for financial audit records.