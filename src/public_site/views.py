from django.conf import settings
from django.core.paginator import Paginator
from django.http import Http404
from django.shortcuts import get_object_or_404, render

from .models import FAQ, Article, Category


def get_membership_register_url() -> str:
    return getattr(
        settings,
        "MEMBERSHIP_REGISTER_URL",
        getattr(settings, "MEMBERSHIP_REGISTRATION_URL", "/membership/apply/"),
    )


def can_preview_drafts(user) -> bool:
    if not user.is_authenticated:
        return False
    return bool(
        user.is_staff
        or user.is_superuser
        or getattr(user, "is_editor", False)
        or getattr(user, "is_secretariat", False)
        or getattr(user, "role", None) in ("editor", "secretariat", "admin")
    )


def home_view(request):
    latest_articles = (
        Article.objects.filter(status=Article.Status.PUBLISHED)
        .select_related("category")[:3]
    )
    context = {
        "membership_register_url": get_membership_register_url(),
        "featured_faqs": FAQ.objects.filter(is_published=True)[:3],
        "latest_articles": latest_articles,
    }
    return render(request, "public_site/home.html", context)


def about_view(request):
    context = {
        "membership_register_url": get_membership_register_url(),
    }
    return render(request, "public_site/about.html", context)


def how_to_join_view(request):
    context = {
        "membership_register_url": get_membership_register_url(),
    }
    return render(request, "public_site/how_to_join.html", context)


def faq_view(request):
    faqs = FAQ.objects.filter(is_published=True)
    context = {
        "faqs": faqs,
        "membership_register_url": get_membership_register_url(),
    }
    return render(request, "public_site/faq.html", context)


def article_list_view(request, category_slug=None):
    categories = Category.objects.all()
    articles_qs = Article.objects.filter(
        status=Article.Status.PUBLISHED
    ).select_related("category")

    active_category = None
    if category_slug:
        active_category = get_object_or_404(Category, slug=category_slug)
        articles_qs = articles_qs.filter(category=active_category)

    paginator = Paginator(articles_qs, 6)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    context = {
        "categories": categories,
        "active_category": active_category,
        "page_obj": page_obj,
        "articles": page_obj.object_list,
        "membership_register_url": get_membership_register_url(),
    }
    return render(request, "public_site/article_list.html", context)


def article_detail_view(request, slug):
    article = get_object_or_404(
        Article.objects.select_related("category"),
        slug=slug,
    )

    is_preview = False
    if article.status != Article.Status.PUBLISHED:
        if can_preview_drafts(request.user):
            is_preview = True
        else:
            raise Http404("Article not found or not published.")

    related_articles = (
        Article.objects.filter(
            status=Article.Status.PUBLISHED,
            category=article.category,
        )
        .exclude(id=article.id)[:3]
    )

    context = {
        "article": article,
        "is_preview": is_preview,
        "related_articles": related_articles,
        "membership_register_url": get_membership_register_url(),
    }
    return render(request, "public_site/article_detail.html", context)