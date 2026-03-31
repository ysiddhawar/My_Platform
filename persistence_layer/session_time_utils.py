from __future__ import annotations

from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from models.trading_platform_session import TradingPlatformSession


def minutes_within_local_day(
    session: TradingPlatformSession,
    local_day: str,
    *,
    as_of: datetime | None = None,
) -> float:
    tz = _resolve_timezone(session.timezone_name)
    day_start = datetime.fromisoformat(local_day).replace(tzinfo=tz)
    day_end = day_start + timedelta(days=1)

    effective_end = session.closed_at or as_of or datetime.now(timezone.utc)
    start_utc = _ensure_aware(session.opened_at)
    end_utc = _ensure_aware(effective_end)
    if end_utc <= start_utc:
      return 0.0

    start_local = start_utc.astimezone(tz)
    end_local = end_utc.astimezone(tz)

    overlap_start = max(start_local, day_start)
    overlap_end = min(end_local, day_end)
    if overlap_end <= overlap_start:
        return 0.0

    minutes = max((overlap_end - overlap_start).total_seconds(), 0.0) / 60.0
    return round(min(minutes, 1440.0), 2)


def session_overlaps_local_day(
    session: TradingPlatformSession,
    local_day: str,
    *,
    as_of: datetime | None = None,
) -> bool:
    return minutes_within_local_day(session, local_day, as_of=as_of) > 0


def session_local_days(
    session: TradingPlatformSession,
    *,
    as_of: datetime | None = None,
) -> list[str]:
    tz = _resolve_timezone(session.timezone_name)
    effective_end = session.closed_at or as_of or datetime.now(timezone.utc)
    start_local = _ensure_aware(session.opened_at).astimezone(tz)
    end_local = _ensure_aware(effective_end).astimezone(tz)
    if end_local <= start_local:
        return [start_local.date().isoformat()]

    days: list[str] = []
    cursor = start_local.date()
    end_date = end_local.date()
    while cursor <= end_date:
        days.append(cursor.isoformat())
        cursor += timedelta(days=1)
    return days


def _ensure_aware(value: datetime) -> datetime:
    return value if value.tzinfo else value.replace(tzinfo=timezone.utc)


def _resolve_timezone(timezone_name: str) -> ZoneInfo:
    try:
        return ZoneInfo(timezone_name or "UTC")
    except Exception:
        return ZoneInfo("UTC")
