"""The read-only project API: list, detail, timeline, records, and the PR9 scoping."""

from datetime import timedelta

import pytest
from django.utils import timezone

from apps.accounts.models import Role
from apps.accounts.tests.factories import StaffFactory, UserFactory
from apps.activity.models import ActivityAction
from apps.activity.services import log_activity
from apps.clients.tests.factories import ClientFactory
from apps.core.choices import DecisionChannel
from apps.designs.models import ApprovalDecision, RevisionStatus
from apps.designs.tests.factories import ApprovalFactory, DesignRevisionFactory
from apps.projects.models import DocumentType, ProjectStatus, ProjectType, Stage
from apps.projects.tests.factories import DocumentFactory, ProjectFactory, StageUpdateFactory
from apps.quotations.models import QuotationStatus
from apps.quotations.tests.factories import QuotationFactory

pytestmark = pytest.mark.django_db


@pytest.fixture
def manager():
    return StaffFactory(role=Role.PROJECT_MANAGER, full_name="Andrea Villanueva")


@pytest.fixture
def production():
    return StaffFactory(role=Role.PRODUCTION)


@pytest.fixture
def designer():
    return StaffFactory(role=Role.DESIGNER)


def numbers(response) -> list[str]:
    return [item["project_number"] for item in response.json()["results"]]


# --- Access ------------------------------------------------------------------------------


@pytest.mark.parametrize(
    "path",
    [
        "/api/projects/",
        "/api/projects/1/",
        "/api/projects/1/timeline/",
        "/api/projects/1/quotations/",
        "/api/projects/1/revisions/",
        "/api/projects/1/documents/",
        "/api/files/document/1/",
        "/api/dashboard/",
        "/api/approvals/pending/",
        "/api/notifications/",
        "/api/clients/",
    ],
)
def test_every_endpoint_requires_sign_in(api_client, path):
    response = api_client.get(path)

    assert response.status_code == 401
    assert response.json()["code"] == "not_authenticated"


def test_tc7_client_cannot_open_other_clients_project(login):
    """TC7 (PR9): another client's project does not exist for this client: API and files."""
    own_client, other_client = ClientFactory(), ClientFactory()
    client_user = UserFactory(client=own_client)
    own = ProjectFactory(client=own_client, title="Our booth")
    other = ProjectFactory(client=other_client, title="Their booth", stage=Stage.DESIGN)
    quotation = QuotationFactory(project=other, status=QuotationStatus.SENT, sent_at=timezone.now())
    revision = DesignRevisionFactory(project=other)
    document = DocumentFactory(project=other, visible_to_client=True)
    api = login(client_user)

    listed = api.get("/api/projects/")
    assert numbers(listed) == [own.project_number]
    assert api.get("/api/projects/?q=Their").json()["count"] == 0

    for path in (
        f"/api/projects/{other.pk}/",
        f"/api/projects/{other.pk}/timeline/",
        f"/api/projects/{other.pk}/quotations/",
        f"/api/projects/{other.pk}/revisions/",
        f"/api/projects/{other.pk}/documents/",
        f"/api/files/quotation/{quotation.pk}/",
        f"/api/files/render/{revision.pk}/",
        f"/api/files/render/{revision.pk}/?variant=thumb",
        f"/api/files/document/{document.pk}/",
    ):
        response = api.get(path)
        # 404, not 403: the response does not reveal that the project exists.
        assert response.status_code == 404, path
        assert response.json()["code"] == "not_found"

    assert api.get(f"/api/projects/{own.pk}/").status_code == 200


def test_staff_of_every_role_see_all_projects(login, manager, designer, production):
    ProjectFactory.create_batch(3)

    for member in (manager, designer, production, StaffFactory(role=Role.ADMIN)):
        assert login(member).get("/api/projects/").json()["count"] == 3


# --- List --------------------------------------------------------------------------------


def test_list_is_paginated_with_twenty_projects_per_page(login, manager):
    ProjectFactory.create_batch(23)

    first = login(manager).get("/api/projects/").json()
    second = login(manager).get("/api/projects/?page=2").json()

    assert (first["count"], first["page"], first["page_size"], first["total_pages"]) == (
        23,
        1,
        20,
        2,
    )
    assert len(first["results"]) == 20
    assert len(second["results"]) == 3
    assert second["next"] is None


def test_list_item_has_what_the_table_needs(login, manager):
    project = ProjectFactory(
        title="Trade fair booth",
        project_type=ProjectType.EVENT_BOOTH,
        manager=manager,
        target_date=timezone.localdate() - timedelta(days=2),
        stage=Stage.PRODUCTION,
    )

    item = login(manager).get("/api/projects/").json()["results"][0]

    assert item["project_number"] == project.project_number
    assert item["title"] == "Trade fair booth"
    assert item["client"] == {"id": project.client_id, "company_name": project.client.company_name}
    assert item["project_type_label"] == "Event booth"
    assert (item["stage"], item["stage_label"]) == ("production", "Production")
    assert item["manager"]["full_name"] == "Andrea Villanueva"
    assert item["is_overdue"] is True
    assert item["days_until_target"] == -2
    assert item["next_step"]["text"] == "In production"
    assert set(item["stage_dates"]) == {
        "request",
        "design",
        "production",
        "delivery_installation",
        "turnover",
    }


def test_list_filters_by_stage_status_type_and_client(login, manager):
    client = ClientFactory()
    design = ProjectFactory(stage=Stage.DESIGN, client=client)
    sign = ProjectFactory(project_type=ProjectType.BRAND_SIGN)
    done = ProjectFactory(stage=Stage.TURNOVER, status=ProjectStatus.COMPLETED)
    api = login(manager)

    assert numbers(api.get("/api/projects/?stage=design")) == [design.project_number]
    assert numbers(api.get("/api/projects/?status=completed")) == [done.project_number]
    assert numbers(api.get("/api/projects/?project_type=brand_sign")) == [sign.project_number]
    assert numbers(api.get(f"/api/projects/?client={client.pk}")) == [design.project_number]


def test_list_rejects_unknown_filter_values(login, manager):
    response = login(manager).get("/api/projects/?stage=painting")

    assert response.status_code == 400
    assert response.json()["code"] == "validation_error"
    assert "stage" in response.json()["fields"]


def test_list_search_matches_number_title_and_client(login, manager):
    aurelia = ClientFactory(company_name="Aurelia Audio Labs")
    counter = ProjectFactory(
        client=aurelia, title="Experience counter", project_number="FS-2026-0041"
    )
    sign = ProjectFactory(title="Illuminated brand sign", project_number="FS-2026-0042")
    api = login(manager)

    assert numbers(api.get("/api/projects/?q=aurelia")) == [counter.project_number]
    assert numbers(api.get("/api/projects/?q=brand+sign")) == [sign.project_number]
    assert numbers(api.get("/api/projects/?q=0042")) == [sign.project_number]
    assert api.get("/api/projects/?q=nothing-like-this").json()["count"] == 0


def test_list_needs_action_depends_on_who_asks(login, manager, designer, production):
    approver = UserFactory()
    to_quote = ProjectFactory()
    to_design = ProjectFactory(stage=Stage.DESIGN)
    to_build = ProjectFactory(stage=Stage.PRODUCTION)
    to_decide = ProjectFactory(client=approver.client, approvers=[approver])
    QuotationFactory(project=to_decide, status=QuotationStatus.SENT, sent_at=timezone.now())
    path = "/api/projects/?needs_action=1&ordering=created"

    assert numbers(login(manager).get(path)) == [
        to_quote.project_number,
        to_design.project_number,
    ]
    assert numbers(login(designer).get(path)) == [to_design.project_number]
    assert numbers(login(production).get(path)) == [to_build.project_number]
    assert numbers(login(approver).get(path)) == [to_decide.project_number]
    waiting = login(manager).get("/api/projects/?waiting_on=client")
    assert numbers(waiting) == [to_decide.project_number]


def test_list_overdue_and_due_within(login, manager):
    today = timezone.localdate()
    late = ProjectFactory(target_date=today - timedelta(days=3))
    soon = ProjectFactory(target_date=today + timedelta(days=5))
    ProjectFactory(target_date=today + timedelta(days=30))
    api = login(manager)

    assert numbers(api.get("/api/projects/?overdue=1")) == [late.project_number]
    assert numbers(api.get("/api/projects/?due_within=7")) == [soon.project_number]


def test_list_orders_by_last_update_by_default_and_by_target_date(login, manager):
    today = timezone.localdate()
    now = timezone.now()
    older = ProjectFactory(
        target_date=today + timedelta(days=5), created_at=now - timedelta(days=9)
    )
    newer = ProjectFactory(
        target_date=today + timedelta(days=50), created_at=now - timedelta(days=2)
    )
    api = login(manager)

    assert numbers(api.get("/api/projects/")) == [newer.project_number, older.project_number]
    assert numbers(api.get("/api/projects/?ordering=target_date")) == [
        older.project_number,
        newer.project_number,
    ]
    assert numbers(api.get("/api/projects/?ordering=-target_date")) == [
        newer.project_number,
        older.project_number,
    ]

    # Activity on the older project brings it to the top of "last update".
    log_activity(action=ActivityAction.QUOTATION_SENT, actor=manager, project=older)
    assert numbers(api.get("/api/projects/")) == [older.project_number, newer.project_number]


# --- Detail --------------------------------------------------------------------------------


@pytest.fixture
def design_project(manager, designer):
    """A project in Design with two approvers, one accepted quotation, and two revisions."""
    client = ClientFactory(company_name="Aurelia Audio Labs", notes="Pays late. Staff only.")
    joanna = UserFactory(client=client, full_name="Joanna Cruz")
    mark = UserFactory(client=client, full_name="Mark Bautista")
    viewer = UserFactory(client=client, full_name="Ella Navarro")
    project = ProjectFactory(
        client=client,
        stage=Stage.DESIGN,
        manager=manager,
        designer=designer,
        approvers=[joanna, mark],
        title="Experience counter",
    )
    now = timezone.now()
    StageUpdateFactory(project=project, created_at=now - timedelta(days=20), updated_by=joanna)
    StageUpdateFactory(
        project=project,
        from_stage=Stage.REQUEST,
        to_stage=Stage.DESIGN,
        created_at=now - timedelta(days=15),
        updated_by=mark,
    )
    quotation = QuotationFactory(
        project=project,
        status=QuotationStatus.ACCEPTED,
        sent_at=now - timedelta(days=17),
        decided_at=now - timedelta(days=15),
        decided_by=mark,
        decision_channel=DecisionChannel.PORTAL,
    )
    r1 = DesignRevisionFactory(
        project=project,
        status=RevisionStatus.CHANGES_REQUESTED,
        uploaded_by=designer,
        uploaded_at=now - timedelta(days=10),
    )
    ApprovalFactory(revision=r1, approver=joanna)
    ApprovalFactory(
        revision=r1,
        approver=mark,
        decision=ApprovalDecision.CHANGES_REQUESTED,
        comment="Warm white lighting, please.",
    )
    r2 = DesignRevisionFactory(
        project=project, uploaded_by=designer, uploaded_at=now - timedelta(days=3)
    )
    ApprovalFactory(revision=r2, approver=joanna)
    return {
        "project": project,
        "joanna": joanna,
        "mark": mark,
        "viewer": viewer,
        "quotation": quotation,
        "r1": r1,
        "r2": r2,
    }


def test_detail_for_staff_has_everything_above_the_tabs(login, manager, design_project):
    project = design_project["project"]

    body = login(manager).get(f"/api/projects/{project.pk}/").json()

    assert body["title"] == "Experience counter"
    assert body["location"] == project.location
    assert body["dimensions"] == project.dimensions
    assert body["next_step"]["text"] == "R2 waiting for 1 of 2 approvers"
    assert body["next_step"]["item"] == {
        "kind": "revision",
        "id": design_project["r2"].pk,
        "label": "Design R2",
    }
    assert [person["full_name"] for person in body["approvers"]] == [
        "Joanna Cruz",
        "Mark Bautista",
    ]
    assert body["manager"]["email"] == manager.email
    assert body["designer"]["role"] == "designer"
    assert body["client"]["notes"] == "Pays late. Staff only."
    assert body["current_quotation"]["label"] == "v1"
    assert body["current_quotation"]["decision"] == "accepted"
    assert body["current_revision"]["label"] == "R2"
    assert body["approved_revision"] is None
    assert body["counts"] == {"quotations": 1, "revisions": 2, "documents": 0}
    assert body["stage_dates"]["design"] is not None
    assert body["stage_dates"]["production"] is None
    assert body["viewer"] == {"is_designated_approver": False, "can_view_quotations": True}


def test_detail_for_a_client_leaves_out_staff_only_fields(login, design_project):
    project = design_project["project"]

    body = login(design_project["mark"]).get(f"/api/projects/{project.pk}/").json()

    # Staff-only notes and client contact details never reach the client portal.
    assert body["client"] == {"id": project.client_id, "company_name": "Aurelia Audio Labs"}
    assert "Pays late" not in str(body)
    assert body["designer"] is None
    assert body["manager"]["full_name"] == "Andrea Villanueva"
    assert body["next_step"]["text"] == "Please review design R2"
    assert body["next_step"]["action_needed"] is True
    assert body["viewer"]["is_designated_approver"] is True

    other = login(design_project["viewer"]).get(f"/api/projects/{project.pk}/").json()
    assert other["viewer"]["is_designated_approver"] is False
    assert other["next_step"]["text"] == "Waiting for your approver to review design R2"


def test_detail_for_production_has_no_quotation_and_no_pending_revision(
    login, production, design_project
):
    project = design_project["project"]

    body = login(production).get(f"/api/projects/{project.pk}/").json()

    assert body["current_quotation"] is None
    assert body["viewer"]["can_view_quotations"] is False
    # R2 still waits for approval, so production staff only get the history.
    assert body["current_revision"]["label"] == "R1"
    assert body["counts"]["quotations"] == 0
    assert body["counts"]["revisions"] == 1
    assert body["next_step"]["item"]["id"] is None


def test_detail_shows_the_approved_design_once_a_revision_is_locked(login, manager):
    approver = UserFactory()
    project = ProjectFactory(client=approver.client, stage=Stage.PRODUCTION, approvers=[approver])
    DesignRevisionFactory(project=project, status=RevisionStatus.CHANGES_REQUESTED)
    locked = DesignRevisionFactory(
        project=project, status=RevisionStatus.APPROVED, locked_at=timezone.now()
    )
    ApprovalFactory(revision=locked, approver=approver)

    body = login(manager).get(f"/api/projects/{project.pk}/").json()

    approved = body["approved_revision"]
    assert approved["label"] == "R2"
    assert approved["is_locked"] is True
    assert approved["alt_text"] == f"Design R2 of {project.project_number}"
    assert approved["render"]["url"] == f"/api/files/render/{locked.pk}/"
    assert approved["render"]["is_image"] is True
    assert (approved["approved_count"], approved["approver_count"]) == (1, 1)


# --- Quotations, revisions, documents, timeline ------------------------------------------------


def test_quotation_versions_are_listed_newest_first_with_their_decisions(
    login, manager, design_project
):
    project = design_project["project"]
    QuotationFactory(project=project, status=QuotationStatus.DRAFT)

    versions = login(manager).get(f"/api/projects/{project.pk}/quotations/").json()

    assert [(v["label"], v["status"], v["is_latest"]) for v in versions] == [
        ("v2", "draft", True),
        ("v1", "accepted", False),
    ]
    accepted = versions[1]
    assert accepted["amount"] == "125000.00"
    assert accepted["decided_by"]["full_name"] == "Mark Bautista"
    assert accepted["decision_channel_label"] == "Client portal"
    assert accepted["file"]["is_pdf"] is True
    assert accepted["file"]["name"] == f"{project.project_number}-quotation-v1.pdf"


def test_clients_do_not_get_draft_quotations_and_production_gets_none(
    login, production, designer, design_project
):
    project = design_project["project"]
    QuotationFactory(project=project, status=QuotationStatus.DRAFT)
    path = f"/api/projects/{project.pk}/quotations/"

    for_client = login(design_project["mark"]).get(path).json()
    assert [v["label"] for v in for_client] == ["v1"]

    assert len(login(designer).get(path).json()) == 2

    refused = login(production).get(path)
    assert refused.status_code == 403
    assert refused.json()["code"] == "permission_denied"


def test_revisions_carry_one_approval_line_per_designated_approver(login, manager, design_project):
    project = design_project["project"]

    r2, r1 = login(manager).get(f"/api/projects/{project.pk}/revisions/").json()

    assert (r2["label"], r2["status"]) == ("R2", "pending_approval")
    assert [(line["approver"]["full_name"], line["state"]) for line in r2["approvals"]] == [
        ("Joanna Cruz", "approved"),
        ("Mark Bautista", "pending"),
    ]
    assert (r2["approved_count"], r2["approver_count"]) == (1, 2)
    assert [(line["approver"]["full_name"], line["state"]) for line in r1["approvals"]] == [
        ("Joanna Cruz", "approved"),
        ("Mark Bautista", "changes_requested"),
    ]
    assert r1["approvals"][1]["comment"] == "Warm white lighting, please."


def test_a_decision_recorded_on_behalf_names_the_channel_and_the_recorder(login, manager):
    approver = UserFactory(full_name="Nico Ramos")
    project = ProjectFactory(client=approver.client, stage=Stage.PRODUCTION, approvers=[approver])
    revision = DesignRevisionFactory(
        project=project, status=RevisionStatus.APPROVED, locked_at=timezone.now()
    )
    ApprovalFactory(
        revision=revision,
        approver=approver,
        decided_on_behalf=True,
        decision_channel=DecisionChannel.PHONE,
        recorded_by=manager,
    )

    line = login(manager).get(f"/api/projects/{project.pk}/revisions/").json()[0]["approvals"][0]

    assert line["decided_on_behalf"] is True
    assert line["decision_channel_label"] == "Phone"
    assert line["recorded_by"]["short_name"] == "A. Villanueva"
    assert line["approver"]["short_name"] == "N. Ramos"


def test_an_approver_who_never_decided_shows_as_no_decision_on_a_closed_revision(
    login, manager, design_project
):
    project = design_project["project"]
    late_approver = UserFactory(client=project.client, full_name="Liza Mendoza")
    project.approver_links.create(user=late_approver)

    _, r1 = login(manager).get(f"/api/projects/{project.pk}/revisions/").json()

    assert r1["approvals"][-1]["approver"]["full_name"] == "Liza Mendoza"
    assert r1["approvals"][-1]["state"] == "no_decision"


def test_production_gets_the_approved_revision_first_and_no_pending_one(login, production):
    project = ProjectFactory(stage=Stage.DESIGN, design_reopened=True)
    DesignRevisionFactory(project=project, status=RevisionStatus.CHANGES_REQUESTED)
    DesignRevisionFactory(project=project, status=RevisionStatus.APPROVED, locked_at=timezone.now())
    DesignRevisionFactory(project=project, status=RevisionStatus.CHANGES_REQUESTED)
    DesignRevisionFactory(project=project)

    revisions = login(production).get(f"/api/projects/{project.pk}/revisions/").json()

    assert [r["label"] for r in revisions] == ["R2", "R3", "R1"]


def test_documents_respect_client_visibility_and_role(login, manager, production):
    project = ProjectFactory()
    client_user = UserFactory(client=project.client)
    DocumentFactory(project=project, original_name="brief.png", visible_to_client=True)
    DocumentFactory(project=project, original_name="internal-notes.pdf", visible_to_client=False)
    DocumentFactory(
        project=project,
        original_name="signed-quotation.pdf",
        doc_type=DocumentType.QUOTATION,
        visible_to_client=True,
    )
    path = f"/api/projects/{project.pk}/documents/"

    def names(user):
        return sorted(item["original_name"] for item in login(user).get(path).json())

    assert names(manager) == ["brief.png", "internal-notes.pdf", "signed-quotation.pdf"]
    assert names(client_user) == ["brief.png", "signed-quotation.pdf"]
    assert names(production) == ["brief.png", "internal-notes.pdf"]
    detail = login(client_user).get(f"/api/projects/{project.pk}/").json()
    assert detail["counts"]["documents"] == 2


def test_timeline_has_stage_updates_and_activity_in_plain_language(login, manager, design_project):
    project = design_project["project"]
    log_activity(
        action=ActivityAction.QUOTATION_CREATED,
        actor=manager,
        project=project,
        details={"version_no": 2},
    )
    log_activity(
        action=ActivityAction.REVISION_UPLOADED,
        actor=manager,
        project=project,
        details={"revision_no": 2},
    )

    staff = login(manager).get(f"/api/projects/{project.pk}/timeline/").json()
    client = login(design_project["mark"]).get(f"/api/projects/{project.pk}/timeline/").json()

    assert [update["text"] for update in staff["stage_updates"]] == [
        "Project created in Request",
        "Moved from Request to Design",
    ]
    assert [update["text"] for update in client["stage_updates"]] == [
        "We received your request",
        "Quotation accepted. We started the design",
    ]
    assert staff["stage_updates"][1]["source_label"] == "Process rule"
    assert [(a["actor_name"], a["text"]) for a in staff["activity"]] == [
        ("Andrea Villanueva", "uploaded design R2"),
        ("Andrea Villanueva", "saved quotation v2 as a draft"),
    ]
    # Drafts are internal: the client's timeline does not mention them.
    assert [a["text"] for a in client["activity"]] == ["uploaded design R2"]
