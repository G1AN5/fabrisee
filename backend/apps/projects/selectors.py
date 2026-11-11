"""Read-side helpers for projects.

* `scoped_projects` / `scoped_documents`: who may see what (process rule PR9).
* `ProjectState`: the quotations, revisions, approvers, and stage updates of a project,
  read once (use `with_related` to load many projects without extra queries).
* `open_steps` / `next_step`: what has to happen next, and who has to do it. The staff
  dashboard, the "needs action" filter, the pending approvals list, and the sentence on
  every project header all come from here, so they always agree.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from functools import cached_property

from django.db.models import OuterRef, Prefetch, Q, Subquery
from django.db.models.functions import Coalesce
from django.utils import timezone

from apps.accounts.models import Role
from apps.activity.models import ActivityLog
from apps.core.formatting import short_date, time_ago
from apps.core.models import SystemSetting
from apps.designs.models import Approval, DesignRevision, RevisionStatus
from apps.quotations.models import Quotation, QuotationStatus

from .models import (
    STAGE_ORDER,
    Document,
    DocumentType,
    Project,
    ProjectApprover,
    ProjectStatus,
    Stage,
    StageUpdate,
    stage_index,
)

MANAGING_ROLES = (Role.ADMIN, Role.PROJECT_MANAGER)
DESIGN_ROLES = (Role.ADMIN, Role.PROJECT_MANAGER, Role.DESIGNER)
PRODUCTION_ROLES = (Role.PRODUCTION,)


# --- Who may see what (PR9) ------------------------------------------------------------


def scoped_projects(user):
    """Projects the user may see: clients only those of their own client, staff all."""
    if not getattr(user, "is_authenticated", False) or not user.is_active:
        return Project.objects.none()
    if user.is_client_user:
        return Project.objects.filter(client_id=user.client_id)
    if user.is_company_staff:
        return Project.objects.all()
    return Project.objects.none()


def scoped_documents(user):
    """Documents the user may see.

    Clients see only client-visible documents of their own projects. Production staff do
    not see quotations, so they do not see documents filed as quotations either.
    """
    queryset = Document.objects.filter(project__in=scoped_projects(user))
    if user.is_client_user:
        return queryset.filter(visible_to_client=True)
    if user.role == Role.PRODUCTION:
        return queryset.exclude(doc_type=DocumentType.QUOTATION)
    return queryset


# --- Loading projects with everything the read side needs ------------------------------


def with_related(queryset):
    """Load the relations `ProjectState` reads, in a fixed number of queries."""
    return queryset.select_related("client", "manager", "designer", "created_by").prefetch_related(
        Prefetch(
            "quotations",
            queryset=Quotation.objects.select_related("prepared_by", "decided_by", "recorded_by"),
        ),
        Prefetch(
            "revisions",
            queryset=DesignRevision.objects.select_related("uploaded_by").prefetch_related(
                Prefetch(
                    "approvals",
                    queryset=Approval.objects.select_related("approver", "recorded_by"),
                )
            ),
        ),
        Prefetch(
            "approver_links",
            queryset=ProjectApprover.objects.select_related("user").order_by("id"),
        ),
        Prefetch("stage_updates", queryset=StageUpdate.objects.select_related("updated_by")),
    )


def with_last_activity(queryset):
    """Annotate `last_activity_at`: the time of the latest activity on the project."""
    latest = (
        ActivityLog.objects.filter(project=OuterRef("pk"))
        .order_by("-created_at")
        .values("created_at")[:1]
    )
    return queryset.annotate(last_activity_at=Coalesce(Subquery(latest), "created_at"))


@dataclass
class ProjectState:
    """One project with its quotations, revisions, approvers, and stage updates."""

    project: Project
    quotations: list[Quotation]  # newest version first
    revisions: list[DesignRevision]  # newest revision first
    approvers: list  # designated approvers, in the order they were designated
    stage_updates: list[StageUpdate]  # oldest first

    @classmethod
    def of(cls, project: Project) -> "ProjectState":
        return cls(
            project=project,
            quotations=sorted(project.quotations.all(), key=lambda q: -q.version_no),
            revisions=sorted(project.revisions.all(), key=lambda r: -r.revision_no),
            approvers=[link.user for link in project.approver_links.all()],
            stage_updates=sorted(project.stage_updates.all(), key=lambda s: (s.created_at, s.pk)),
        )

    @cached_property
    def approver_ids(self) -> set[int]:
        return {user.pk for user in self.approvers}

    @cached_property
    def latest_quotation(self) -> Quotation | None:
        return self.quotations[0] if self.quotations else None

    @cached_property
    def sent_quotation(self) -> Quotation | None:
        return next((q for q in self.quotations if q.status == QuotationStatus.SENT), None)

    @cached_property
    def latest_revision(self) -> DesignRevision | None:
        return self.revisions[0] if self.revisions else None

    @cached_property
    def pending_revision(self) -> DesignRevision | None:
        return next(
            (r for r in self.revisions if r.status == RevisionStatus.PENDING_APPROVAL), None
        )

    @cached_property
    def approved_revision(self) -> DesignRevision | None:
        """The approved design: the newest revision that was approved and locked."""
        return next((r for r in self.revisions if r.status == RevisionStatus.APPROVED), None)

    def approvals(self, revision: DesignRevision) -> list[Approval]:
        return sorted(revision.approvals.all(), key=lambda a: (a.created_at, a.pk))

    def entered_stage_at(self, stage: str) -> datetime | None:
        """When the project most recently entered `stage`."""
        moments = [update.created_at for update in self.stage_updates if update.to_stage == stage]
        return moments[-1] if moments else None

    @cached_property
    def stage_dates(self) -> dict[str, datetime | None]:
        """The date the project entered each stage it has reached (for the stage tracker)."""
        current = stage_index(self.project.stage)
        dates: dict[str, datetime | None] = dict.fromkeys(STAGE_ORDER)
        for update in self.stage_updates:
            if stage_index(update.to_stage) <= current:
                dates[update.to_stage] = update.created_at
        if dates[Stage.REQUEST] is None:
            dates[Stage.REQUEST] = self.project.created_at
        return dates

    def visible_quotations(self, viewer) -> list[Quotation]:
        """Quotations `viewer` may see: clients only sent versions, production none."""
        if viewer.role == Role.PRODUCTION:
            return []
        if viewer.is_client_user:
            return [q for q in self.quotations if q.was_sent]
        return self.quotations

    def visible_revisions(self, viewer) -> list[DesignRevision]:
        """Revisions `viewer` may see: production not the one still waiting for approval."""
        if viewer.role == Role.PRODUCTION:
            return [r for r in self.revisions if r.status != RevisionStatus.PENDING_APPROVAL]
        return self.revisions


# --- What happens next -----------------------------------------------------------------


@dataclass
class OpenStep:
    """Something that has to happen before a project can move on."""

    code: str
    side: str  # "staff", "client", or "none" (nothing to do: completed, cancelled, on hold)
    staff_text: str
    client_text: str
    # For a client decision: the text for an approver who still has to decide, and the
    # text for an approver who already did.
    approver_text: str = ""
    decided_text: str = ""
    since: datetime | None = None
    item: Quotation | DesignRevision | None = None
    # Staff roles that are expected to do this step.
    roles: tuple[str, ...] = ()
    # Designated approvers who still have to decide.
    pending_approvers: list = field(default_factory=list)
    approver_count: int = 0

    @property
    def item_kind(self) -> str | None:
        if isinstance(self.item, Quotation):
            return "quotation"
        if isinstance(self.item, DesignRevision):
            return "revision"
        return None

    @property
    def item_label(self) -> str | None:
        if isinstance(self.item, Quotation):
            return f"Quotation {self.item.label}"
        if isinstance(self.item, DesignRevision):
            return f"Design {self.item.label}"
        return None

    def needs_action_from(self, viewer) -> bool:
        if self.side == "staff":
            return viewer.is_company_staff and viewer.role in self.roles
        if self.side == "client":
            return any(user.pk == viewer.pk for user in self.pending_approvers)
        return False


@dataclass(frozen=True)
class NextStep:
    """The next step of a project, worded for one viewer."""

    code: str
    text: str
    waiting_on: str  # "staff" | "client" | "none"
    action_needed: bool  # the viewer is expected to act now
    since: datetime | None = None
    item_kind: str | None = None
    item_id: int | None = None
    item_label: str | None = None


def _quotation_step(state: ProjectState, now: datetime, *, revised: bool) -> OpenStep:
    """The quotation step of the Request stage, or of a requote after approval (PR8)."""
    quotation = state.latest_quotation
    adjective = "revised " if revised else ""
    preparing = (
        "We are preparing a revised quotation" if revised else ("We are preparing your quotation")
    )
    status = quotation.status if quotation else None

    if status == QuotationStatus.SENT:
        if not state.approvers:
            return OpenStep(
                code="designate_approver",
                side="staff",
                staff_text=(
                    f"Designate an approver so the client can decide on quotation {quotation.label}"
                ),
                client_text="Waiting for your approver",
                since=quotation.sent_at,
                item=quotation,
                roles=MANAGING_ROLES,
            )
        return OpenStep(
            code="quotation_pending",
            side="client",
            staff_text=(
                f"Waiting for the client to decide on {adjective}quotation {quotation.label} "
                f"(sent {time_ago(quotation.sent_at, now)})"
            ),
            client_text=f"Waiting for your approver to decide on quotation {quotation.label}",
            approver_text=f"Please review quotation {quotation.label}",
            since=quotation.sent_at,
            item=quotation,
            # TO CONFIRM: any one designated approver decides on a quotation.
            pending_approvers=list(state.approvers),
            approver_count=len(state.approvers),
        )
    if status == QuotationStatus.DRAFT:
        returned_before = any(q.decided_at and q.client_comment for q in state.quotations[1:])
        return OpenStep(
            code="send_quotation",
            side="staff",
            staff_text=f"Send {adjective}quotation {quotation.label} to the client",
            client_text=("We are preparing a revised quotation" if returned_before else preparing),
            since=quotation.created_at,
            item=quotation,
            roles=MANAGING_ROLES,
        )
    if status == QuotationStatus.RETURNED:
        return OpenStep(
            code="revise_quotation",
            side="staff",
            staff_text=(
                f"Prepare a new quotation version ({quotation.label} was returned with comments)"
            ),
            client_text="We are preparing a revised quotation",
            since=quotation.decided_at,
            item=quotation,
            roles=MANAGING_ROLES,
        )
    if status == QuotationStatus.ACCEPTED and not revised:
        # The quotation is accepted but the project never left Request (data problem).
        return OpenStep(
            code="stage_mismatch",
            side="staff",
            staff_text=(
                f"Quotation {quotation.label} is accepted but the project is still in Request. "
                "An administrator can correct the stage"
            ),
            client_text="We are starting your design",
            since=quotation.decided_at,
            roles=(Role.ADMIN,),
        )
    return OpenStep(
        code="prepare_quotation",
        side="staff",
        staff_text=(
            "Prepare the revised quotation (the cost changes)" if revised else "Prepare a quotation"
        ),
        client_text=preparing,
        since=state.entered_stage_at(Stage.DESIGN if revised else Stage.REQUEST),
        roles=MANAGING_ROLES,
    )


def _revision_step(state: ProjectState) -> OpenStep | None:
    """The design revision step of the Design stage; None when it is already complete."""
    project = state.project
    pending = state.pending_revision
    if pending is not None:
        decided_ids = {approval.approver_id for approval in state.approvals(pending)}
        remaining = [user for user in state.approvers if user.pk not in decided_ids]
        total = len(state.approvers)
        if total == 0:
            return OpenStep(
                code="designate_approver",
                side="staff",
                staff_text=(
                    f"Designate an approver so the client can review design {pending.label}"
                ),
                client_text="Waiting for your approver",
                since=pending.uploaded_at,
                item=pending,
                roles=MANAGING_ROLES,
            )
        staff_text = (
            f"{pending.label} waiting for the client's approval"
            if total == 1
            else f"{pending.label} waiting for {len(remaining)} of {total} approvers"
        )
        return OpenStep(
            code="revision_pending",
            side="client",
            staff_text=staff_text,
            client_text=f"Waiting for your approver to review design {pending.label}",
            approver_text=f"Please review design {pending.label}",
            decided_text="Waiting for other approvers",
            since=pending.uploaded_at,
            item=pending,
            pending_approvers=remaining,
            approver_count=total,
        )

    entered_design = state.entered_stage_at(Stage.DESIGN)
    approved = state.approved_revision
    if (
        project.design_reopened
        and approved is not None
        and approved.locked_at
        and entered_design
        and approved.locked_at >= entered_design
    ):
        # PR8: a new revision was approved after the design was reopened.
        return None

    latest = state.latest_revision
    if latest is None:
        staff_text, client_text = (
            "Upload the first design revision",
            "Our designers are working on your design",
        )
    elif latest.status == RevisionStatus.CHANGES_REQUESTED:
        staff_text, client_text = (
            f"Upload the next design revision (changes requested on {latest.label})",
            "Our designers are working on the changes you requested",
        )
    elif project.design_reopened:
        staff_text, client_text = (
            "Upload a new design revision (the design was reopened)",
            "We are updating your design",
        )
    else:
        staff_text, client_text = (
            "Upload the next design revision",
            "Our designers are working on your design",
        )
    return OpenStep(
        code="upload_revision",
        side="staff",
        staff_text=staff_text,
        client_text=client_text,
        since=entered_design,
        roles=DESIGN_ROLES,
    )


def open_steps(state: ProjectState, now: datetime | None = None) -> list[OpenStep]:
    """Everything that is open on a project right now (usually exactly one step)."""
    now = now or timezone.now()
    project = state.project

    if project.status == ProjectStatus.CANCELLED:
        return [OpenStep("cancelled", "none", "Project cancelled", "This project was cancelled")]
    if project.status == ProjectStatus.ON_HOLD:
        return [OpenStep("on_hold", "none", "Project on hold", "This project is on hold")]
    if project.stage == Stage.TURNOVER or project.status == ProjectStatus.COMPLETED:
        turned_over = state.entered_stage_at(Stage.TURNOVER)
        staff_text = f"Turned over on {short_date(turned_over)}" if turned_over else "Completed"
        return [OpenStep("completed", "none", staff_text, "Project completed", since=turned_over)]

    if project.stage == Stage.REQUEST:
        return [_quotation_step(state, now, revised=False)]

    if project.stage == Stage.DESIGN:
        steps: list[OpenStep] = []
        revision_step = _revision_step(state)
        if revision_step is not None:
            steps.append(revision_step)
        if project.requires_requote:
            steps.append(_quotation_step(state, now, revised=True))
        if not steps:
            steps.append(
                OpenStep(
                    code="stage_mismatch",
                    side="staff",
                    staff_text=(
                        "The design is approved but the project is still in Design. "
                        "An administrator can correct the stage"
                    ),
                    client_text="Your design is approved",
                    roles=(Role.ADMIN,),
                )
            )
        return steps

    if project.stage == Stage.PRODUCTION:
        since = state.entered_stage_at(Stage.PRODUCTION)
        return [
            OpenStep(
                code="in_production",
                side="staff",
                staff_text=f"In production since {short_date(since)}" if since else "In production",
                client_text="Your display is being built",
                since=since,
                roles=PRODUCTION_ROLES,
            )
        ]

    since = state.entered_stage_at(Stage.DELIVERY_INSTALLATION)
    return [
        OpenStep(
            code="in_delivery",
            side="staff",
            staff_text="Delivery and installation in progress",
            client_text="Your display is being delivered and installed",
            since=since,
            roles=PRODUCTION_ROLES,
        )
    ]


def next_step(state: ProjectState, viewer, now: datetime | None = None) -> NextStep:
    """The next step of a project in one short sentence, worded for `viewer`."""
    steps = open_steps(state, now)
    step = next((s for s in steps if s.needs_action_from(viewer)), None)
    if step is None:
        own_side = "client" if viewer.is_client_user else "staff"
        step = next((s for s in steps if s.side == own_side), steps[0])

    action_needed = step.needs_action_from(viewer)
    if not viewer.is_client_user:
        text = step.staff_text
    elif step.side != "client":
        text = step.client_text
    elif action_needed:
        text = step.approver_text
    elif viewer.pk in state.approver_ids and step.decided_text:
        text = step.decided_text
    else:
        text = step.client_text

    return NextStep(
        code=step.code,
        text=text,
        waiting_on=step.side,
        action_needed=action_needed,
        since=step.since,
        item_kind=step.item_kind,
        item_id=step.item.pk if step.item is not None else None,
        item_label=step.item_label,
    )


# --- Pending decisions (dashboard "Needs attention", Approvals page, PR6) ----------------


@dataclass
class PendingDecision:
    """A quotation or design revision that waits for a client decision."""

    kind: str  # "quotation" | "revision"
    item: Quotation | DesignRevision
    label: str
    project: Project
    waiting_since: datetime
    pending_approvers: list
    approver_count: int
    last_reminded_at: datetime | None
    is_overdue: bool  # waiting longer than the reminder threshold

    @property
    def decided_count(self) -> int:
        return self.approver_count - len(self.pending_approvers)


def reminder_threshold() -> timedelta:
    return timedelta(hours=SystemSetting.load().reminder_hours)


def pending_decisions_of(
    state: ProjectState, now: datetime, threshold: timedelta
) -> list[PendingDecision]:
    decisions = []
    for step in open_steps(state, now):
        if step.side != "client" or step.item is None or step.since is None:
            continue
        decisions.append(
            PendingDecision(
                kind=step.item_kind,
                item=step.item,
                label=step.item_label,
                project=state.project,
                waiting_since=step.since,
                pending_approvers=step.pending_approvers,
                approver_count=step.approver_count,
                last_reminded_at=step.item.last_reminded_at,
                is_overdue=now - step.since >= threshold,
            )
        )
    return decisions


def open_project_states(viewer) -> list[ProjectState]:
    """The projects in progress that `viewer` may see, with their related records."""
    projects = with_related(
        with_last_activity(scoped_projects(viewer)).filter(status=ProjectStatus.ACTIVE)
    )
    return [ProjectState.of(project) for project in projects]


def pending_decisions(viewer, now: datetime | None = None) -> list[PendingDecision]:
    """All pending client decisions on projects `viewer` may see, longest wait first."""
    now = now or timezone.now()
    threshold = reminder_threshold()
    decisions = [
        decision
        for state in open_project_states(viewer)
        for decision in pending_decisions_of(state, now, threshold)
    ]
    return sorted(decisions, key=lambda decision: decision.waiting_since)


# --- List filters that depend on the next step -------------------------------------------


def ids_needing_action(viewer, now: datetime | None = None) -> list[int]:
    """Projects where `viewer` is expected to act now."""
    now = now or timezone.now()
    return [
        state.project.pk
        for state in open_project_states(viewer)
        if next_step(state, viewer, now).action_needed
    ]


def ids_waiting_on_client(viewer, now: datetime | None = None) -> list[int]:
    """Projects with a quotation or revision that waits for a client decision."""
    now = now or timezone.now()
    return [
        state.project.pk
        for state in open_project_states(viewer)
        if any(step.side == "client" for step in open_steps(state, now))
    ]


def overdue_filter(viewer, now: datetime | None = None) -> Q:
    """Past the target date, or a decision pending longer than the reminder threshold."""
    now = now or timezone.now()
    today = timezone.localtime(now).date()
    late_decisions = {
        decision.project.pk for decision in pending_decisions(viewer, now) if decision.is_overdue
    }
    past_target = Q(status__in=[ProjectStatus.ACTIVE, ProjectStatus.ON_HOLD], target_date__lt=today)
    return past_target | Q(pk__in=late_decisions)
