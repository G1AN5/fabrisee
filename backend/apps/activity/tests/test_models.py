import pytest

from apps.accounts.tests.factories import StaffFactory
from apps.activity.models import ActivityAction, ActivityLog, AppendOnlyError
from apps.activity.services import CLIENT_VISIBLE_ACTIONS, describe, log_activity
from apps.activity.tests.factories import ActivityLogFactory
from apps.projects.tests.factories import ProjectFactory

pytestmark = pytest.mark.django_db


def test_log_activity_records_actor_project_action_and_time():
    project = ProjectFactory()

    entry = log_activity(
        action=ActivityAction.QUOTATION_SENT,
        actor=project.manager,
        project=project,
        details={"version_no": 2},
    )

    assert entry.actor == project.manager
    assert entry.project == project
    assert entry.details == {"version_no": 2}
    assert entry.created_at is not None


def test_activity_entries_cannot_be_changed():
    entry = ActivityLogFactory()

    entry.action = ActivityAction.SETTINGS_CHANGED
    with pytest.raises(AppendOnlyError):
        entry.save()
    with pytest.raises(AppendOnlyError):
        ActivityLog.objects.filter(pk=entry.pk).update(action=ActivityAction.SETTINGS_CHANGED)

    entry.refresh_from_db()
    assert entry.action == ActivityAction.PROJECT_UPDATED


def test_activity_entries_cannot_be_deleted():
    entry = ActivityLogFactory()

    with pytest.raises(AppendOnlyError):
        entry.delete()
    with pytest.raises(AppendOnlyError):
        ActivityLog.objects.all().delete()

    assert ActivityLog.objects.count() == 1


def test_descriptions_read_as_plain_sentences():
    manager = StaffFactory(full_name="Andrea Villanueva")

    def text(action, **details):
        return describe(ActivityLog(action=action, actor=manager, details=details))

    assert text(ActivityAction.QUOTATION_SENT, version_no=2) == (
        "sent quotation v2 to the client",
        True,
    )
    assert text(ActivityAction.REVISION_UPLOADED, revision_no=3) == ("uploaded design R3", True)
    assert text(
        ActivityAction.REVISION_APPROVED_BY,
        revision_no=3,
        on_behalf=True,
        approver_name="N. Ramos",
        channel="phone",
    ) == ("recorded the approval of design R3 on behalf of N. Ramos (phone)", True)
    assert text(ActivityAction.REVISION_LOCKED, revision_no=3) == (
        "Design R3 was approved by all designated approvers and locked as the approved design",
        False,
    )
    assert text(
        ActivityAction.STAGE_CHANGED,
        from_stage="design",
        to_stage="production",
        source="rule",
        rule="PR5",
    ) == (
        "The project moved from Design to Production (design approved by all designated approvers)",
        False,
    )
    assert text(
        ActivityAction.STAGE_CHANGED, from_stage="production", to_stage="delivery_installation"
    ) == ("moved the project from Production to Delivery and Installation", True)


def test_every_action_has_a_description():
    for action in ActivityAction:
        text, _ = describe(ActivityLog(action=action, details={}))
        assert text, action


def test_internal_steps_are_not_client_visible():
    assert ActivityAction.QUOTATION_CREATED not in CLIENT_VISIBLE_ACTIONS  # drafts
    assert ActivityAction.OVERDUE_ALERT_SENT not in CLIENT_VISIBLE_ACTIONS
    assert ActivityAction.USER_LOGIN not in CLIENT_VISIBLE_ACTIONS
    assert ActivityAction.STAGE_CHANGED in CLIENT_VISIBLE_ACTIONS
