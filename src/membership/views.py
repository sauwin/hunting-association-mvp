from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .forms import FeeCalculatorPreviewForm, MembershipApplicationForm
from .models import ConsentRecord, MemberProfile, MembershipStatusHistory
from .services import (
     DEFAULT_CONSENT_TEXT,
    DEFAULT_CONSENT_VERSION,
    DELETION_REQUEST_PROCEDURE_TEXT,
    calculate_fee_breakdown,
    create_frozen_fee_quote,
    get_active_fee_rule,
)


def fee_calculator_view(request: HttpRequest) -> HttpResponse:
    """Public/member fee calculator preview with sample/placeholder breakdown."""
    active_rule = get_active_fee_rule()
    form = FeeCalculatorPreviewForm(request.GET or None)

    member_type = MemberProfile.MemberType.HUNTER
    include_insurance = False
    apply_reduced_rate = False

    if form.is_valid():
        member_type = form.cleaned_data["member_type"]
        include_insurance = form.cleaned_data["include_insurance"]
        apply_reduced_rate = form.cleaned_data["apply_reduced_rate"]

    breakdown = calculate_fee_breakdown(
        member_type=member_type,
        include_insurance=include_insurance,
        apply_reduced_rate=apply_reduced_rate,
        fee_rule=active_rule,
    )

    return render(
        request,
        "membership/fee_calculator.html",
        {
            "form": form,
            "breakdown": breakdown,
            "active_rule": active_rule,
        },
    )


@login_required
def apply_membership(request: HttpRequest) -> HttpResponse:
    """Submit or update a membership application, record consent, and freeze a fee quote."""
    existing_profile = MemberProfile.objects.filter(user=request.user).first()
    active_rule = get_active_fee_rule()

    if request.method == "POST":
        form = MembershipApplicationForm(
            request.POST,
            instance=existing_profile,
            user=request.user,
        )
        if form.is_valid():
            with transaction.atomic():
                request.user.first_name = form.cleaned_data["first_name"].strip()
                request.user.last_name = form.cleaned_data["last_name"].strip()
                request.user.save(update_fields=["first_name", "last_name"])

                is_new_profile = existing_profile is None
                profile = form.save(commit=False)
                profile.user = request.user
                if is_new_profile:
                    profile.status = MemberProfile.Status.APPLICANT
                profile.save()

                if is_new_profile:
                    MembershipStatusHistory.objects.create(
                        member=profile,
                        previous_status="",
                        new_status=profile.status,
                        changed_by=request.user,
                        note="Initial membership application submitted.",
                    )

                ConsentRecord.objects.create(
                    user=request.user,
                    purpose=ConsentRecord.Purpose.MEMBERSHIP_PROCESSING,
                    consent_version=DEFAULT_CONSENT_VERSION,
                    consent_text_snapshot=DEFAULT_CONSENT_TEXT,
                    accepted=True,
                )

                quote = create_frozen_fee_quote(
                    member=profile,
                    include_insurance=form.cleaned_data["include_insurance"],
                    apply_reduced_rate=form.cleaned_data["apply_reduced_rate"],
                    fee_rule=active_rule,
                )

            messages.success(
                request,
                f"Application saved and frozen fee quote #{quote.pk} "
                f"({quote.total_amount} {quote.currency}) generated.",
            )
            return redirect("membership:application_overview")
    else:
        form = MembershipApplicationForm(
            instance=existing_profile,
            user=request.user,
        )

    preview_breakdown = calculate_fee_breakdown(
        member_type=(
            existing_profile.member_type
            if existing_profile
            else MemberProfile.MemberType.HUNTER
        ),
        include_insurance=False,
        apply_reduced_rate=False,
        fee_rule=active_rule,
    )

    return render(
        request,
        "membership/apply.html",
        {
            "form": form,
            "existing_profile": existing_profile,
            "active_rule": active_rule,
            "preview_breakdown": preview_breakdown,
            "consent_version": DEFAULT_CONSENT_VERSION,
            "consent_text": DEFAULT_CONSENT_TEXT,
        },
    )


@login_required
def application_overview(request: HttpRequest) -> HttpResponse:
    """Display the member's profile status, frozen fee quotes, consents, and payment records."""
    profile = MemberProfile.objects.filter(user=request.user).first()
    quotes = profile.fee_quotes.all() if profile else []
    latest_quote = quotes[0] if quotes else None
    consents = request.user.consent_records.all()
    status_history = profile.status_history.all() if profile else []
    payments = profile.payments.all() if profile else []

    return render(
        request,
        "membership/application_overview.html",
        {
            "profile": profile,
            "latest_quote": latest_quote,
            "quotes": quotes,
            "consents": consents,
            "status_history": status_history,
            "payments": payments,
            "deletion_procedure": DELETION_REQUEST_PROCEDURE_TEXT,
        },
    )


@login_required
def member_card_view(
    request: HttpRequest, member_id: int | None = None
) -> HttpResponse:
    """Render a printable/downloadable HTML digital member card with strictly MVP fields."""
    if member_id is not None:
        profile = get_object_or_404(
            MemberProfile.objects.select_related("user"),
            pk=member_id,
        )
        if profile.user_id != request.user.id and not request.user.can_manage_members:
            raise PermissionDenied(
                "You do not have permission to access another member's card."
            )
    else:
        profile = (
            MemberProfile.objects.filter(user=request.user)
            .select_related("user")
            .first()
        )
        if profile is None:
            messages.info(
                request,
                "Please submit a membership application before accessing your digital member card.",
            )
            return redirect("membership:apply")

    full_name = (
        f"{profile.user.first_name} {profile.user.last_name}".strip()
        or profile.user.username
    )
    card_context = {
        "member_id_display": profile.member_number or "PENDING-APPROVAL",
        "member_full_name": full_name,
        "status_display": profile.get_status_display(),
        "status_code": profile.status,
        "valid_until": profile.valid_until,
    }

    response = render(request, "membership/member_card.html", card_context)
    if request.GET.get("download") == "1":
        response["Content-Disposition"] = (
            f'attachment; filename="member_card_{profile.user.username}.html"'
        )
    return response


@login_required
def export_my_data(request: HttpRequest) -> JsonResponse:
    """Export all personal membership, quote, consent, and payment data as JSON (GDPR self-service)."""
    profile = MemberProfile.objects.filter(user=request.user).first()

    payload = {
        "exported_at": timezone.now().isoformat(),
        "notice": "SYNTHETIC DEMO DATA EXPORT — Hunting Association MVP",
        "deletion_request_procedure": DELETION_REQUEST_PROCEDURE_TEXT,
        "account": {
            "username": request.user.username,
            "email": request.user.email,
            "first_name": request.user.first_name,
            "last_name": request.user.last_name,
            "role": request.user.role,
            "date_joined": request.user.date_joined.isoformat(),
        },
        "member_profile": None,
        "fee_quotes": [],
        "consents": [
            {
                "purpose": c.purpose,
                "consent_version": c.consent_version,
                "consent_text_snapshot": c.consent_text_snapshot,
                "accepted": c.accepted,
                "accepted_at": c.accepted_at.isoformat(),
            }
            for c in request.user.consent_records.all()
        ],
        "status_history": [],
        "payments": [],
    }

    if profile is not None:
        payload["member_profile"] = {
            "member_number": profile.member_number,
            "member_type": profile.member_type,
            "status": profile.status,
            "phone": profile.phone,
            "street_address": profile.street_address,
            "city": profile.city,
            "postal_code": profile.postal_code,
            "hunting_licence_number": profile.hunting_licence_number,
            "licence_valid_until": (
                profile.licence_valid_until.isoformat()
                if profile.licence_valid_until
                else None
            ),
            "insurance_valid_until": (
                profile.insurance_valid_until.isoformat()
                if profile.insurance_valid_until
                else None
            ),
            "valid_from": (
                profile.valid_from.isoformat() if profile.valid_from else None
            ),
            "valid_until": (
                profile.valid_until.isoformat() if profile.valid_until else None
            ),
            "created_at": profile.created_at.isoformat(),
            "updated_at": profile.updated_at.isoformat(),
        }
        payload["fee_quotes"] = [
            {
                "id": q.pk,
                "rule_version_snapshot": q.rule_version_snapshot,
                "member_type_snapshot": q.member_type_snapshot,
                "base_amount": str(q.base_amount),
                "include_insurance": q.include_insurance,
                "insurance_amount": str(q.insurance_amount),
                "apply_reduced_rate": q.apply_reduced_rate,
                "discount_amount": str(q.discount_amount),
                "total_amount": str(q.total_amount),
                "currency": q.currency,
                "placeholder_label": q.placeholder_label,
                "created_at": q.created_at.isoformat(),
            }
            for q in profile.fee_quotes.all()
        ]
        payload["status_history"] = [
            {
                "previous_status": h.previous_status,
                "new_status": h.new_status,
                "note": h.note,
                "changed_at": h.changed_at.isoformat(),
            }
            for h in profile.status_history.all()
        ]
        payload["payments"] = [
            {
                "status": p.status,
                "amount": str(p.amount),
                "currency": p.currency,
                "reference": p.reference,
                "payment_date": (
                    p.payment_date.isoformat() if p.payment_date else None
                ),
                "created_at": p.created_at.isoformat(),
            }
            for p in profile.payments.all()
        ]

    response = JsonResponse(payload, json_dumps_params={"indent": 2})
    response["Content-Disposition"] = (
        f'attachment; filename="membership_data_{request.user.username}.json"'
    )
    return response