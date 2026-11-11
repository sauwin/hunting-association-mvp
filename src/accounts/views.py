import hashlib
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.core.cache import cache
from django.shortcuts import redirect, render
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_http_methods

from .forms import EmailOrUsernameLoginForm, RegistrationForm


def _get_login_rate_limit_key(request, identifier: str = "") -> str:
    """Build a deterministic cache key per client IP and login identifier."""
    ip_addr = request.META.get("REMOTE_ADDR", "unknown")
    normalized_id = identifier.strip().lower()
    raw_key = f"login_attempts:{ip_addr}:{normalized_id}"
    digest = hashlib.sha256(raw_key.encode("utf-8")).hexdigest()
    return f"auth_rl_{digest}"


@require_http_methods(["GET", "POST"])
def register_view(request):
    if request.user.is_authenticated:
        return redirect("accounts:dashboard")

    if request.method == "POST":
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Account registered successfully.")
            return redirect("accounts:dashboard")
    else:
        form = RegistrationForm()

    return render(request, "accounts/register.html", {"form": form})


@require_http_methods(["GET", "POST"])
def login_view(request):
    if request.user.is_authenticated:
        return redirect("accounts:dashboard")

    max_attempts = getattr(settings, "LOGIN_RATE_LIMIT_ATTEMPTS", 5)
    timeout = getattr(settings, "LOGIN_RATE_LIMIT_TIMEOUT", 300)

    if request.method == "POST":
        identifier = request.POST.get("identifier", "")
        rl_key = _get_login_rate_limit_key(request, identifier)
        attempts = cache.get(rl_key, 0)

        if attempts >= max_attempts:
            form = EmailOrUsernameLoginForm(request=request)
            form.cleaned_data = {}
            form.add_error(
                None,
                "Too many failed login attempts. Please wait a few minutes and try again.",
            )
            return render(
                request,
                "accounts/login.html",
                {"form": form, "rate_limited": True},
                status=429,
            )

        form = EmailOrUsernameLoginForm(request=request, data=request.POST)
        if form.is_valid():
            cache.delete(rl_key)
            user = form.get_user()
            login(request, user)
            next_url = request.GET.get("next") or request.POST.get("next")
            if next_url and url_has_allowed_host_and_scheme(
                url=next_url,
                allowed_hosts={request.get_host()},
                require_https=request.is_secure(),
            ):
                return redirect(next_url)
            return redirect("accounts:dashboard")

        cache.set(rl_key, attempts + 1, timeout)
    else:
        form = EmailOrUsernameLoginForm(request=request)

    return render(request, "accounts/login.html", {"form": form})


@require_http_methods(["GET", "POST"])
def logout_view(request):
    logout(request)
    messages.info(request, "You have been signed out.")
    return redirect("accounts:login")


@login_required
def dashboard_view(request):
    return render(request, "accounts/dashboard.html", {"user": request.user})