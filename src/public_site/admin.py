from django.contrib import admin
from .models import FAQ


@admin.register(FAQ)
class FAQAdmin(admin.ModelAdmin):
    list_display = ("question", "display_order", "is_published", "updated_at")
    list_editable = ("display_order", "is_published")
    list_filter = ("is_published",)
    search_fields = ("question", "answer")
    ordering = ("display_order", "id")