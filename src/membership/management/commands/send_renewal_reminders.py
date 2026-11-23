from datetime import date, timedelta

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from common.notifications import SUPPORTED_CHANNELS, send
from membership.models import MemberProfile


class Command(BaseCommand):
    help = (
        "MVP scheduled-job stub: find active members whose membership expires "
        "within the configured window and dispatch renewal reminder notifications."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--days",
            type=int,
            default=30,
            help="Number of days ahead to check for expiring memberships (default: 30).",
        )
        parser.add_argument(
            "--date",
            dest="reference_date",
            type=str,
            default=None,
            help="Reference date in ISO format YYYY-MM-DD (defaults to today).",
        )
        parser.add_argument(
            "--channel",
            type=str,
            default="email",
            choices=sorted(SUPPORTED_CHANNELS),
            help="Notification channel to use (default: email).",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Preview matching members without dispatching notifications.",
        )

    def handle(self, *args, **options):
        days = options["days"]
        if days < 0:
            raise CommandError("--days must be a non-negative integer.")

        reference_date_str = options["reference_date"]
        if reference_date_str:
            try:
                reference_date = date.fromisoformat(reference_date_str)
            except ValueError as exc:
                raise CommandError(
                    "Invalid --date format. Expected YYYY-MM-DD."
                ) from exc
        else:
            reference_date = timezone.localdate()

        cutoff_date = reference_date + timedelta(days=days)
        channel = options["channel"]
        dry_run = options["dry_run"]

        expiring_profiles = (
            MemberProfile.objects.select_related("user")
            .filter(
                status=MemberProfile.Status.ACTIVE,
                valid_until__isnull=False,
                valid_until__gte=reference_date,
                valid_until__lte=cutoff_date,
            )
            .order_by("valid_until", "pk")
        )

        sent_count = 0
        skipped_count = 0

        for profile in expiring_profiles:
            recipient = (profile.user.email or "").strip()
            if not recipient:
                skipped_count += 1
                self.stdout.write(
                    self.style.WARNING(
                        f"Skipped member '{profile.user.username}' (no email configured)."
                    )
                )
                continue

            days_remaining = (profile.valid_until - reference_date).days
            member_name = (
                f"{profile.user.first_name} {profile.user.last_name}".strip()
                or profile.user.username
            )
            context = {
                "member_name": member_name,
                "member_number": profile.member_number or "Pending",
                "valid_until": profile.valid_until.isoformat(),
                "days_remaining": days_remaining,
            }

            if dry_run:
                self.stdout.write(
                    f"[DRY-RUN] Would notify {recipient} "
                    f"(member={context['member_number']}, valid_until={context['valid_until']}, "
                    f"days_remaining={days_remaining})"
                )
            else:
                send(
                    channel=channel,
                    recipient=recipient,
                    template="renewal_reminder",
                    context=context,
                )
                self.stdout.write(
                    f"Sent renewal reminder via '{channel}' to {recipient} "
                    f"(valid_until={context['valid_until']})"
                )
            sent_count += 1

        mode_label = "DRY-RUN complete" if dry_run else "Renewal reminder job complete"
        self.stdout.write(
            self.style.SUCCESS(
                f"{mode_label}: processed={sent_count}, skipped={skipped_count}, "
                f"window={reference_date.isoformat()}..{cutoff_date.isoformat()}."
            )
        )