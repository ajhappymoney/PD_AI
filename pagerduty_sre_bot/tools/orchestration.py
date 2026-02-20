"""Event Orchestration full CRUD — global orchestrations, routing, service orchestrations."""

from pagerduty_sre_bot.clients import pd_client
from pagerduty_sre_bot.helpers import safe_list, unwrap, is_dry_run_action
from pagerduty_sre_bot.retry import with_retry

_dry_run = False


def set_dry_run(v: bool) -> None:
    global _dry_run
    _dry_run = v


# ── Orchestration CRUD ─────────────────────────────────

def tool_list_event_orchestrations(args: dict) -> dict:
    """List all global event orchestrations."""
    raw = safe_list("event_orchestrations")
    if isinstance(raw, dict) and "error" in raw:
        return raw
    items = unwrap(raw) if isinstance(raw, dict) else raw
    return {
        "total": len(items),
        "orchestrations": [
            {
                "id": o["id"], "name": o.get("name"),
                "description": o.get("description", ""),
                "routes": o.get("routes"),
                "integrations": [
                    {"id": i.get("id"), "label": i.get("label")}
                    for i in o.get("integrations", [])
                ] if o.get("integrations") else [],
                "team": o.get("team", {}).get("summary") if o.get("team") else None,
            }
            for o in items
        ],
    }


@with_retry()
def tool_get_event_orchestration(args: dict) -> dict:
    """Get details of a single event orchestration."""
    try:
        resp = pd_client.get(f"event_orchestrations/{args['orchestration_id']}")
        if resp.status_code < 300:
            return resp.json().get("orchestration", {})
        return {"error": f"HTTP {resp.status_code}: {resp.text}"}
    except Exception as e:
        return {"error": str(e)}


@with_retry()
def tool_create_event_orchestration(args: dict) -> dict:
    """Create a new global event orchestration."""
    dry = is_dry_run_action(_dry_run, f"create_event_orchestration name='{args.get('name')}'")
    if dry:
        return dry
    try:
        body: dict = {
            "orchestration": {
                "name": args["name"],
            }
        }
        if args.get("description"):
            body["orchestration"]["description"] = args["description"]
        if args.get("team_id"):
            body["orchestration"]["team"] = {"id": args["team_id"], "type": "team_reference"}

        resp = pd_client.post("event_orchestrations", json=body)
        if resp.status_code < 300:
            o = resp.json().get("orchestration", {})
            return {
                "success": True,
                "orchestration": {
                    "id": o.get("id"),
                    "name": o.get("name"),
                    "integrations": o.get("integrations", []),
                },
            }
        return {"error": f"HTTP {resp.status_code}: {resp.text}"}
    except Exception as e:
        return {"error": str(e)}


@with_retry()
def tool_update_event_orchestration(args: dict) -> dict:
    """Update a global event orchestration (name, description, team)."""
    dry = is_dry_run_action(_dry_run, f"update_event_orchestration {args['orchestration_id']}")
    if dry:
        return dry
    try:
        oid = args["orchestration_id"]
        payload: dict = {}
        if args.get("name"):        payload["name"] = args["name"]
        if args.get("description"): payload["description"] = args["description"]
        if args.get("team_id"):
            payload["team"] = {"id": args["team_id"], "type": "team_reference"}

        resp = pd_client.put(f"event_orchestrations/{oid}", json={"orchestration": payload})
        if resp.status_code < 300:
            o = resp.json().get("orchestration", {})
            return {"success": True, "orchestration": {"id": o.get("id"), "name": o.get("name")}}
        return {"error": f"HTTP {resp.status_code}: {resp.text}"}
    except Exception as e:
        return {"error": str(e)}


@with_retry()
def tool_delete_event_orchestration(args: dict) -> dict:
    """Delete a global event orchestration."""
    dry = is_dry_run_action(_dry_run, f"delete_event_orchestration {args['orchestration_id']}")
    if dry:
        return dry
    try:
        resp = pd_client.delete(f"event_orchestrations/{args['orchestration_id']}")
        if resp.status_code < 300:
            return {"success": True, "deleted_orchestration_id": args["orchestration_id"]}
        return {"error": f"HTTP {resp.status_code}: {resp.text}"}
    except Exception as e:
        return {"error": str(e)}


# ── Orchestration Router (Global Routing Rules) ────────

@with_retry()
def tool_get_orchestration_router(args: dict) -> dict:
    """Get the global routing rules for an orchestration."""
    try:
        resp = pd_client.get(f"event_orchestrations/{args['orchestration_id']}/router")
        if resp.status_code < 300:
            return resp.json().get("orchestration_path", {})
        return {"error": f"HTTP {resp.status_code}"}
    except Exception as e:
        return {"error": str(e)}


@with_retry()
def tool_update_orchestration_router(args: dict) -> dict:
    """Update the global routing rules for an orchestration."""
    dry = is_dry_run_action(_dry_run, f"update_orchestration_router {args['orchestration_id']}")
    if dry:
        return dry
    try:
        oid = args["orchestration_id"]
        body = {"orchestration_path": args["orchestration_path"]}
        resp = pd_client.put(f"event_orchestrations/{oid}/router", json=body)
        if resp.status_code < 300:
            return {"success": True, "orchestration_path": resp.json().get("orchestration_path", {})}
        return {"error": f"HTTP {resp.status_code}: {resp.text}"}
    except Exception as e:
        return {"error": str(e)}


# ── Orchestration Unrouted Rules ───────────────────────

@with_retry()
def tool_get_orchestration_unrouted(args: dict) -> dict:
    """Get the unrouted rules for an orchestration."""
    try:
        resp = pd_client.get(f"event_orchestrations/{args['orchestration_id']}/unrouted")
        if resp.status_code < 300:
            return resp.json().get("orchestration_path", {})
        return {"error": f"HTTP {resp.status_code}"}
    except Exception as e:
        return {"error": str(e)}


@with_retry()
def tool_update_orchestration_unrouted(args: dict) -> dict:
    """Update the unrouted rules for an orchestration."""
    dry = is_dry_run_action(_dry_run, f"update_orchestration_unrouted {args['orchestration_id']}")
    if dry:
        return dry
    try:
        oid = args["orchestration_id"]
        body = {"orchestration_path": args["orchestration_path"]}
        resp = pd_client.put(f"event_orchestrations/{oid}/unrouted", json=body)
        if resp.status_code < 300:
            return {"success": True}
        return {"error": f"HTTP {resp.status_code}: {resp.text}"}
    except Exception as e:
        return {"error": str(e)}


# ── Service Orchestration Rules ────────────────────────

@with_retry()
def tool_get_service_orchestration(args: dict) -> dict:
    """Get the event orchestration rules for a service."""
    try:
        resp = pd_client.get(f"event_orchestrations/services/{args['service_id']}")
        if resp.status_code < 300:
            return resp.json().get("orchestration_path", {})
        return {"error": f"HTTP {resp.status_code}"}
    except Exception as e:
        return {"error": str(e)}


@with_retry()
def tool_update_service_orchestration(args: dict) -> dict:
    """Update the event orchestration rules for a service."""
    dry = is_dry_run_action(_dry_run, f"update_service_orchestration service={args['service_id']}")
    if dry:
        return dry
    try:
        sid = args["service_id"]
        body = {"orchestration_path": args["orchestration_path"]}
        resp = pd_client.put(f"event_orchestrations/services/{sid}", json=body)
        if resp.status_code < 300:
            return {"success": True}
        return {"error": f"HTTP {resp.status_code}: {resp.text}"}
    except Exception as e:
        return {"error": str(e)}


# ── Orchestration Integrations ─────────────────────────

@with_retry()
def tool_list_orchestration_integrations(args: dict) -> dict:
    """List integrations (routing keys) for an orchestration."""
    try:
        resp = pd_client.get(f"event_orchestrations/{args['orchestration_id']}/integrations")
        if resp.status_code < 300:
            data = resp.json()
            integrations = data.get("integrations", [])
            return {
                "orchestration_id": args["orchestration_id"],
                "integrations": [
                    {"id": i.get("id"), "label": i.get("label"),
                     "parameters": i.get("parameters", {})}
                    for i in integrations
                ],
            }
        return {"error": f"HTTP {resp.status_code}"}
    except Exception as e:
        return {"error": str(e)}


@with_retry()
def tool_create_orchestration_integration(args: dict) -> dict:
    """Create a new integration (routing key) for an orchestration."""
    dry = is_dry_run_action(_dry_run, f"create_orchestration_integration {args['orchestration_id']}")
    if dry:
        return dry
    try:
        oid = args["orchestration_id"]
        body: dict = {"integration": {"label": args.get("label", "SRE Bot Integration")}}
        resp = pd_client.post(f"event_orchestrations/{oid}/integrations", json=body)
        if resp.status_code < 300:
            i = resp.json().get("integration", {})
            return {
                "success": True,
                "integration": {
                    "id": i.get("id"),
                    "label": i.get("label"),
                    "parameters": i.get("parameters", {}),
                },
            }
        return {"error": f"HTTP {resp.status_code}: {resp.text}"}
    except Exception as e:
        return {"error": str(e)}