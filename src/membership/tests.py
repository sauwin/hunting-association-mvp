from decimal import Decimal
from io import StringIO

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase

from .models import ConsentRecord, FeeQuote, FeeRule, MemberProfile
from .services import (
    DEFAULT_CONSENT_TEXT,
    DEFAULT_CONSENT_VERSION,
    calculate_fee_breakdown,
    create_frozen_fee_quote,
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

        # Update existing rule prices in place and create a new rule version
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