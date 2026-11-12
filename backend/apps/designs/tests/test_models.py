import pytest
from django.db import IntegrityError, transaction
from django.db.models import ProtectedError
from django.utils import timezone

from apps.core.tests.files import png_upload
from apps.designs.models import ApprovalDecision, RevisionStatus
from apps.designs.tests.factories import ApprovalFactory, DesignRevisionFactory
from apps.projects.tests.factories import ProjectFactory

pytestmark = pytest.mark.django_db


def test_revisions_are_numbered_per_project_and_shown_as_r_numbers():
    project = ProjectFactory()
    first = DesignRevisionFactory(project=project, status=RevisionStatus.CHANGES_REQUESTED)
    second = DesignRevisionFactory(project=project)

    assert (first.label, second.label) == ("R1", "R2")
    with pytest.raises(IntegrityError), transaction.atomic():
        DesignRevisionFactory(project=project, revision_no=2, status=RevisionStatus.SUPERSEDED)


def test_only_one_revision_per_project_can_be_pending_approval():
    project = ProjectFactory()
    DesignRevisionFactory(project=project)

    with pytest.raises(IntegrityError), transaction.atomic():
        DesignRevisionFactory(project=project)


def test_an_approver_decides_once_per_revision():
    approval = ApprovalFactory()

    with pytest.raises(IntegrityError), transaction.atomic():
        ApprovalFactory(revision=approval.revision, approver=approval.approver)


def test_a_change_request_needs_a_comment():
    with pytest.raises(IntegrityError), transaction.atomic():
        ApprovalFactory(decision=ApprovalDecision.CHANGES_REQUESTED, comment="")

    ApprovalFactory(decision=ApprovalDecision.CHANGES_REQUESTED, comment="Lower the counter.")
    ApprovalFactory(decision=ApprovalDecision.APPROVED, comment="")


def test_the_approved_design_is_locked_against_file_changes():
    revision = DesignRevisionFactory(status=RevisionStatus.APPROVED, locked_at=timezone.now())

    revision.render = png_upload("replacement.png")
    with pytest.raises(ProtectedError):
        revision.save()

    revision.refresh_from_db()
    revision.spec_sheet = png_upload("new-spec.png")
    with pytest.raises(ProtectedError):
        revision.save()


def test_a_pending_revision_can_still_be_updated():
    revision = DesignRevisionFactory()

    revision.notes = "Lighting added."
    revision.status = RevisionStatus.SUPERSEDED
    revision.save()

    revision.refresh_from_db()
    assert revision.status == RevisionStatus.SUPERSEDED


def test_revisions_and_approvals_are_never_deleted():
    approval = ApprovalFactory()

    with pytest.raises(ProtectedError):
        approval.delete()
    with pytest.raises(ProtectedError):
        approval.revision.delete()
