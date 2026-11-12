from datetime import datetime

from django.utils import timezone

from .models import ActivityAction, ActivityLog

# Actions a client may see on the timeline of their own project. Drafts, reminders to
# staff, and other internal steps stay inside the staff workspace (PR9).
CLIENT_VISIBLE_ACTIONS = frozenset(
    {
        ActivityAction.REQUEST_SUBMITTED,
        ActivityAction.PROJECT_CREATED,
        ActivityAction.QUOTATION_SENT,
        ActivityAction.QUOTATION_ACCEPTED,
        ActivityAction.QUOTATION_RETURNED,
        ActivityAction.REVISION_UPLOADED,
        ActivityAction.REVISION_APPROVED_BY,
        ActivityAction.REVISION_CHANGES_REQUESTED_BY,
        ActivityAction.REVISION_LOCKED,
        ActivityAction.STAGE_CHANGED,
        ActivityAction.STAGE_OVERRIDDEN,
        ActivityAction.DESIGN_REOPENED,
    }
)

STAGE_LABELS = {
    "request": "Request",
    "design": "Design",
    "production": "Production",
    "delivery_installation": "Delivery and Installation",
    "turnover": "Turnover",
}
CHANNEL_LABELS = {"email": "email", "phone": "phone", "in_person": "in person"}
RULE_REASONS = {
    "PR2": "request submitted",
    "PR3": "quotation accepted",
    "PR5": "design approved by all designated approvers",
    "PR8": "design reopened",
}


def log_activity(
    *,
    action: str,
    actor=None,
    project=None,
    details: dict | None = None,
    at: datetime | None = None,
) -> ActivityLog:
    """Append one entry to the activity log. Every service calls this for what it did."""
    return ActivityLog.objects.create(
        action=action,
        actor=actor,
        project=project,
        details=details or {},
        created_at=at or timezone.now(),
    )


def _on_behalf(details: dict) -> str:
    """` on behalf of J. Cruz (phone)` when staff recorded a client's decision."""
    if not details.get("on_behalf"):
        return ""
    name = details.get("approver_name", "the client")
    channel = CHANNEL_LABELS.get(details.get("channel", ""), "")
    return f" on behalf of {name}" + (f" ({channel})" if channel else "")


def describe(entry: ActivityLog) -> tuple[str, bool]:
    """Describe an activity entry in plain language.

    Returns `(text, names_actor)`. When `names_actor` is true the text continues a sentence
    that starts with the actor's name ("Andrea Villanueva" + " sent quotation v1 to the
    client"); otherwise the text is a complete sentence about something the system did.
    """
    details = entry.details or {}
    action = entry.action
    version = details.get("version_no", "?")
    revision = details.get("revision_no", "?")
    from_stage = STAGE_LABELS.get(details.get("from_stage", ""), "")
    to_stage = STAGE_LABELS.get(details.get("to_stage", ""), "")

    match action:
        case ActivityAction.REQUEST_SUBMITTED:
            name = details.get("on_behalf_of")
            suffix = f" on behalf of {name}" if name else ""
            return f"submitted the project request{suffix}", True
        case ActivityAction.PROJECT_CREATED:
            return "created the project", True
        case ActivityAction.PROJECT_UPDATED:
            return "updated the project details", True
        case ActivityAction.APPROVERS_CHANGED:
            names = details.get("approvers") or []
            if not names:
                return "removed the designated approvers", True
            noun = "approver" if len(names) == 1 else "approvers"
            return f"set the designated {noun}: {', '.join(names)}", True
        case ActivityAction.QUOTATION_CREATED:
            return f"saved quotation v{version} as a draft", True
        case ActivityAction.QUOTATION_SENT:
            return f"sent quotation v{version} to the client", True
        case ActivityAction.QUOTATION_ACCEPTED:
            if details.get("on_behalf"):
                return f"recorded the acceptance of quotation v{version}{_on_behalf(details)}", True
            return f"accepted quotation v{version}", True
        case ActivityAction.QUOTATION_RETURNED:
            if details.get("on_behalf"):
                return f"recorded the return of quotation v{version}{_on_behalf(details)}", True
            return f"returned quotation v{version} with comments", True
        case ActivityAction.REVISION_UPLOADED:
            return f"uploaded design R{revision}", True
        case ActivityAction.REVISION_SUPERSEDED:
            return f"Design R{revision} was superseded by a newer revision", False
        case ActivityAction.REVISION_APPROVED_BY:
            if details.get("on_behalf"):
                return f"recorded the approval of design R{revision}{_on_behalf(details)}", True
            return f"approved design R{revision}", True
        case ActivityAction.REVISION_CHANGES_REQUESTED_BY:
            if details.get("on_behalf"):
                return (
                    f"recorded a change request on design R{revision}{_on_behalf(details)}",
                    True,
                )
            return f"requested changes to design R{revision}", True
        case ActivityAction.REVISION_LOCKED:
            return (
                f"Design R{revision} was approved by all designated approvers "
                "and locked as the approved design",
                False,
            )
        case ActivityAction.STAGE_CHANGED:
            if details.get("source") == "rule":
                reason = RULE_REASONS.get(details.get("rule", ""), "")
                suffix = f" ({reason})" if reason else ""
                return f"The project moved from {from_stage} to {to_stage}{suffix}", False
            return f"moved the project from {from_stage} to {to_stage}", True
        case ActivityAction.STAGE_OVERRIDDEN:
            return (
                f"changed the stage from {from_stage} to {to_stage} (administrator override)",
                True,
            )
        case ActivityAction.DESIGN_REOPENED:
            suffix = (
                "; the cost changes, so a new quotation is needed"
                if details.get("cost_changes")
                else ""
            )
            return f"reopened the design after approval{suffix}", True
        case ActivityAction.DOCUMENT_UPLOADED:
            name = details.get("name")
            return (f"uploaded the document “{name}”" if name else "uploaded a document"), True
        case ActivityAction.REMINDER_SENT:
            item = details.get("item", "a pending decision")
            names = ", ".join(details.get("recipients") or []) or "the pending approvers"
            return f"A reminder about {item} was sent to {names}", False
        case ActivityAction.OVERDUE_ALERT_SENT:
            item = details.get("item", "a pending decision")
            name = details.get("recipient", "the project manager")
            return f"An overdue alert about {item} was sent to {name}", False
        case ActivityAction.USER_LOGIN:
            return "signed in", True
        case ActivityAction.SETTINGS_CHANGED:
            return "changed the system settings", True
    return entry.get_action_display(), False
