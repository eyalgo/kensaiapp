"""The text of one tide alert (SRS FR-3, FR-4)."""

from datetime import datetime
from zoneinfo import ZoneInfo


def alert_text(harbour: str, kind: str, at_utc: datetime, zone: str) -> str:
    """Return the alert for one tide, its time in the harbour's own zone."""
    local = at_utc.astimezone(ZoneInfo(zone))
    return f"{harbour}: {kind} tide at {local:%H:%M} {local.tzname()}"
