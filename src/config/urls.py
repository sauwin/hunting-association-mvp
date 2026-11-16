from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/", include("accounts.urls")),
    path("membership/", include("membership.urls")),
    path("", include("public_site.urls")),
]