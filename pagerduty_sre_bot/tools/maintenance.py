"""Maintenance window tools."""

from pagerduty_sre_bot.clients import pd_client
from pagerduty_sre_bot.helpers import safe_list, unwrap, is_dry_run_action
from pagerduty_sre_bot.retry import with_retry

_dry_run = False


def set_dry_run(v: bool) -> None:
    global _dry_run
    _dry_run = v


def tool_list_maintenance_windows(args: dict) -> dict:
    params = {}
    if args.get("service_ids"): params["service_ids[]"] = args["service_ids"]
    if args.get("team_ids"):    params["team_ids[]"] = args["team_ids"]
    if args.get("filter"):      params["filter"] = args["filter"]
    raw = safe_list("maintenance_windows", params)
    if isinstance(raw, dict) and "error" in raw:
        return raw
    items = unwrap(raw) if isinstance(raw, dict) else raw
    return {
        "total": len(items),
        "maintenance_windows": [
            {
                "id": mw["id"], "description": mw.get("description", ""),
                "start_time": mw.get("start_time"), "end_time": mw.get("end_time"),
                "services": [s.get("summary") for s in mw.get("services", [])],
                "created_by": mw.get("created_by", {}).get("summary") if mw.get("created_by") else None,
            }
            for mw in items
        ],
    }


@with_retry()
def tool_create_maintenance_window(args: dict) -> dict:
    dry = is_dry_run_action(_dry_run, f"create_maintenance_window start={args['start_time']}")
    if dry:
        return dry
    try:
        body = {
            "type": "maintenance_window",
            "start_time": args["start_time"],
            "end_time": args["end_time"],
            "services": [{"id": sid, "type": "service_reference"} for sid in args["service_ids"]],
        }
        if args.get("description"):
            body["description"] = args["description"]
        mw = pd_client.rpost("maintenance_windows", json=body)
        return {"success": True, "maintenance_window": {"id": mw["id"]}}
    except Exception as e:
        return {"error": str(e)}


@with_retry()
def tool_delete_maintenance_window(args: dict) -> dict:
    dry = is_dry_run_action(_dry_run, f"delete_maintenance_window {args['window_id']}")
    if dry:
        return dry
    try:
        pd_client.delete(f"maintenance_windows/{args['window_id']}")
        return {"success": True, "deleted": args["window_id"]}
    except Exception as e:
        return {"error": str(e)}