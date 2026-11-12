from decimal import Decimal
from django.conf import settings
from django.db import models
from django.utils import timezone


class MemberProfile(models.Model):
    class MemberType(models.TextChoices):
        HUNTER = "hunter", "Hunter"
        NON_HUNTER = "non_hunter", "Non-Hunter"

    class Status(models.TextChoices):
        APPLICANT = "applicant", "Applicant"
        ACTIVE = "active", "Active"
        EXPIRED = "expired", "Expired"
        SUSPENDED = "suspended", "Suspended"

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="member_profile",
    )
    member_number = models.CharField(
        max_length=32,
        unique=True,
        blank=True,
        null=True,
        help_text="Assigned unique member ID (e.g. SPK-2026-0001).",
    )
    member_type = models.CharField(
        max_length=20,
        choices=MemberType.choices,
        default=MemberType.HUNTER,
    )
    phone = models.CharField(max_length=40)
    street_address = models.CharField(max_length=255)
    city = models.CharField(max_length=120)
    postal_code = models.CharField(max_length=20)

    # Optional fields required for eligibility contract checks
    hunting_licence_number = models.CharField(max_length=64, blank=True)
    licence_valid_until = models.DateField(blank=True, null=True)
    insurance_valid_until = models.DateField(blank=True, null=True)

    # Membership lifecycle & validity dates
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.APPLICANT,
    )
    valid_from = models.DateField(blank=True, null=True)
    valid_until = models.DateField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        identifier = self.member_number or self.user.username
        return f"{identifier} ({self.get_status_display()})"


class MembershipStatusHistory(models.Model):
    member = models.ForeignKey(
        MemberProfile,
        on_delete=models.CASCADE,
        related_name="status_history",
    )
    previous_status = models.CharField(
        max_length=20,
        choices=MemberProfile.Status.choices,
        blank=True,
    )
    new_status = models.CharField(
        max_length=20,
        choices=MemberProfile.Status.choices,
    )
    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="recorded_status_changes",
    )
    note = models.CharField(max_length=255, blank=True)
    changed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-changed_at"]

    def __str__(self) -> str:
        return f"{self.member_id}: {self.previous_status or 'none'} -> {self.new_status}"


class FeeRule(models.Model):
    version = models.CharField(
        max_length=32,
        unique=True,
        help_text="Immutable rule version code (e.g. 2026-v1-sample).",
    )
    name = models.CharField(max_length=150)
    base_fee_hunter = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default=Decimal("60.00"),
    )
    base_fee_non_hunter = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default=Decimal("35.00"),
    )
    insurance_addon_fee = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default=Decimal("25.00"),
    )
    reduced_discount_amount = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default=Decimal("15.00"),
        help_text="Optional student/senior reduced-fee discount placeholder.",
    )
    currency = models.CharField(max_length=8, default="EUR")
    is_active = models.BooleanField(default=True)
    is_placeholder = models.BooleanField(
        default=True,
        help_text="All MVP fee amounts must be marked sample/placeholder until approved.",
    )
    effective_from = models.DateField(default=timezone.now)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-effective_from", "-created_at"]

    def __str__(self) -> str:
        label = " [SAMPLE/PLACEHOLDER]" if self.is_placeholder else ""
        return f"{self.name} ({self.version}){label}"


class FeeQuote(models.Model):
    member = models.ForeignKey(
        MemberProfile,
        on_delete=models.CASCADE,
        related_name="fee_quotes",
    )
    fee_rule = models.ForeignKey(
        FeeRule,
        on_delete=models.PROTECT,
        related_name="quotes",
    )
    # Frozen snapshot fields so later FeeRule edits never alter stored quotes
    rule_version_snapshot = models.CharField(max_length=32)
    member_type_snapshot = models.CharField(
        max_length=20,
        choices=MemberProfile.MemberType.choices,
    )
    base_amount = models.DecimalField(max_digits=8, decimal_places=2)
    include_insurance = models.BooleanField(default=False)
    insurance_amount = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default=Decimal("0.00"),
    )
    apply_reduced_rate = models.BooleanField(default=False)
    discount_amount = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default=Decimal("0.00"),
    )
    total_amount = models.DecimalField(max_digits=8, decimal_places=2)
    currency = models.CharField(max_length=8, default="EUR")
    placeholder_label = models.CharField(
        max_length=255,
        default="SAMPLE / PLACEHOLDER FEE QUOTE — Subject to association approval",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"Quote #{self.pk} ({self.rule_version_snapshot}): {self.total_amount} {self.currency}"


class ConsentRecord(models.Model):
    class Purpose(models.TextChoices):
        MEMBERSHIP_PROCESSING = (
            "membership_processing",
            "Membership Application & Administration (Demo)",
        )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="consent_records",
    )
    purpose = models.CharField(
        max_length=64,
        choices=Purpose.choices,
        default=Purpose.MEMBERSHIP_PROCESSING,
    )
    consent_version = models.CharField(max_length=32, default="2026-v1-demo")
    consent_text_snapshot = models.TextField()
    accepted = models.BooleanField(default=True)
    accepted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-accepted_at"]

    def __str__(self) -> str:
        return f"{self.user.username} - {self.purpose} ({self.consent_version})"


class PaymentRecord(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        PAID = "paid", "Paid"
        OVERDUE = "overdue", "Overdue"
        CANCELLED = "cancelled", "Cancelled"

    member = models.ForeignKey(
        MemberProfile,
        on_delete=models.CASCADE,
        related_name="payments",
    )
    quote = models.ForeignKey(
        FeeQuote,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="payments",
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )
    amount = models.DecimalField(max_digits=8, decimal_places=2)
    currency = models.CharField(max_length=8, default="EUR")
    reference = models.CharField(max_length=100, blank=True)
    payment_date = models.DateField(blank=True, null=True)
    recorded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="recorded_payments",
    )
    notes = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.member} - {self.amount} {self.currency} ({self.status})"