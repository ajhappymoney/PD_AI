"""Time parsing and ISO-8601 helpers."""

from datetime import datetime, timezone, timedelta
from typing import Optional

import dateparser


def parse_nl_time(text: str, default_tz: str = "UTC") -> Optional[str]:
    """
    Parse natural-language time into ISO-8601 UTC.
    Examples: 'yesterday', 'last Monday 9am', '3 days ago', 'now'
    """
    if not text:
        return None
    dt = dateparser.parse(
        text,
        settings={
            "RETURN_AS_TIMEZONE_AWARE": True,
            "TIMEZONE": default_tz,
            "PREFER_LOCALE_DATE_FORMAT": False,
            "TO_TIMEZONE": "UTC",
        },
    )
    if dt:
        return dt.strftime("%Y-%m-%dT%H:%M:%SZ")
    return None


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def iso_now() -> str:
    return now_utc().strftime("%Y-%m-%dT%H:%M:%SZ")


def iso_hours_ago(n: float) -> str:
    return (now_utc() - timedelta(hours=n)).strftime("%Y-%m-%dT%H:%M:%SZ")


def fmt_ts(iso_str: str) -> Optional[datetime]:
    """Parse an ISO-8601 string into a datetime."""
    if not iso_str:
        return None
    for fmt in (
            "%Y-%m-%dT%H:%M:%SZ",
            "%Y-%m-%dT%H:%M:%S%z",
            "%Y-%m-%dT%H:%M:%S.%fZ",
            "%Y-%m-%dT%H:%M:%S.%f%z",
    ):
        try:
            return datetime.strptime(iso_str, fmt)
        except ValueError:
            continue
    return None


def diff_minutes(start_str: str, end_str: str) -> Optional[float]:
    """Compute difference in minutes between two ISO timestamps."""
    s, e = fmt_ts(start_str), fmt_ts(end_str)
    if s and e:
        if s.tzinfo is None:
            s = s.replace(tzinfo=timezone.utc)
        if e.tzinfo is None:
            e = e.replace(tzinfo=timezone.utc)
        return round((e - s).total_seconds() / 60, 2)
    return None