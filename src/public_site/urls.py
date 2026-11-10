from django.urls import path
from . import views

app_name = "public_site"

urlpatterns = [
    path("", views.home_view, name="home"),
    path("about/", views.about_view, name="about"),
    path("how-to-join/", views.how_to_join_view, name="how_to_join"),
    path("faq/", views.faq_view, name="faq"),
]