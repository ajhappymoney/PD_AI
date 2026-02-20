"""Advanced analysis tools: patterns, SLA breaches, burnout, postmortem."""

import json
import difflib
from collections import Counter, defaultdict
from pathlib import Path
from datetime import timezone

from pagerduty_sre_bot.clients import pd_client, groq_client
from pagerduty_sre_bot.helpers import safe_list, unwrap, MAX_RESULTS
from pagerduty_sre_bot.time_utils import fmt_ts
from pagerduty_sre_bot.output import cprint
from pagerduty_sre_bot.tools.incidents import tool_get_incident, tool_get_incident_timeline, tool_get_incident_notes, tool_get_incident_alerts
from pagerduty_sre_bot.tools.notifications import tool_list_notifications
from pagerduty_sre_bot.tools.analytics import tool_get_analytics_incidents


def tool_generate_postmortem(args: dict, model_primary: str = "moonshotai/kimi-k2-instruct-0905") -> dict:
    """Auto-generate a structured postmortem for a resolved incident."""
    iid = args["incident_id"]

    cprint(f"[dim]  📋 Gathering incident data for {iid}…[/dim]")
    inc = tool_get_incident({"incident_id": iid})
    timeline = tool_get_incident_timeline({"incident_id": iid})
    notes = tool_get_incident_notes({"incident_id": iid})
    alerts = tool_get_incident_alerts({"incident_id": iid})

    if "error" in inc:
        return {"error": f"Could not fetch incident: {inc['error']}"}

    context = json.dumps({
        "incident": inc,
        "timeline": timeline.get("timeline_entries", [])[:50],
        "notes": notes.get("notes", []),
        "alerts": alerts.get("alerts", [])[:20],
    }, indent=2, default=str)

    prompt = (
        "You are an expert SRE writing a postmortem. Given the incident data, "
        "generate a comprehensive postmortem in Markdown with sections: "
        "Summary, Timeline, Root Cause, Impact, Contributing Factors, Detection, "
        "Response, Action Items (table), Lessons Learned."
    )

    try:
        resp = groq_client.chat.completions.create(
            model=model_primary,
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": f"Incident data:\n\n{context[:12000]}"},
            ],
            max_tokens=2000,
        )
        text = resp.choices[0].message.content or ""
    except Exception as e:
        return {"error": f"LLM postmortem generation failed: {e}"}

    filename = args.get("output_file") or f"postmortem_{iid}.md"
    try:
        Path(filename).write_text(text)
        cprint(f"[green]✅ Postmortem saved to {filename}[/green]")
    except Exception as e:
        cprint(f"[yellow]⚠  Could not save file: {e}[/yellow]")

    return {
        "success": True,
        "incident_id": iid,
        "output_file": filename,
        "postmortem_preview": text[:800] + ("…" if len(text) > 800 else ""),
    }


def tool_analyze_patterns(args: dict) -> dict:
    """Find recurring incident patterns."""
    top_n = args.get("top_n", 10)
    params = {
        "since": args["since"], "until": args["until"],
        "statuses[]": ["triggered", "acknowledged", "resolved"],
        "sort_by": "created_at:desc",
    }
    if args.get("service_ids"): params["service_ids[]"] = args["service_ids"]
    if args.get("team_ids"):    params["team_ids[]"] = args["team_ids"]

    raw = safe_list("incidents", params, MAX_RESULTS)
    incidents = unwrap(raw) if isinstance(raw, dict) else raw

    if not incidents:
        return {"message": "No incidents found in the specified window."}

    svc_counts: Counter = Counter()
    hour_counts: Counter = Counter()
    day_counts: Counter = Counter()
    urg_counts: Counter = Counter()
    titles: list = []

    for inc in incidents:
        svc = inc.get("service", {}).get("summary", "Unknown")
        svc_counts[svc] += 1
        urg_counts[inc.get("urgency", "unknown")] += 1
        ts = fmt_ts(inc.get("created_at", ""))
        if ts:
            if ts.tzinfo is None:
                ts = ts.replace(tzinfo=timezone.utc)
            hour_counts[ts.hour] += 1
            day_counts[ts.strftime("%A")] += 1
        titles.append(inc.get("title", ""))

    # Cluster similar titles
    clusters: list = []
    seen: set = set()
    for i, t1 in enumerate(titles):
        if i in seen:
            continue
        cluster = [t1]
        for j, t2 in enumerate(titles[i + 1:], start=i + 1):
            if j in seen:
                continue
            if difflib.SequenceMatcher(None, t1.lower(), t2.lower()).ratio() >= 0.6:
                cluster.append(t2)
                seen.add(j)
        if len(cluster) > 1:
            clusters.append({"representative": t1, "count": len(cluster), "similar_titles": cluster[:5]})
        seen.add(i)
    clusters.sort(key=lambda x: x["count"], reverse=True)

    peak_hours = [{"hour_utc": f"{h:02d}:00", "incident_count": c} for h, c in hour_counts.most_common(5)]

    insight = ""
    if svc_counts:
        top_svc, top_cnt = svc_counts.most_common(1)[0]
        top_hr = hour_counts.most_common(1)[0][0] if hour_counts else "N/A"
        insight = f"Top noise source: {top_svc} ({top_cnt} incidents). Peak hour: {top_hr:02d}:00 UTC."

    return {
        "window": {"since": args["since"], "until": args["until"]},
        "total_incidents_analysed": len(incidents),
        "top_noisy_services": [{"service": s, "incident_count": c} for s, c in svc_counts.most_common(top_n)],
        "urgency_distribution": dict(urg_counts),
        "peak_hours_utc": peak_hours,
        "busiest_days": [{"day": d, "count": c} for d, c in day_counts.most_common(3)],
        "recurring_title_clusters": clusters[:top_n],
        "insight": insight or "Insufficient data for pattern analysis.",
    }


def tool_check_sla_breaches(args: dict, config: dict | None = None) -> dict:
    """Find incidents that breached MTTA or MTTR SLA targets."""
    sla_mtta = (config or {}).get("sla", {}).get("mtta_minutes", 5) * 60
    sla_mttr = (config or {}).get("sla", {}).get("mttr_minutes", 60) * 60

    mtta_threshold = args.get("mtta_threshold_seconds", sla_mtta)
    mttr_threshold = args.get("mttr_threshold_seconds", sla_mttr)

    analytics = tool_get_analytics_incidents({
        "since": args["since"],
        "until": args["until"],
        "service_ids": args.get("service_ids"),
        "team_ids": args.get("team_ids"),
    })
    if "error" in analytics:
        return analytics

    breaches = []
    mtta_bc = mttr_bc = 0

    for inc in analytics.get("analytics_incidents", []):
        mtta_s = inc.get("seconds_to_first_ack")
        mttr_s = inc.get("seconds_to_resolve")
        mb = mtta_s is not None and mtta_s > mtta_threshold
        rb = mttr_s is not None and mttr_s > mttr_threshold
        if mb: mtta_bc += 1
        if rb: mttr_bc += 1
        if mb or rb:
            breaches.append({
                "incident_id": inc["incident_id"],
                "incident_number": inc.get("incident_number"),
                "title": inc.get("title"),
                "service": inc.get("service_name"),
                "urgency": inc.get("urgency"),
                "created_at": inc.get("created_at"),
                "mtta_seconds": mtta_s, "mtta_breach": mb,
                "mtta_overage_sec": round(mtta_s - mtta_threshold, 0) if mb else None,
                "mttr_seconds": mttr_s, "mttr_breach": rb,
                "mttr_overage_sec": round(mttr_s - mttr_threshold, 0) if rb else None,
            })

    total = len(analytics.get("analytics_incidents", []))
    return {
        "window": {"since": args["since"], "until": args["until"]},
        "sla_thresholds": {"mtta_seconds": mtta_threshold, "mttr_seconds": mttr_threshold},
        "total_analysed": total,
        "total_breaches": len(breaches),
        "mtta_breach_count": mtta_bc,
        "mttr_breach_count": mttr_bc,
        "breach_rate_pct": round(len(breaches) / total * 100, 1) if total else 0,
        "breaches": sorted(breaches, key=lambda x: (x.get("mtta_overage_sec") or 0) + (x.get("mttr_overage_sec") or 0), reverse=True),
    }


def tool_oncall_load_report(args: dict) -> dict:
    """Analyse paging frequency to detect on-call burnout risk."""
    notif_raw = tool_list_notifications({"since": args["since"], "until": args["until"], "include": ["users"]})
    if "error" in notif_raw:
        return notif_raw

    notifications = notif_raw.get("notifications", [])
    user_pages: Counter = Counter()
    user_after: Counter = Counter()
    user_weekend: Counter = Counter()

    for n in notifications:
        user = n.get("user") or "Unknown"
        user_pages[user] += 1
        ts_str = n.get("started_at", "")
        if ts_str:
            ts = fmt_ts(ts_str)
            if ts:
                if ts.tzinfo is None:
                    ts = ts.replace(tzinfo=timezone.utc)
                if ts.hour < 8 or ts.hour >= 22:
                    user_after[user] += 1
                if ts.weekday() >= 5:
                    user_weekend[user] += 1

    THRESHOLD = 10
    window_days = 1
    try:
        s, e = fmt_ts(args["since"]), fmt_ts(args["until"])
        if s and e:
            if s.tzinfo is None: s = s.replace(tzinfo=timezone.utc)
            if e.tzinfo is None: e = e.replace(tzinfo=timezone.utc)
            window_days = max(1, (e - s).days)
    except Exception:
        pass

    report = []
    for user, pages in user_pages.most_common():
        ppw = round(pages / window_days * 7, 1)
        ah = user_after[user]
        we = user_weekend[user]
        risk = "🔴 HIGH" if ppw > THRESHOLD else "🟡 MEDIUM" if ppw > THRESHOLD * 0.6 else "🟢 LOW"
        report.append({
            "user": user, "total_pages": pages, "pages_per_week": ppw,
            "after_hours_pages": ah, "weekend_pages": we,
            "after_hours_pct": round(ah / pages * 100, 1) if pages else 0,
            "burnout_risk": risk,
        })

    return {
        "window": {"since": args["since"], "until": args["until"], "days": window_days},
        "total_notifications": len(notifications),
        "users_paged": len(report),
        "burnout_threshold": f"{THRESHOLD} pages/week",
        "on_call_load": report,
        "high_risk_users": [r["user"] for r in report if "HIGH" in r["burnout_risk"]],
    }