"""On-call listing tools."""

from pagerduty_sre_bot.helpers import safe_list, unwrap


def tool_list_oncalls(args: dict) -> dict:
    params = {}
    for k, pk in (
            ("schedule_ids", "schedule_ids[]"),
            ("escalation_policy_ids", "escalation_policy_ids[]"),
            ("user_ids", "user_ids[]"),
    ):
        if args.get(k):
            params[pk] = args[k]
    for k in ("since", "until"):
        if args.get(k):
            params[k] = args[k]
    if args.get("earliest"):
        params["earliest"] = args["earliest"]

    raw = safe_list("oncalls", params)
    if isinstance(raw, dict) and "error" in raw:
        return raw
    items = unwrap(raw) if isinstance(raw, dict) else raw
    return {
        "total": len(items),
        "oncalls": [
            {
                "user": oc.get("user", {}).get("summary"),
                "user_id": oc.get("user", {}).get("id"),
                "schedule": oc.get("schedule", {}).get("summary") if oc.get("schedule") else None,
                "escalation_policy": oc.get("escalation_policy", {}).get("summary"),
                "escalation_level": oc.get("escalation_level"),
                "start": oc.get("start"),
                "end": oc.get("end"),
            }
            for oc in items
        ],
    }