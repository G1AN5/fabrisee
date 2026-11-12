import time

from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.notifications.reminders import send_due_reminders


class Command(BaseCommand):
    help = (
        "Run the reminder check (PR6) in a loop, every REMINDER_CHECK_MINUTES minutes. "
        "Part of `make dev`; in production cron can call `send_due_reminders` instead."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--once", action="store_true", help="Run a single check and exit (used by tests)."
        )

    def handle(self, *args, once=False, **options):
        minutes = max(1, settings.REMINDER_CHECK_MINUTES)
        self.stdout.write(f"Scheduler started: checking for due reminders every {minutes} min.")
        announced_pending_work = False
        try:
            while True:
                run = send_due_reminders(timezone.now())
                if run.implemented:
                    if run.reminders_sent or run.alerts_sent:
                        self.stdout.write(
                            f"{timezone.localtime(run.checked_at):%Y-%m-%d %H:%M} "
                            f"sent {run.reminders_sent} reminder(s), {run.alerts_sent} alert(s)."
                        )
                elif not announced_pending_work:
                    self.stdout.write(
                        "Reminder rules (PR6) arrive in Milestone 7; nothing is sent yet."
                    )
                    announced_pending_work = True
                if once:
                    return
                time.sleep(minutes * 60)
        except KeyboardInterrupt:
            self.stdout.write("Scheduler stopped.")
