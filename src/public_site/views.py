from django.conf import settings
from django.shortcuts import render
from .models import FAQ


def get_membership_register_url() -> str:
    return getattr(
        settings,
        "MEMBERSHIP_REGISTER_URL",
        getattr(settings, "MEMBERSHIP_REGISTRATION_URL", "/membership/apply/"),
    )


def home_view(request):
    context = {
        "membership_register_url": get_membership_register_url(),
        "featured_faqs": FAQ.objects.filter(is_published=True)[:3],
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