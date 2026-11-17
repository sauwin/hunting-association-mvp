from django.urls import path

from . import views

app_name = "public_site"

urlpatterns = [
    path("", views.home_view, name="home"),
    path("about/", views.about_view, name="about"),
    path("how-to-join/", views.how_to_join_view, name="how_to_join"),
    path("faq/", views.faq_view, name="faq"),
    path("news/", views.article_list_view, name="article_list"),
    path(
        "news/category/<slug:category_slug>/",
        views.article_list_view,
        name="article_list_by_category",
    ),
    path("news/<slug:slug>/", views.article_detail_view, name="article_detail"),
]