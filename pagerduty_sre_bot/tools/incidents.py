"""Incident CRUD and management tools."""

from pagerduty_sre_bot.clients import pd_client
from pagerduty_sre_bot.helpers import safe_list, unwrap, is_dry_run_action
from pagerduty_sre_bot.retry import with_retry
from pagerduty_sre_bot.time_utils import diff_minutes

# Module-level dry_run flag — set by conversation.py before dispatching
_dry_run = False


def set_dry_run(v: bool) -> None:
    global _dry_run
    _dry_run = v


def tool_list_incidents(args: dict) -> dict:
    params = {
        "since": args["since"],
        "until": args["until"],
        "sort_by": f"{args.get('sort_by', 'created_at')}:desc",
    }
    params["statuses[]"] = args.get("statuses") or ["triggered", "acknowledged", "resolved"]
    if args.get("urgencies"):
        params["urgencies[]"] = args["urgencies"]
    if args.get("service_ids"):
        params["service_ids[]"] = args["service_ids"]
    if args.get("team_ids"):
        params["team_ids[]"] = args["team_ids"]

    raw = safe_list("incidents", params, args.get("limit", 25))
    if isinstance(raw, dict) and "error" in raw:
        return raw

    items = unwrap(raw) if isinstance(raw, dict) else raw
    truncated = isinstance(raw, dict) and raw.get("truncated", False)

    results = [
        {
            "id": i["id"],
            "title": i["title"],
            "status": i["status"],
            "urgency": i.get("urgency"),
            "priority": i.get("priority", {}).get("summary") if i.get("priority") else None,
            "service": i.get("service", {}).get("summary"),
            "service_id": i.get("service", {}).get("id"),
            "created_at": i["created_at"],
            "resolved_at": i.get("resolved_at"),
            "assigned_to": [a.get("assignee", {}).get("summary") for a in i.get("assignments", [])],
            "escalation_policy": i.get("escalation_policy", {}).get("summary"),
            "incident_number": i.get("incident_number"),
            "html_url": i.get("html_url"),
        }
        for i in items
    ]
    out = {"total": len(results), "incidents": results}
    if truncated:
        out["truncated"] = True
    return out


@with_retry()
def tool_get_incident(args: dict) -> dict:
    try:
        inc = pd_client.rget(f"incidents/{args['incident_id']}")
        return {
            "id": inc["id"], "title": inc["title"], "status": inc["status"],
            "urgency": inc.get("urgency"), "priority": inc.get("priority"),
            "service": inc.get("service"), "created_at": inc["created_at"],
            "resolved_at": inc.get("resolved_at"),
            "last_status_change_at": inc.get("last_status_change_at"),
            "assignments": inc.get("assignments"),
            "acknowledgements": inc.get("acknowledgements"),
            "escalation_policy": inc.get("escalation_policy"),
            "teams": inc.get("teams"), "alert_counts": inc.get("alert_counts"),
            "body": inc.get("body"), "html_url": inc.get("html_url"),
            "incident_number": inc.get("incident_number"),
        }
    except Exception as e:
        return {"error": str(e)}


@with_retry()
def tool_get_incident_timeline(args: dict) -> dict:
    try:
        logs = list(pd_client.iter_all(
            f"incidents/{args['incident_id']}/log_entries",
            params={"is_overview": False},
        ))
        return {
            "incident_id": args["incident_id"],
            "timeline_entries": [
                {
                    "type": l["type"],
                    "created_at": l["created_at"],
                    "summary": l.get("summary", ""),
                    "agent": l.get("agent", {}).get("summary") if l.get("agent") else None,
                    "channel": l.get("channel", {}).get("type") if l.get("channel") else None,
                    "assignees": [a.get("summary") for a in l.get("assignees", [])] if l.get("assignees") else None,
                }
                for l in logs
            ],
        }
    except Exception as e:
        return {"error": str(e)}


def tool_get_incident_notes(args: dict) -> dict:
    raw = safe_list(f"incidents/{args['incident_id']}/notes")
    if isinstance(raw, dict) and "error" in raw:
        return raw
    items = unwrap(raw) if isinstance(raw, dict) else raw
    return {
        "incident_id": args["incident_id"],
        "notes": [
            {"id": n["id"], "content": n["content"], "created_at": n["created_at"],
             "user": n.get("user", {}).get("summary")}
            for n in items
        ],
    }


def tool_get_incident_alerts(args: dict) -> dict:
    raw = safe_list(f"incidents/{args['incident_id']}/alerts")
    if isinstance(raw, dict) and "error" in raw:
        return raw
    items = unwrap(raw) if isinstance(raw, dict) else raw
    return {
        "incident_id": args["incident_id"],
        "alerts": [
            {
                "id": a["id"], "status": a["status"], "severity": a.get("severity"),
                "summary": a.get("summary"), "created_at": a["created_at"],
                "body": a.get("body", {}).get("details") if a.get("body") else None,
            }
            for a in items
        ],
    }


@with_retry()
def tool_manage_incident(args: dict) -> dict:
    dry = is_dry_run_action(_dry_run, f"manage_incident {args['incident_id']} → {args['action']}")
    if dry:
        return dry

    iid = args["incident_id"]
    action = args["action"]
    try:
        if action in ("acknowledge", "resolve"):
            status = "acknowledged" if action == "acknowledge" else "resolved"
            pd_client.rput("incidents", json=[{"id": iid, "type": "incident_reference", "status": status}])
            return {"success": True, "action": action, "incident_id": iid}

        if action == "reassign":
            atype = args.get("assignee_type", "user_reference")
            pd_client.rput("incidents", json=[{
                "id": iid, "type": "incident_reference",
                "assignments": [{"assignee": {"id": args["assignee_id"], "type": atype}}],
            }])
            return {"success": True, "action": "reassigned", "incident_id": iid, "assignee": args["assignee_id"]}

        if action == "change_urgency":
            pd_client.rput("incidents", json=[{"id": iid, "type": "incident_reference", "urgency": args["urgency"]}])
            return {"success": True, "action": "urgency_changed", "incident_id": iid, "urgency": args["urgency"]}

        if action == "snooze":
            resp = pd_client.post(f"incidents/{iid}/snooze", json={"duration": args.get("snooze_duration", 3600)})
            return {"success": resp.ok, "action": "snoozed", "incident_id": iid}

        if action == "add_note":
            resp = pd_client.post(f"incidents/{iid}/notes", json={"note": {"content": args["note_content"]}})
            return {"success": resp.ok, "action": "note_added", "incident_id": iid}

        if action == "merge":
            merge_refs = [{"id": mid, "type": "incident_reference"} for mid in args.get("merge_ids", [])]
            resp = pd_client.put(f"incidents/{iid}/merge", json={"source_incidents": merge_refs})
            return {"success": resp.ok, "action": "merged", "incident_id": iid}

        return {"error": f"Unknown action: {action}"}
    except Exception as e:
        return {"error": str(e)}


@with_retry()
def tool_create_incident(args: dict) -> dict:
    dry = is_dry_run_action(_dry_run, f"create_incident title='{args['title']}' service={args['service_id']}")
    if dry:
        return dry
    try:
        body = {
            "type": "incident",
            "title": args["title"],
            "service": {"id": args["service_id"], "type": "service_reference"},
            "urgency": args.get("urgency", "high"),
        }
        if args.get("body"):
            body["body"] = {"type": "incident_body", "details": args["body"]}
        if args.get("escalation_policy_id"):
            body["escalation_policy"] = {"id": args["escalation_policy_id"], "type": "escalation_policy_reference"}
        if args.get("priority_id"):
            body["priority"] = {"id": args["priority_id"], "type": "priority_reference"}
        inc = pd_client.rpost("incidents", json=body)
        return {"success": True, "incident": {"id": inc["id"], "title": inc["title"], "html_url": inc.get("html_url")}}
    except Exception as e:
        return {"error": str(e)}