"""Utility tools: time resolution."""

from pagerduty_sre_bot.time_utils import parse_nl_time


def tool_resolve_time(args: dict) -> dict:
    """Convert natural-language time expression to ISO-8601 UTC."""
    expr = args.get("expression", "")
    iso = parse_nl_time(expr)
    if iso:
        return {"expression": expr, "iso8601_utc": iso}
    return {
        "error": f"Could not parse time expression: '{expr}'",
        "hint": "Try 'yesterday', 'last Monday 9am', '3 hours ago', '2025-01-15'",
    }