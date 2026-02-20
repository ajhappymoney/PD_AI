"""Service CRUD and integration tools."""

from pagerduty_sre_bot.clients import pd_client
from pagerduty_sre_bot.helpers import safe_list, unwrap, is_dry_run_action
from pagerduty_sre_bot.cache import cache_get, cache_set, cache_clear
from pagerduty_sre_bot.retry import with_retry

_dry_run = False


def set_dry_run(v: bool) -> None:
    global _dry_run
    _dry_run = v


def tool_list_services(args: dict) -> dict:
    cache_key = f"services:{args.get('query', '')}:{args.get('team_ids', '')}"
    cached = cache_get(cache_key)
    if cached:
        return cached

    params = {}
    if args.get("query"):    params["query"] = args["query"]
    if args.get("team_ids"): params["team_ids[]"] = args["team_ids"]
    if args.get("include"):  params["include[]"] = args["include"]

    raw = safe_list("services", params)
    if isinstance(raw, dict) and "error" in raw:
        return raw

    items = unwrap(raw) if isinstance(raw, dict) else raw
    result = {
        "total": len(items),
        "services": [
            {
                "id": s["id"], "name": s["name"], "status": s.get("status"),
                "description": s.get("description", ""),
                "escalation_policy": s.get("escalation_policy", {}).get("summary"),
                "teams": [t.get("summary") for t in s.get("teams", [])],
                "html_url": s.get("html_url"),
            }
            for s in items
        ],
    }
    cache_set(cache_key, result)
    return result


@with_retry()
def tool_get_service(args: dict) -> dict:
    try:
        params = {}
        if args.get("include"):
            params["include[]"] = args["include"]
        return pd_client.rget(f"services/{args['service_id']}", params=params)
    except Exception as e:
        return {"error": str(e)}


@with_retry()
def tool_create_service(args: dict) -> dict:
    dry = is_dry_run_action(_dry_run, f"create_service name='{args['name']}'")
    if dry:
        return dry
    try:
        body: dict = {
            "type": "service",
            "name": args["name"],
            "escalation_policy": {"id": args["escalation_policy_id"], "type": "escalation_policy_reference"},
        }
        if args.get("description"):    body["description"] = args["description"]
        if args.get("urgency_rule"):   body["incident_urgency_rule"] = {"type": "constant", "urgency": args["urgency_rule"]}
        if args.get("alert_creation"): body["alert_creation"] = args["alert_creation"]
        svc = pd_client.rpost("services", json=body)
        cache_clear("services:")
        return {"success": True, "service": {"id": svc["id"], "name": svc["name"]}}
    except Exception as e:
        return {"error": str(e)}


@with_retry()
def tool_update_service(args: dict) -> dict:
    dry = is_dry_run_action(_dry_run, f"update_service {args['service_id']}")
    if dry:
        return dry
    try:
        sid = args["service_id"]
        payload: dict = {"id": sid, "type": "service"}
        if args.get("name"):        payload["name"] = args["name"]
        if args.get("description"): payload["description"] = args["description"]
        if args.get("status"):      payload["status"] = args["status"]
        if args.get("escalation_policy_id"):
            payload["escalation_policy"] = {"id": args["escalation_policy_id"], "type": "escalation_policy_reference"}
        updated = pd_client.rput(f"services/{sid}", json=payload)
        cache_clear("services:")
        return {"success": True, "service": {"id": updated["id"], "name": updated["name"], "status": updated.get("status")}}
    except Exception as e:
        return {"error": str(e)}


@with_retry()
def tool_delete_service(args: dict) -> dict:
    dry = is_dry_run_action(_dry_run, f"delete_service {args['service_id']}")
    if dry:
        return dry
    try:
        pd_client.delete(f"services/{args['service_id']}")
        cache_clear("services:")
        return {"success": True, "deleted_service_id": args["service_id"]}
    except Exception as e:
        return {"error": str(e)}


def tool_list_service_integrations(args: dict) -> dict:
    raw = safe_list(f"services/{args['service_id']}/integrations")
    if isinstance(raw, dict) and "error" in raw:
        return raw
    items = unwrap(raw) if isinstance(raw, dict) else raw
    return {
        "integrations": [
            {
                "id": i["id"], "name": i.get("name"), "type": i.get("type"),
                "integration_key": i.get("integration_key"),
                "vendor": i.get("vendor", {}).get("summary") if i.get("vendor") else None,
            }
            for i in items
        ],
    }


@with_retry()
def tool_create_service_integration(args: dict) -> dict:
    dry = is_dry_run_action(_dry_run, f"create_service_integration service={args['service_id']}")
    if dry:
        return dry
    try:
        body = {"type": args["type"], "name": args["name"]}
        if args.get("vendor_id"):
            body["vendor"] = {"id": args["vendor_id"], "type": "vendor_reference"}
        resp = pd_client.rpost(f"services/{args['service_id']}/integrations", json=body)
        return {"success": True, "integration": {"id": resp["id"], "integration_key": resp.get("integration_key")}}
    except Exception as e:
        return {"error": str(e)}