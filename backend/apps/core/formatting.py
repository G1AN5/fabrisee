"""Plain-language dates for sentences built on the server (next step, timeline)."""

from datetime import date, datetime

from django.utils import timezone


def short_date(value: date | datetime, today: date | None = None) -> str:
    """`Nov 3` in the current year, `Nov 3, 2025` otherwise (Manila time)."""
    if isinstance(value, datetime):
        value = timezone.localtime(value).date()
    today = today or timezone.localdate()
    text = f"{value:%b} {value.day}"
    return text if value.year == today.year else f"{text}, {value.year}"


def time_ago(moment: datetime, now: datetime | None = None) -> str:
    """`just now`, `5 minutes ago`, `3 hours ago`, `2 days ago`, then the date."""
    now = now or timezone.now()
    seconds = max(0, int((now - moment).total_seconds()))
    minutes, hours, days = seconds // 60, seconds // 3600, seconds // 86400
    if minutes < 1:
        return "just now"
    if hours < 1:
        return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
    if days < 1:
        return f"{hours} hour{'s' if hours != 1 else ''} ago"
    if days <= 30:
        return f"{days} day{'s' if days != 1 else ''} ago"
    return f"on {short_date(moment, timezone.localtime(now).date())}"
