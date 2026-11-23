from django.urls import path

from . import views

app_name = "membership"

urlpatterns = [
    path("calculator/", views.fee_calculator_view, name="fee_calculator"),
    path("apply/", views.apply_membership, name="apply"),
    path("my-application/", views.application_overview, name="application_overview"),
    path("my-card/", views.member_card_view, name="my_card"),
    path("cards/<int:member_id>/", views.member_card_view, name="member_card_detail"),
    path("export-data/", views.export_my_data, name="export_my_data"),
    path("api/eligibility/", views.eligibility_api_view, name="eligibility_api"),
    # Secretariat Back Office
    path("backoffice/", views.backoffice_member_list, name="backoffice_member_list"),
    path(
        "backoffice/members/quick-add/",
        views.backoffice_quick_add_member,
        name="backoffice_quick_add",
    ),
    path(
        "backoffice/members/<int:member_id>/",
        views.backoffice_member_detail,
        name="backoffice_member_detail",
    ),
    path(
        "backoffice/payments/<int:payment_id>/status/",
        views.backoffice_update_payment_status,
        name="backoffice_update_payment_status",
    ),
    path(
        "backoffice/export-csv/",
        views.backoffice_export_csv,
        name="backoffice_export_csv",
    ),
]