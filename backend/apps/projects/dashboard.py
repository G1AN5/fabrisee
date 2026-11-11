"""The management dashboard (`GET /api/dashboard/`).

Read-only: stage changes follow the process rules, so the dashboard shows where every
project stands and what needs attention, and links to the place where staff can act.
"""

from datetime import datetime, timedelta

from django.utils import timezone

from apps.accounts.models import Role
from apps.accounts.permissions import Capability, has_capability
from apps.activity.models import ActivityLog
from apps.core.models import SystemSetting

from .models import STAGE_ORDER, ProjectStatus, Stage
from .presenters import present_activity, present_pending_decision, present_project_card
from .selectors import (
    ProjectState,
    open_steps,
    pending_decisions_of,
    scoped_projects,
    with_last_activity,
    with_related,
)

STAGE_COLUMN_LIMIT = 5
RECENT_ACTIVITY_LIMIT = 8
DUE_SOON_DAYS = 7


def build_dashboard(viewer, now: datetime | None = None) -> dict:
    now = now or timezone.now()
    today = timezone.localtime(now).date()
    setting = SystemSetting.load()
    threshold = timedelta(hours=setting.reminder_hours)

    scoped = with_last_activity(scoped_projects(viewer))
    in_progress = with_related(
        scoped.filter(status__in=[ProjectStatus.ACTIVE, ProjectStatus.ON_HOLD])
    )
    states = [ProjectState.of(project) for project in in_progress]
    active = [state for state in states if state.project.status == ProjectStatus.ACTIVE]

    def card(state: ProjectState) -> dict:
        return present_project_card(state, viewer, now)

    def by_target_date(state: ProjectState):
        return (state.project.target_date, state.project.pk)

    decisions = sorted(
        (decision for state in active for decision in pending_decisions_of(state, now, threshold)),
        key=lambda decision: decision.waiting_since,
    )
    overdue_decisions = [decision for decision in decisions if decision.is_overdue]
    overdue_projects = sorted(
        (state for state in states if state.project.is_overdue(today)), key=by_target_date
    )
    due_soon = sorted(
        (
            state
            for state in active
            if today <= state.project.target_date <= today + timedelta(days=DUE_SOON_DAYS)
        ),
        key=by_target_date,
    )

    completed = scoped.filter(status=ProjectStatus.COMPLETED)
    completed_count = completed.count()
    recently_completed = [
        ProjectState.of(project)
        for project in with_related(completed.order_by("-last_activity_at", "-id"))[
            :STAGE_COLUMN_LIMIT
        ]
    ]

    columns, stage_counts = [], {}
    for stage in STAGE_ORDER:
        if stage == Stage.TURNOVER:
            count, shown = completed_count, recently_completed
        else:
            in_stage = sorted(
                (state for state in states if state.project.stage == stage), key=by_target_date
            )
            count, shown = len(in_stage), in_stage[:STAGE_COLUMN_LIMIT]
        stage_counts[stage] = count
        columns.append(
            {
                "stage": stage,
                "stage_label": Stage(stage).label,
                "count": count,
                "projects": [card(state) for state in shown],
            }
        )

    recent_activity = []
    if has_capability(viewer, Capability.VIEW_ACTIVITY_LOG):
        entries = (
            ActivityLog.objects.filter(project__isnull=False)
            .select_related("actor", "project")
            .order_by("-created_at", "-id")[:RECENT_ACTIVITY_LIMIT]
        )
        recent_activity = [present_activity(entry, with_project=True) for entry in entries]

    return {
        "generated_at": now,
        "role": viewer.role,
        "reminder_hours": setting.reminder_hours,
        "kpis": {
            "active_projects": len(active),
            "waiting_for_client": len(decisions),
            "overdue_items": len(overdue_decisions) + len(overdue_projects),
            "overdue_decisions": len(overdue_decisions),
            "overdue_projects": len(overdue_projects),
            "due_next_7_days": len(due_soon),
        },
        "stage_counts": stage_counts,
        "by_stage": columns,
        "pending_decisions": [
            present_pending_decision(decision, viewer, now) for decision in decisions
        ],
        "overdue_projects": [card(state) for state in overdue_projects],
        "due_soon": [card(state) for state in due_soon],
        "focus": _focus(viewer, active, card, by_target_date, now),
        "recent_activity": recent_activity,
    }


def _focus(viewer, active, card, by_target_date, now) -> dict | None:
    """The list a role sees first: designers what to prepare, production what to build."""
    if viewer.role == Role.DESIGNER:
        to_prepare = sorted(
            (
                state
                for state in active
                if any(step.code == "upload_revision" for step in open_steps(state, now))
            ),
            key=by_target_date,
        )
        return {
            "key": "revisions_to_prepare",
            "title": "Revisions to prepare",
            "empty_text": "No revisions to prepare. Every design is with the client or approved.",
            "projects": [card(state) for state in to_prepare],
        }
    if viewer.role == Role.PRODUCTION:
        to_build = sorted(
            (state for state in active if state.project.stage == Stage.PRODUCTION),
            key=by_target_date,
        )
        return {
            "key": "ready_to_build",
            "title": "Approved and ready to build",
            "empty_text": "Nothing is waiting in production right now.",
            "projects": [card(state) for state in to_build],
        }
    return None
