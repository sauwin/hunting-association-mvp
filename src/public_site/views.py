import logging

from django.conf import settings
from django.contrib import messages
from django.core.paginator import Paginator
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import NoReverseMatch, reverse

from .forms import MembershipEnquiryForm, VolunteerEnquiryForm
from .models import FAQ, Article, Category, Representative

logger = logging.getLogger(__name__)


def _safe_reverse(url_name: str, fallback: str) -> str:
    try:
        return reverse(url_name)
    except NoReverseMatch:
        return fallback


def get_membership_register_url() -> str:
    configured = getattr(
        settings,
        "MEMBERSHIP_REGISTER_URL",
        getattr(settings, "MEMBERSHIP_REGISTRATION_URL", None),
    )
    if configured:
        return configured
    return _safe_reverse("membership:apply", "/membership/apply/")


def get_student_a_handoff_context() -> dict:
    return {
        "membership_register_url": get_membership_register_url(),
        "account_register_url": _safe_reverse("accounts:register", "/accounts/register/"),
        "membership_apply_url": _safe_reverse("membership:apply", "/membership/apply/"),
        "membership_calculator_url": _safe_reverse(
            "membership:fee_calculator", "/membership/calculator/"
        ),
    }


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
        **get_student_a_handoff_context(),
        "featured_faqs": FAQ.objects.filter(is_published=True)[:3],
        "latest_articles": latest_articles,
    }
    return render(request, "public_site/home.html", context)


def about_view(request):
    context = {
        **get_student_a_handoff_context(),
    }
    return render(request, "public_site/about.html", context)


def how_to_join_view(request):
    context = {
        **get_student_a_handoff_context(),
    }
    return render(request, "public_site/how_to_join.html", context)


def faq_view(request):
    faqs = FAQ.objects.filter(is_published=True)
    context = {
        "faqs": faqs,
        **get_student_a_handoff_context(),
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
        **get_student_a_handoff_context(),
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
        **get_student_a_handoff_context(),
    }
    return render(request, "public_site/article_detail.html", context)


def representatives_view(request):
    active_reps = Representative.objects.filter(is_active=True)
    regions = (
        active_reps.order_by("region")
        .values_list("region", flat=True)
        .distinct()
    )

    selected_region = request.GET.get("region", "").strip()
    if selected_region:
        active_reps = active_reps.filter(region=selected_region)

    context = {
        "representatives": active_reps,
        "regions": regions,
        "selected_region": selected_region,
        **get_student_a_handoff_context(),
    }
    return render(request, "public_site/representatives.html", context)


def volunteer_view(request):
    if request.method == "POST":
        form = VolunteerEnquiryForm(request.POST)
        if form.is_valid():
            enquiry = form.save()
            logger.info(
                "New volunteer enquiry submitted: id=%s region=%s",
                enquiry.id,
                enquiry.region,
            )
            messages.success(
                request,
                "Ďakujeme za váš záujem o dobrovoľníctvo! Vašu prihlášku sme zaznamenali a čoskoro sa vám ozveme.",
            )
            return redirect("public_site:volunteer")
    else:
        form = VolunteerEnquiryForm()

    context = {
        "form": form,
        **get_student_a_handoff_context(),
    }
    return render(request, "public_site/volunteer.html", context)


def membership_interest_view(request):
    if request.method == "POST":
        form = MembershipEnquiryForm(request.POST)
        if form.is_valid():
            enquiry = form.save()
            logger.info(
                "New membership enquiry submitted: id=%s type=%s region=%s",
                enquiry.id,
                enquiry.preferred_membership_type,
                enquiry.region,
            )
            messages.success(
                request,
                "Ďakujeme za váš záujem o členstvo! Váš dopyt sme zaevidovali. Ak ste pripravení podať riadnu prihlášku, môžete tak urobiť priamo online nižšie.",
            )
            return redirect("public_site:membership_interest")
    else:
        form = MembershipEnquiryForm()

    context = {
        "form": form,
        **get_student_a_handoff_context(),
    }
    return render(request, "public_site/membership_interest.html", context)