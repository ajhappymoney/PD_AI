"""Automation Actions — list, get, create, invoke actions; manage runners."""

from pagerduty_sre_bot.clients import pd_client
from pagerduty_sre_bot.helpers import safe_list, unwrap, is_dry_run_action, MAX_RESULTS
from pagerduty_sre_bot.retry import with_retry

_dry_run = False


def set_dry_run(v: bool) -> None:
    global _dry_run
    _dry_run = v


# ── Actions ────────────────────────────────────────────

def tool_list_automation_actions(args: dict) -> dict:
    """List automation actions."""
    params = {}
    if args.get("query"):       params["query"] = args["query"]
    if args.get("service_id"):  params["service_id"] = args["service_id"]
    try:
        records = []
        for a in pd_client.iter_cursor("automation_actions/actions", params=params):
            records.append({
                "id": a.get("id"), "name": a.get("name"),
                "description": a.get("description", ""),
                "type": a.get("type"),
                "action_type": a.get("action_type"),
                "runner_id": a.get("runner", {}).get("id") if a.get("runner") else None,
                "runner_name": a.get("runner", {}).get("name") if a.get("runner") else None,
                "creation_time": a.get("creation_time"),
                "services_count": len(a.get("services", [])),
            })
            if len(records) >= MAX_RESULTS:
                break
        return {"total": len(records), "automation_actions": records}
    except Exception as e:
        return {"error": str(e)}


@with_retry()
def tool_get_automation_action(args: dict) -> dict:
    """Get details of a single automation action."""
    try:
        resp = pd_client.get(f"automation_actions/actions/{args['action_id']}")
        if resp.status_code < 300:
            a = resp.json().get("action", {})
            return {
                "id": a.get("id"), "name": a.get("name"),
                "description": a.get("description"),
                "type": a.get("type"), "action_type": a.get("action_type"),
                "runner": a.get("runner"),
                "services": [
                    {"id": s.get("id"), "name": s.get("summary", s.get("name"))}
                    for s in a.get("services", [])
                ],
                "action_data_reference": a.get("action_data_reference"),
                "creation_time": a.get("creation_time"),
                "modify_time": a.get("modify_time"),
            }
        return {"error": f"HTTP {resp.status_code}: {resp.text}"}
    except Exception as e:
        return {"error": str(e)}


@with_retry()
def tool_create_automation_action(args: dict) -> dict:
    """Create a new automation action."""
    dry = is_dry_run_action(_dry_run, f"create_automation_action name='{args.get('name')}'")
    if dry:
        return dry
    try:
        body: dict = {
            "action": {
                "name": args["name"],
                "action_type": args.get("action_type", "process_automation"),
                "runner": args.get("runner_id"),
                "action_data_reference": args.get("action_data_reference", {}),
            }
        }
        if args.get("description"):
            body["action"]["description"] = args["description"]
        if args.get("services"):
            body["action"]["services"] = [
                {"id": sid, "type": "service_reference"} for sid in args["services"]
            ]

        resp = pd_client.post("automation_actions/actions", json=body)
        if resp.status_code < 300:
            a = resp.json().get("action", {})
            return {"success": True, "action": {"id": a.get("id"), "name": a.get("name")}}
        return {"error": f"HTTP {resp.status_code}: {resp.text}"}
    except Exception as e:
        return {"error": str(e)}


@with_retry()
def tool_update_automation_action(args: dict) -> dict:
    """Update an automation action."""
    dry = is_dry_run_action(_dry_run, f"update_automation_action {args['action_id']}")
    if dry:
        return dry
    try:
        aid = args["action_id"]
        payload: dict = {}
        for k in ("name", "description", "action_type", "action_data_reference"):
            if args.get(k) is not None:
                payload[k] = args[k]
        resp = pd_client.put(f"automation_actions/actions/{aid}", json={"action": payload})
        if resp.status_code < 300:
            a = resp.json().get("action", {})
            return {"success": True, "action": {"id": a.get("id"), "name": a.get("name")}}
        return {"error": f"HTTP {resp.status_code}: {resp.text}"}
    except Exception as e:
        return {"error": str(e)}


@with_retry()
def tool_delete_automation_action(args: dict) -> dict:
    """Delete an automation action."""
    dry = is_dry_run_action(_dry_run, f"delete_automation_action {args['action_id']}")
    if dry:
        return dry
    try:
        resp = pd_client.delete(f"automation_actions/actions/{args['action_id']}")
        if resp.status_code < 300:
            return {"success": True, "deleted_action_id": args["action_id"]}
        return {"error": f"HTTP {resp.status_code}: {resp.text}"}
    except Exception as e:
        return {"error": str(e)}


@with_retry()
def tool_invoke_automation_action(args: dict) -> dict:
    """Invoke (run) an automation action on an incident."""
    dry = is_dry_run_action(_dry_run, f"invoke_automation_action {args['action_id']} on {args.get('incident_id')}")
    if dry:
        return dry
    try:
        aid = args["action_id"]
        body: dict = {"invocation": {}}
        if args.get("incident_id"):
            body["invocation"]["incident_id"] = args["incident_id"]
        if args.get("alert_id"):
            body["invocation"]["alert_id"] = args["alert_id"]

        resp = pd_client.post(f"automation_actions/actions/{aid}/invocations", json=body)
        if resp.status_code < 300:
            inv = resp.json().get("invocation", {})
            return {
                "success": True,
                "invocation": {
                    "id": inv.get("id"),
                    "state": inv.get("state"),
                    "action_id": aid,
                },
            }
        return {"error": f"HTTP {resp.status_code}: {resp.text}"}
    except Exception as e:
        return {"error": str(e)}


def tool_list_automation_action_invocations(args: dict) -> dict:
    """List invocations for an automation action."""
    try:
        params = {}
        if args.get("state"):
            params["state"] = args["state"]
        records = []
        for inv in pd_client.iter_cursor(
                f"automation_actions/actions/{args['action_id']}/invocations", params=params
        ):
            records.append({
                "id": inv.get("id"), "state": inv.get("state"),
                "created_at": inv.get("creation_time"),
                "incident_id": inv.get("incident_id"),
            })
            if len(records) >= MAX_RESULTS:
                break
        return {"total": len(records), "invocations": records}
    except Exception as e:
        return {"error": str(e)}


# ── Runners ────────────────────────────────────────────

def tool_list_automation_runners(args: dict) -> dict:
    """List automation action runners."""
    try:
        records = []
        for r in pd_client.iter_cursor("automation_actions/runners"):
            records.append({
                "id": r.get("id"), "name": r.get("name"),
                "description": r.get("description", ""),
                "type": r.get("type"),
                "runner_type": r.get("runner_type"),
                "status": r.get("status"),
                "creation_time": r.get("creation_time"),
            })
            if len(records) >= MAX_RESULTS:
                break
        return {"total": len(records), "runners": records}
    except Exception as e:
        return {"error": str(e)}


@with_retry()
def tool_get_automation_runner(args: dict) -> dict:
    """Get details of a single automation runner."""
    try:
        resp = pd_client.get(f"automation_actions/runners/{args['runner_id']}")
        if resp.status_code < 300:
            return resp.json().get("runner", {})
        return {"error": f"HTTP {resp.status_code}"}
    except Exception as e:
        return {"error": str(e)}


# ── Service Association ────────────────────────────────

@with_retry()
def tool_associate_automation_action_service(args: dict) -> dict:
    """Associate an automation action with a service."""
    dry = is_dry_run_action(_dry_run, f"associate action {args['action_id']} → service {args['service_id']}")
    if dry:
        return dry
    try:
        resp = pd_client.post(
            f"automation_actions/actions/{args['action_id']}/services",
            json={"service": {"id": args["service_id"], "type": "service_reference"}},
        )
        if resp.status_code < 300:
            return {"success": True}
        return {"error": f"HTTP {resp.status_code}: {resp.text}"}
    except Exception as e:
        return {"error": str(e)}


@with_retry()
def tool_dissociate_automation_action_service(args: dict) -> dict:
    """Remove an automation action from a service."""
    dry = is_dry_run_action(_dry_run, f"dissociate action {args['action_id']} from service {args['service_id']}")
    if dry:
        return dry
    try:
        resp = pd_client.delete(
            f"automation_actions/actions/{args['action_id']}/services/{args['service_id']}"
        )
        if resp.status_code < 300:
            return {"success": True}
        return {"error": f"HTTP {resp.status_code}: {resp.text}"}
    except Exception as e:
        return {"error": str(e)}