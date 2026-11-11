"""The permission matrix of the build guide (section 7), row by row."""

import pytest
from rest_framework.test import APIRequestFactory

from apps.accounts.models import Role
from apps.accounts.permissions import (
    ROLE_CAPABILITIES,
    Capability,
    IsClientUser,
    IsCompanyStaff,
    capabilities_of,
    has_capability,
    permissions_payload,
    require,
)
from apps.accounts.tests.factories import StaffFactory, UserFactory

C = Capability
CLIENT, ADMIN, PM, DESIGNER, PRODUCTION = (
    Role.CLIENT,
    Role.ADMIN,
    Role.PROJECT_MANAGER,
    Role.DESIGNER,
    Role.PRODUCTION,
)

# capability -> roles that have it (guide section 7)
MATRIX = {
    # View projects: client "own", every staff role all projects.
    C.VIEW_ALL_PROJECTS: {ADMIN, PM, DESIGNER, PRODUCTION},
    # Submit a project request: client (own client), admin and manager (on behalf).
    C.SUBMIT_REQUEST: {CLIENT, ADMIN, PM},
    C.SUBMIT_REQUEST_ON_BEHALF: {ADMIN, PM},
    # Edit project details, designate approvers.
    C.EDIT_PROJECTS: {ADMIN, PM},
    # Manage clients: admin and manager; designer and production view only.
    C.VIEW_CLIENTS: {ADMIN, PM, DESIGNER, PRODUCTION},
    C.MANAGE_CLIENTS: {ADMIN, PM},
    # Manage users and settings: admin only.
    C.MANAGE_USERS: {ADMIN},
    C.MANAGE_SETTINGS: {ADMIN},
    # Quotations: upload or send (admin, manager); view (not production); decide.
    C.MANAGE_QUOTATIONS: {ADMIN, PM},
    C.VIEW_QUOTATIONS: {CLIENT, ADMIN, PM, DESIGNER},
    C.DECIDE_QUOTATIONS: {CLIENT},
    # Design revisions: upload (admin, manager, designer); view (all); decide.
    C.UPLOAD_REVISIONS: {ADMIN, PM, DESIGNER},
    C.VIEW_REVISIONS: {CLIENT, ADMIN, PM, DESIGNER, PRODUCTION},
    C.DECIDE_REVISIONS: {CLIENT},
    # Decisions on behalf of a client: admin and manager.
    C.DECIDE_ON_BEHALF: {ADMIN, PM},
    # Change stage (PR7): admin, manager, production.
    C.CHANGE_STAGE: {ADMIN, PM, PRODUCTION},
    # Reopen design (PR8): admin and manager; the client can request it.
    C.REOPEN_DESIGN: {ADMIN, PM},
    C.REQUEST_CHANGE: {CLIENT},
    # Override stage: admin only.
    C.OVERRIDE_STAGE: {ADMIN},
    # Upload documents: every role (scoped by the document services).
    C.UPLOAD_DOCUMENTS: {CLIENT, ADMIN, PM, DESIGNER, PRODUCTION},
    # Dashboard: staff (the client has the portal home).
    C.VIEW_DASHBOARD: {ADMIN, PM, DESIGNER, PRODUCTION},
    C.VIEW_APPROVALS: {ADMIN, PM, DESIGNER},
    # Activity log and exports: admin; manager without exports.
    C.VIEW_ACTIVITY_LOG: {ADMIN, PM},
    C.EXPORT_ACTIVITY: {ADMIN},
    # Email outbox: admin only.
    C.VIEW_EMAIL_OUTBOX: {ADMIN},
}


def test_the_matrix_covers_every_capability_and_role():
    assert set(MATRIX) == set(Capability)
    assert set(ROLE_CAPABILITIES) == set(Role)


@pytest.mark.parametrize("capability", list(Capability))
def test_each_capability_belongs_to_exactly_the_roles_in_the_guide(capability):
    roles_with_capability = {
        role for role, capabilities in ROLE_CAPABILITIES.items() if capability in capabilities
    }

    assert roles_with_capability == MATRIX[capability]


@pytest.mark.django_db
def test_capabilities_follow_the_role_of_the_user():
    client_user = UserFactory()
    production = StaffFactory(role=Role.PRODUCTION)

    assert has_capability(client_user, C.DECIDE_REVISIONS)
    assert not has_capability(client_user, C.VIEW_DASHBOARD)
    assert has_capability(production, C.CHANGE_STAGE)
    assert not has_capability(production, C.VIEW_QUOTATIONS)


@pytest.mark.django_db
def test_inactive_and_anonymous_users_have_no_capabilities():
    from django.contrib.auth.models import AnonymousUser

    inactive_admin = StaffFactory(role=Role.ADMIN, is_active=False)

    assert capabilities_of(inactive_admin) == frozenset()
    assert capabilities_of(AnonymousUser()) == frozenset()


@pytest.mark.django_db
def test_permissions_payload_lists_every_capability_as_true_or_false():
    payload = permissions_payload(StaffFactory(role=Role.DESIGNER))

    assert set(payload) == {capability.value for capability in Capability}
    assert payload["upload_revisions"] is True
    assert payload["manage_quotations"] is False


@pytest.mark.django_db
def test_permission_classes_check_role_and_capability():
    request = APIRequestFactory().get("/")
    admin_only = require(C.MANAGE_SETTINGS)()

    request.user = StaffFactory(role=Role.ADMIN)
    assert admin_only.has_permission(request, None)
    assert IsCompanyStaff().has_permission(request, None)
    assert not IsClientUser().has_permission(request, None)

    request.user = StaffFactory(role=Role.PROJECT_MANAGER)
    assert not admin_only.has_permission(request, None)

    request.user = UserFactory()
    assert not admin_only.has_permission(request, None)
    assert not IsCompanyStaff().has_permission(request, None)
    assert IsClientUser().has_permission(request, None)
