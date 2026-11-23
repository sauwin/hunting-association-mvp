import logging
from typing import Any

from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string

logger = logging.getLogger("common.notifications")

SUPPORTED_CHANNELS = frozenset({"email", "log"})

TEMPLATE_SUBJECTS: dict[str, str] = {
    "application_received": "[Hunting Association MVP] Membership Application Received (Sample)",
    "renewal_reminder": "[Hunting Association MVP] Membership Renewal Reminder (Sample)",
    "enquiry_acknowledgement": "[Hunting Association MVP] Enquiry Received (Sample)",
}


def render_notification(
    template: str,
    context: dict[str, Any] | None = None,
) -> tuple[str, str]:
    """Render subject and plain-text body for a supported notification template."""
    if template not in TEMPLATE_SUBJECTS:
        supported = ", ".join(sorted(TEMPLATE_SUBJECTS))
        raise ValueError(
            f"Unsupported notification template '{template}'. Supported templates: {supported}."
        )

    subject = TEMPLATE_SUBJECTS[template]
    body = render_to_string(f"notifications/{template}.txt", context or {}).strip()
    return subject, body


def send(
    channel: str,
    recipient: str,
    template: str,
    context: dict[str, Any] | None = None,
) -> bool:
    """
    Shared MVP notification interface owned by Student A (docs/contracts.md).

    Logs structured notification output and, for the 'email' channel, dispatches
    through Django's configured email backend (console backend by default in MVP).
    """
    normalized_channel = (channel or "").strip().lower()
    if normalized_channel not in SUPPORTED_CHANNELS:
        supported = ", ".join(sorted(SUPPORTED_CHANNELS))
        raise ValueError(
            f"Unsupported notification channel '{channel}'. Supported channels: {supported}."
        )

    cleaned_recipient = (recipient or "").strip()
    if not cleaned_recipient:
        raise ValueError("Notification recipient must be a non-empty string.")

    subject, body = render_notification(template, context)

    logger.info(
        "Notification dispatched | channel=%s | recipient=%s | template=%s | subject=%s",
        normalized_channel,
        cleaned_recipient,
        template,
        subject,
    )

    if normalized_channel == "email":
        send_mail(
            subject=subject,
            message=body,
            from_email=getattr(
                settings,
                "DEFAULT_FROM_EMAIL",
                "noreply@hunting-association-mvp.local",
            ),
            recipient_list=[cleaned_recipient],
            fail_silently=False,
        )

    return True