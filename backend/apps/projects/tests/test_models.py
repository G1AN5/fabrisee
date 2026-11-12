from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.utils import timezone

from apps.accounts.models import Role
from apps.accounts.tests.factories import StaffFactory, UserFactory
from apps.core.models import SystemSetting
from apps.projects.models import (
    STAGE_ORDER,
    ProjectApprover,
    ProjectStatus,
    Stage,
    stage_index,
)
from apps.projects.numbering import next_project_number
from apps.projects.tests.factories import ProjectApproverFactory, ProjectFactory

pytestmark = pytest.mark.django_db

MANILA = ZoneInfo("Asia/Manila")


def test_stages_are_in_the_order_of_the_project_lifecycle():
    assert STAGE_ORDER == [
        "request",
        "design",
        "production",
        "delivery_installation",
        "turnover",
    ]
    assert stage_index(Stage.PRODUCTION) == 2
    assert Stage.DELIVERY_INSTALLATION.label == "Delivery and Installation"


def test_a_new_project_starts_in_the_request_stage_and_is_active():
    project = ProjectFactory()

    assert project.stage == Stage.REQUEST
    assert project.status == ProjectStatus.ACTIVE
    assert project.design_reopened is False
    assert project.requires_requote is False


def test_project_numbers_follow_the_prefix_year_sequence_format():
    now = datetime(2026, 11, 11, 9, 0, tzinfo=MANILA)

    with transaction.atomic():
        first = next_project_number(now)
        second = next_project_number(now)

    assert first == "FS-2026-0001"
    assert second == "FS-2026-0002"


def test_project_number_sequence_restarts_every_year_and_uses_the_prefix_setting():
    settings = SystemSetting.load()
    settings.project_number_prefix = "FBS"
    settings.save()

    with transaction.atomic():
        next_project_number(datetime(2026, 12, 31, 23, 0, tzinfo=MANILA))
        last_of_year = next_project_number(datetime(2026, 12, 31, 23, 30, tzinfo=MANILA))
        first_of_year = next_project_number(datetime(2027, 1, 1, 0, 30, tzinfo=MANILA))

    assert last_of_year == "FBS-2026-0002"
    assert first_of_year == "FBS-2027-0001"


def test_project_number_year_uses_manila_time():
    # 16:30 UTC on Dec 31 is already Jan 1 in Manila (UTC+8).
    late_utc = datetime(2026, 12, 31, 16, 30, tzinfo=ZoneInfo("UTC"))

    with transaction.atomic():
        number = next_project_number(late_utc)

    assert number == "FS-2027-0001"


def test_project_number_must_be_unique():
    ProjectFactory(project_number="FS-2026-0100")

    with pytest.raises(IntegrityError), transaction.atomic():
        ProjectFactory(project_number="FS-2026-0100")


def test_a_user_can_be_designated_approver_of_a_project_only_once():
    link = ProjectApproverFactory()

    with pytest.raises(IntegrityError), transaction.atomic():
        ProjectApprover.objects.create(project=link.project, user=link.user)


def test_designated_approver_must_be_an_active_user_of_the_projects_client():
    project = ProjectFactory()
    other_clients_user = UserFactory()
    staff_member = StaffFactory()
    inactive_user = UserFactory(client=project.client, is_active=False)
    own_user = UserFactory(client=project.client)

    for user in (other_clients_user, staff_member, inactive_user):
        with pytest.raises(ValidationError):
            ProjectApprover(project=project, user=user).full_clean()

    ProjectApprover(project=project, user=own_user).full_clean()


def test_manager_must_be_a_project_manager_or_administrator():
    project = ProjectFactory()
    project.manager = StaffFactory(role=Role.DESIGNER)

    with pytest.raises(ValidationError) as error:
        project.clean()

    assert "manager" in error.value.message_dict
    project.manager = StaffFactory(role=Role.ADMIN)
    project.clean()


def test_project_is_overdue_after_its_target_date_unless_finished():
    today = timezone.localdate()
    late = ProjectFactory(target_date=today - timedelta(days=1))
    due_today = ProjectFactory(target_date=today)
    completed = ProjectFactory(
        target_date=today - timedelta(days=10),
        stage=Stage.TURNOVER,
        status=ProjectStatus.COMPLETED,
    )

    assert late.is_overdue()
    assert not due_today.is_overdue()
    assert not completed.is_overdue()
