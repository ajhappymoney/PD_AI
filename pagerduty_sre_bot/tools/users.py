"""User CRUD and contact/notification tools."""

from pagerduty_sre_bot.clients import pd_client
from pagerduty_sre_bot.helpers import safe_list, unwrap, is_dry_run_action
from pagerduty_sre_bot.cache import cache_get, cache_set, cache_clear
from pagerduty_sre_bot.retry import with_retry

_dry_run = False


def set_dry_run(v: bool) -> None:
    global _dry_run
    _dry_run = v


def tool_list_users(args: dict) -> dict:
    cache_key = f"users:{args.get('query', '')}:{args.get('team_ids', '')}"
    cached = cache_get(cache_key)
    if cached:
        return cached

    params = {}
    if args.get("query"):    params["query"] = args["query"]
    if args.get("team_ids"): params["team_ids[]"] = args["team_ids"]
    if args.get("include"):  params["include[]"] = args["include"]

    raw = safe_list("users", params)
    if isinstance(raw, dict) and "error" in raw:
        return raw

    items = unwrap(raw) if isinstance(raw, dict) else raw
    result = {
        "total": len(items),
        "users": [
            {
                "id": u["id"], "name": u["name"], "email": u.get("email"),
                "role": u.get("role"), "job_title": u.get("job_title"),
                "time_zone": u.get("time_zone"), "html_url": u.get("html_url"),
            }
            for u in items
        ],
    }
    cache_set(cache_key, result)
    return result


@with_retry()
def tool_get_user(args: dict) -> dict:
    try:
        params = {}
        if args.get("include"):
            params["include[]"] = args["include"]
        return pd_client.rget(f"users/{args['user_id']}", params=params)
    except Exception as e:
        return {"error": str(e)}


@with_retry()
def tool_create_user(args: dict) -> dict:
    dry = is_dry_run_action(_dry_run, f"create_user name='{args['name']}' email={args['email']}")
    if dry:
        return dry
    try:
        body = {"type": "user", "name": args["name"], "email": args["email"]}
        for f in ("role", "time_zone", "job_title"):
            if args.get(f):
                body[f] = args[f]
        user = pd_client.rpost("users", json=body)
        cache_clear("users:")
        return {"success": True, "user": {"id": user["id"], "name": user["name"], "email": user.get("email")}}
    except Exception as e:
        return {"error": str(e)}


@with_retry()
def tool_update_user(args: dict) -> dict:
    dry = is_dry_run_action(_dry_run, f"update_user {args['user_id']}")
    if dry:
        return dry
    try:
        uid = args["user_id"]
        payload: dict = {"id": uid, "type": "user"}
        for field in ("name", "email", "role", "job_title", "time_zone"):
            if args.get(field):
                payload[field] = args[field]
        updated = pd_client.rput(f"users/{uid}", json=payload)
        cache_clear("users:")
        return {"success": True, "user": {"id": updated["id"], "name": updated["name"]}}
    except Exception as e:
        return {"error": str(e)}


@with_retry()
def tool_delete_user(args: dict) -> dict:
    dry = is_dry_run_action(_dry_run, f"delete_user {args['user_id']}")
    if dry:
        return dry
    try:
        pd_client.delete(f"users/{args['user_id']}")
        cache_clear("users:")
        return {"success": True, "deleted_user_id": args["user_id"]}
    except Exception as e:
        return {"error": str(e)}


def tool_get_user_contact_methods(args: dict) -> dict:
    raw = safe_list(f"users/{args['user_id']}/contact_methods")
    items = unwrap(raw) if isinstance(raw, dict) else raw
    return {
        "user_id": args["user_id"],
        "contact_methods": [
            {"id": m["id"], "type": m["type"], "label": m.get("label"),
             "address": m.get("address"), "country_code": m.get("country_code")}
            for m in items
        ],
    }


def tool_get_user_notification_rules(args: dict) -> dict:
    raw = safe_list(f"users/{args['user_id']}/notification_rules")
    items = unwrap(raw) if isinstance(raw, dict) else raw
    return {
        "user_id": args["user_id"],
        "notification_rules": [
            {
                "id": r["id"], "type": r["type"], "urgency": r.get("urgency"),
                "start_delay_in_minutes": r.get("start_delay_in_minutes"),
                "contact_method": r.get("contact_method", {}).get("summary") if r.get("contact_method") else None,
            }
            for r in items
        ],
    }