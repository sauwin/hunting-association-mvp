from decimal import Decimal
from django.core.management.base import BaseCommand

from membership.models import FeeRule


class Command(BaseCommand):
    help = "Seed synthetic sample/placeholder membership fee rules for the MVP demo."

    def handle(self, *args, **options):
        rule, created = FeeRule.objects.update_or_create(
            version="2026-v1-sample",
            defaults={
                "name": "2026 Standard Membership Fee Schedule (Sample)",
                "base_fee_hunter": Decimal("60.00"),
                "base_fee_non_hunter": Decimal("35.00"),
                "insurance_addon_fee": Decimal("25.00"),
                "reduced_discount_amount": Decimal("15.00"),
                "currency": "EUR",
                "is_active": True,
                "is_placeholder": True,
            },
        )
        action = "Created" if created else "Updated"
        self.stdout.write(
            self.style.SUCCESS(
                f"{action} sample fee rule: {rule.version} ({rule.currency})"
            )
        )