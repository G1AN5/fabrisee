"""Email backend for development: store every message in the email log.

Nothing leaves the machine. The administrator reads the messages on the "Email outbox"
page, which shows that notifications work without a real mail server.
"""

import sys

from django.conf import settings
from django.core.mail.backends.base import BaseEmailBackend

# Header set by `apps.notifications.services` on messages it already logged.
EMAIL_LOG_HEADER = "X-FabriSee-Email-Log"


class DatabaseEmailBackend(BaseEmailBackend):
    def send_messages(self, email_messages):
        from .models import EmailLog, EmailStatus

        count = 0
        for message in email_messages or []:
            html = ""
            for content, mimetype in getattr(message, "alternatives", None) or []:
                if mimetype == "text/html":
                    html = content
            already_logged = EMAIL_LOG_HEADER in (message.extra_headers or {})
            if not already_logged:
                # Mail sent outside notify() (for example Django's password reset email).
                for recipient in message.recipients():
                    EmailLog.objects.create(
                        to=recipient,
                        subject=message.subject,
                        body_text=message.body,
                        body_html=html,
                        status=EmailStatus.LOGGED,
                    )
            if settings.EMAIL_LOG_TO_CONSOLE:
                self._print(message)
            count += 1
        return count

    @staticmethod
    def _print(message) -> None:
        recipients = ", ".join(message.recipients())
        sys.stdout.write(f"[email] To: {recipients} | {message.subject}\n")
        sys.stdout.flush()
