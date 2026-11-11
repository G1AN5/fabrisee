"""Who may see what (PR9) and what happens next on a project."""

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import pytest
from django.contrib.auth.models import AnonymousUser
from django.utils import timezone

from apps.accounts.models import Role
from apps.accounts.tests.factories import StaffFactory, UserFactory
from apps.activity.models import ActivityAction
from apps.activity.services import log_activity
from apps.clients.tests.factories import ClientFactory
from apps.core.models import SystemSetting
from apps.designs.models import ApprovalDecision, RevisionStatus
from apps.designs.selectors import scoped_revisions
from apps.designs.tests.factories import ApprovalFactory, DesignRevisionFactory
from apps.projects.models import (
    DocumentType,
    Project,
    ProjectStatus,
    Stage,
    StageUpdateSource,
)
from apps.projects.selectors import (
    ProjectState,
    ids_needing_action,
    ids_waiting_on_client,
    next_step,
    open_steps,
    overdue_filter,
    pending_decisions,
    scoped_documents,
    scoped_projects,
    with_last_activity,
    with_related,
)
from apps.projects.tests.factories import DocumentFactory, ProjectFactory, StageUpdateFactory
from apps.quotations.models import QuotationStatus
from apps.quotations.selectors import scoped_quotations
from apps.quotations.tests.factories import QuotationFactory

pytestmark = pytest.mark.django_db

MANILA = ZoneInfo("Asia/Manila")
NOW = datetime(2026, 11, 11, 15, 0, tzinfo=MANILA)


def state_of(project: Project) -> ProjectState:
    return ProjectState.of(with_related(Project.objects.filter(pk=project.pk)).get())


def step_for(project: Project, viewer):
    return next_step(state_of(project), viewer, NOW)


@pytest.fixture
def staff():
    return {
        Role.ADMIN: StaffFactory(role=Role.ADMIN),
        Role.PROJECT_MANAGER: StaffFactory(role=Role.PROJECT_MANAGER),
        Role.DESIGNER: StaffFactory(role=Role.DESIGNER),
        Role.PRODUCTION: StaffFactory(role=Role.PRODUCTION),
    }


@pytest.fixture
def manager(staff):
    return staff[Role.PROJECT_MANAGER]


# --- PR9: who may see what -----------------------------------------------------------


def test_client_users_see_only_the_projects_of_their_own_client(staff):
    own_client, other_client = ClientFactory(), ClientFactory()
    own = ProjectFactory(client=own_client)
    ProjectFactory(client=other_client)
    client_user = UserFactory(client=own_client)

    assert list(scoped_projects(client_user)) == [own]
    for member in staff.values():
        assert scoped_projects(member).count() == 2


def test_inactive_and_anonymous_users_see_no_projects():
    ProjectFactory()

    assert not scoped_projects(AnonymousUser()).exists()
    assert not scoped_projects(StaffFactory(is_active=False)).exists()


def test_clients_see_only_client_visible_documents_of_their_own_projects(manager):
    project = ProjectFactory()
    visible = DocumentFactory(project=project, visible_to_client=True)
    internal = DocumentFactory(project=project, visible_to_client=False)
    DocumentFactory(visible_to_client=True)  # another client's project
    client_user = UserFactory(client=project.client)

    assert list(scoped_documents(client_user)) == [visible]
    assert set(scoped_documents(manager).filter(project=project)) == {visible, internal}


def test_production_staff_do_not_see_documents_filed_as_quotations(staff):
    project = ProjectFactory()
    quotation_copy = DocumentFactory(project=project, doc_type=DocumentType.QUOTATION)
    reference = DocumentFactory(project=project, doc_type=DocumentType.REFERENCE)

    assert list(scoped_documents(staff[Role.PRODUCTION])) == [reference]
    assert set(scoped_documents(staff[Role.DESIGNER])) == {quotation_copy, reference}


def test_clients_see_only_quotations_that_were_sent_to_them(staff):
    project = ProjectFactory()
    sent = QuotationFactory(
        project=project, status=QuotationStatus.SUPERSEDED, sent_at=NOW - timedelta(days=4)
    )
    draft = QuotationFactory(project=project, status=QuotationStatus.DRAFT)
    QuotationFactory(status=QuotationStatus.SENT, sent_at=NOW)  # another client's project
    client_user = UserFactory(client=project.client)

    assert list(scoped_quotations(client_user)) == [sent]
    assert set(scoped_quotations(staff[Role.PROJECT_MANAGER]).filter(project=project)) == {
        sent,
        draft,
    }
    # The designer may view quotations; production staff may not.
    assert scoped_quotations(staff[Role.DESIGNER]).count() == 3
    assert not scoped_quotations(staff[Role.PRODUCTION]).exists()


def test_tc8_production_sees_approved_revision_first(staff):
    """TC8: production staff get the approved design first, then the history."""
    project = ProjectFactory(stage=Stage.DESIGN)
    r1 = DesignRevisionFactory(project=project, status=RevisionStatus.CHANGES_REQUESTED)
    r2 = DesignRevisionFactory(
        project=project, status=RevisionStatus.APPROVED, locked_at=NOW - timedelta(days=9)
    )
    r3 = DesignRevisionFactory(project=project, status=RevisionStatus.CHANGES_REQUESTED)
    r4 = DesignRevisionFactory(project=project, status=RevisionStatus.PENDING_APPROVAL)

    for_production = list(scoped_revisions(staff[Role.PRODUCTION]))
    for_designer = list(scoped_revisions(staff[Role.DESIGNER]))

    # The approved design comes first; the revision still waiting for approval is hidden.
    assert for_production == [r2, r3, r1]
    assert for_designer == [r4, r3, r2, r1]
    assert state_of(project).visible_revisions(staff[Role.PRODUCTION]) == [r3, r2, r1]


def test_clients_see_the_revisions_of_their_own_projects_only():
    revision = DesignRevisionFactory()
    DesignRevisionFactory()
    client_user = UserFactory(client=revision.project.client)

    assert list(scoped_revisions(client_user)) == [revision]


# --- Next step: the table of the build guide (section 6) --------------------------------


def test_request_without_quotation(manager):
    project = ProjectFactory()
    client_user = UserFactory(client=project.client)

    assert step_for(project, manager).text == "Prepare a quotation"
    assert step_for(project, manager).action_needed
    assert step_for(project, client_user).text == "We are preparing your quotation"
    assert not step_for(project, client_user).action_needed


def test_quotation_sent(manager):
    approver, colleague = UserFactory(), None
    project = ProjectFactory(client=approver.client, approvers=[approver])
    colleague = UserFactory(client=approver.client)
    QuotationFactory(project=project, status=QuotationStatus.SUPERSEDED)
    quotation = QuotationFactory(
        project=project, status=QuotationStatus.SENT, sent_at=NOW - timedelta(days=2, hours=3)
    )

    staff_step = step_for(project, manager)
    assert staff_step.text == "Waiting for the client to decide on quotation v2 (sent 2 days ago)"
    assert staff_step.waiting_on == "client"
    assert not staff_step.action_needed
    assert (staff_step.item_kind, staff_step.item_id) == ("quotation", quotation.pk)

    approver_step = step_for(project, approver)
    assert approver_step.text == "Please review quotation v2"
    assert approver_step.action_needed
    assert step_for(project, colleague).text == (
        "Waiting for your approver to decide on quotation v2"
    )
    assert not step_for(project, colleague).action_needed


def test_quotation_draft_and_returned(manager):
    approver = UserFactory()
    project = ProjectFactory(client=approver.client, approvers=[approver])
    returned = QuotationFactory(
        project=project,
        status=QuotationStatus.RETURNED,
        sent_at=NOW - timedelta(days=5),
        decided_at=NOW - timedelta(days=4),
        decided_by=approver,
        client_comment="Too expensive.",
    )

    assert step_for(project, manager).text == (
        "Prepare a new quotation version (v1 was returned with comments)"
    )
    assert step_for(project, approver).text == "We are preparing a revised quotation"

    returned.status = QuotationStatus.SUPERSEDED
    returned.save()
    QuotationFactory(project=project, status=QuotationStatus.DRAFT)

    assert step_for(project, manager).text == "Send quotation v2 to the client"
    assert step_for(project, manager).action_needed
    assert step_for(project, approver).text == "We are preparing a revised quotation"


def test_sent_quotation_without_designated_approver_needs_staff_action(manager):
    project = ProjectFactory()
    QuotationFactory(project=project, status=QuotationStatus.SENT, sent_at=NOW)

    step = step_for(project, manager)

    assert step.text == "Designate an approver so the client can decide on quotation v1"
    assert step.waiting_on == "staff"
    assert step.action_needed


def test_design_without_pending_revision(staff):
    project = ProjectFactory(stage=Stage.DESIGN)
    client_user = UserFactory(client=project.client)

    assert step_for(project, staff[Role.DESIGNER]).text == "Upload the first design revision"
    assert step_for(project, client_user).text == "Our designers are working on your design"

    DesignRevisionFactory(project=project, status=RevisionStatus.CHANGES_REQUESTED)

    assert step_for(project, staff[Role.DESIGNER]).text == (
        "Upload the next design revision (changes requested on R1)"
    )
    assert step_for(project, client_user).text == (
        "Our designers are working on the changes you requested"
    )


def test_revision_pending_with_two_approvers(manager):
    client = ClientFactory()
    first, second, viewer = (UserFactory(client=client) for _ in range(3))
    project = ProjectFactory(client=client, stage=Stage.DESIGN, approvers=[first, second])
    DesignRevisionFactory(project=project, status=RevisionStatus.CHANGES_REQUESTED)
    revision = DesignRevisionFactory(project=project, uploaded_at=NOW - timedelta(days=3))
    ApprovalFactory(revision=revision, approver=first)

    staff_step = step_for(project, manager)
    assert staff_step.text == "R2 waiting for 1 of 2 approvers"
    assert staff_step.waiting_on == "client"
    assert (staff_step.item_kind, staff_step.item_label) == ("revision", "Design R2")

    assert step_for(project, second).text == "Please review design R2"
    assert step_for(project, second).action_needed
    assert step_for(project, first).text == "Waiting for other approvers"
    assert not step_for(project, first).action_needed
    assert step_for(project, viewer).text == "Waiting for your approver to review design R2"


def test_revision_pending_with_one_approver(manager):
    approver = UserFactory()
    project = ProjectFactory(client=approver.client, stage=Stage.DESIGN, approvers=[approver])
    DesignRevisionFactory(project=project)

    assert step_for(project, manager).text == "R1 waiting for the client's approval"
    assert step_for(project, approver).text == "Please review design R1"


def test_production_delivery_and_turnover(staff):
    project = ProjectFactory(stage=Stage.PRODUCTION)
    client_user = UserFactory(client=project.client)
    StageUpdateFactory(
        project=project,
        from_stage=Stage.DESIGN,
        to_stage=Stage.PRODUCTION,
        created_at=datetime(2026, 11, 3, 10, 0, tzinfo=MANILA),
    )

    production_step = step_for(project, staff[Role.PRODUCTION])
    assert production_step.text == "In production since Nov 3"
    assert production_step.action_needed
    assert not step_for(project, staff[Role.PROJECT_MANAGER]).action_needed
    assert step_for(project, client_user).text == "Your display is being built"

    project.stage = Stage.DELIVERY_INSTALLATION
    project.save()
    assert step_for(project, staff[Role.PRODUCTION]).text == (
        "Delivery and installation in progress"
    )
    assert step_for(project, client_user).text == "Your display is being delivered and installed"

    project.stage = Stage.TURNOVER
    project.status = ProjectStatus.COMPLETED
    project.save()
    StageUpdateFactory(
        project=project,
        from_stage=Stage.DELIVERY_INSTALLATION,
        to_stage=Stage.TURNOVER,
        source=StageUpdateSource.MANUAL,
        created_at=datetime(2026, 11, 9, 16, 0, tzinfo=MANILA),
    )
    turnover_step = step_for(project, staff[Role.PRODUCTION])
    assert turnover_step.text == "Turned over on Nov 9"
    assert turnover_step.waiting_on == "none"
    assert not turnover_step.action_needed
    assert step_for(project, client_user).text == "Project completed"


def test_cancelled_and_on_hold_projects_have_nothing_to_do(manager):
    cancelled = ProjectFactory(status=ProjectStatus.CANCELLED)
    on_hold = ProjectFactory(status=ProjectStatus.ON_HOLD)
    client_user = UserFactory(client=cancelled.client)

    assert step_for(cancelled, manager).text == "Project cancelled"
    assert step_for(cancelled, client_user).text == "This project was cancelled"
    assert step_for(on_hold, manager).text == "Project on hold"
    assert step_for(on_hold, manager).waiting_on == "none"


@pytest.mark.parametrize(
    ("role", "expected"),
    [
        (Role.ADMIN, {"quotation", "revision"}),
        (Role.PROJECT_MANAGER, {"quotation", "revision"}),
        (Role.DESIGNER, {"revision"}),
        (Role.PRODUCTION, {"production"}),
    ],
)
def test_each_staff_role_is_asked_to_act_on_its_own_steps(staff, role, expected):
    projects = {
        "quotation": ProjectFactory(),  # prepare a quotation
        "revision": ProjectFactory(stage=Stage.DESIGN),  # upload a revision
        "production": ProjectFactory(stage=Stage.PRODUCTION),
    }

    needing_action = {
        name for name, project in projects.items() if step_for(project, staff[role]).action_needed
    }

    assert needing_action == expected


# --- PR8: a change after approval ------------------------------------------------------


def test_reopened_design_needs_a_new_revision_and_a_new_quotation(manager):
    """PR8: both a new approved revision and, if the cost changes, a new quotation."""
    approver = UserFactory()
    project = ProjectFactory(
        client=approver.client,
        stage=Stage.DESIGN,
        design_reopened=True,
        requires_requote=True,
        approvers=[approver],
    )
    QuotationFactory(
        project=project,
        status=QuotationStatus.ACCEPTED,
        sent_at=NOW - timedelta(days=30),
        decided_at=NOW - timedelta(days=29),
    )
    DesignRevisionFactory(
        project=project, status=RevisionStatus.APPROVED, locked_at=NOW - timedelta(days=20)
    )
    StageUpdateFactory(
        project=project,
        from_stage=Stage.PRODUCTION,
        to_stage=Stage.DESIGN,
        created_at=NOW - timedelta(days=2),
    )

    steps = open_steps(state_of(project), NOW)

    assert [step.code for step in steps] == ["upload_revision", "prepare_quotation"]
    assert steps[0].staff_text == "Upload a new design revision (the design was reopened)"
    assert steps[1].staff_text == "Prepare the revised quotation (the cost changes)"
    assert step_for(project, approver).text == "We are updating your design"

    # Once the new revision is approved, only the quotation is left.
    DesignRevisionFactory(
        project=project, status=RevisionStatus.APPROVED, locked_at=NOW - timedelta(hours=3)
    )
    remaining = open_steps(state_of(project), NOW)
    assert [step.code for step in remaining] == ["prepare_quotation"]

    # While the revised quotation waits for the client, the approver is asked to decide.
    QuotationFactory(project=project, status=QuotationStatus.SENT, sent_at=NOW - timedelta(hours=1))
    assert step_for(project, approver).text == "Please review quotation v2"
    assert step_for(project, manager).text == (
        "Waiting for the client to decide on revised quotation v2 (sent 1 hour ago)"
    )


# --- Stage dates, pending decisions, filters ---------------------------------------------


def test_stage_dates_cover_only_the_stages_reached():
    project = ProjectFactory(stage=Stage.DESIGN)
    created = StageUpdateFactory(project=project, created_at=NOW - timedelta(days=10))
    to_design = StageUpdateFactory(
        project=project,
        from_stage=Stage.REQUEST,
        to_stage=Stage.DESIGN,
        created_at=NOW - timedelta(days=7),
    )

    dates = state_of(project).stage_dates

    assert dates[Stage.REQUEST] == created.created_at
    assert dates[Stage.DESIGN] == to_design.created_at
    assert dates[Stage.PRODUCTION] is None
    assert dates[Stage.TURNOVER] is None


def test_stage_dates_after_a_reopened_design_drop_the_later_stages():
    """PR8: back in Design, the tracker no longer shows a Production date."""
    project = ProjectFactory(stage=Stage.DESIGN, design_reopened=True)
    StageUpdateFactory(project=project, created_at=NOW - timedelta(days=30))
    StageUpdateFactory(
        project=project,
        from_stage=Stage.DESIGN,
        to_stage=Stage.PRODUCTION,
        created_at=NOW - timedelta(days=12),
    )
    reopened = StageUpdateFactory(
        project=project,
        from_stage=Stage.PRODUCTION,
        to_stage=Stage.DESIGN,
        created_at=NOW - timedelta(days=1),
    )

    dates = state_of(project).stage_dates

    assert dates[Stage.DESIGN] == reopened.created_at
    assert dates[Stage.PRODUCTION] is None


def test_pending_decisions_are_overdue_after_the_reminder_threshold(manager):
    approver = UserFactory()
    recent = ProjectFactory(client=approver.client, approvers=[approver])
    QuotationFactory(project=recent, status=QuotationStatus.SENT, sent_at=NOW - timedelta(hours=47))
    late = ProjectFactory(client=approver.client, stage=Stage.DESIGN, approvers=[approver])
    DesignRevisionFactory(project=late, uploaded_at=NOW - timedelta(hours=49))
    ProjectFactory()  # nothing pending

    decisions = pending_decisions(manager, NOW)

    assert [(d.kind, d.project, d.is_overdue) for d in decisions] == [
        ("revision", late, True),
        ("quotation", recent, False),
    ]
    assert decisions[0].pending_approvers == [approver]
    assert decisions[0].decided_count == 0


def test_the_overdue_threshold_follows_the_setting(manager):
    approver = UserFactory()
    project = ProjectFactory(client=approver.client, approvers=[approver])
    QuotationFactory(
        project=project, status=QuotationStatus.SENT, sent_at=NOW - timedelta(hours=30)
    )
    assert not pending_decisions(manager, NOW)[0].is_overdue

    settings = SystemSetting.load()
    settings.reminder_hours = 24
    settings.save()

    assert pending_decisions(manager, NOW)[0].is_overdue


def test_client_users_only_get_pending_decisions_of_their_own_client():
    approver, other_approver = UserFactory(), UserFactory()
    own = ProjectFactory(client=approver.client, approvers=[approver])
    QuotationFactory(project=own, status=QuotationStatus.SENT, sent_at=NOW)
    other = ProjectFactory(client=other_approver.client, approvers=[other_approver])
    QuotationFactory(project=other, status=QuotationStatus.SENT, sent_at=NOW)

    assert [d.project for d in pending_decisions(approver, NOW)] == [own]


def test_needs_action_and_waiting_on_client_filters(staff):
    approver = UserFactory()
    to_quote = ProjectFactory()
    waiting = ProjectFactory(client=approver.client, approvers=[approver])
    QuotationFactory(project=waiting, status=QuotationStatus.SENT, sent_at=NOW)
    in_production = ProjectFactory(stage=Stage.PRODUCTION)
    ProjectFactory(stage=Stage.TURNOVER, status=ProjectStatus.COMPLETED)

    assert ids_needing_action(staff[Role.PROJECT_MANAGER], NOW) == [to_quote.pk]
    assert ids_needing_action(staff[Role.PRODUCTION], NOW) == [in_production.pk]
    assert ids_needing_action(approver, NOW) == [waiting.pk]
    assert ids_waiting_on_client(staff[Role.PROJECT_MANAGER], NOW) == [waiting.pk]


def test_overdue_filter_covers_late_projects_and_late_decisions(manager):
    today = timezone.localtime(NOW).date()
    approver = UserFactory()
    past_target = ProjectFactory(target_date=today - timedelta(days=1), stage=Stage.PRODUCTION)
    late_decision = ProjectFactory(client=approver.client, approvers=[approver])
    QuotationFactory(
        project=late_decision, status=QuotationStatus.SENT, sent_at=NOW - timedelta(days=3)
    )
    ProjectFactory(target_date=today)  # due today is not overdue
    ProjectFactory(
        target_date=today - timedelta(days=30),
        stage=Stage.TURNOVER,
        status=ProjectStatus.COMPLETED,
    )

    overdue = Project.objects.filter(overdue_filter(manager, NOW))

    assert set(overdue) == {past_target, late_decision}


def test_last_activity_is_the_latest_activity_entry_or_the_creation_date(manager):
    quiet = ProjectFactory(created_at=NOW - timedelta(days=9))
    busy = ProjectFactory(created_at=NOW - timedelta(days=20))
    log_activity(
        action=ActivityAction.QUOTATION_SENT,
        actor=manager,
        project=busy,
        at=NOW - timedelta(days=5),
    )
    latest = log_activity(
        action=ActivityAction.REVISION_UPLOADED,
        actor=manager,
        project=busy,
        at=NOW - timedelta(hours=2),
    )

    annotated = {p.pk: p.last_activity_at for p in with_last_activity(Project.objects.all())}

    assert annotated[quiet.pk] == quiet.created_at
    assert annotated[busy.pk] == latest.created_at


def test_loading_many_projects_takes_a_fixed_number_of_queries(
    manager, django_assert_max_num_queries
):
    for _ in range(6):
        approver = UserFactory()
        project = ProjectFactory(client=approver.client, stage=Stage.DESIGN, approvers=[approver])
        QuotationFactory(project=project, status=QuotationStatus.ACCEPTED)
        revision = DesignRevisionFactory(project=project)
        ApprovalFactory(revision=revision, approver=approver, decision=ApprovalDecision.APPROVED)
        StageUpdateFactory(project=project)

    with django_assert_max_num_queries(8):
        projects = list(with_related(with_last_activity(scoped_projects(manager))))
        steps = [next_step(ProjectState.of(project), manager, NOW) for project in projects]

    assert len(steps) == 6
