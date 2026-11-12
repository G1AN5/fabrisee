"""The Django admin site: every page opens, and history can be read but not changed."""

import pytest
from django.contrib import admin
from django.urls import reverse
from django.utils import timezone

from apps.accounts.models import User
from apps.activity.models import ActivityLog
from apps.activity.tests.factories import ActivityLogFactory
from apps.core.models import SystemSetting
from apps.designs.models import Approval, DesignRevision, RevisionStatus
from apps.designs.tests.factories import ApprovalFactory, DesignRevisionFactory
from apps.notifications.models import EmailLog, Notification
from apps.notifications.tests.factories import EmailLogFactory, NotificationFactory
from apps.projects.models import Document, Project, StageUpdate
from apps.projects.tests.factories import DocumentFactory, ProjectFactory, StageUpdateFactory
from apps.quotations.models import Quotation, QuotationStatus
from apps.quotations.tests.factories import QuotationFactory

pytestmark = pytest.mark.django_db


@pytest.fixture
def owner(client):
    user = User.objects.create_superuser(
        email="owner@fabrisee.test", password="Correct-Horse-42", full_name="Teresa Lim"
    )
    client.force_login(user)
    return user


@pytest.fixture
def records():
    project = ProjectFactory()
    StageUpdateFactory(project=project)
    DocumentFactory(project=project)
    QuotationFactory(project=project, status=QuotationStatus.ACCEPTED)
    revision = DesignRevisionFactory(
        project=project, status=RevisionStatus.APPROVED, locked_at=timezone.now()
    )
    ApprovalFactory(revision=revision)
    NotificationFactory(project=project)
    EmailLogFactory()
    ActivityLogFactory(project=project)
    SystemSetting.load()
    return project


def test_every_admin_list_and_record_page_opens(client, owner, records):
    for model in admin.site._registry:
        options = model._meta
        changelist = reverse(f"admin:{options.app_label}_{options.model_name}_changelist")
        assert client.get(changelist).status_code == 200, changelist

        record = model.objects.first()
        if record is not None:
            change = reverse(
                f"admin:{options.app_label}_{options.model_name}_change", args=[record.pk]
            )
            assert client.get(change).status_code == 200, change


@pytest.mark.parametrize("model", [ActivityLog, StageUpdate, Approval, Notification, EmailLog])
def test_history_records_cannot_be_added_changed_or_deleted_in_the_admin(rf, owner, records, model):
    model_admin = admin.site._registry[model]
    request = rf.get("/admin/")
    request.user = owner

    assert model_admin.has_view_permission(request)
    assert not model_admin.has_add_permission(request)
    assert not model_admin.has_change_permission(request)
    assert not model_admin.has_delete_permission(request)


@pytest.mark.parametrize("model", [Project, Quotation, DesignRevision, Document])
def test_project_records_are_never_added_or_deleted_in_the_admin(rf, owner, records, model):
    model_admin = admin.site._registry[model]
    request = rf.get("/admin/")
    request.user = owner

    assert not model_admin.has_add_permission(request)
    assert not model_admin.has_delete_permission(request)


def test_the_stage_of_a_project_is_read_only_in_the_admin(rf, owner, records):
    model_admin = admin.site._registry[Project]
    request = rf.get("/admin/")
    request.user = owner

    assert {"project_number", "stage"} <= set(model_admin.get_readonly_fields(request, records))


def test_accepted_quotations_and_approved_revisions_are_fully_read_only(rf, owner, records):
    request = rf.get("/admin/")
    request.user = owner
    quotation = Quotation.objects.get()
    revision = DesignRevision.objects.get()

    quotation_fields = admin.site._registry[Quotation].get_readonly_fields(request, quotation)
    revision_fields = admin.site._registry[DesignRevision].get_readonly_fields(request, revision)

    assert {"amount", "file", "notes"} <= set(quotation_fields)
    assert {"render", "spec_sheet", "notes"} <= set(revision_fields)


def test_users_of_the_admin_site_need_staff_status(client):
    manager = User.objects.create_user(
        email="pm@fabrisee.test",
        password="x",
        full_name="Andrea Villanueva",
        role="project_manager",
    )
    client.force_login(manager)

    response = client.get(reverse("admin:index"))

    # The role decides what a user may do in FabriSee; only "staff status" opens the admin.
    assert response.status_code == 302
    assert "/admin/login/" in response["Location"]
