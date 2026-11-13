from django.contrib import admin

from .models import (
    ConsentRecord,
    FeeQuote,
    FeeRule,
    MemberProfile,
    MembershipStatusHistory,
    PaymentRecord,
)


@admin.register(MemberProfile)
class MemberProfileAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "member_number",
        "member_type",
        "status",
        "valid_until",
        "licence_valid_until",
        "insurance_valid_until",
    )
    list_filter = ("status", "member_type")
    search_fields = ("user__username", "user__email", "member_number", "phone")


@admin.register(FeeRule)
class FeeRuleAdmin(admin.ModelAdmin):
    list_display = (
        "version",
        "name",
        "base_fee_hunter",
        "base_fee_non_hunter",
        "insurance_addon_fee",
        "is_active",
        "is_placeholder",
    )
    list_filter = ("is_active", "is_placeholder")


@admin.register(FeeQuote)
class FeeQuoteAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "member",
        "rule_version_snapshot",
        "total_amount",
        "currency",
        "created_at",
    )
    readonly_fields = ("created_at",)


@admin.register(ConsentRecord)
class ConsentRecordAdmin(admin.ModelAdmin):
    list_display = ("user", "purpose", "consent_version", "accepted", "accepted_at")


@admin.register(MembershipStatusHistory)
class MembershipStatusHistoryAdmin(admin.ModelAdmin):
    list_display = ("member", "previous_status", "new_status", "changed_by", "changed_at")


@admin.register(PaymentRecord)
class PaymentRecordAdmin(admin.ModelAdmin):
    list_display = ("member", "amount", "currency", "status", "reference", "payment_date")
    list_filter = ("status",)