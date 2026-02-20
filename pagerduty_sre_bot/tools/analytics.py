"""Analytics and full incident analysis tools."""

from collections import Counter

from pagerduty_sre_bot.clients import pd_client
from pagerduty_sre_bot.helpers import safe_list, unwrap, MAX_RESULTS
from pagerduty_sre_bot.retry import with_retry
from pagerduty_sre_bot.time_utils import diff_minutes


@with_retry()
def tool_get_analytics_incidents(args: dict) -> dict:
    try:
        filters: dict = {}
        if args.get("since"):       filters["created_at_start"] = args["since"]
        if args.get("until"):       filters["created_at_end"] = args["until"]
        if args.get("service_ids"): filters["service_ids"] = args["service_ids"]
        if args.get("team_ids"):    filters["team_ids"] = args["team_ids"]
        if args.get("urgencies") and len(args["urgencies"]) == 1:
            filters["urgency"] = args["urgencies"][0]

        results = []
        for item in pd_client.iter_analytics_raw_incidents(filters=filters):
            results.append({
                "incident_id": item.get("id"),
                "incident_number": item.get("incident_number"),
                "title": item.get("title", item.get("description", "")),
                "urgency": item.get("urgency"),
                "status": item.get("status"),
                "service_name": item.get("service_name"),
                "created_at": item.get("created_at"),
                "resolved_at": item.get("resolved_at"),
                "seconds_to_first_ack": item.get("seconds_to_first_ack"),
                "seconds_to_resolve": item.get("seconds_to_resolve"),
                "seconds_to_engage": item.get("seconds_to_engage"),
                "engaged_seconds": item.get("engaged_seconds"),
                "escalation_count": item.get("escalation_count"),
                "assignment_count": item.get("assignment_count"),
                "engaged_user_count": item.get("engaged_user_count"),
            })
            if len(results) >= MAX_RESULTS:
                break
        return {"total": len(results), "analytics_incidents": results}
    except Exception as e:
        return {"error": str(e)}


@with_retry()
def tool_get_analytics_services(args: dict) -> dict:
    try:
        filters: dict = {}
        if args.get("since"):       filters["created_at_start"] = args["since"]
        if args.get("until"):       filters["created_at_end"] = args["until"]
        if args.get("service_ids"): filters["service_ids"] = args["service_ids"]
        if args.get("team_ids"):    filters["team_ids"] = args["team_ids"]
        resp = pd_client.post("analytics/metrics/incidents/services", json={"filters": filters})
        if resp.ok:
            return resp.json().get("data", [])
        return {"error": f"HTTP {resp.status_code}: {resp.text}"}
    except Exception as e:
        return {"error": str(e)}


@with_retry()
def tool_get_analytics_teams(args: dict) -> dict:
    try:
        filters: dict = {}
        if args.get("since"):    filters["created_at_start"] = args["since"]
        if args.get("until"):    filters["created_at_end"] = args["until"]
        if args.get("team_ids"): filters["team_ids"] = args["team_ids"]
        resp = pd_client.post("analytics/metrics/incidents/teams", json={"filters": filters})
        if resp.ok:
            return resp.json().get("data", [])
        return {"error": f"HTTP {resp.status_code}: {resp.text}"}
    except Exception as e:
        return {"error": str(e)}


def tool_full_incident_analysis(args: dict) -> dict:
    params = {
        "since": args["since"],
        "until": args["until"],
        "statuses[]": ["triggered", "acknowledged", "resolved"],
        "sort_by": "created_at:desc",
    }
    if args.get("service_ids"): params["service_ids[]"] = args["service_ids"]
    if args.get("team_ids"):    params["team_ids[]"] = args["team_ids"]

    raw = safe_list("incidents", params)
    if isinstance(raw, dict) and "error" in raw:
        return raw
    incidents = unwrap(raw) if isinstance(raw, dict) else raw

    svc_count: Counter = Counter()
    urg_count: Counter = Counter()
    sts_count: Counter = Counter()
    all_mtta: list = []
    all_mttr: list = []
    total_esc = 0
    results = []

    for inc in incidents:
        trigger = ack = resolve = None
        esc = 0
        try:
            for log in pd_client.iter_all(
                    f"incidents/{inc['id']}/log_entries", params={"is_overview": True}
            ):
                lt = log["type"]
                if lt == "trigger_log_entry":
                    trigger = log["created_at"]
                elif lt == "acknowledge_log_entry" and not ack:
                    ack = log["created_at"]
                elif lt == "resolve_log_entry":
                    resolve = log["created_at"]
                elif lt == "escalate_log_entry":
                    esc += 1
        except Exception:
            pass

        mtta = diff_minutes(trigger, ack) if trigger and ack else None
        mttr = diff_minutes(trigger, resolve) if trigger and resolve else None
        if mtta is not None:
            all_mtta.append(mtta)
        if mttr is not None:
            all_mttr.append(mttr)
        total_esc += esc

        svc = inc.get("service", {}).get("summary", "Unknown")
        svc_count[svc] += 1
        urg_count[inc.get("urgency", "unknown")] += 1
        sts_count[inc.get("status", "unknown")] += 1

        results.append({
            "id": inc["id"],
            "incident_number": inc.get("incident_number"),
            "title": inc["title"],
            "service": svc,
            "status": inc["status"],
            "urgency": inc.get("urgency"),
            "created_at": inc["created_at"],
            "mtta_minutes": mtta,
            "mttr_minutes": mttr,
            "escalations": esc,
        })

    avg_mtta = round(sum(all_mtta) / len(all_mtta), 2) if all_mtta else None
    avg_mttr = round(sum(all_mttr) / len(all_mttr), 2) if all_mttr else None

    return {
        "time_window": {"since": args["since"], "until": args["until"]},
        "summary": {
            "total_incidents": len(results),
            "status_distribution": dict(sts_count),
            "urgency_distribution": dict(urg_count),
            "service_distribution": dict(svc_count),
            "average_mtta_minutes": avg_mtta,
            "average_mttr_minutes": avg_mttr,
            "total_escalations": total_esc,
        },
        "incidents": results,
    }