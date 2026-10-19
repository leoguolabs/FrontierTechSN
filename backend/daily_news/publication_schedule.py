"""Daily release slots, independent of when production finishes."""

from datetime import date, datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo

from backend.models import TaskResponse

# HH:MM denotes a release minute. Polling can claim a ready edition anywhere
# within that minute; a missed slot never becomes an immediate catch-up post.
RELEASE_WINDOW = timedelta(minutes=1)


def daily_release_at(edition_date: date, publish_time: str, timezone_name: str) -> datetime:
    hour, minute = (int(part) for part in publish_time.split(":"))
    local = datetime.combine(edition_date, time(hour, minute), ZoneInfo(timezone_name))
    # UTC storage also resolves daylight-saving gaps forward and uses the
    # first occurrence of an ambiguous wall-clock time.
    return local.astimezone(timezone.utc)


def planned_release_at(task: TaskResponse) -> datetime:
    if not task.config.publish_time or not task.planned_publish_at:
        raise ValueError("No publication time was saved for this edition; manual publication required")
    value = datetime.fromisoformat(task.planned_publish_at)
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("The saved publication time must include a timezone")
    return value.astimezone(timezone.utc)
