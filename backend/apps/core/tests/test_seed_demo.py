"""The demo data (build guide, section 12): accounts, the eight situations, and its rules.

The data is loaded once for the whole module (it takes a few seconds). Tests that need an
empty database are in test_seed_commands.py.
"""

import itertools
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import pytest
from django.core.files.storage import default_storage
from django.db import transaction
from django.test import override_settings

from apps.accounts.models import Role, User
from apps.activity.models import ActivityAction, ActivityLog
from apps.clients.models import Client
from apps.core.choices import DecisionChannel
from apps.core.demo.accounts import DEMO_PASSWORD, USERS
from apps.core.demo.seed import DemoDataError, demo_data_exists, seed_demo
from apps.core.files import detect_mime_type
from apps.designs.models import ApprovalDecision, DesignRevision, RevisionStatus
from apps.notifications.models import EmailLog, Notification, NotificationEvent
from apps.projects.models import (
    Document,
    DocumentType,
    Project,
    ProjectStatus,
    Stage,
    StageUpdate,
    StageUpdateSource,
)
from apps.projects.selectors import pending_decisions
from apps.quotations.models import Quotation, QuotationStatus

MANILA = ZoneInfo("Asia/Manila")
NOW = datetime(2026, 11, 11, 14, 30, tzinfo=MANILA)
THREE_DAYS = timedelta(days=3)


@pytest.fixture(scope="module")
def demo(django_db_setup, django_db_blocker, tmp_path_factory):
    """The demo data, loaded once for this module and rolled back afterwards."""
    media_root = tmp_path_factory.mktemp("demo-media")
    with (
        django_db_blocker.unblock(),
        override_settings(MEDIA_ROOT=media_root),
        transaction.atomic(),
    ):
        seed_demo(NOW)
        yield media_root
        transaction.set_rollback(True)


@pytest.fixture
def demo_media(demo, settings):
    """Point the storage of the running test at the files of the demo data."""
    settings.MEDIA_ROOT = demo
    return demo


def project(title: str) -> Project:
    return Project.objects.get(title=title)


pytestmark = pytest.mark.django_db


# --- Accounts -----------------------------------------------------------------------


def test_the_ten_demo_accounts_exist_with_their_roles(demo):
    by_email = {user.email: user for user in User.objects.select_related("client")}

    assert len(by_email) == 10
    assert by_email["owner@fabrisee.test"].role == Role.ADMIN
    assert by_email["pm@fabrisee.test"].role == Role.PROJECT_MANAGER
    assert by_email["designer@fabrisee.test"].role == Role.DESIGNER
    assert by_email["production@fabrisee.test"].role == Role.PRODUCTION
    clients = {
        "joanna@aurelia.test": "Aurelia Audio Labs",
        "mark@aurelia.test": "Aurelia Audio Labs",
        "liza@tindahantech.test": "Tindahan Tech PH",
        "nico@kapetirya.test": "Kapetirya Coffee House",
        "bianca@lunaria.test": "Lunaria Skin Studio",
        "ella@lunaria.test": "Lunaria Skin Studio",
    }
    for email, company in clients.items():
        assert by_email[email].role == Role.CLIENT
        assert by_email[email].client.company_name == company
    assert all(user.check_password(DEMO_PASSWORD) for user in by_email.values())


def test_only_the_owner_can_open_the_django_admin(demo):
    admins = User.objects.filter(is_staff=True)

    assert [user.email for user in admins] == ["owner@fabrisee.test"]
    assert admins.get().is_superuser


def test_one_account_still_has_to_acknowledge_the_privacy_notice(demo):
    pending = User.objects.filter(privacy_acknowledged_at__isnull=True)

    assert [user.email for user in pending] == ["ella@lunaria.test"]


def test_demo_accounts_use_reserved_test_domains(demo):
    assert all(user.email.endswith(".test") for user in USERS)
    assert all(client.email.endswith(".test") for client in Client.objects.all())


# --- The eight situations --------------------------------------------------------------


def test_there_is_one_project_for_each_situation(demo):
    situations = {
        "Experience counter and brand wall": (Stage.DESIGN, ProjectStatus.ACTIVE),
        "Product display stands (set of 6)": (Stage.REQUEST, ProjectStatus.ACTIVE),
        "Café counter and menu signage": (Stage.PRODUCTION, ProjectStatus.ACTIVE),
        "Trade fair booth, 3 m × 6 m": (Stage.DELIVERY_INSTALLATION, ProjectStatus.ACTIVE),
        "Window display refresh": (Stage.TURNOVER, ProjectStatus.COMPLETED),
        "Illuminated brand sign": (Stage.REQUEST, ProjectStatus.ACTIVE),
        "Pop-up booth for weekend market": (Stage.DESIGN, ProjectStatus.ACTIVE),
        "End-cap product display": (Stage.REQUEST, ProjectStatus.ACTIVE),
    }

    found = {p.title: (p.stage, p.status) for p in Project.objects.all()}

    assert found == situations


def test_project_numbers_follow_the_order_of_creation(demo):
    projects = list(Project.objects.order_by("created_at"))

    assert [p.project_number for p in projects] == [f"FS-2026-{n:04d}" for n in range(1, 9)]


def test_1_revision_r2_waits_for_one_of_two_approvers_for_three_days(demo):
    experience = project("Experience counter and brand wall")
    r1, r2 = experience.revisions.order_by("revision_no")

    assert r1.status == RevisionStatus.CHANGES_REQUESTED
    assert r2.status == RevisionStatus.PENDING_APPROVAL
    assert NOW - r2.uploaded_at >= THREE_DAYS
    decisions = {a.approver.email: a.decision for a in r2.approvals.select_related("approver")}
    assert decisions == {"joanna@aurelia.test": ApprovalDecision.APPROVED}
    assert {u.email for u in experience.approvers.all()} == {
        "joanna@aurelia.test",
        "mark@aurelia.test",
    }
    # The overdue reminder (PR6) is visible: Mark was reminded and the manager alerted.
    assert r2.last_reminded_at == r2.uploaded_at + timedelta(hours=48)
    reminder = Notification.objects.get(
        project=experience, event=NotificationEvent.DECISION_REMINDER
    )
    alert = Notification.objects.get(
        project=experience, event=NotificationEvent.DECISION_OVERDUE_ALERT
    )
    assert reminder.user.email == "mark@aurelia.test"
    assert alert.user == experience.manager


def test_2_quotation_v1_was_sent_three_days_ago_without_a_decision(demo):
    stands = project("Product display stands (set of 6)")
    quotation = stands.quotations.get()

    assert quotation.status == QuotationStatus.SENT
    assert NOW - quotation.sent_at >= THREE_DAYS
    assert quotation.decided_at is None
    assert quotation.last_reminded_at is not None


def test_3_r3_is_approved_and_locked_with_r1_and_r2_in_the_history(demo):
    cafe = project("Café counter and menu signage")
    r1, r2, r3 = cafe.revisions.order_by("revision_no")

    assert (r1.status, r2.status) == (
        RevisionStatus.CHANGES_REQUESTED,
        RevisionStatus.CHANGES_REQUESTED,
    )
    assert r3.status == RevisionStatus.APPROVED
    assert r3.is_locked
    assert cafe.stage == Stage.PRODUCTION
    # The decision was recorded on behalf of the client, with the channel.
    approval = r3.approvals.get()
    assert approval.decided_on_behalf
    assert approval.decision_channel == DecisionChannel.PHONE
    assert approval.approver.email == "nico@kapetirya.test"
    assert approval.recorded_by.email == "pm@fabrisee.test"
    # The project is past its target date, so the dashboard shows an overdue project.
    assert cafe.is_overdue(NOW.date())


def test_4_the_trade_fair_booth_is_in_delivery_and_installation(demo):
    booth = project("Trade fair booth, 3 m × 6 m")
    last = booth.stage_updates.order_by("created_at").last()

    assert booth.stage == Stage.DELIVERY_INSTALLATION
    assert (last.from_stage, last.to_stage) == (Stage.PRODUCTION, Stage.DELIVERY_INSTALLATION)
    assert last.source == StageUpdateSource.MANUAL
    assert last.updated_by.role == Role.PRODUCTION
    assert last.remarks


def test_5_the_completed_project_has_turnover_documents(demo):
    window = project("Window display refresh")
    turnover = window.documents.filter(doc_type=DocumentType.TURNOVER)

    assert window.status == ProjectStatus.COMPLETED
    assert turnover.count() == 2
    assert all(document.visible_to_client for document in turnover)
    # One internal document is not visible to the client (PR9).
    internal = window.documents.get(visible_to_client=False)
    assert internal.doc_type == DocumentType.OTHER


def test_6_the_new_request_has_no_quotation_and_no_approvers_yet(demo):
    sign = project("Illuminated brand sign")

    assert sign.stage == Stage.REQUEST
    assert not sign.quotations.exists()
    assert not sign.approvers.exists()
    assert sign.documents.filter(doc_type=DocumentType.REFERENCE).count() == 2
    assert NOW - sign.created_at < timedelta(days=1)


def test_7_r1_has_changes_requested_and_r2_is_not_uploaded_yet(demo):
    popup = project("Pop-up booth for weekend market")
    revision = popup.revisions.get()
    approval = revision.approvals.get()

    assert revision.status == RevisionStatus.CHANGES_REQUESTED
    assert approval.decision == ApprovalDecision.CHANGES_REQUESTED
    assert "foldable" in approval.comment
    assert popup.stage == Stage.DESIGN


def test_8_quotation_v1_was_returned_with_comments_and_v2_is_a_draft(demo):
    endcap = project("End-cap product display")
    v1, v2 = endcap.quotations.order_by("version_no")

    # A new version supersedes the returned one; the decision stays on record.
    assert v1.status == QuotationStatus.SUPERSEDED
    assert v1.decided_by.email == "bianca@lunaria.test"
    assert "budget" in v1.client_comment
    assert v2.status == QuotationStatus.DRAFT
    assert v2.sent_at is None
    assert v2.amount < v1.amount
    assert ActivityLog.objects.filter(
        project=endcap, action=ActivityAction.QUOTATION_RETURNED
    ).exists()


# --- Consistency of the history ----------------------------------------------------------


def test_the_stage_of_every_project_matches_its_last_stage_update(demo):
    for item in Project.objects.all():
        updates = list(item.stage_updates.order_by("created_at", "id"))

        assert updates[0].from_stage == ""
        assert updates[0].to_stage == Stage.REQUEST
        assert updates[-1].to_stage == item.stage
        for previous, current in itertools.pairwise(updates):
            assert current.from_stage == previous.to_stage
            assert current.created_at >= previous.created_at


def test_moves_into_design_and_production_come_only_from_the_rules(demo):
    """PR3 and PR5: nobody moved a project to Design or Production by hand."""
    by_rule = StageUpdate.objects.filter(to_stage__in=[Stage.DESIGN, Stage.PRODUCTION])

    assert by_rule.exists()
    assert set(by_rule.values_list("source", flat=True)) == {StageUpdateSource.RULE}
    for update in by_rule.filter(to_stage=Stage.DESIGN):
        assert update.project.quotations.filter(status=QuotationStatus.ACCEPTED).exists()
    for update in by_rule.filter(to_stage=Stage.PRODUCTION):
        assert update.project.revisions.filter(status=RevisionStatus.APPROVED).exists()


def test_an_approved_revision_was_approved_by_every_designated_approver(demo):
    for revision in DesignRevision.objects.filter(status=RevisionStatus.APPROVED):
        approvers = set(revision.project.approvers.values_list("pk", flat=True))
        approved_by = set(
            revision.approvals.filter(decision=ApprovalDecision.APPROVED).values_list(
                "approver_id", flat=True
            )
        )

        assert approvers
        assert approvers == approved_by
        assert revision.locked_at is not None


def test_the_amount_of_every_quotation_is_positive_and_has_a_pdf(demo, demo_media):
    for quotation in Quotation.objects.all():
        assert quotation.amount > 0
        assert default_storage.exists(quotation.file.name)
        with quotation.file.open("rb") as handle:
            assert detect_mime_type(handle) == "application/pdf"


def test_every_revision_has_a_render_a_spec_sheet_and_a_thumbnail(demo, demo_media):
    for revision in DesignRevision.objects.all():
        with revision.render.open("rb") as handle:
            assert detect_mime_type(handle) == "image/png"
        with revision.spec_sheet.open("rb") as handle:
            assert detect_mime_type(handle) == "application/pdf"
        with revision.thumbnail.open("rb") as handle:
            assert detect_mime_type(handle) == "image/webp"


def test_stored_files_have_random_names_and_documents_keep_the_original_name(demo, demo_media):
    document = Document.objects.get(original_name="turnover-checklist.pdf")

    assert "turnover-checklist" not in document.file.name
    assert document.size_bytes == default_storage.size(document.file.name)
    assert document.content_type == "application/pdf"


def test_nothing_in_the_history_is_dated_in_the_future(demo):
    assert not ActivityLog.objects.filter(created_at__gt=NOW).exists()
    assert not Notification.objects.filter(created_at__gt=NOW).exists()
    assert not StageUpdate.objects.filter(created_at__gt=NOW).exists()


# --- Notifications, email log, pending decisions -----------------------------------------


def test_every_demo_user_has_notifications_and_at_least_one_is_unread(demo):
    for user in User.objects.all():
        own = Notification.objects.filter(user=user)

        assert own.exists(), user.email
        assert own.filter(is_read=False).exists(), user.email


def test_every_notification_has_a_logged_email_with_the_project_number(demo):
    assert Notification.objects.count() == EmailLog.objects.count()
    email = EmailLog.objects.select_related("notification__project").first()

    assert email.notification is not None
    assert email.subject.startswith(f"[FabriSee] {email.notification.project.project_number} · ")


def test_notifications_link_to_the_area_of_the_recipient(demo):
    for notification in Notification.objects.select_related("user"):
        expected = "/portal/projects/" if notification.user.is_client_user else "/app/projects/"

        assert notification.link.startswith(expected)


def test_the_dashboard_has_two_overdue_pending_decisions(demo):
    manager = User.objects.get(email="pm@fabrisee.test")

    decisions = pending_decisions(manager, NOW)

    assert [(d.project.title, d.label) for d in decisions] == [
        ("Product display stands (set of 6)", "Quotation v1"),
        ("Experience counter and brand wall", "Design R2"),
    ]
    assert all(decision.is_overdue for decision in decisions)
    assert [u.full_name for u in decisions[1].pending_approvers] == ["Mark Bautista"]


# --- Loading rules -----------------------------------------------------------------------


def test_demo_data_is_not_loaded_twice(demo):
    assert demo_data_exists()

    with pytest.raises(DemoDataError):
        seed_demo(NOW)
