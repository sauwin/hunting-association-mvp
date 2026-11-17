from django.contrib import admin
from django.utils import timezone

from .models import FAQ, Article, Category


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