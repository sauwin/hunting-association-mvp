from datetime import date
from decimal import Decimal
from typing import Any

from django.db import transaction
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.db.models import Q

from .models import FeeQuote, FeeRule, MemberProfile, MembershipStatusHistory

DEFAULT_CONSENT_VERSION = "2026-v1-demo"
DEFAULT_CONSENT_TEXT = (
    "I consent to the processing of my synthetic demo data for testing the "
    "Hunting Association membership application and administration workflow. "
    "(SAMPLE / PLACEHOLDER TEXT — Not legal compliance wording)."
)
PLACEHOLDER_QUOTE_LABEL = (
    "SAMPLE / PLACEHOLDER FEE QUOTE — Subject to association approval"
)
DELETION_REQUEST_PROCEDURE_TEXT = (
    "Personal data deletion requests in this MVP are handled manually by the "
    "association secretariat. When a member requests erasure, authorised staff "
    "verify whether statutory or accounting retention rules apply, set the "
    "membership record to inactive, and anonymise or delete personal profile "
    "fields and consent records. (SAMPLE / PLACEHOLDER PROCEDURE — Not legal "
    "compliance wording; requires client/legal review before production)."
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


def generate_member_number(member: MemberProfile) -> str:
    """Generate a unique synthetic member ID (e.g. HA-2026-0001) for an approved member."""
    if member.member_number:
        return member.member_number

    year = timezone.localdate().year
    candidate = f"HA-{year}-{member.pk:04d}"
    if not MemberProfile.objects.filter(member_number=candidate).exclude(pk=member.pk).exists():
        return candidate

    return f"HA-{year}-{member.pk:04d}-{timezone.now().strftime('%H%M%S')}"


def transition_member_status(
    member: MemberProfile,
    new_status: str,
    changed_by=None,
    valid_from: date | None = None,
    valid_until: date | None = None,
    note: str = "",
) -> MemberProfile:
    """Transition a member between lifecycle statuses and record an audit trail entry."""
    valid_statuses = {choice[0] for choice in MemberProfile.Status.choices}
    if new_status not in valid_statuses:
        raise ValueError(f"Invalid membership status: {new_status}")

    with transaction.atomic():
        previous_status = member.status
        member.status = new_status

        if valid_from is not None:
            member.valid_from = valid_from
        elif new_status == MemberProfile.Status.ACTIVE and member.valid_from is None:
            member.valid_from = timezone.localdate()

        if valid_until is not None:
            member.valid_until = valid_until

        if new_status == MemberProfile.Status.ACTIVE and not member.member_number:
            member.member_number = generate_member_number(member)

        member.save()

        MembershipStatusHistory.objects.create(
            member=member,
            previous_status=previous_status,
            new_status=new_status,
            changed_by=changed_by,
            note=note or f"Status transitioned from {previous_status} to {new_status}.",
        )

    return member

def _parse_target_date(target_date: date | str | None) -> date:
    if target_date is None:
        return timezone.localdate()
    if isinstance(target_date, str):
        return date.fromisoformat(target_date)
    return target_date


def _resolve_member_profile(user_or_email: Any) -> MemberProfile | None:
    if user_or_email is None:
        return None
    if isinstance(user_or_email, MemberProfile):
        return user_or_email

    user_model = get_user_model()
    if isinstance(user_or_email, user_model):
        return (
            MemberProfile.objects.select_related("user")
            .filter(user=user_or_email)
            .first()
        )

    identifier = str(user_or_email).strip()
    if not identifier:
        return None

    return (
        MemberProfile.objects.select_related("user")
        .filter(
            Q(user__email__iexact=identifier)
            | Q(user__username__iexact=identifier)
            | Q(member_number__iexact=identifier)
        )
        .first()
    )


def check_eligibility(
    user_or_email: Any,
    target_date: date | str | None = None,
) -> dict[str, Any]:
    """
    Verify membership active status, hunting licence validity, and insurance validity
    for a target date (contract defined in docs/contracts.md).
    """
    check_date = _parse_target_date(target_date)
    profile = _resolve_member_profile(user_or_email)

    if profile is None:
        return {
            "active": False,
            "licenceValid": False,
            "insuranceValid": False,
            "validUntil": None,
        }

    is_active = (
        profile.status == MemberProfile.Status.ACTIVE
        and profile.valid_until is not None
        and (profile.valid_from is None or profile.valid_from <= check_date)
        and check_date <= profile.valid_until
    )
    licence_valid = bool(
        profile.licence_valid_until and profile.licence_valid_until >= check_date
    )
    insurance_valid = bool(
        profile.insurance_valid_until and profile.insurance_valid_until >= check_date
    )
    valid_until = profile.valid_until.isoformat() if profile.valid_until else None

    return {
        "active": is_active,
        "licenceValid": licence_valid,
        "insuranceValid": insurance_valid,
        "validUntil": valid_until,
    }