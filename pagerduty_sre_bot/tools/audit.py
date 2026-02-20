"""Audit record tools."""

from pagerduty_sre_bot.clients import pd_client
from pagerduty_sre_bot.helpers import MAX_RESULTS


def tool_list_audit_records(args: dict) -> dict:
    params = {}
    if args.get("since"): params["since"] = args["since"]
    if args.get("until"): params["until"] = args["until"]
    if args.get("root_resource_types"):
        params["root_resource_types[]"] = args["root_resource_types"]
    try:
        records = []
        for r in pd_client.iter_cursor("audit/records", params=params):
            records.append({
                "id": r.get("id"),
                "execution_time": r.get("execution_time"),
                "method": r.get("method", {}).get("type") if r.get("method") else None,
                "actors": [a.get("name", a.get("id")) for a in r.get("actors", [])],
                "root_resource": r.get("root_resource", {}).get("type"),
                "root_resource_name": r.get("root_resource", {}).get("name"),
                "action": r.get("action"),
            })
            if len(records) >= MAX_RESULTS:
                break
        return {"total": len(records), "audit_records": records}
    except Exception as e:
        return {"error": str(e)}