"""The management dashboard and the pending approvals list."""

from datetime import timedelta

import pytest
from django.utils import timezone

from apps.accounts.models import Role
from apps.accounts.tests.factories import StaffFactory, UserFactory
from apps.activity.models import ActivityAction
from apps.activity.services import log_activity
from apps.designs.models import RevisionStatus
from apps.designs.tests.factories import ApprovalFactory, DesignRevisionFactory
from apps.projects.models import ProjectStatus, Stage
from apps.projects.tests.factories import ProjectFactory, StageUpdateFactory
from apps.quotations.models import QuotationStatus
from apps.quotations.tests.factories import QuotationFactory

pytestmark = pytest.mark.django_db


@pytest.fixture
def manager():
    return StaffFactory(role=Role.PROJECT_MANAGER, full_name="Andrea Villanueva")


@pytest.fixture
def portfolio(manager):
    """Six projects: every stage, one late decision, one fresh decision, one late project."""
    now, today = timezone.now(), timezone.localdate()
    approver = UserFactory(full_name="Liza Mendoza")
    second = UserFactory(client=approver.client, full_name="Mark Bautista")

    new_request = ProjectFactory(title="New request", target_date=today + timedelta(days=60))
    quoted = ProjectFactory(
        title="Quoted",
        client=approver.client,
        approvers=[approver],
        target_date=today + timedelta(days=40),
    )
    QuotationFactory(project=quoted, status=QuotationStatus.SENT, sent_at=now - timedelta(days=3))
    in_design = ProjectFactory(
        title="In design",
        client=approver.client,
        stage=Stage.DESIGN,
        approvers=[approver, second],
        target_date=today + timedelta(days=5),
    )
    revision = DesignRevisionFactory(project=in_design, uploaded_at=now - timedelta(hours=20))
    ApprovalFactory(revision=revision, approver=approver)
    in_production = ProjectFactory(
        title="In production", stage=Stage.PRODUCTION, target_date=today - timedelta(days=2)
    )
    DesignRevisionFactory(
        project=in_production, status=RevisionStatus.APPROVED, locked_at=now - timedelta(days=6)
    )
    StageUpdateFactory(
        project=in_production,
        from_stage=Stage.DESIGN,
        to_stage=Stage.PRODUCTION,
        created_at=now - timedelta(days=6),
    )
    delivering = ProjectFactory(
        title="Delivering",
        stage=Stage.DELIVERY_INSTALLATION,
        target_date=today + timedelta(days=2),
    )
    done = ProjectFactory(
        title="Done",
        stage=Stage.TURNOVER,
        status=ProjectStatus.COMPLETED,
        target_date=today - timedelta(days=20),
    )
    ProjectFactory(title="Cancelled", status=ProjectStatus.CANCELLED)
    log_activity(
        action=ActivityAction.QUOTATION_SENT,
        actor=manager,
        project=quoted,
        details={"version_no": 1},
    )
    return {
        "new_request": new_request,
        "quoted": quoted,
        "in_design": in_design,
        "in_production": in_production,
        "delivering": delivering,
        "done": done,
        "approver": approver,
        "second": second,
    }


def test_tc9_dashboard_shows_stage_counts_pending_and_overdue(login, manager, portfolio):
    """TC9: projects per stage, pending decisions with waiting time, and overdue items."""
    response = login(manager).get("/api/dashboard/")

    assert response.status_code == 200
    body = response.json()

    # Counts by stage (cancelled projects are left out).
    assert body["stage_counts"] == {
        "request": 2,
        "design": 1,
        "production": 1,
        "delivery_installation": 1,
        "turnover": 1,
    }
    assert [(column["stage"], column["count"]) for column in body["by_stage"]] == [
        ("request", 2),
        ("design", 1),
        ("production", 1),
        ("delivery_installation", 1),
        ("turnover", 1),
    ]

    # Pending decisions, longest wait first, with who still has to decide.
    pending = body["pending_decisions"]
    assert [(item["project"]["title"], item["label"]) for item in pending] == [
        ("Quoted", "Quotation v1"),
        ("In design", "Design R1"),
    ]
    assert pending[0]["is_overdue"] is True  # waiting 3 days, threshold 48 hours
    assert pending[0]["waiting_hours"] == pytest.approx(72, abs=0.2)
    assert pending[1]["is_overdue"] is False
    assert [person["full_name"] for person in pending[1]["pending_approvers"]] == ["Mark Bautista"]
    assert (pending[1]["decided_count"], pending[1]["approver_count"]) == (1, 2)

    # Overdue items: one late decision and one project past its target date.
    assert [project["title"] for project in body["overdue_projects"]] == ["In production"]
    assert body["kpis"] == {
        "active_projects": 5,
        "waiting_for_client": 2,
        "overdue_items": 2,
        "overdue_decisions": 1,
        "overdue_projects": 1,
        "due_next_7_days": 2,
    }
    assert [project["title"] for project in body["due_soon"]] == ["Delivering", "In design"]
    assert body["reminder_hours"] == 48


def test_dashboard_numbers_match_the_filtered_project_lists(login, manager, portfolio):
    api = login(manager)
    kpis = api.get("/api/dashboard/").json()["kpis"]

    assert api.get("/api/projects/?status=active").json()["count"] == kpis["active_projects"]
    assert (
        api.get("/api/projects/?waiting_on=client").json()["count"] == (kpis["waiting_for_client"])
    )
    assert api.get("/api/projects/?due_within=7").json()["count"] == kpis["due_next_7_days"]
    assert api.get("/api/projects/?overdue=1").json()["count"] == 2


def test_dashboard_stage_columns_hold_cards_with_the_next_step(login, manager, portfolio):
    columns = {
        column["stage"]: column
        for column in login(manager).get("/api/dashboard/").json()["by_stage"]
    }

    request_cards = columns["request"]["projects"]
    assert [card["title"] for card in request_cards] == ["Quoted", "New request"]
    assert request_cards[1]["next_step"]["text"] == "Prepare a quotation"
    assert columns["turnover"]["projects"][0]["title"] == "Done"
    assert columns["production"]["projects"][0]["approved_revision"]["label"] == "R1"


def test_dashboard_stage_columns_show_at_most_five_cards_but_count_all(login, manager):
    ProjectFactory.create_batch(7, stage=Stage.DESIGN)

    column = login(manager).get("/api/dashboard/").json()["by_stage"][1]

    assert column["count"] == 7
    assert len(column["projects"]) == 5


def test_recent_activity_is_for_administrators_and_project_managers(login, manager, portfolio):
    for_manager = login(manager).get("/api/dashboard/").json()
    for_designer = login(StaffFactory(role=Role.DESIGNER)).get("/api/dashboard/").json()

    entry = for_manager["recent_activity"][0]
    assert entry["actor_name"] == "Andrea Villanueva"
    assert entry["text"] == "sent quotation v1 to the client"
    assert entry["project"]["title"] == "Quoted"
    assert for_manager["focus"] is None
    assert for_designer["recent_activity"] == []


def test_designers_see_revisions_to_prepare_first(login, portfolio):
    waiting_for_revision = ProjectFactory(title="Needs R1", stage=Stage.DESIGN)

    focus = login(StaffFactory(role=Role.DESIGNER)).get("/api/dashboard/").json()["focus"]

    assert focus["key"] == "revisions_to_prepare"
    assert focus["title"] == "Revisions to prepare"
    # "In design" already has a revision with the client, so only the new one is listed.
    assert [card["title"] for card in focus["projects"]] == [waiting_for_revision.title]


def test_production_sees_approved_and_ready_to_build_first(login, portfolio):
    body = login(StaffFactory(role=Role.PRODUCTION)).get("/api/dashboard/").json()

    assert body["focus"]["key"] == "ready_to_build"
    assert body["focus"]["title"] == "Approved and ready to build"
    assert [card["title"] for card in body["focus"]["projects"]] == ["In production"]
    assert body["focus"]["projects"][0]["approved_revision"]["label"] == "R1"
    # Pending decisions are shown as status only: production cannot open the items.
    assert all(item["id"] is None for item in body["pending_decisions"])


def test_dashboard_is_for_staff_only(login, portfolio):
    response = login(portfolio["approver"]).get("/api/dashboard/")

    assert response.status_code == 403
    assert response.json()["code"] == "permission_denied"


def test_pending_approvals_list_all_open_decisions(login, manager, portfolio):
    body = login(manager).get("/api/approvals/pending/").json()

    assert (body["count"], body["overdue_count"]) == (2, 1)
    first = body["results"][0]
    assert first["kind"] == "quotation"
    assert first["project"]["client_name"] == portfolio["quoted"].client.company_name
    assert first["last_reminded_at"] is None


def test_pending_approvals_are_not_for_production_or_clients(login, portfolio):
    for user in (StaffFactory(role=Role.PRODUCTION), portfolio["approver"]):
        assert login(user).get("/api/approvals/pending/").status_code == 403
    assert login(StaffFactory(role=Role.DESIGNER)).get("/api/approvals/pending/").status_code == 200
