"""Schedule CRUD, override, and on-call tools."""

from pagerduty_sre_bot.clients import pd_client
from pagerduty_sre_bot.helpers import safe_list, unwrap, is_dry_run_action
from pagerduty_sre_bot.retry import with_retry

_dry_run = False


def set_dry_run(v: bool) -> None:
    global _dry_run
    _dry_run = v


# ── List / Get ────────────────────────────────────────

def tool_list_schedules(args: dict) -> dict:
    params = {}
    if args.get("query"):
        params["query"] = args["query"]
    raw = safe_list("schedules", params)
    if isinstance(raw, dict) and "error" in raw:
        return raw
    items = unwrap(raw) if isinstance(raw, dict) else raw
    return {
        "total": len(items),
        "schedules": [
            {
                "id": s["id"], "name": s["name"], "description": s.get("description", ""),
                "time_zone": s.get("time_zone"), "html_url": s.get("html_url"),
                "users": [u.get("summary") for u in s.get("users", [])],
                "teams": [t.get("summary") for t in s.get("teams", [])],
            }
            for s in items
        ],
    }


@with_retry()
def tool_get_schedule(args: dict) -> dict:
    try:
        params = {}
        if args.get("since"): params["since"] = args["since"]
        if args.get("until"): params["until"] = args["until"]
        return pd_client.rget(f"schedules/{args['schedule_id']}", params=params)
    except Exception as e:
        return {"error": str(e)}


# ── Create / Update / Delete ──────────────────────────

@with_retry()
def tool_create_schedule(args: dict) -> dict:
    """Create a new on-call schedule with layers."""
    dry = is_dry_run_action(_dry_run, f"create_schedule name='{args.get('name')}'")
    if dry:
        return dry
    try:
        body: dict = {
            "type": "schedule",
            "name": args["name"],
            "time_zone": args.get("time_zone", "UTC"),
        }
        if args.get("description"):
            body["description"] = args["description"]

        layers = []
        for layer in args.get("schedule_layers", []):
            l: dict = {
                "name": layer.get("name", "Layer 1"),
                "start": layer["start"],
                "rotation_virtual_start": layer.get("rotation_virtual_start", layer["start"]),
                "rotation_turn_length_seconds": layer.get("rotation_turn_length_seconds", 86400),
                "users": [
                    {"user": {"id": uid, "type": "user_reference"}}
                    for uid in layer.get("user_ids", [])
                ],
            }
            if layer.get("end"):
                l["end"] = layer["end"]
            if layer.get("restrictions"):
                l["restrictions"] = layer["restrictions"]
            layers.append(l)

        body["schedule_layers"] = layers

        if args.get("teams"):
            body["teams"] = [{"id": tid, "type": "team_reference"} for tid in args["teams"]]

        sched = pd_client.rpost("schedules", json=body)
        return {"success": True, "schedule": {"id": sched["id"], "name": sched["name"], "html_url": sched.get("html_url")}}
    except Exception as e:
        return {"error": str(e)}


@with_retry()
def tool_update_schedule(args: dict) -> dict:
    """Update an existing schedule (name, timezone, layers, teams)."""
    dry = is_dry_run_action(_dry_run, f"update_schedule {args['schedule_id']}")
    if dry:
        return dry
    try:
        sid = args["schedule_id"]
        current = pd_client.rget(f"schedules/{sid}")
        payload: dict = {"id": sid, "type": "schedule"}

        payload["name"] = args.get("name", current.get("name"))
        payload["time_zone"] = args.get("time_zone", current.get("time_zone"))
        if args.get("description") is not None:
            payload["description"] = args["description"]

        if args.get("schedule_layers"):
            layers = []
            for layer in args["schedule_layers"]:
                l: dict = {
                    "name": layer.get("name", "Layer 1"),
                    "start": layer["start"],
                    "rotation_virtual_start": layer.get("rotation_virtual_start", layer["start"]),
                    "rotation_turn_length_seconds": layer.get("rotation_turn_length_seconds", 86400),
                    "users": [
                        {"user": {"id": uid, "type": "user_reference"}}
                        for uid in layer.get("user_ids", [])
                    ],
                }
                if layer.get("id"):
                    l["id"] = layer["id"]
                if layer.get("end"):
                    l["end"] = layer["end"]
                layers.append(l)
            payload["schedule_layers"] = layers
        else:
            payload["schedule_layers"] = current.get("schedule_layers", [])

        if args.get("teams"):
            payload["teams"] = [{"id": tid, "type": "team_reference"} for tid in args["teams"]]

        updated = pd_client.rput(f"schedules/{sid}", json=payload)
        return {"success": True, "schedule": {"id": updated["id"], "name": updated["name"]}}
    except Exception as e:
        return {"error": str(e)}


@with_retry()
def tool_delete_schedule(args: dict) -> dict:
    """Delete a schedule. WARNING: irreversible."""
    dry = is_dry_run_action(_dry_run, f"delete_schedule {args['schedule_id']}")
    if dry:
        return dry
    try:
        pd_client.delete(f"schedules/{args['schedule_id']}")
        return {"success": True, "deleted_schedule_id": args["schedule_id"]}
    except Exception as e:
        return {"error": str(e)}


# ── Overrides ─────────────────────────────────────────

def tool_list_schedule_overrides(args: dict) -> dict:
    raw = safe_list(
        f"schedules/{args['schedule_id']}/overrides",
        {"since": args["since"], "until": args["until"]},
    )
    items = unwrap(raw) if isinstance(raw, dict) and "items" in raw else (raw if isinstance(raw, list) else [])
    return {
        "schedule_id": args["schedule_id"],
        "overrides": [
            {"id": o["id"], "start": o["start"], "end": o["end"],
             "user": o.get("user", {}).get("summary")}
            for o in items
        ],
    }


@with_retry()
def tool_create_schedule_override(args: dict) -> dict:
    dry = is_dry_run_action(_dry_run, f"create_schedule_override schedule={args['schedule_id']}")
    if dry:
        return dry
    try:
        body = {
            "start": args["start"], "end": args["end"],
            "user": {"id": args["user_id"], "type": "user_reference"},
        }
        resp = pd_client.rpost(f"schedules/{args['schedule_id']}/overrides", json=[body])
        return {"success": True, "override": resp}
    except Exception as e:
        return {"error": str(e)}


@with_retry()
def tool_delete_schedule_override(args: dict) -> dict:
    dry = is_dry_run_action(_dry_run, f"delete_schedule_override {args['override_id']}")
    if dry:
        return dry
    try:
        pd_client.delete(f"schedules/{args['schedule_id']}/overrides/{args['override_id']}")
        return {"success": True}
    except Exception as e:
        return {"error": str(e)}


# ── Users on call ─────────────────────────────────────

def tool_list_schedule_users_on_call(args: dict) -> dict:
    params = {}
    if args.get("since"): params["since"] = args["since"]
    if args.get("until"): params["until"] = args["until"]
    raw = safe_list(f"schedules/{args['schedule_id']}/users", params)
    items = unwrap(raw) if isinstance(raw, dict) else raw
    return {
        "schedule_id": args["schedule_id"],
        "users": [{"id": u["id"], "name": u["name"], "email": u.get("email")} for u in items],
    }