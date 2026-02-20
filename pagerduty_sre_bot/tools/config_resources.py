"""Tags, vendors, webhooks, extensions, business services, and other config tools."""

from pagerduty_sre_bot.clients import pd_client
from pagerduty_sre_bot.helpers import safe_list, unwrap, is_dry_run_action
from pagerduty_sre_bot.retry import with_retry

_dry_run = False


def set_dry_run(v: bool) -> None:
    global _dry_run
    _dry_run = v


# ── Tags ───────────────────────────────────────────

def tool_list_tags(args: dict) -> dict:
    params = {}
    if args.get("query"): params["query"] = args["query"]
    raw = safe_list("tags", params)
    if isinstance(raw, dict) and "error" in raw:
        return raw
    items = unwrap(raw) if isinstance(raw, dict) else raw
    return {"total": len(items), "tags": [{"id": t["id"], "label": t.get("label")} for t in items]}


@with_retry()
def tool_manage_tags(args: dict) -> dict:
    dry = is_dry_run_action(_dry_run, f"manage_tags {args['resource_type']}/{args['resource_id']}")
    if dry:
        return dry
    try:
        body: dict = {}
        if args.get("add_tags"):    body["add"] = args["add_tags"]
        if args.get("remove_tags"): body["remove"] = args["remove_tags"]
        pd_client.post(f"{args['resource_type']}/{args['resource_id']}/change_tags", json=body)
        return {"success": True}
    except Exception as e:
        return {"error": str(e)}


# ── Vendors ────────────────────────────────────────

def tool_list_vendors(args: dict) -> dict:
    params = {}
    if args.get("query"): params["query"] = args["query"]
    raw = safe_list("vendors", params)
    items = unwrap(raw) if isinstance(raw, dict) else raw
    return {
        "total": len(items),
        "vendors": [
            {"id": v["id"], "name": v["name"], "description": v.get("description", "")[:200],
             "website_url": v.get("website_url")}
            for v in items
        ],
    }


# ── Response Plays ─────────────────────────────────

def tool_list_response_plays(args: dict) -> dict:
    params = {}
    if args.get("query"): params["query"] = args["query"]
    raw = safe_list("response_plays", params)
    items = unwrap(raw) if isinstance(raw, dict) else raw
    return {
        "total": len(items),
        "response_plays": [
            {"id": p["id"], "name": p.get("name"), "description": p.get("description", ""), "type": p.get("type")}
            for p in items
        ],
    }


# ── Business Services ──────────────────────────────

def tool_list_business_services(_args: dict) -> dict:
    raw = safe_list("business_services")
    items = unwrap(raw) if isinstance(raw, dict) else raw
    return {
        "total": len(items),
        "business_services": [
            {"id": s["id"], "name": s["name"], "description": s.get("description", ""),
             "point_of_contact": s.get("point_of_contact"), "html_url": s.get("html_url")}
            for s in items
        ],
    }


@with_retry()
def tool_get_business_service(args: dict) -> dict:
    try:
        return pd_client.rget(f"business_services/{args['business_service_id']}")
    except Exception as e:
        return {"error": str(e)}


# ── Service Dependencies ───────────────────────────

@with_retry()
def tool_get_service_dependencies(args: dict) -> dict:
    try:
        stype = "business_services" if args["service_type"] == "business" else "services"
        resp = pd_client.get(f"service_dependencies/{stype}/{args['service_id']}")
        return resp.json().get("relationships", []) if resp.ok else {"error": f"HTTP {resp.status_code}"}
    except Exception as e:
        return {"error": str(e)}


# ── Status Dashboards ──────────────────────────────

def tool_list_status_dashboards(_args: dict) -> dict:
    raw = safe_list("status_dashboards")
    items = unwrap(raw) if isinstance(raw, dict) else raw
    return {"dashboards": [{"id": d["id"], "name": d.get("name"), "url_slug": d.get("url_slug")} for d in items]}


# ── Event Orchestration / Rulesets ─────────────────

def tool_list_event_orchestrations(_args: dict) -> dict:
    raw = safe_list("event_orchestrations")
    items = unwrap(raw) if isinstance(raw, dict) else raw
    return {
        "orchestrations": [
            {"id": o["id"], "name": o.get("name"), "description": o.get("description", ""), "routes": o.get("routes")}
            for o in items
        ],
    }


def tool_list_rulesets(_args: dict) -> dict:
    raw = safe_list("rulesets")
    items = unwrap(raw) if isinstance(raw, dict) else raw
    return {"rulesets": [{"id": r["id"], "name": r.get("name"), "type": r.get("type")} for r in items]}


# ── Webhooks ───────────────────────────────────────

def tool_list_webhook_subscriptions(_args: dict) -> dict:
    raw = safe_list("webhook_subscriptions")
    items = unwrap(raw) if isinstance(raw, dict) else raw
    return {
        "subscriptions": [
            {
                "id": s["id"], "description": s.get("description", ""), "type": s.get("type"),
                "delivery_method": s.get("delivery_method"), "events": s.get("events"), "filter": s.get("filter"),
            }
            for s in items
        ],
    }


@with_retry()
def tool_create_webhook_subscription(args: dict) -> dict:
    dry = is_dry_run_action(_dry_run, f"create_webhook_subscription url={args['delivery_method_url']}")
    if dry:
        return dry
    try:
        body: dict = {
            "type": "webhook_subscription",
            "delivery_method": {"type": "http_delivery_method", "url": args["delivery_method_url"]},
            "events": args["events"],
            "filter": {"type": args["filter_type"]},
        }
        if args.get("filter_id"):   body["filter"]["id"] = args["filter_id"]
        if args.get("description"): body["description"] = args["description"]
        sub = pd_client.rpost("webhook_subscriptions", json=body)
        return {"success": True, "subscription": {"id": sub["id"]}}
    except Exception as e:
        return {"error": str(e)}


# ── Abilities / Extensions / Workflows ─────────────

@with_retry()
def tool_list_abilities(_args: dict) -> dict:
    try:
        resp = pd_client.get("abilities")
        return {"abilities": resp.json().get("abilities", [])} if resp.ok else {"error": f"HTTP {resp.status_code}"}
    except Exception as e:
        return {"error": str(e)}


def tool_list_extensions(args: dict) -> dict:
    params = {}
    if args.get("query"):               params["query"] = args["query"]
    if args.get("extension_schema_id"): params["extension_schema_id"] = args["extension_schema_id"]
    raw = safe_list("extensions", params)
    items = unwrap(raw) if isinstance(raw, dict) else raw
    return {
        "total": len(items),
        "extensions": [
            {
                "id": e["id"], "name": e.get("name"), "type": e.get("type"),
                "endpoint_url": e.get("endpoint_url"),
                "extension_schema": e.get("extension_schema", {}).get("summary") if e.get("extension_schema") else None,
            }
            for e in items
        ],
    }


def tool_list_incident_workflows(args: dict) -> dict:
    params = {}
    if args.get("query"): params["query"] = args["query"]
    raw = safe_list("incident_workflows", params)
    items = unwrap(raw) if isinstance(raw, dict) else raw
    return {
        "total": len(items),
        "workflows": [
            {"id": w["id"], "name": w.get("name"), "description": w.get("description", ""),
             "created_at": w.get("created_at")}
            for w in items
        ],
    }


# ── Priorities ─────────────────────────────────────

def tool_list_priorities(_args: dict) -> dict:
    raw = safe_list("priorities")
    items = unwrap(raw) if isinstance(raw, dict) else raw
    return {
        "priorities": [
            {"id": p["id"], "name": p["name"], "description": p.get("description", ""), "order": p.get("order")}
            for p in items
        ],
    }