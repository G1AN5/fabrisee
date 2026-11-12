from datetime import datetime

from django.utils import timezone

from apps.core.models import SystemSetting

from .models import ProjectSequence


def next_project_number(now: datetime | None = None) -> str:
    """Issue the next project number: `{prefix}-{year}-{sequence:04d}` (PR2).

    Must be called inside `transaction.atomic()`. The sequence restarts every year; the
    row lock (PostgreSQL) or the IMMEDIATE transaction (SQLite) keeps numbers unique when
    two requests arrive at the same time.
    """
    # TO CONFIRM: project number format (build guide, Appendix A). Default: FS-YYYY-NNNN.
    year = timezone.localtime(now or timezone.now()).year
    ProjectSequence.objects.get_or_create(year=year)
    sequence = ProjectSequence.objects.select_for_update().get(year=year)
    sequence.last_number += 1
    sequence.save(update_fields=["last_number"])
    prefix = SystemSetting.load().project_number_prefix
    return f"{prefix}-{year}-{sequence.last_number:04d}"
