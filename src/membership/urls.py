from django.urls import path

from . import views

app_name = "membership"

urlpatterns = [
    path("calculator/", views.fee_calculator_view, name="fee_calculator"),
    path("apply/", views.apply_membership, name="apply"),
    path("my-application/", views.application_overview, name="application_overview"),
    path("export-data/", views.export_my_data, name="export_my_data"),
]