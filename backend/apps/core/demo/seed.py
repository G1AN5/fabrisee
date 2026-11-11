"""Load the demo data (called by `manage.py seed_demo`)."""

from datetime import datetime, timedelta

from django.db import transaction
from django.utils import timezone

from apps.accounts.models import User
from apps.clients.models import Client
from apps.core.models import SystemSetting
from apps.projects.models import Project

from .accounts import CLIENTS, DEMO_PASSWORD, OWNER_EMAIL, USERS
from .projects import STORIES
from .scenario import DemoBuilder


class DemoDataError(Exception):
    """The demo data cannot be loaded into this database."""


def demo_data_exists() -> bool:
    return User.objects.filter(email=OWNER_EMAIL).exists()


@transaction.atomic
def seed_demo(now: datetime | None = None) -> dict[str, int]:
    """Create the demo accounts, clients, and the eight demo projects.

    Refuses to add demo data to a database that already has clients or projects.
    """
    now = now or timezone.now()
    if demo_data_exists():
        raise DemoDataError("The demo data is already loaded.")
    if Client.objects.exists() or Project.objects.exists():
        raise DemoDataError(
            "This database already has clients or projects. Demo data is only loaded into "
            "an empty database."
        )

    SystemSetting.load()
    builder = DemoBuilder(now)
    joined = now - timedelta(days=120)

    for definition in CLIENTS:
        builder.clients[definition.key] = Client.objects.create(
            company_name=definition.company_name,
            contact_person=definition.contact_person,
            email=definition.email,
            phone=definition.phone,
            address=definition.address,
            notes=definition.notes,
            created_at=joined,
        )
    for definition in USERS:
        client = builder.clients[definition.client_key] if definition.client_key else None
        user = User(
            email=definition.email,
            full_name=definition.full_name,
            role=definition.role,
            job_title=definition.job_title,
            phone=definition.phone,
            client=client,
            is_staff=definition.is_superuser,
            is_superuser=definition.is_superuser,
            privacy_acknowledged_at=joined if definition.privacy_acknowledged else None,
            created_at=joined,
        )
        user.set_password(DEMO_PASSWORD)
        user.save()
        builder.users[definition.key] = user

    for story in STORIES:
        story(builder)
    builder.finalize_read_state()

    return {
        "clients": Client.objects.count(),
        "users": User.objects.count(),
        "projects": Project.objects.count(),
    }
