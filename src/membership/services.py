from decimal import Decimal
from typing import Any

from .models import FeeQuote, FeeRule, MemberProfile

DEFAULT_CONSENT_VERSION = "2026-v1-demo"
DEFAULT_CONSENT_TEXT = (
    "I consent to the processing of my synthetic demo data for testing the "
    "Hunting Association membership application and administration workflow. "
    "(SAMPLE / PLACEHOLDER TEXT — Not legal compliance wording)."
)
PLACEHOLDER_QUOTE_LABEL = (
    "SAMPLE / PLACEHOLDER FEE QUOTE — Subject to association approval"
)


def get_active_fee_rule() -> FeeRule:
    """Return the most recent active FeeRule, or create a default placeholder rule."""
    rule = FeeRule.objects.filter(is_active=True).first()
    if rule is not None:
        return rule

    return FeeRule.objects.create(
        version="2026-v1-sample",
        name="2026 Standard Membership Fee Schedule (Sample)",
        base_fee_hunter=Decimal("60.00"),
        base_fee_non_hunter=Decimal("35.00"),
        insurance_addon_fee=Decimal("25.00"),
        reduced_discount_amount=Decimal("15.00"),
        currency="EUR",
        is_active=True,
        is_placeholder=True,
    )


def calculate_fee_breakdown(
    member_type: str,
    include_insurance: bool = False,
    apply_reduced_rate: bool = False,
    fee_rule: FeeRule | None = None,
) -> dict[str, Any]:
    """Calculate an indicative membership fee breakdown from a FeeRule."""
    rule = fee_rule or get_active_fee_rule()

    if member_type == MemberProfile.MemberType.HUNTER:
        base_amount = rule.base_fee_hunter
    else:
        base_amount = rule.base_fee_non_hunter

    insurance_amount = (
        rule.insurance_addon_fee if include_insurance else Decimal("0.00")
    )
    discount_amount = (
        rule.reduced_discount_amount if apply_reduced_rate else Decimal("0.00")
    )

    total_amount = max(
        Decimal("0.00"),
        base_amount + insurance_amount - discount_amount,
    )

    return {
        "fee_rule": rule,
        "rule_version": rule.version,
        "member_type": member_type,
        "base_amount": base_amount,
        "include_insurance": include_insurance,
        "insurance_amount": insurance_amount,
        "apply_reduced_rate": apply_reduced_rate,
        "discount_amount": discount_amount,
        "total_amount": total_amount,
        "currency": rule.currency,
        "is_placeholder": rule.is_placeholder,
        "placeholder_label": PLACEHOLDER_QUOTE_LABEL,
    }


def create_frozen_fee_quote(
    member: MemberProfile,
    include_insurance: bool = False,
    apply_reduced_rate: bool = False,
    fee_rule: FeeRule | None = None,
) -> FeeQuote:
    """Create and persist an immutable FeeQuote snapshot for a member."""
    breakdown = calculate_fee_breakdown(
        member_type=member.member_type,
        include_insurance=include_insurance,
        apply_reduced_rate=apply_reduced_rate,
        fee_rule=fee_rule,
    )

    return FeeQuote.objects.create(
        member=member,
        fee_rule=breakdown["fee_rule"],
        rule_version_snapshot=breakdown["rule_version"],
        member_type_snapshot=breakdown["member_type"],
        base_amount=breakdown["base_amount"],
        include_insurance=breakdown["include_insurance"],
        insurance_amount=breakdown["insurance_amount"],
        apply_reduced_rate=breakdown["apply_reduced_rate"],
        discount_amount=breakdown["discount_amount"],
        total_amount=breakdown["total_amount"],
        currency=breakdown["currency"],
        placeholder_label=breakdown["placeholder_label"],
    )