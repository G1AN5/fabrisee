from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from apps.core.demo.accounts import DEMO_PASSWORD, USERS
from apps.core.demo.seed import DemoDataError, demo_data_exists, seed_demo


class Command(BaseCommand):
    help = (
        "Load the fictitious demo data: ten accounts, four clients, and eight projects with "
        "generated images and PDFs. Runs only when ALLOW_DEMO_SEED=1. Never use in production."
    )

    def handle(self, *args, **options):
        if not settings.ALLOW_DEMO_SEED:
            raise CommandError(
                "Demo data is disabled (ALLOW_DEMO_SEED is not 1). "
                "Production databases must never load the demo data."
            )
        if demo_data_exists():
            self.stdout.write(
                "The demo data is already loaded. Run `make reset-demo` to start over."
            )
            return
        try:
            counts = seed_demo()
        except DemoDataError as error:
            raise CommandError(str(error)) from error

        self.stdout.write(
            self.style.SUCCESS(
                f"Demo data loaded: {counts['clients']} clients, {counts['users']} users, "
                f"{counts['projects']} projects."
            )
        )
        self.stdout.write("")
        self.stdout.write(f"Demo accounts (password for all: {DEMO_PASSWORD})")
        for user in USERS:
            self.stdout.write(f"  {user.email:<28} {user.full_name:<20} {user.role}")
        self.stdout.write("")
        self.stdout.write("Demo only: do not use this password or this data in production.")
