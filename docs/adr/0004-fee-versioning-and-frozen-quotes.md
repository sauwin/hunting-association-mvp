# ADR 0004: Database-Configured Fee Rules and Immutable Frozen Quotes

- **Status:** Accepted
- **Date:** 2026-11-05
- **Deciders:** Student A (Maksym Druziuk)

## Context
The MVP requires a transparent fee calculator configured via database rules (at minimum: base fee, optional insurance add-on, and reduced-fee rule) using sample/placeholder amounts pending association approval. A strict acceptance criterion states that changing a fee rule must affect newly generated quotes without rewriting previously stored quotes.

## Decision
Separate the fee calculation schema into two distinct models within the `membership` app:
1. **`FeeRule` (Mutable / Versioned Configuration):** Stores `version_code` (e.g., `2026-STD-v1`), `member_type`, `base_fee`, `insurance_addon_fee`, `reduced_fee_discount`, and an `is_active` flag. When fees change, staff either create a new `FeeRule` version and mark it active or update configuration for future calculations.
2. **`FeeQuote` (Immutable Snapshot):** When an applicant submits an application or requests a quote, the calculator copies the exact numerical values (`frozen_base_amount`, `frozen_addon_amount`, `frozen_discount_amount`, `total_amount`) and `rule_version_snapshot` directly into `FeeQuote`, linking to `FeeRule` with `on_delete=models.PROTECT`.

## Consequences
- **Positive:** Historical quotes and audit trails remain 100% intact even if `FeeRule` amounts are modified later; simple to explain and verify during live code walkthroughs and automated tests.
- **Negative:** Slight data denormalisation between `FeeRule` and `FeeQuote`, which is intentional and required for financial snapshot integrity.