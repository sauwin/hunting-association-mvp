from io import StringIO

from django.core.management import call_command
from django.test import TestCase


class MigrationDriftTests(TestCase):
    """Project rule: every schema change ships with a migration.

    If a model is edited (fields, choices, constraints...) without running
    `makemigrations`, a clean database and a deployed database silently end
    up with different schemas. This test fails as soon as that happens.
    """

    def test_models_and_migrations_are_in_sync(self):
        out = StringIO()
        try:
            call_command(
                "makemigrations", "--check", "--dry-run", stdout=out, stderr=out
            )
        except SystemExit:
            self.fail(
                "Models have changes without a migration - run "
                "`python manage.py makemigrations`.\n" + out.getvalue()
            )
