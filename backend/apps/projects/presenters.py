"""Turn projects and their records into API responses for one viewer.

What a viewer receives depends on who they are (process rule PR9): clients never get
staff-only fields, drafts, or internal documents; production staff never get quotations.
The functions here only shape data that the selectors already scoped.
"""

from datetime import datetime

from django.utils import timezone

from apps.accounts.models import Role
from apps.accounts.serializers import ContactSerializer, UserBriefSerializer
from apps.activity.services import describe
from apps.core.choices import DecisionChannel
from apps.core.files import PDF_MIME_TYPE, guess_content_type, is_image
from apps.designs.models import DesignRevision, RevisionStatus
from apps.quotations.models import Quotation

from .models import STAGE_ORDER, Stage, StageUpdateSource
from .selectors import NextStep, PendingDecision, ProjectState, next_step

# What a client reads on the progress timeline for each stage a project enters.
CLIENT_STAGE_TEXT = {
    Stage.REQUEST: "We received your request",
    Stage.DESIGN: "Quotation accepted. We started the design",
    Stage.PRODUCTION: "Design approved. Your display is being built",
    Stage.DELIVERY_INSTALLATION: "Your display is being delivered and installed",
    Stage.TURNOVER: "Your project was turned over",
}


def user_brief(user) -> dict | None:
    return UserBriefSerializer(user).data if user is not None else None


def contact(user) -> dict | None:
    return ContactSerializer(user).data if user is not None else None


def _size(field) -> int | None:
    try:
        return field.size
    except (OSError, ValueError):
        return None


def file_ref(kind: str, pk: int, *, name: str, content_type: str, size: int | None) -> dict:
    """A file the viewer may open through the permission-checked file endpoint."""
    return {
        "url": f"/api/files/{kind}/{pk}/",
        "name": name,
        "content_type": content_type,
        "size_bytes": size,
        "is_image": is_image(content_type),
        "is_pdf": content_type == PDF_MIME_TYPE,
    }


def _extension(field) -> str:
    name = field.name or ""
    return name[name.rfind(".") :].lower() if "." in name else ""


def channel_label(channel: str) -> str:
    return DecisionChannel(channel).label if channel else ""


# --- Next step -----------------------------------------------------------------------


def present_next_step(step: NextStep, viewer) -> dict:
    item = None
    if step.item_kind is not None:
        # Production staff do not open quotations or revisions that wait for approval.
        can_open = viewer.role != Role.PRODUCTION
        item = {
            "kind": step.item_kind,
            "id": step.item_id if can_open else None,
            "label": step.item_label,
        }
    return {
        "code": step.code,
        "text": step.text,
        "waiting_on": step.waiting_on,
        "action_needed": step.action_needed,
        "since": step.since,
        "item": item,
    }


# --- Quotations ------------------------------------------------------------------------


def present_quotation(quotation: Quotation, state: ProjectState) -> dict:
    project = state.project
    latest = state.latest_quotation
    return {
        "id": quotation.pk,
        "version_no": quotation.version_no,
        "label": quotation.label,
        "amount": str(quotation.amount),
        "status": quotation.status,
        "status_label": quotation.get_status_display(),
        "is_latest": latest is not None and latest.pk == quotation.pk,
        "notes": quotation.notes,
        "prepared_by": user_brief(quotation.prepared_by),
        "created_at": quotation.created_at,
        "sent_at": quotation.sent_at,
        "decided_by": user_brief(quotation.decided_by),
        "decided_at": quotation.decided_at,
        # "accepted" or "returned" once decided, also after a newer version superseded it.
        "decision": _quotation_decision(quotation),
        "client_comment": quotation.client_comment,
        "decided_on_behalf": quotation.decided_on_behalf,
        "decision_channel": quotation.decision_channel,
        "decision_channel_label": channel_label(quotation.decision_channel),
        "recorded_by": user_brief(quotation.recorded_by),
        "last_reminded_at": quotation.last_reminded_at,
        "file": file_ref(
            "quotation",
            quotation.pk,
            name=f"{project.project_number}-quotation-{quotation.label}.pdf",
            content_type=PDF_MIME_TYPE,
            size=_size(quotation.file),
        ),
    }


def _quotation_decision(quotation: Quotation) -> str | None:
    if quotation.decided_at is None:
        return None
    if quotation.status == "accepted":
        return "accepted"
    return "returned"


# --- Design revisions ------------------------------------------------------------------


def present_revision(revision: DesignRevision, state: ProjectState) -> dict:
    project = state.project
    approvals = state.approvals(revision)
    by_approver = {approval.approver_id: approval for approval in approvals}
    is_open = revision.status == RevisionStatus.PENDING_APPROVAL

    # One line per designated approver, then decisions of people who are no longer
    # designated (the history keeps them).
    panel = []
    for approver in state.approvers:
        panel.append(_approval_line(approver, by_approver.pop(approver.pk, None), is_open))
    for approval in by_approver.values():
        panel.append(_approval_line(approval.approver, approval, is_open))

    render_type = guess_content_type(revision.render.name)
    spec_sheet = None
    if revision.spec_sheet:
        spec_sheet = file_ref(
            "spec",
            revision.pk,
            name=(
                f"{project.project_number}-{revision.label}-spec-sheet"
                f"{_extension(revision.spec_sheet)}"
            ),
            content_type=guess_content_type(revision.spec_sheet.name),
            size=_size(revision.spec_sheet),
        )
    return {
        "id": revision.pk,
        "revision_no": revision.revision_no,
        "label": revision.label,
        "status": revision.status,
        "status_label": revision.get_status_display(),
        "is_locked": revision.is_locked,
        "locked_at": revision.locked_at,
        "notes": revision.notes,
        "uploaded_by": user_brief(revision.uploaded_by),
        "uploaded_at": revision.uploaded_at,
        "last_reminded_at": revision.last_reminded_at,
        "alt_text": f"Design {revision.label} of {project.project_number}",
        "render": file_ref(
            "render",
            revision.pk,
            name=f"{project.project_number}-{revision.label}-render{_extension(revision.render)}",
            content_type=render_type,
            size=_size(revision.render),
        ),
        "spec_sheet": spec_sheet,
        "thumbnail_url": (
            f"/api/files/render/{revision.pk}/?variant=thumb" if revision.thumbnail else None
        ),
        "approvals": panel,
        "approved_count": sum(1 for line in panel if line["decision"] == "approved"),
        "approver_count": len(state.approvers),
    }


def _approval_line(approver, approval, revision_is_open: bool) -> dict:
    if approval is None:
        return {
            "approver": user_brief(approver),
            "decision": None,
            # Still expected to decide, or the revision closed before they did.
            "state": "pending" if revision_is_open else "no_decision",
            "comment": "",
            "decided_at": None,
            "decided_on_behalf": False,
            "decision_channel": "",
            "decision_channel_label": "",
            "recorded_by": None,
        }
    return {
        "approver": user_brief(approver),
        "decision": approval.decision,
        "state": approval.decision,
        "comment": approval.comment,
        "decided_at": approval.created_at,
        "decided_on_behalf": approval.decided_on_behalf,
        "decision_channel": approval.decision_channel,
        "decision_channel_label": channel_label(approval.decision_channel),
        "recorded_by": user_brief(approval.recorded_by),
    }


def revision_summary(revision: DesignRevision | None) -> dict | None:
    """The few fields a project card needs about the approved design."""
    if revision is None:
        return None
    return {
        "id": revision.pk,
        "label": revision.label,
        "locked_at": revision.locked_at,
        "thumbnail_url": (
            f"/api/files/render/{revision.pk}/?variant=thumb" if revision.thumbnail else None
        ),
    }


# --- Documents, stage updates, activity ----------------------------------------------------


def present_document(document) -> dict:
    return {
        "id": document.pk,
        "doc_type": document.doc_type,
        "doc_type_label": document.get_doc_type_display(),
        "original_name": document.original_name,
        "visible_to_client": document.visible_to_client,
        "uploaded_by": user_brief(document.uploaded_by),
        "created_at": document.created_at,
        "file": file_ref(
            "document",
            document.pk,
            name=document.original_name,
            content_type=document.content_type,
            size=document.size_bytes,
        ),
        "thumbnail_url": (
            f"/api/files/document/{document.pk}/?variant=thumb" if document.thumbnail else None
        ),
    }


def present_stage_update(update, viewer) -> dict:
    to_label = Stage(update.to_stage).label
    from_label = Stage(update.from_stage).label if update.from_stage else ""
    if not update.from_stage:
        staff_text = "Project created in Request"
    else:
        staff_text = f"Moved from {from_label} to {to_label}"
    client_text = CLIENT_STAGE_TEXT[Stage(update.to_stage)]
    if update.from_stage and STAGE_ORDER.index(update.to_stage) < STAGE_ORDER.index(
        update.from_stage
    ):
        client_text = "The design was reopened for changes"
    return {
        "id": update.pk,
        "from_stage": update.from_stage,
        "from_stage_label": from_label,
        "to_stage": update.to_stage,
        "to_stage_label": to_label,
        "text": client_text if viewer.is_client_user else staff_text,
        "remarks": update.remarks,
        "source": update.source,
        "source_label": StageUpdateSource(update.source).label,
        "updated_by": user_brief(update.updated_by),
        "created_at": update.created_at,
    }


def present_activity(entry, *, with_project: bool = False) -> dict:
    text, names_actor = describe(entry)
    data = {
        "id": entry.pk,
        "action": entry.action,
        "action_label": entry.get_action_display(),
        "actor": user_brief(entry.actor) if entry.actor_id else None,
        # The name that starts the sentence; empty when the text is a full sentence.
        "actor_name": entry.actor.full_name if names_actor and entry.actor_id else None,
        "text": text,
        "created_at": entry.created_at,
    }
    if with_project:
        project = entry.project
        data["project"] = (
            {"id": project.pk, "project_number": project.project_number, "title": project.title}
            if project is not None
            else None
        )
    return data


# --- Projects ----------------------------------------------------------------------------


def present_project_card(state: ProjectState, viewer, now: datetime | None = None) -> dict:
    """A project as shown in lists, on the dashboard, and on the client's home."""
    now = now or timezone.now()
    project = state.project
    today = timezone.localtime(now).date()
    last_activity = getattr(project, "last_activity_at", None) or project.updated_at
    return {
        "id": project.pk,
        "project_number": project.project_number,
        "title": project.title,
        "client": {"id": project.client_id, "company_name": project.client.company_name},
        "project_type": project.project_type,
        "project_type_label": project.get_project_type_display(),
        "stage": project.stage,
        "stage_label": project.get_stage_display(),
        "status": project.status,
        "status_label": project.get_status_display(),
        "target_date": project.target_date,
        "is_overdue": project.is_overdue(today),
        "days_until_target": (project.target_date - today).days,
        "manager": user_brief(project.manager),
        "next_step": present_next_step(next_step(state, viewer, now), viewer),
        "stage_dates": state.stage_dates,
        "approved_revision": revision_summary(state.approved_revision),
        "last_activity_at": last_activity,
        "created_at": project.created_at,
    }


def present_project_detail(
    state: ProjectState, viewer, now: datetime | None = None, *, document_count: int = 0
) -> dict:
    """Everything the project page shows above its tabs, for one viewer."""
    now = now or timezone.now()
    project = state.project
    is_client = viewer.is_client_user
    data = present_project_card(state, viewer, now)

    quotations = state.visible_quotations(viewer)
    revisions = state.visible_revisions(viewer)
    pending = state.pending_revision if state.pending_revision in revisions else None
    current_revision = pending or (revisions[0] if revisions else None)
    approved = state.approved_revision

    client = project.client
    client_data = {"id": client.pk, "company_name": client.company_name}
    if not is_client:
        # Contact details and staff-only notes never reach the client portal.
        client_data.update(
            {
                "contact_person": client.contact_person,
                "email": client.email,
                "phone": client.phone,
                "address": client.address,
                "notes": client.notes,
            }
        )

    data.update(
        {
            "client": client_data,
            "location": project.location,
            "dimensions": project.dimensions,
            "description": project.description,
            "manager": contact(project.manager),
            "designer": None if is_client else user_brief(project.designer),
            "created_by": user_brief(project.created_by),
            "design_reopened": project.design_reopened,
            "requires_requote": project.requires_requote,
            "approvers": [contact(user) for user in state.approvers],
            "current_quotation": (present_quotation(quotations[0], state) if quotations else None),
            "current_revision": (
                present_revision(current_revision, state) if current_revision else None
            ),
            "approved_revision": present_revision(approved, state) if approved else None,
            "counts": {
                "quotations": len(quotations),
                "revisions": len(revisions),
                "documents": document_count,
            },
            "viewer": {
                "is_designated_approver": viewer.pk in state.approver_ids,
                "can_view_quotations": viewer.role != Role.PRODUCTION,
            },
        }
    )
    return data


# --- Pending decisions ----------------------------------------------------------------------


def present_pending_decision(decision: PendingDecision, viewer, now: datetime) -> dict:
    project = decision.project
    waiting = now - decision.waiting_since
    can_open = viewer.role != Role.PRODUCTION
    return {
        "kind": decision.kind,
        "id": decision.item.pk if can_open else None,
        "label": decision.label,
        "project": {
            "id": project.pk,
            "project_number": project.project_number,
            "title": project.title,
            "client_name": project.client.company_name,
        },
        "waiting_since": decision.waiting_since,
        "waiting_hours": round(waiting.total_seconds() / 3600, 1),
        "is_overdue": decision.is_overdue,
        "pending_approvers": [user_brief(user) for user in decision.pending_approvers],
        "approver_count": decision.approver_count,
        "decided_count": decision.decided_count,
        "last_reminded_at": decision.last_reminded_at,
    }
