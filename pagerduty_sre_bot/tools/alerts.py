"""Alerts management — list, get, update, and bulk-manage alerts."""

from pagerduty_sre_bot.clients import pd_client
from pagerduty_sre_bot.helpers import safe_list, unwrap, is_dry_run_action
from pagerduty_sre_bot.retry import with_retry

_dry_run = False


def set_dry_run(v: bool) -> None:
    global _dry_run
    _dry_run = v


def tool_list_alerts(args: dict) -> dict:
    """List alerts account-wide or filtered by service/time."""
    params: dict = {}
    if args.get("since"):       params["since"] = args["since"]
    if args.get("until"):       params["until"] = args["until"]
    if args.get("statuses"):    params["statuses[]"] = args["statuses"]
    if args.get("service_ids"): params["service_ids[]"] = args["service_ids"]
    if args.get("sort_by"):     params["sort_by"] = args["sort_by"]

    raw = safe_list("alerts", params, args.get("limit", 25))
    if isinstance(raw, dict) and "error" in raw:
        return raw

    items = unwrap(raw) if isinstance(raw, dict) else raw
    truncated = isinstance(raw, dict) and raw.get("truncated", False)

    results = [
        {
            "id": a["id"],
            "status": a["status"],
            "severity": a.get("severity"),
            "summary": a.get("summary"),
            "created_at": a["created_at"],
            "service": a.get("service", {}).get("summary") if a.get("service") else None,
            "incident": {
                "id": a.get("incident", {}).get("id"),
                "summary": a.get("incident", {}).get("summary"),
            } if a.get("incident") else None,
            "suppressed": a.get("suppressed"),
            "alert_key": a.get("alert_key"),
        }
        for a in items
    ]
    out = {"total": len(results), "alerts": results}
    if truncated:
        out["truncated"] = True
    return out


@with_retry()
def tool_get_alert(args: dict) -> dict:
    """Get a single alert by incident ID and alert ID."""
    try:
        alert = pd_client.rget(f"incidents/{args['incident_id']}/alerts/{args['alert_id']}")
        return {
            "id": alert["id"], "status": alert["status"],
            "severity": alert.get("severity"), "summary": alert.get("summary"),
            "created_at": alert["created_at"],
            "body": alert.get("body"),
            "incident": alert.get("incident"),
            "service": alert.get("service"),
            "suppressed": alert.get("suppressed"),
            "alert_key": alert.get("alert_key"),
        }
    except Exception as e:
        return {"error": str(e)}


@with_retry()
def tool_update_alert(args: dict) -> dict:
    """Update an alert — typically to resolve it."""
    dry = is_dry_run_action(_dry_run, f"update_alert {args.get('alert_id')} → {args.get('status')}")
    if dry:
        return dry
    try:
        iid = args["incident_id"]
        aid = args["alert_id"]
        payload = {"id": aid, "type": "alert", "status": args.get("status", "resolved")}
        updated = pd_client.rput(f"incidents/{iid}/alerts/{aid}", json=payload)
        return {"success": True, "alert": {"id": updated["id"], "status": updated.get("status")}}
    except Exception as e:
        return {"error": str(e)}


@with_retry()
def tool_manage_incident_alerts(args: dict) -> dict:
    """Bulk-update alerts on an incident (e.g. resolve all alerts)."""
    dry = is_dry_run_action(_dry_run, f"manage_incident_alerts incident={args.get('incident_id')}")
    if dry:
        return dry
    try:
        iid = args["incident_id"]
        status = args.get("status", "resolved")
        alerts_payload = [
            {"id": aid, "type": "alert", "status": status}
            for aid in args.get("alert_ids", [])
        ]
        if not alerts_payload:
            return {"error": "No alert_ids provided"}
        pd_client.rput(f"incidents/{iid}/alerts", json=alerts_payload)
        return {"success": True, "incident_id": iid, "alerts_updated": len(alerts_payload), "new_status": status}
    except Exception as e:
        return {"error": str(e)}