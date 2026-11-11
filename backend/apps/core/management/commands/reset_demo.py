import shutil
from pathlib import Path

from django.conf import settings
from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError

UPLOAD_FOLDERS = ("documents", "quotations", "designs", "thumbnails")


class Command(BaseCommand):
    help = (
        "Delete ALL data and uploaded files, then load fresh demo data. "
        "Runs only when ALLOW_DEMO_SEED=1. Never use in production."
    )

    def add_arguments(self, parser):
        parser.add_argument("--yes", action="store_true", help="Do not ask for confirmation.")

    def handle(self, *args, yes=False, **options):
        if not settings.ALLOW_DEMO_SEED:
            raise CommandError(
                "Demo data is disabled (ALLOW_DEMO_SEED is not 1). "
                "reset_demo deletes all data and must never run in production."
            )
        if not yes:
            answer = input(
                "This deletes ALL data and uploaded files, then loads the demo data.\n"
                "Type 'reset' to continue: "
            )
            if answer.strip().lower() != "reset":
                self.stdout.write("Cancelled. Nothing was changed.")
                return

        call_command("migrate", interactive=False, verbosity=0)
        call_command("flush", interactive=False, verbosity=0)
        media_root = Path(settings.MEDIA_ROOT)
        for folder in UPLOAD_FOLDERS:
            shutil.rmtree(media_root / folder, ignore_errors=True)
        self.stdout.write("All data and uploaded files were deleted.")
        call_command("seed_demo", stdout=self.stdout)
