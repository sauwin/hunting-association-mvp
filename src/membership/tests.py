import csv
import json
from datetime import date
from decimal import Decimal
from io import StringIO

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse

from .models import (
    ConsentRecord,
    FeeQuote,
    FeeRule,
    MemberProfile,
    MembershipStatusHistory,
    PaymentRecord,
)

from .services import (
    DEFAULT_CONSENT_TEXT,
    DEFAULT_CONSENT_VERSION,
    calculate_fee_breakdown,
    create_frozen_fee_quote,
    transition_member_status,
)

User = get_user_model()


class MembershipModelsAndFeeCalculatorTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="applicant_demo",
            email="applicant@example.test",
            password="StrongPassword123!",
        )
        self.profile = MemberProfile.objects.create(
            user=self.user,
            member_type=MemberProfile.MemberType.HUNTER,
            phone="+421900111222",
            street_address="Lesna 12",
            city="Nitra",
            postal_code="94901",
        )
        self.rule = FeeRule.objects.create(
            version="2026-v1-sample",
            name="2026 Standard Membership Fee Schedule (Sample)",
            base_fee_hunter=Decimal("60.00"),
            base_fee_non_hunter=Decimal("35.00"),
            insurance_addon_fee=Decimal("25.00"),
            reduced_discount_amount=Decimal("15.00"),
            currency="EUR",
            is_active=True,
            is_placeholder=True,
        )

    def test_seed_membership_demo_command_creates_placeholder_rule(self):
        FeeRule.objects.all().delete()
        out = StringIO()
        call_command("seed_membership_demo", stdout=out)

        seeded_rule = FeeRule.objects.get(version="2026-v1-sample")
        self.assertTrue(seeded_rule.is_active)
        self.assertTrue(seeded_rule.is_placeholder)
        self.assertEqual(seeded_rule.base_fee_hunter, Decimal("60.00"))
        self.assertIn("Created sample fee rule", out.getvalue())

    def test_calculate_fee_breakdown_with_addons_and_discounts(self):
        hunter_breakdown = calculate_fee_breakdown(
            member_type=MemberProfile.MemberType.HUNTER,
            include_insurance=True,
            apply_reduced_rate=False,
            fee_rule=self.rule,
        )
        self.assertEqual(hunter_breakdown["base_amount"], Decimal("60.00"))
        self.assertEqual(hunter_breakdown["insurance_amount"], Decimal("25.00"))
        self.assertEqual(hunter_breakdown["discount_amount"], Decimal("0.00"))
        self.assertEqual(hunter_breakdown["total_amount"], Decimal("85.00"))
        self.assertTrue(hunter_breakdown["is_placeholder"])
        self.assertIn("SAMPLE / PLACEHOLDER", hunter_breakdown["placeholder_label"])

        non_hunter_reduced = calculate_fee_breakdown(
            member_type=MemberProfile.MemberType.NON_HUNTER,
            include_insurance=False,
            apply_reduced_rate=True,
            fee_rule=self.rule,
        )
        self.assertEqual(non_hunter_reduced["base_amount"], Decimal("35.00"))
        self.assertEqual(non_hunter_reduced["discount_amount"], Decimal("15.00"))
        self.assertEqual(non_hunter_reduced["total_amount"], Decimal("20.00"))

    def test_changing_fee_rule_does_not_overwrite_existing_frozen_quotes(self):
        """Acceptance criterion: changing a fee rule affects new quotes but does not rewrite stored quotes."""
        initial_quote = create_frozen_fee_quote(
            member=self.profile,
            include_insurance=True,
            apply_reduced_rate=False,
            fee_rule=self.rule,
        )
        self.assertEqual(initial_quote.total_amount, Decimal("85.00"))
        self.assertEqual(initial_quote.rule_version_snapshot, "2026-v1-sample")

        self.rule.base_fee_hunter = Decimal("95.00")
        self.rule.insurance_addon_fee = Decimal("40.00")
        self.rule.save()

        new_rule = FeeRule.objects.create(
            version="2026-v2-sample",
            name="2026 Updated Fee Schedule (Sample)",
            base_fee_hunter=Decimal("100.00"),
            base_fee_non_hunter=Decimal("50.00"),
            insurance_addon_fee=Decimal("30.00"),
            reduced_discount_amount=Decimal("10.00"),
            currency="EUR",
            is_active=True,
            is_placeholder=True,
        )

        new_quote = create_frozen_fee_quote(
            member=self.profile,
            include_insurance=True,
            apply_reduced_rate=False,
            fee_rule=new_rule,
        )

        initial_quote.refresh_from_db()
        self.assertEqual(initial_quote.base_amount, Decimal("60.00"))
        self.assertEqual(initial_quote.insurance_amount, Decimal("25.00"))
        self.assertEqual(initial_quote.total_amount, Decimal("85.00"))
        self.assertEqual(initial_quote.rule_version_snapshot, "2026-v1-sample")

        self.assertEqual(new_quote.total_amount, Decimal("130.00"))
        self.assertEqual(new_quote.rule_version_snapshot, "2026-v2-sample")
        self.assertEqual(FeeQuote.objects.count(), 2)

    def test_member_profile_default_lifecycle_and_versioned_consent(self):
        self.assertEqual(self.profile.status, MemberProfile.Status.APPLICANT)

        consent = ConsentRecord.objects.create(
            user=self.user,
            consent_version=DEFAULT_CONSENT_VERSION,
            consent_text_snapshot=DEFAULT_CONSENT_TEXT,
            accepted=True,
        )
        self.assertTrue(consent.accepted)
        self.assertEqual(consent.consent_version, "2026-v1-demo")
        self.assertIn("SAMPLE / PLACEHOLDER", consent.consent_text_snapshot)


class MembershipApplicationAndExportViewsTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="web_applicant",
            email="web_applicant@example.test",
            password="StrongPassword123!",
        )
        self.rule = FeeRule.objects.create(
            version="2026-v1-sample",
            name="2026 Standard Membership Fee Schedule (Sample)",
            base_fee_hunter=Decimal("60.00"),
            base_fee_non_hunter=Decimal("35.00"),
            insurance_addon_fee=Decimal("25.00"),
            reduced_discount_amount=Decimal("15.00"),
            currency="EUR",
            is_active=True,
            is_placeholder=True,
        )

    def test_fee_calculator_view_renders_sample_breakdown(self):
        response = self.client.get(
            reverse("membership:fee_calculator"),
            {
                "member_type": MemberProfile.MemberType.HUNTER,
                "include_insurance": "on",
                "apply_reduced_rate": "on",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "70.00 EUR")
        self.assertContains(response, "SAMPLE / PLACEHOLDER")

    def test_apply_membership_rejects_missing_consent_or_missing_licence_number(self):
        self.client.force_login(self.user)
        response = self.client.post(
            reverse("membership:apply"),
            {
                "first_name": "Jan",
                "last_name": "Novak",
                "member_type": MemberProfile.MemberType.HUNTER,
                "phone": "+421900333444",
                "street_address": "Hlavna 5",
                "city": "Nitra",
                "postal_code": "94901",
                "hunting_licence_number": "",
                "licence_valid_until": "2027-12-31",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(MemberProfile.objects.filter(user=self.user).exists())
        self.assertContains(
            response,
            "Please provide a hunting licence number when specifying a licence expiry date.",
        )

    def test_apply_membership_creates_profile_consent_status_history_and_quote(self):
        self.client.force_login(self.user)
        response = self.client.post(
            reverse("membership:apply"),
            {
                "first_name": "Jan",
                "last_name": "Novak",
                "member_type": MemberProfile.MemberType.HUNTER,
                "phone": "+421900333444",
                "street_address": "Hlavna 5",
                "city": "Nitra",
                "postal_code": "94901",
                "hunting_licence_number": "SK-NR-2026-001",
                "licence_valid_until": "2027-12-31",
                "insurance_valid_until": "2027-12-31",
                "include_insurance": "on",
                "consent_accepted": "on",
            },
        )
        self.assertRedirects(response, reverse("membership:application_overview"))

        profile = MemberProfile.objects.get(user=self.user)
        self.assertEqual(profile.status, MemberProfile.Status.APPLICANT)
        self.assertEqual(
            MembershipStatusHistory.objects.filter(member=profile).count(), 1
        )
        self.assertEqual(ConsentRecord.objects.filter(user=self.user).count(), 1)

        quote = FeeQuote.objects.get(member=profile)
        self.assertEqual(quote.total_amount, Decimal("85.00"))
        self.assertEqual(quote.rule_version_snapshot, "2026-v1-sample")

    def test_export_my_data_returns_gdpr_json_bundle(self):
        self.client.force_login(self.user)
        self.client.post(
            reverse("membership:apply"),
            {
                "first_name": "Jan",
                "last_name": "Novak",
                "member_type": MemberProfile.MemberType.NON_HUNTER,
                "phone": "+421900333444",
                "street_address": "Hlavna 5",
                "city": "Nitra",
                "postal_code": "94901",
                "apply_reduced_rate": "on",
                "consent_accepted": "on",
            },
        )

        export_response = self.client.get(reverse("membership:export_my_data"))
        self.assertEqual(export_response.status_code, 200)
        self.assertEqual(export_response["Content-Type"], "application/json")

        payload = json.loads(export_response.content)
        self.assertEqual(payload["account"]["username"], "web_applicant")
        self.assertEqual(payload["member_profile"]["city"], "Nitra")
        self.assertEqual(len(payload["fee_quotes"]), 1)
        self.assertEqual(payload["fee_quotes"][0]["total_amount"], "20.00")
        self.assertEqual(len(payload["consents"]), 1)


class MembershipLifecycleAndCardTests(TestCase):
    def setUp(self):
        self.member_user = User.objects.create_user(
            username="card_member",
            email="card_member@example.test",
            password="StrongPassword123!",
            first_name="Peter",
            last_name="Kovac",
            role=User.Role.MEMBER,
        )
        self.other_user = User.objects.create_user(
            username="other_member",
            email="other_member@example.test",
            password="StrongPassword123!",
            first_name="Marek",
            last_name="Horvath",
            role=User.Role.MEMBER,
        )
        self.secretariat_user = User.objects.create_user(
            username="secretariat_staff",
            email="secretariat@example.test",
            password="StrongPassword123!",
            role=User.Role.SECRETARIAT,
        )
        self.profile = MemberProfile.objects.create(
            user=self.member_user,
            member_type=MemberProfile.MemberType.HUNTER,
            phone="+421900555666",
            street_address="Lesna 99",
            city="Nitra",
            postal_code="94901",
            hunting_licence_number="SK-SECRET-777",
        )
        self.other_profile = MemberProfile.objects.create(
            user=self.other_user,
            member_type=MemberProfile.MemberType.NON_HUNTER,
            phone="+421900777888",
            street_address="Dubova 4",
            city="Trnava",
            postal_code="91701",
        )

    def test_transition_member_status_generates_member_number_and_logs_history(self):
        self.assertEqual(self.profile.status, MemberProfile.Status.APPLICANT)
        self.assertIsNone(self.profile.member_number)

        expiry = date(2027, 12, 31)
        transition_member_status(
            member=self.profile,
            new_status=MemberProfile.Status.ACTIVE,
            changed_by=self.secretariat_user,
            valid_until=expiry,
            note="Approved after fee payment verification.",
        )

        self.profile.refresh_from_db()
        self.assertEqual(self.profile.status, MemberProfile.Status.ACTIVE)
        self.assertTrue(self.profile.member_number.startswith("HA-"))
        self.assertEqual(self.profile.valid_until, expiry)

        transition_member_status(
            member=self.profile,
            new_status=MemberProfile.Status.SUSPENDED,
            changed_by=self.secretariat_user,
            note="Temporary administrative hold.",
        )
        self.profile.refresh_from_db()
        self.assertEqual(self.profile.status, MemberProfile.Status.SUSPENDED)
        self.assertEqual(self.profile.status_history.count(), 2)

    def test_member_card_displays_only_mvp_fields_and_supports_download(self):
        transition_member_status(
            member=self.profile,
            new_status=MemberProfile.Status.ACTIVE,
            changed_by=self.secretariat_user,
            valid_until=date(2027, 12, 31),
        )
        self.client.force_login(self.member_user)

        response = self.client.get(reverse("membership:my_card"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.profile.member_number)
        self.assertContains(response, "Peter Kovac")
        self.assertContains(response, "Active")
        self.assertContains(response, "2027-12-31")

        # Private fields must NOT appear on the digital member card
        self.assertNotContains(response, "+421900555666")
        self.assertNotContains(response, "Lesna 99")
        self.assertNotContains(response, "SK-SECRET-777")

        download_response = self.client.get(
            f"{reverse('membership:my_card')}?download=1"
        )
        self.assertEqual(download_response.status_code, 200)
        self.assertIn("attachment;", download_response["Content-Disposition"])

    def test_member_cannot_access_another_members_card_but_secretariat_can(self):
        self.client.force_login(self.member_user)
        forbidden_response = self.client.get(
            reverse(
                "membership:member_card_detail",
                kwargs={"member_id": self.other_profile.pk},
            )
        )
        self.assertEqual(forbidden_response.status_code, 403)

        self.client.force_login(self.secretariat_user)
        allowed_response = self.client.get(
            reverse(
                "membership:member_card_detail",
                kwargs={"member_id": self.other_profile.pk},
            )
        )
        self.assertEqual(allowed_response.status_code, 200)
        self.assertContains(allowed_response, "Marek Horvath")

class SecretariatBackOfficeTests(TestCase):
    def setUp(self):
        self.secretariat_user = User.objects.create_user(
            username="secretariat_bo",
            email="secretariat_bo@example.test",
            password="StrongPassword123!",
            role=User.Role.SECRETARIAT,
        )
        self.member_user = User.objects.create_user(
            username="regular_member",
            email="regular_member@example.test",
            password="StrongPassword123!",
            first_name="Lukas",
            last_name="Bielik",
            role=User.Role.MEMBER,
        )
        self.rule = FeeRule.objects.create(
            version="2026-v1-sample",
            name="2026 Standard Membership Fee Schedule (Sample)",
            base_fee_hunter=Decimal("60.00"),
            base_fee_non_hunter=Decimal("35.00"),
            insurance_addon_fee=Decimal("25.00"),
            reduced_discount_amount=Decimal("15.00"),
            currency="EUR",
            is_active=True,
            is_placeholder=True,
        )
        self.profile = MemberProfile.objects.create(
            user=self.member_user,
            member_type=MemberProfile.MemberType.HUNTER,
            phone="+421900111999",
            street_address="Lesna 15",
            city="Nitra",
            postal_code="94901",
            status=MemberProfile.Status.APPLICANT,
        )
        self.quote = create_frozen_fee_quote(
            member=self.profile,
            include_insurance=True,
            apply_reduced_rate=False,
            fee_rule=self.rule,
        )

    def test_member_cannot_access_secretariat_backoffice_actions(self):
        payment = PaymentRecord.objects.create(
            member=self.profile,
            quote=self.quote,
            status=PaymentRecord.Status.PENDING,
            amount=Decimal("85.00"),
            currency="EUR",
            reference="REF-001",
        )

        # Unauthenticated requests redirect to login
        anon_response = self.client.get(reverse("membership:backoffice_member_list"))
        self.assertEqual(anon_response.status_code, 302)
        self.assertIn("/accounts/login/", anon_response["Location"])

        # Authenticated regular member is blocked with HTTP 403 on all staff endpoints
        self.client.force_login(self.member_user)
        self.assertEqual(
            self.client.get(reverse("membership:backoffice_member_list")).status_code,
            403,
        )
        self.assertEqual(
            self.client.get(
                reverse(
                    "membership:backoffice_member_detail",
                    kwargs={"member_id": self.profile.pk},
                )
            ).status_code,
            403,
        )
        self.assertEqual(
            self.client.get(reverse("membership:backoffice_quick_add")).status_code,
            403,
        )
        self.assertEqual(
            self.client.get(reverse("membership:backoffice_export_csv")).status_code,
            403,
        )
        self.assertEqual(
            self.client.post(
                reverse(
                    "membership:backoffice_update_payment_status",
                    kwargs={"payment_id": payment.pk},
                ),
                {"status": PaymentRecord.Status.PAID},
            ).status_code,
            403,
        )

    def test_backoffice_member_list_search_filter_and_pagination(self):
        for idx in range(11):
            extra_user = User.objects.create_user(
                username=f"extra_member_{idx}",
                email=f"extra_{idx}@example.test",
                password="StrongPassword123!",
                first_name=f"Member{idx}",
                last_name="Test",
                role=User.Role.MEMBER,
            )
            MemberProfile.objects.create(
                user=extra_user,
                member_type=MemberProfile.MemberType.NON_HUNTER,
                phone=f"+421900000{idx:03d}",
                street_address="Hlavna 1",
                city="Trnava",
                postal_code="91701",
                status=MemberProfile.Status.ACTIVE,
            )

        self.client.force_login(self.secretariat_user)

        page_1 = self.client.get(reverse("membership:backoffice_member_list"))
        self.assertEqual(page_1.status_code, 200)
        self.assertEqual(len(page_1.context["page_obj"]), 10)
        self.assertEqual(page_1.context["page_obj"].paginator.num_pages, 2)

        page_2 = self.client.get(
            reverse("membership:backoffice_member_list"), {"page": 2}
        )
        self.assertEqual(page_2.status_code, 200)
        self.assertEqual(len(page_2.context["page_obj"]), 2)

        filtered = self.client.get(
            reverse("membership:backoffice_member_list"),
            {
                "q": "Nitra",
                "status": MemberProfile.Status.APPLICANT,
                "member_type": MemberProfile.MemberType.HUNTER,
            },
        )
        self.assertEqual(filtered.status_code, 200)
        self.assertEqual(len(filtered.context["page_obj"]), 1)
        self.assertContains(filtered, "Lukas Bielik")

    def test_secretariat_can_approve_application_and_manage_manual_payments(self):
        self.client.force_login(self.secretariat_user)
        detail_url = reverse(
            "membership:backoffice_member_detail",
            kwargs={"member_id": self.profile.pk},
        )

        # Approve application and set validity dates
        approve_response = self.client.post(
            detail_url,
            {
                "action": "update_status",
                "status": MemberProfile.Status.ACTIVE,
                "valid_from": "2026-11-19",
                "valid_until": "2027-11-19",
                "note": "Approved by secretariat.",
            },
        )
        self.assertRedirects(approve_response, detail_url)

        self.profile.refresh_from_db()
        self.assertEqual(self.profile.status, MemberProfile.Status.ACTIVE)
        self.assertTrue(self.profile.member_number.startswith("HA-"))
        self.assertEqual(self.profile.valid_from, date(2026, 11, 19))
        self.assertEqual(self.profile.valid_until, date(2027, 11, 19))
        history_entry = self.profile.status_history.first()
        self.assertEqual(history_entry.changed_by, self.secretariat_user)

        # Record a manual pending payment
        payment_response = self.client.post(
            detail_url,
            {
                "action": "record_payment",
                "quote": self.quote.pk,
                "status": PaymentRecord.Status.PENDING,
                "amount": "85.00",
                "currency": "EUR",
                "reference": "VS-2026-0042",
                "notes": "Awaiting bank transfer confirmation.",
            },
        )
        self.assertRedirects(payment_response, detail_url)

        payment = PaymentRecord.objects.get(member=self.profile)
        self.assertEqual(payment.status, PaymentRecord.Status.PENDING)
        self.assertEqual(payment.amount, Decimal("85.00"))
        self.assertEqual(payment.reference, "VS-2026-0042")
        self.assertEqual(payment.recorded_by, self.secretariat_user)
        self.assertIsNone(payment.payment_date)

        # Update manual payment status to paid (auto-populates payment_date)
        update_response = self.client.post(
            reverse(
                "membership:backoffice_update_payment_status",
                kwargs={"payment_id": payment.pk},
            ),
            {"status": PaymentRecord.Status.PAID},
        )
        self.assertRedirects(update_response, detail_url)

        payment.refresh_from_db()
        self.assertEqual(payment.status, PaymentRecord.Status.PAID)
        self.assertIsNotNone(payment.payment_date)
        self.assertEqual(payment.recorded_by, self.secretariat_user)

    def test_secretariat_quick_add_creates_member_profile_history_and_quote(self):
        self.client.force_login(self.secretariat_user)
        response = self.client.post(
            reverse("membership:backoffice_quick_add"),
            {
                "username": "quick_demo_member",
                "email": "quick_demo@example.test",
                "first_name": "Martin",
                "last_name": "Kral",
                "member_type": MemberProfile.MemberType.HUNTER,
                "status": MemberProfile.Status.ACTIVE,
                "phone": "+421900222333",
                "street_address": "Polna 8",
                "city": "Nitra",
                "postal_code": "94901",
                "hunting_licence_number": "SK-NR-2026-900",
                "licence_valid_until": "2028-01-31",
                "insurance_valid_until": "2027-12-31",
                "valid_from": "2026-11-19",
                "valid_until": "2027-12-31",
                "include_insurance": "on",
            },
        )

        created_profile = MemberProfile.objects.get(
            user__username="quick_demo_member"
        )
        self.assertRedirects(
            response,
            reverse(
                "membership:backoffice_member_detail",
                kwargs={"member_id": created_profile.pk},
            ),
        )
        self.assertEqual(created_profile.status, MemberProfile.Status.ACTIVE)
        self.assertTrue(created_profile.member_number.startswith("HA-"))
        self.assertEqual(created_profile.status_history.count(), 1)
        self.assertEqual(created_profile.fee_quotes.count(), 1)
        self.assertEqual(
            created_profile.fee_quotes.first().total_amount,
            Decimal("85.00"),
        )

    def test_secretariat_can_export_filtered_csv(self):
        transition_member_status(
            member=self.profile,
            new_status=MemberProfile.Status.ACTIVE,
            changed_by=self.secretariat_user,
            valid_from=date(2026, 11, 19),
            valid_until=date(2027, 12, 31),
        )
        PaymentRecord.objects.create(
            member=self.profile,
            quote=self.quote,
            status=PaymentRecord.Status.PAID,
            amount=Decimal("85.00"),
            currency="EUR",
            reference="CSV-REF-01",
            payment_date=date(2026, 11, 19),
            recorded_by=self.secretariat_user,
        )

        other_user = User.objects.create_user(
            username="pending_applicant",
            email="pending@example.test",
            password="StrongPassword123!",
            role=User.Role.MEMBER,
        )
        MemberProfile.objects.create(
            user=other_user,
            member_type=MemberProfile.MemberType.NON_HUNTER,
            phone="+421900888777",
            street_address="Nova 3",
            city="Bratislava",
            postal_code="81101",
            status=MemberProfile.Status.APPLICANT,
        )

        self.client.force_login(self.secretariat_user)
        response = self.client.get(
            reverse("membership:backoffice_export_csv"),
            {"status": MemberProfile.Status.ACTIVE},
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response["Content-Type"].startswith("text/csv"))
        self.assertIn('filename="members_export.csv"', response["Content-Disposition"])

        rows = list(csv.DictReader(StringIO(response.content.decode("utf-8"))))
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["username"], "regular_member")
        self.assertEqual(rows[0]["status"], "active")
        self.assertEqual(rows[0]["valid_until"], "2027-12-31")
        self.assertEqual(rows[0]["latest_payment_status"], "paid")