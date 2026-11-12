"""The wording of notifications, one function per event (build guide, section 9.1).

Services and the demo data use the same functions, so a notification reads the same
wherever it comes from. Every function returns a `Message(title, body)`; the title is
also the email subject after the project number.
"""

from typing import NamedTuple

from apps.projects.models import Stage


class Message(NamedTuple):
    title: str
    body: str


def _days(hours: float) -> str:
    days = int(hours // 24)
    if days >= 1:
        return f"{days} day{'s' if days != 1 else ''}"
    whole_hours = max(1, int(hours))
    return f"{whole_hours} hour{'s' if whole_hours != 1 else ''}"


def request_submitted(project, submitted_by) -> Message:
    return Message(
        f"New project request from {project.client.company_name}",
        f"{submitted_by.full_name} submitted “{project.title}”. Prepare a quotation.",
    )


def quotation_sent(quotation, *, decision_needed: bool) -> Message:
    if decision_needed:
        return Message(
            f"Quotation {quotation.label} is waiting for your decision",
            "Please review the quotation, then accept it or return it with comments.",
        )
    return Message(
        f"Quotation {quotation.label} was sent to your company",
        "Your designated approver will decide on it.",
    )


def quotation_decided(quotation, *, accepted: bool, decided_by) -> Message:
    if accepted:
        return Message(
            f"Quotation {quotation.label} was accepted",
            f"Accepted by {decided_by.full_name}. The project moved to Design.",
        )
    return Message(
        f"Quotation {quotation.label} was returned with comments",
        f"{decided_by.full_name}: “{quotation.client_comment}” A new version is needed.",
    )


def revision_uploaded(revision, *, decision_needed: bool) -> Message:
    if decision_needed:
        return Message(
            f"Design {revision.label} is waiting for your approval",
            "Please review the design, then approve it or request changes.",
        )
    return Message(
        f"Design {revision.label} was uploaded",
        "The designated approvers were asked to review it.",
    )


def revision_changes_requested(revision, *, requested_by, comment: str) -> Message:
    return Message(
        f"Changes requested on design {revision.label}",
        f"{requested_by.full_name}: “{comment}” A new revision is needed.",
    )


def revision_approved(revision, *, for_client: bool) -> Message:
    if for_client:
        return Message(
            f"Design {revision.label} is approved",
            "All designated approvers approved the design. Your display is going into production.",
        )
    return Message(
        f"Design {revision.label} is approved and locked",
        "All designated approvers approved it. It is the approved design, "
        "and the project moved to Production.",
    )


def decision_reminder(item_label: str, *, waiting_hours: float) -> Message:
    return Message(
        f"Reminder: {item_label} is waiting for your decision",
        f"It has been waiting for {_days(waiting_hours)}. The project continues once you decide.",
    )


def decision_overdue_alert(item_label: str, *, waiting_hours: float, pending_names) -> Message:
    names = ", ".join(pending_names) or "the client"
    return Message(
        f"{item_label} has had no decision for {_days(waiting_hours)}",
        f"Still waiting for: {names}. A reminder was sent.",
    )


CLIENT_STAGE_TEXT = {
    Stage.DESIGN: ("Your project moved to Design", "Our designers are working on your design."),
    Stage.PRODUCTION: ("Your display is in production", "Your display is being built."),
    Stage.DELIVERY_INSTALLATION: (
        "Your display is being delivered and installed",
        "Production is finished. Delivery and installation are in progress.",
    ),
    Stage.TURNOVER: ("Your project is complete", "Your display was turned over. Thank you."),
}


def stage_changed(project, to_stage: str, *, for_client: bool, remarks: str = "") -> Message:
    label = Stage(to_stage).label
    if for_client:
        title, body = CLIENT_STAGE_TEXT.get(Stage(to_stage), (f"Your project moved to {label}", ""))
        return Message(title, body)
    return Message(f"The project moved to {label}", remarks)


def project_turned_over(project, *, for_client: bool) -> Message:
    if for_client:
        return Message(
            "Your project is complete",
            "Your display was turned over. The turnover documents are in the project documents.",
        )
    return Message("The project was turned over", "The project is completed.")
