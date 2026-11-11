from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.notifications.reminders import send_due_reminders


class Command(BaseCommand):
    help = "Run the reminder check (PR6) once. Intended for cron in production."

    def handle(self, *args, **options):
        run = send_due_reminders(timezone.now())
        if not run.implemented:
            self.stdout.write("Reminder rules (PR6) arrive in Milestone 7; nothing was sent.")
            return
        self.stdout.write(f"Sent {run.reminders_sent} reminder(s) and {run.alerts_sent} alert(s).")
