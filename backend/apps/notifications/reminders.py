"""Reminders for decisions left pending (process rule PR6).

Milestone 7 implements the rule. Until then `send_due_reminders` only reports that there
is nothing to do, so that `make dev` (which runs the scheduler) already works.
"""

from dataclasses import dataclass
from datetime import datetime

from django.utils import timezone


@dataclass(frozen=True)
class ReminderRun:
    checked_at: datetime
    reminders_sent: int = 0
    alerts_sent: int = 0
    implemented: bool = False


def send_due_reminders(now: datetime | None = None) -> ReminderRun:
    """Remind pending approvers and alert the manager when a decision is overdue.

    TODO(M7, PR6): for every `sent` quotation and `pending_approval` revision older than
    `SystemSetting.reminder_hours` whose last reminder is older than that threshold, remind
    each approver who has not decided, alert the project manager, set `last_reminded_at`
    and log `reminder_sent` / `overdue_alert_sent`. Must be safe to run twice at once.
    """
    return ReminderRun(checked_at=now or timezone.now())
