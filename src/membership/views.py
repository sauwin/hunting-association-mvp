import csv

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Q
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST
from datetime import date

from accounts.models import User
from accounts.permissions import role_required

from .forms import (
    FeeCalculatorPreviewForm,
    ManualPaymentForm,
    MembershipApplicationForm,
    MemberStatusUpdateForm,
    SecretariatQuickAddMemberForm,
)
from .models import (
    ConsentRecord,
    MemberProfile,
    MembershipStatusHistory,
    PaymentRecord,
)
from .services import (
    DEFAULT_CONSENT_TEXT,
    DEFAULT_CONSENT_VERSION,
    DELETION_REQUEST_PROCEDURE_TEXT,
    calculate_fee_breakdown,
    check_eligibility,
    create_frozen_fee_quote,
    get_active_fee_rule,
    transition_member_status,
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

    # Where the "Back" button should lead: staff looking at somebody else's card go back
    # to that member's back-office page, everybody else to their own membership overview.
    if profile.user_id != request.user.id:
        card_context["back_url"] = reverse(
            "membership:backoffice_member_detail", args=[profile.pk]
        )
        card_context["back_label"] = "Back to member detail"
    else:
        card_context["back_url"] = reverse("membership:application_overview")
        card_context["back_label"] = "Back to My Membership"

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


def _filter_member_queryset(request: HttpRequest):
    """Apply shared search, status, and member_type filters for back-office list and CSV export."""
    queryset = (
        MemberProfile.objects.select_related("user")
        .prefetch_related("payments")
        .all()
    )
    search_query = (request.GET.get("q") or "").strip()
    status_filter = (request.GET.get("status") or "").strip()
    member_type_filter = (request.GET.get("member_type") or "").strip()

    if search_query:
        queryset = queryset.filter(
            Q(member_number__icontains=search_query)
            | Q(user__username__icontains=search_query)
            | Q(user__email__icontains=search_query)
            | Q(user__first_name__icontains=search_query)
            | Q(user__last_name__icontains=search_query)
            | Q(city__icontains=search_query)
            | Q(phone__icontains=search_query)
        )

    valid_statuses = {choice[0] for choice in MemberProfile.Status.choices}
    if status_filter in valid_statuses:
        queryset = queryset.filter(status=status_filter)

    valid_types = {choice[0] for choice in MemberProfile.MemberType.choices}
    if member_type_filter in valid_types:
        queryset = queryset.filter(member_type=member_type_filter)

    return queryset, search_query, status_filter, member_type_filter


@role_required(User.Role.SECRETARIAT, User.Role.ADMIN)
def backoffice_member_list(request: HttpRequest) -> HttpResponse:
    """Searchable, filterable, and paginated member directory for secretariat staff."""
    queryset, search_query, status_filter, member_type_filter = (
        _filter_member_queryset(request)
    )
    paginator = Paginator(queryset, 10)
    page_obj = paginator.get_page(request.GET.get("page"))

    return render(
        request,
        "membership/backoffice/member_list.html",
        {
            "page_obj": page_obj,
            "search_query": search_query,
            "status_filter": status_filter,
            "member_type_filter": member_type_filter,
            "status_choices": MemberProfile.Status.choices,
            "member_type_choices": MemberProfile.MemberType.choices,
            "total_count": MemberProfile.objects.count(),
            "applicant_count": MemberProfile.objects.filter(
                status=MemberProfile.Status.APPLICANT
            ).count(),
            "active_count": MemberProfile.objects.filter(
                status=MemberProfile.Status.ACTIVE
            ).count(),
        },
    )


@role_required(User.Role.SECRETARIAT, User.Role.ADMIN)
def backoffice_member_detail(
    request: HttpRequest, member_id: int
) -> HttpResponse:
    """Secretariat member detail view for lifecycle approval/updates and manual payment recording."""
    profile = get_object_or_404(
        MemberProfile.objects.select_related("user"),
        pk=member_id,
    )

    status_form = MemberStatusUpdateForm(
        initial={
            "status": profile.status,
            "valid_from": profile.valid_from,
            "valid_until": profile.valid_until,
        }
    )
    payment_form = ManualPaymentForm(member=profile)

    if request.method == "POST":
        action = request.POST.get("action")

        if action == "update_status":
            status_form = MemberStatusUpdateForm(request.POST)
            if status_form.is_valid():
                transition_member_status(
                    member=profile,
                    new_status=status_form.cleaned_data["status"],
                    changed_by=request.user,
                    valid_from=status_form.cleaned_data["valid_from"],
                    valid_until=status_form.cleaned_data["valid_until"],
                    note=status_form.cleaned_data["note"],
                )
                messages.success(
                    request,
                    f"Membership status updated to '{profile.get_status_display()}' "
                    f"(Member ID: {profile.member_number or 'Pending'}).",
                )
                return redirect(
                    "membership:backoffice_member_detail",
                    member_id=profile.pk,
                )

        elif action == "record_payment":
            payment_form = ManualPaymentForm(request.POST, member=profile)
            if payment_form.is_valid():
                payment = payment_form.save(commit=False)
                payment.member = profile
                payment.recorded_by = request.user
                payment.save()
                messages.success(
                    request,
                    f"Recorded {payment.get_status_display().lower()} payment of "
                    f"{payment.amount} {payment.currency} (Ref: {payment.reference or '—'}).",
                )
                return redirect(
                    "membership:backoffice_member_detail",
                    member_id=profile.pk,
                )

    return render(
        request,
        "membership/backoffice/member_detail.html",
        {
            "profile": profile,
            "status_form": status_form,
            "payment_form": payment_form,
            "quotes": profile.fee_quotes.all(),
            "payments": profile.payments.select_related("quote", "recorded_by").all(),
            "status_history": profile.status_history.select_related("changed_by").all(),
            "consents": profile.user.consent_records.all(),
            "payment_status_choices": PaymentRecord.Status.choices,
        },
    )


@require_POST
@role_required(User.Role.SECRETARIAT, User.Role.ADMIN)
def backoffice_update_payment_status(
    request: HttpRequest, payment_id: int
) -> HttpResponse:
    """Update the manual status of an existing payment record with staff audit attribution."""
    payment = get_object_or_404(
        PaymentRecord.objects.select_related("member"),
        pk=payment_id,
    )
    new_status = (request.POST.get("status") or "").strip()
    valid_statuses = {choice[0] for choice in PaymentRecord.Status.choices}

    if new_status not in valid_statuses:
        messages.error(request, "Invalid payment status selected.")
    else:
        payment.status = new_status
        payment.recorded_by = request.user
        if new_status == PaymentRecord.Status.PAID and payment.payment_date is None:
            payment.payment_date = timezone.localdate()
        payment.save(update_fields=["status", "recorded_by", "payment_date", "updated_at"])
        messages.success(
            request,
            f"Payment #{payment.pk} updated to {payment.get_status_display()}.",
        )

    return redirect(
        "membership:backoffice_member_detail",
        member_id=payment.member_id,
    )


@role_required(User.Role.SECRETARIAT, User.Role.ADMIN)
def backoffice_quick_add_member(request: HttpRequest) -> HttpResponse:
    """Allow secretariat staff to quick-add a synthetic member, profile, and initial frozen quote."""
    if request.method == "POST":
        form = SecretariatQuickAddMemberForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                user = User.objects.create_user(
                    username=form.cleaned_data["username"],
                    email=form.cleaned_data["email"],
                    password=None,
                    first_name=form.cleaned_data["first_name"].strip(),
                    last_name=form.cleaned_data["last_name"].strip(),
                    role=User.Role.MEMBER,
                )
                profile = MemberProfile.objects.create(
                    user=user,
                    member_type=form.cleaned_data["member_type"],
                    phone=form.cleaned_data["phone"].strip(),
                    street_address=form.cleaned_data["street_address"].strip(),
                    city=form.cleaned_data["city"].strip(),
                    postal_code=form.cleaned_data["postal_code"].strip(),
                    hunting_licence_number=(
                        form.cleaned_data["hunting_licence_number"] or ""
                    ).strip(),
                    licence_valid_until=form.cleaned_data["licence_valid_until"],
                    insurance_valid_until=form.cleaned_data["insurance_valid_until"],
                    status=MemberProfile.Status.APPLICANT,
                    valid_from=form.cleaned_data["valid_from"],
                    valid_until=form.cleaned_data["valid_until"],
                )

                initial_status = form.cleaned_data["status"]
                if initial_status != MemberProfile.Status.APPLICANT:
                    transition_member_status(
                        member=profile,
                        new_status=initial_status,
                        changed_by=request.user,
                        valid_from=form.cleaned_data["valid_from"],
                        valid_until=form.cleaned_data["valid_until"],
                        note="Quick-added by secretariat.",
                    )
                else:
                    MembershipStatusHistory.objects.create(
                        member=profile,
                        previous_status="",
                        new_status=MemberProfile.Status.APPLICANT,
                        changed_by=request.user,
                        note="Quick-added by secretariat.",
                    )

                create_frozen_fee_quote(
                    member=profile,
                    include_insurance=form.cleaned_data["include_insurance"],
                    apply_reduced_rate=form.cleaned_data["apply_reduced_rate"],
                    fee_rule=get_active_fee_rule(),
                )

            messages.success(
                request,
                f"Member '{user.username}' created with status '{profile.get_status_display()}'.",
            )
            return redirect(
                "membership:backoffice_member_detail",
                member_id=profile.pk,
            )
    else:
        form = SecretariatQuickAddMemberForm()

    return render(
        request,
        "membership/backoffice/quick_add.html",
        {"form": form},
    )


@role_required(User.Role.SECRETARIAT, User.Role.ADMIN)
def backoffice_export_csv(request: HttpRequest) -> HttpResponse:
    """Export the filtered member directory as a basic CSV file for secretariat administration."""
    queryset, _, _, _ = _filter_member_queryset(request)

    response = HttpResponse(content_type="text/csv; charset=utf-8")
    response["Content-Disposition"] = 'attachment; filename="members_export.csv"'

    writer = csv.writer(response)
    writer.writerow(
        [
            "member_number",
            "username",
            "first_name",
            "last_name",
            "email",
            "member_type",
            "status",
            "valid_from",
            "valid_until",
            "phone",
            "city",
            "licence_valid_until",
            "insurance_valid_until",
            "latest_payment_status",
        ]
    )

    for profile in queryset:
        payments = list(profile.payments.all())
        latest_payment_status = payments[0].status if payments else ""
        writer.writerow(
            [
                profile.member_number or "",
                profile.user.username,
                profile.user.first_name,
                profile.user.last_name,
                profile.user.email,
                profile.member_type,
                profile.status,
                profile.valid_from.isoformat() if profile.valid_from else "",
                profile.valid_until.isoformat() if profile.valid_until else "",
                profile.phone,
                profile.city,
                (
                    profile.licence_valid_until.isoformat()
                    if profile.licence_valid_until
                    else ""
                ),
                (
                    profile.insurance_valid_until.isoformat()
                    if profile.insurance_valid_until
                    else ""
                ),
                latest_payment_status,
            ]
        )

    return response

def eligibility_api_view(request: HttpRequest) -> JsonResponse:
    """
    Protected JSON API endpoint for the Student A -> Student B eligibility contract.

    Query parameters:
    - date (optional): ISO date YYYY-MM-DD (defaults to today).
    - user / email (optional): target identifier; secretariat/admin may query any member,
      while regular members may only query their own eligibility.
    """
    if request.method != "GET":
        return JsonResponse({"error": "Method not allowed."}, status=405)

    if not request.user.is_authenticated:
        return JsonResponse({"error": "Authentication required."}, status=401)

    date_param = (request.GET.get("date") or "").strip()
    if date_param:
        try:
            target_date = date.fromisoformat(date_param)
        except ValueError:
            return JsonResponse(
                {"error": "Invalid date format. Expected YYYY-MM-DD."},
                status=400,
            )
    else:
        target_date = timezone.localdate()

    requested_identifier = (
        request.GET.get("user") or request.GET.get("email") or ""
    ).strip()

    if requested_identifier:
        if not request.user.can_manage_members:
            own_profile = MemberProfile.objects.filter(user=request.user).first()
            own_identifiers = {
                request.user.username.lower(),
                (request.user.email or "").lower(),
            }
            if own_profile and own_profile.member_number:
                own_identifiers.add(own_profile.member_number.lower())
            if requested_identifier.lower() not in own_identifiers:
                return JsonResponse(
                    {
                        "error": "You do not have permission to check another member's eligibility."
                    },
                    status=403,
                )
        target_subject = requested_identifier
    else:
        target_subject = request.user

    result = check_eligibility(target_subject, target_date=target_date)
    return JsonResponse(result, status=200)