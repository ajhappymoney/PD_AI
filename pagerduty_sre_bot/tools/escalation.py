"""Escalation policy CRUD tools."""

from pagerduty_sre_bot.clients import pd_client
from pagerduty_sre_bot.helpers import safe_list, unwrap, is_dry_run_action
from pagerduty_sre_bot.retry import with_retry

_dry_run = False


def set_dry_run(v: bool) -> None:
    global _dry_run
    _dry_run = v


def tool_list_escalation_policies(args: dict) -> dict:
    params = {}
    if args.get("query"):    params["query"] = args["query"]
    if args.get("team_ids"): params["team_ids[]"] = args["team_ids"]
    raw = safe_list("escalation_policies", params)
    if isinstance(raw, dict) and "error" in raw:
        return raw
    items = unwrap(raw) if isinstance(raw, dict) else raw
    return {
        "total": len(items),
        "escalation_policies": [
            {
                "id": ep["id"], "name": ep["name"], "description": ep.get("description", ""),
                "num_loops": ep.get("num_loops"),
                "teams": [t.get("summary") for t in ep.get("teams", [])],
                "rules_count": len(ep.get("escalation_rules", [])),
                "html_url": ep.get("html_url"),
            }
            for ep in items
        ],
    }


@with_retry()
def tool_get_escalation_policy(args: dict) -> dict:
    try:
        return pd_client.rget(f"escalation_policies/{args['policy_id']}")
    except Exception as e:
        return {"error": str(e)}


@with_retry()
def tool_create_escalation_policy(args: dict) -> dict:
    dry = is_dry_run_action(_dry_run, f"create_escalation_policy name='{args['name']}'")
    if dry:
        return dry
    try:
        rules = []
        for rule in args.get("escalation_rules", []):
            targets = [
                {"id": tid, "type": rule.get("target_type", "user_reference")}
                for tid in rule.get("target_ids", [])
            ]
            rules.append({
                "escalation_delay_in_minutes": rule.get("escalation_delay_in_minutes", 30),
                "targets": targets,
            })
        body: dict = {"type": "escalation_policy", "name": args["name"], "escalation_rules": rules}
        if args.get("description"): body["description"] = args["description"]
        if args.get("num_loops"):   body["num_loops"] = args["num_loops"]
        if args.get("team_id"):     body["teams"] = [{"id": args["team_id"], "type": "team_reference"}]
        ep = pd_client.rpost("escalation_policies", json=body)
        return {"success": True, "escalation_policy": {"id": ep["id"], "name": ep["name"]}}
    except Exception as e:
        return {"error": str(e)}


@with_retry()
def tool_update_escalation_policy(args: dict) -> dict:
    dry = is_dry_run_action(_dry_run, f"update_escalation_policy {args['policy_id']}")
    if dry:
        return dry
    try:
        pid = args["policy_id"]
        payload: dict = {"id": pid, "type": "escalation_policy"}
        if args.get("name"):             payload["name"] = args["name"]
        if args.get("description"):      payload["description"] = args["description"]
        if args.get("num_loops") is not None: payload["num_loops"] = args["num_loops"]
        if args.get("escalation_rules"): payload["escalation_rules"] = args["escalation_rules"]
        updated = pd_client.rput(f"escalation_policies/{pid}", json=payload)
        return {"success": True, "escalation_policy": {"id": updated["id"], "name": updated["name"]}}
    except Exception as e:
        return {"error": str(e)}


@with_retry()
def tool_delete_escalation_policy(args: dict) -> dict:
    dry = is_dry_run_action(_dry_run, f"delete_escalation_policy {args['policy_id']}")
    if dry:
        return dry
    try:
        pd_client.delete(f"escalation_policies/{args['policy_id']}")
        return {"success": True, "deleted_policy_id": args["policy_id"]}
    except Exception as e:
        return {"error": str(e)}