"""Team CRUD and membership tools."""

from pagerduty_sre_bot.clients import pd_client
from pagerduty_sre_bot.helpers import safe_list, unwrap, is_dry_run_action
from pagerduty_sre_bot.retry import with_retry

_dry_run = False


def set_dry_run(v: bool) -> None:
    global _dry_run
    _dry_run = v


def tool_list_teams(args: dict) -> dict:
    params = {}
    if args.get("query"):
        params["query"] = args["query"]
    raw = safe_list("teams", params)
    if isinstance(raw, dict) and "error" in raw:
        return raw
    items = unwrap(raw) if isinstance(raw, dict) else raw
    return {
        "total": len(items),
        "teams": [
            {"id": t["id"], "name": t["name"], "description": t.get("description", ""), "html_url": t.get("html_url")}
            for t in items
        ],
    }


@with_retry()
def tool_get_team(args: dict) -> dict:
    try:
        return pd_client.rget(f"teams/{args['team_id']}")
    except Exception as e:
        return {"error": str(e)}


@with_retry()
def tool_create_team(args: dict) -> dict:
    dry = is_dry_run_action(_dry_run, f"create_team name='{args['name']}'")
    if dry:
        return dry
    try:
        body = {"type": "team", "name": args["name"]}
        if args.get("description"):
            body["description"] = args["description"]
        team = pd_client.rpost("teams", json=body)
        return {"success": True, "team": {"id": team["id"], "name": team["name"]}}
    except Exception as e:
        return {"error": str(e)}


@with_retry()
def tool_update_team(args: dict) -> dict:
    dry = is_dry_run_action(_dry_run, f"update_team {args['team_id']}")
    if dry:
        return dry
    try:
        tid = args["team_id"]
        payload: dict = {"id": tid, "type": "team"}
        if args.get("name"):        payload["name"] = args["name"]
        if args.get("description"): payload["description"] = args["description"]
        updated = pd_client.rput(f"teams/{tid}", json=payload)
        return {"success": True, "team": {"id": updated["id"], "name": updated["name"]}}
    except Exception as e:
        return {"error": str(e)}


@with_retry()
def tool_delete_team(args: dict) -> dict:
    dry = is_dry_run_action(_dry_run, f"delete_team {args['team_id']}")
    if dry:
        return dry
    try:
        pd_client.delete(f"teams/{args['team_id']}")
        return {"success": True, "deleted_team_id": args["team_id"]}
    except Exception as e:
        return {"error": str(e)}


@with_retry()
def tool_manage_team_membership(args: dict) -> dict:
    dry = is_dry_run_action(_dry_run, f"manage_team_membership team={args['team_id']} user={args['user_id']}")
    if dry:
        return dry
    try:
        tid, uid = args["team_id"], args["user_id"]
        if args["action"] == "add":
            role = args.get("role", "responder")
            pd_client.put(f"teams/{tid}/users/{uid}", json={"role": role})
            return {"success": True, "action": "added", "team_id": tid, "user_id": uid, "role": role}
        else:
            pd_client.delete(f"teams/{tid}/users/{uid}")
            return {"success": True, "action": "removed", "team_id": tid, "user_id": uid}
    except Exception as e:
        return {"error": str(e)}


def tool_list_team_members(args: dict) -> dict:
    raw = safe_list(f"teams/{args['team_id']}/members")
    items = unwrap(raw) if isinstance(raw, dict) else raw
    return {
        "team_id": args["team_id"],
        "members": [
            {"user_id": m.get("user", {}).get("id"), "name": m.get("user", {}).get("summary"), "role": m.get("role")}
            for m in items
        ],
    }