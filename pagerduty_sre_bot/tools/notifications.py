"""Notification and log entry tools."""

from pagerduty_sre_bot.helpers import safe_list, unwrap


def tool_list_log_entries(args: dict) -> dict:
    params = {}
    for k in ("since", "until"):
        if args.get(k):
            params[k] = args[k]
    if args.get("is_overview"):
        params["is_overview"] = args["is_overview"]
    raw = safe_list("log_entries", params)
    if isinstance(raw, dict) and "error" in raw:
        return raw
    items = unwrap(raw) if isinstance(raw, dict) else raw
    return {
        "total": len(items),
        "log_entries": [
            {
                "type": l["type"],
                "created_at": l["created_at"],
                "summary": l.get("summary", ""),
                "incident": l.get("incident", {}).get("summary") if l.get("incident") else None,
                "service": l.get("service", {}).get("summary") if l.get("service") else None,
                "agent": l.get("agent", {}).get("summary") if l.get("agent") else None,
            }
            for l in items
        ],
    }


def tool_list_notifications(args: dict) -> dict:
    params = {"since": args["since"], "until": args["until"]}
    if args.get("filter"):  params["filter"] = args["filter"]
    if args.get("include"): params["include[]"] = args["include"]
    raw = safe_list("notifications", params)
    if isinstance(raw, dict) and "error" in raw:
        return raw
    items = unwrap(raw) if isinstance(raw, dict) else raw
    return {
        "total": len(items),
        "notifications": [
            {
                "type": n.get("type"),
                "started_at": n.get("started_at"),
                "address": n.get("address"),
                "user": n.get("user", {}).get("summary") if n.get("user") else None,
                "incident": {
                    "id": n.get("incident", {}).get("id"),
                    "summary": n.get("incident", {}).get("summary"),
                } if n.get("incident") else None,
            }
            for n in items
        ],
    }