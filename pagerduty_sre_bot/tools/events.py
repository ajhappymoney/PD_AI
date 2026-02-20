"""Events API v2 — trigger, acknowledge, resolve alerts; submit change events."""

from pagerduty_sre_bot.clients import send_event_v2, send_change_event
from pagerduty_sre_bot.helpers import is_dry_run_action
from pagerduty_sre_bot.time_utils import iso_now

_dry_run = False


def set_dry_run(v: bool) -> None:
    global _dry_run
    _dry_run = v


def tool_send_event(args: dict) -> dict:
    """
    Send a trigger/acknowledge/resolve event via Events API v2.
    Requires a routing_key (integration key from a service).
    """
    dry = is_dry_run_action(_dry_run, f"send_event action={args.get('event_action')}")
    if dry:
        return dry

    routing_key = args.get("routing_key", "")
    action = args.get("event_action", "trigger")
    dedup_key = args.get("dedup_key")

    if not routing_key:
        return {"error": "routing_key (integration key) is required"}

    body: dict = {"event_action": action}

    if dedup_key:
        body["dedup_key"] = dedup_key

    if action == "trigger":
        body["payload"] = {
            "summary": args.get("summary", "Event from SRE Bot"),
            "source": args.get("source", "pagerduty-sre-bot"),
            "severity": args.get("severity", "critical"),
            "component": args.get("component"),
            "group": args.get("group"),
            "class": args.get("event_class"),
            "custom_details": args.get("custom_details"),
        }
        # Strip None values from payload
        body["payload"] = {k: v for k, v in body["payload"].items() if v is not None}

        if args.get("client"):
            body["client"] = args["client"]
        if args.get("client_url"):
            body["client_url"] = args["client_url"]
        if args.get("links"):
            body["links"] = args["links"]
        if args.get("images"):
            body["images"] = args["images"]

    try:
        result = send_event_v2(routing_key, body)
        sc = result["status_code"]
        if sc == 202:
            resp_body = result["body"]
            return {
                "success": True,
                "event_action": action,
                "dedup_key": resp_body.get("dedup_key"),
                "message": resp_body.get("message"),
                "status": resp_body.get("status"),
            }
        return {"error": f"Events API returned HTTP {sc}", "details": result["body"]}
    except Exception as e:
        return {"error": str(e)}


def tool_send_change_event(args: dict) -> dict:
    """Submit a change event (deployment, config change) via Events API v2."""
    dry = is_dry_run_action(_dry_run, "send_change_event")
    if dry:
        return dry

    routing_key = args.get("routing_key", "")
    if not routing_key:
        return {"error": "routing_key (integration key) is required"}

    body = {
        "routing_key": routing_key,
        "payload": {
            "summary": args.get("summary", "Change event from SRE Bot"),
            "source": args.get("source", "pagerduty-sre-bot"),
            "timestamp": args.get("timestamp", iso_now()),
            "custom_details": args.get("custom_details"),
        },
        "links": args.get("links", []),
    }
    body["payload"] = {k: v for k, v in body["payload"].items() if v is not None}

    try:
        result = send_change_event(routing_key, body)
        if result["status_code"] == 202:
            return {"success": True, "message": "Change event accepted"}
        return {"error": f"HTTP {result['status_code']}", "details": result["body"]}
    except Exception as e:
        return {"error": str(e)}