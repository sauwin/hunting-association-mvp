from django.contrib import admin
from django.utils import timezone

from .models import (
    FAQ,
    Article,
    Category,
    MembershipEnquiry,
    Representative,
    VolunteerEnquiry,
)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug")
    search_fields = ("name", "description")
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display = ("title", "category", "author_byline", "status", "published_at")
    list_filter = ("status", "category", "published_at")
    search_fields = ("title", "summary", "body", "author_byline")
    prepopulated_fields = {"slug": ("title",)}
    actions = ["publish_articles", "unpublish_articles"]

    @admin.action(description="Publish selected articles")
    def publish_articles(self, request, queryset):
        now = timezone.now()
        for article in queryset:
            article.status = Article.Status.PUBLISHED
            if not article.published_at:
                article.published_at = now
            article.save()

    @admin.action(description="Unpublish selected articles (set to Draft)")
    def unpublish_articles(self, request, queryset):
        queryset.update(status=Article.Status.DRAFT)


@admin.register(FAQ)
class FAQAdmin(admin.ModelAdmin):
    list_display = ("question", "display_order", "is_published", "updated_at")
    list_filter = ("is_published",)
    list_editable = ("display_order", "is_published")
    search_fields = ("question", "answer")


@admin.register(Representative)
class RepresentativeAdmin(admin.ModelAdmin):
    list_display = (
        "display_name",
        "region",
        "role",
        "public_contact",
        "is_active",
        "display_order",
    )
    list_filter = ("is_active", "region")
    list_editable = ("is_active", "display_order")
    search_fields = ("display_name", "region", "role", "areas_of_interest")
    actions = ["activate_representatives", "deactivate_representatives"]

    @admin.action(description="Activate selected representatives")
    def activate_representatives(self, request, queryset):
        queryset.update(is_active=True)

    @admin.action(description="Deactivate selected representatives")
    def deactivate_representatives(self, request, queryset):
        queryset.update(is_active=False)


@admin.register(VolunteerEnquiry)
class VolunteerEnquiryAdmin(admin.ModelAdmin):
    list_display = (
        "full_name",
        "region",
        "email",
        "status",
        "consent_given",
        "created_at",
    )
    list_filter = ("status", "region", "consent_given", "created_at")
    list_editable = ("status",)
    search_fields = ("full_name", "email", "region", "interests", "message")
    readonly_fields = (
        "full_name",
        "region",
        "email",
        "phone",
        "interests",
        "message",
        "consent_given",
        "created_at",
        "updated_at",
    )
    actions = ["mark_as_contacted", "mark_as_accepted", "mark_as_declined"]

    @admin.action(description="Mark selected enquiries as Contacted")
    def mark_as_contacted(self, request, queryset):
        queryset.update(status=VolunteerEnquiry.Status.CONTACTED)

    @admin.action(description="Mark selected enquiries as Accepted")
    def mark_as_accepted(self, request, queryset):
        queryset.update(status=VolunteerEnquiry.Status.ACCEPTED)

    @admin.action(description="Mark selected enquiries as Declined")
    def mark_as_declined(self, request, queryset):
        queryset.update(status=VolunteerEnquiry.Status.DECLINED)


@admin.register(MembershipEnquiry)
class MembershipEnquiryAdmin(admin.ModelAdmin):
    list_display = (
        "full_name",
        "preferred_membership_type",
        "region",
        "email",
        "has_hunting_licence",
        "status",
        "consent_given",
        "created_at",
    )
    list_filter = (
        "status",
        "preferred_membership_type",
        "has_hunting_licence",
        "region",
        "consent_given",
        "created_at",
    )
    list_editable = ("status",)
    search_fields = ("full_name", "email", "region", "message")
    readonly_fields = (
        "full_name",
        "email",
        "phone",
        "region",
        "preferred_membership_type",
        "has_hunting_licence",
        "message",
        "consent_given",
        "created_at",
        "updated_at",
    )
    actions = ["mark_as_contacted", "mark_as_converted", "mark_as_closed"]

    @admin.action(description="Mark selected enquiries as Contacted")
    def mark_as_contacted(self, request, queryset):
        queryset.update(status=MembershipEnquiry.Status.CONTACTED)

    @admin.action(description="Mark selected enquiries as Converted to Applicant")
    def mark_as_converted(self, request, queryset):
        queryset.update(status=MembershipEnquiry.Status.CONVERTED)

    @admin.action(description="Mark selected enquiries as Closed")
    def mark_as_closed(self, request, queryset):
        queryset.update(status=MembershipEnquiry.Status.CLOSED)