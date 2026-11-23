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
    path("representatives/", views.representatives_view, name="representatives"),
    path("volunteer/", views.volunteer_view, name="volunteer"),
    path(
        "membership-interest/",
        views.membership_interest_view,
        name="membership_interest",
    ),
    path("robots.txt", views.robots_txt_view, name="robots_txt"),
    path("sitemap.xml", views.sitemap_xml_view, name="sitemap_xml"),
]