"""Loading and resetting the demo data (each test starts with an empty database)."""

from datetime import datetime, timedelta
from io import StringIO
from zoneinfo import ZoneInfo

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError

from apps.accounts.models import User
from apps.activity.models import ActivityLog
from apps.clients.models import Client
from apps.core.demo import drawing
from apps.core.demo.accounts import DEMO_PASSWORD
from apps.core.demo.seed import DemoDataError, seed_demo
from apps.core.tests.files import png_bytes
from apps.designs.models import RevisionStatus
from apps.notifications.models import Notification
from apps.projects.models import Project

MANILA = ZoneInfo("Asia/Manila")
NOW = datetime(2026, 11, 11, 14, 30, tzinfo=MANILA)
THREE_DAYS = timedelta(days=3)

pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def fast_drawing(monkeypatch):
    """Skip the slow image drawing: these tests only care about records and dates."""
    image = png_bytes(size=(320, 200))
    monkeypatch.setattr(drawing, "render_image", lambda *args, **kwargs: image)


def project(title: str) -> Project:
    return Project.objects.get(title=title)


def test_demo_data_is_only_loaded_into_an_empty_database():
    Client.objects.create(company_name="A real client")

    with pytest.raises(DemoDataError, match="already has clients or projects"):
        seed_demo(NOW)


def test_seed_commands_refuse_to_run_when_demo_data_is_disabled(settings):
    settings.ALLOW_DEMO_SEED = False

    with pytest.raises(CommandError, match="ALLOW_DEMO_SEED"):
        call_command("seed_demo")
    with pytest.raises(CommandError, match="ALLOW_DEMO_SEED"):
        call_command("reset_demo", "--yes")
    assert not User.objects.exists()


def test_seed_command_prints_the_accounts_and_skips_a_second_run():
    first, second = StringIO(), StringIO()

    call_command("seed_demo", stdout=first)
    call_command("seed_demo", stdout=second)

    assert "Demo data loaded: 4 clients, 10 users, 8 projects." in first.getvalue()
    assert DEMO_PASSWORD in first.getvalue()
    assert "owner@fabrisee.test" in first.getvalue()
    assert "already loaded" in second.getvalue()
    assert Project.objects.count() == 8


def test_reset_command_deletes_everything_and_loads_fresh_demo_data(settings):
    Client.objects.create(company_name="Left over from earlier")
    stale = settings.MEDIA_ROOT / "documents" / "1"
    stale.mkdir(parents=True)
    (stale / "old-upload.pdf").write_bytes(b"%PDF-1.4 old")
    out = StringIO()

    call_command("reset_demo", "--yes", stdout=out)

    assert not Client.objects.filter(company_name="Left over from earlier").exists()
    assert not (stale / "old-upload.pdf").exists()
    assert Project.objects.count() == 8
    assert "All data and uploaded files were deleted." in out.getvalue()


@pytest.mark.parametrize(
    "moment",
    [
        datetime(2026, 11, 11, 0, 20, tzinfo=MANILA),  # just after midnight
        datetime(2026, 11, 11, 7, 5, tzinfo=MANILA),  # before office hours
        datetime(2026, 11, 11, 23, 50, tzinfo=MANILA),  # late evening
        datetime(2027, 1, 3, 9, 30, tzinfo=MANILA),  # right after New Year
    ],
)
def test_demo_data_can_be_loaded_at_any_time_of_day(moment):
    """Dates are relative to the moment of loading; the situations must still hold."""
    seed_demo(moment)

    r2 = project("Experience counter and brand wall").revisions.get(revision_no=2)
    quotation = project("Product display stands (set of 6)").quotations.get()
    assert r2.status == RevisionStatus.PENDING_APPROVAL
    assert THREE_DAYS <= moment - r2.uploaded_at < timedelta(days=4)
    assert THREE_DAYS <= moment - quotation.sent_at < timedelta(days=4)
    assert not ActivityLog.objects.filter(created_at__gt=moment).exists()
    numbers = list(Project.objects.order_by("created_at").values_list("project_number", flat=True))
    assert len(set(numbers)) == 8
    for user in User.objects.all():
        assert Notification.objects.filter(user=user, is_read=False).exists(), user.email
