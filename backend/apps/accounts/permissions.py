"""What each role may do (build guide, section 7; process rule PR9).

`ROLE_CAPABILITIES` is the single source of truth. The API checks it with the DRF
permission classes below, and `/api/auth/me/` sends it to the React app so the UI shows
only what the user may do. Rules that depend on a particular project (for example
"designated approver of this project") are checked by the services of that feature.
"""

from enum import StrEnum

from rest_framework.permissions import BasePermission

from .models import Role


class Capability(StrEnum):
    VIEW_ALL_PROJECTS = "view_all_projects"  # staff; clients see only their client's projects
    SUBMIT_REQUEST = "submit_request"
    SUBMIT_REQUEST_ON_BEHALF = "submit_request_on_behalf"
    EDIT_PROJECTS = "edit_projects"  # project details and designated approvers
    VIEW_CLIENTS = "view_clients"
    MANAGE_CLIENTS = "manage_clients"
    MANAGE_USERS = "manage_users"
    MANAGE_SETTINGS = "manage_settings"
    VIEW_QUOTATIONS = "view_quotations"  # clients: only sent ones of their own projects
    MANAGE_QUOTATIONS = "manage_quotations"  # upload and send
    DECIDE_QUOTATIONS = "decide_quotations"  # designated approvers
    VIEW_REVISIONS = "view_revisions"  # production: approved design and history
    UPLOAD_REVISIONS = "upload_revisions"
    DECIDE_REVISIONS = "decide_revisions"  # designated approvers
    DECIDE_ON_BEHALF = "decide_on_behalf"  # record a client's decision, with the channel
    CHANGE_STAGE = "change_stage"  # PR7
    REOPEN_DESIGN = "reopen_design"  # PR8
    REQUEST_CHANGE = "request_change"  # client asks for a change after approval
    OVERRIDE_STAGE = "override_stage"
    UPLOAD_DOCUMENTS = "upload_documents"
    VIEW_DASHBOARD = "view_dashboard"
    VIEW_APPROVALS = "view_approvals"  # the list of all pending decisions
    VIEW_ACTIVITY_LOG = "view_activity_log"  # activity across projects
    EXPORT_ACTIVITY = "export_activity"
    VIEW_EMAIL_OUTBOX = "view_email_outbox"


C = Capability

ROLE_CAPABILITIES: dict[str, frozenset[Capability]] = {
    Role.CLIENT: frozenset(
        {
            C.SUBMIT_REQUEST,
            C.VIEW_QUOTATIONS,
            C.DECIDE_QUOTATIONS,
            C.VIEW_REVISIONS,
            C.DECIDE_REVISIONS,
            C.REQUEST_CHANGE,
            C.UPLOAD_DOCUMENTS,
        }
    ),
    Role.ADMIN: frozenset(
        {
            C.VIEW_ALL_PROJECTS,
            C.SUBMIT_REQUEST,
            C.SUBMIT_REQUEST_ON_BEHALF,
            C.EDIT_PROJECTS,
            C.VIEW_CLIENTS,
            C.MANAGE_CLIENTS,
            C.MANAGE_USERS,
            C.MANAGE_SETTINGS,
            C.VIEW_QUOTATIONS,
            C.MANAGE_QUOTATIONS,
            C.VIEW_REVISIONS,
            C.UPLOAD_REVISIONS,
            C.DECIDE_ON_BEHALF,
            C.CHANGE_STAGE,
            C.REOPEN_DESIGN,
            C.OVERRIDE_STAGE,
            C.UPLOAD_DOCUMENTS,
            C.VIEW_DASHBOARD,
            C.VIEW_APPROVALS,
            C.VIEW_ACTIVITY_LOG,
            C.EXPORT_ACTIVITY,
            C.VIEW_EMAIL_OUTBOX,
        }
    ),
    Role.PROJECT_MANAGER: frozenset(
        {
            C.VIEW_ALL_PROJECTS,
            C.SUBMIT_REQUEST,
            C.SUBMIT_REQUEST_ON_BEHALF,
            C.EDIT_PROJECTS,
            C.VIEW_CLIENTS,
            C.MANAGE_CLIENTS,
            C.VIEW_QUOTATIONS,
            C.MANAGE_QUOTATIONS,
            C.VIEW_REVISIONS,
            C.UPLOAD_REVISIONS,
            C.DECIDE_ON_BEHALF,
            C.CHANGE_STAGE,
            C.REOPEN_DESIGN,
            C.UPLOAD_DOCUMENTS,
            C.VIEW_DASHBOARD,
            C.VIEW_APPROVALS,
            C.VIEW_ACTIVITY_LOG,
        }
    ),
    Role.DESIGNER: frozenset(
        {
            C.VIEW_ALL_PROJECTS,
            C.VIEW_CLIENTS,
            C.VIEW_QUOTATIONS,
            C.VIEW_REVISIONS,
            C.UPLOAD_REVISIONS,
            C.UPLOAD_DOCUMENTS,
            C.VIEW_DASHBOARD,
            C.VIEW_APPROVALS,
        }
    ),
    Role.PRODUCTION: frozenset(
        {
            C.VIEW_ALL_PROJECTS,
            C.VIEW_CLIENTS,
            C.VIEW_REVISIONS,
            C.CHANGE_STAGE,
            C.UPLOAD_DOCUMENTS,
            C.VIEW_DASHBOARD,
        }
    ),
}


def capabilities_of(user) -> frozenset[Capability]:
    if not getattr(user, "is_authenticated", False) or not user.is_active:
        return frozenset()
    return ROLE_CAPABILITIES.get(user.role, frozenset())


def has_capability(user, capability: Capability) -> bool:
    return capability in capabilities_of(user)


def permissions_payload(user) -> dict[str, bool]:
    """Every capability with true or false, for `/api/auth/me/`."""
    granted = capabilities_of(user)
    return {capability.value: capability in granted for capability in Capability}


class IsCompanyStaff(BasePermission):
    """Any of the four staff roles (the staff workspace)."""

    message = "This area is for the staff of the company."

    def has_permission(self, request, view):
        user = request.user
        return bool(user and user.is_authenticated and user.is_company_staff)


class IsClientUser(BasePermission):
    """A user of a client company (the client portal)."""

    message = "This area is for client users."

    def has_permission(self, request, view):
        user = request.user
        return bool(user and user.is_authenticated and user.is_client_user)


def require(capability: Capability) -> type[BasePermission]:
    """A DRF permission class that allows only users whose role has `capability`."""

    class HasCapability(BasePermission):
        message = "Your role does not allow this."

        def has_permission(self, request, view):
            return has_capability(request.user, capability)

    HasCapability.__name__ = f"Has_{capability.value}"
    return HasCapability
