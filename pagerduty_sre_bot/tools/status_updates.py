"""Incident status updates, subscriber management, and responder requests."""

from pagerduty_sre_bot.clients import pd_client
from pagerduty_sre_bot.helpers import safe_list, unwrap, is_dry_run_action
from pagerduty_sre_bot.retry import with_retry

_dry_run = False


def set_dry_run(v: bool) -> None:
    global _dry_run
    _dry_run = v


# ── Status Updates ─────────────────────────────────────

def tool_list_incident_status_updates(args: dict) -> dict:
    """List status updates posted to an incident."""
    raw = safe_list(f"incidents/{args['incident_id']}/status_updates")
    if isinstance(raw, dict) and "error" in raw:
        return raw
    items = unwrap(raw) if isinstance(raw, dict) else raw
    return {
        "incident_id": args["incident_id"],
        "status_updates": [
            {
                "id": u.get("id"),
                "message": u.get("message"),
                "created_at": u.get("created_at"),
                "sender": u.get("sender", {}).get("summary") if u.get("sender") else None,
                "subject": u.get("subject"),
                "html_url": u.get("html_url"),
            }
            for u in items
        ],
    }


@with_retry()
def tool_create_incident_status_update(args: dict) -> dict:
    """Send a status update on an incident to notify subscribers/stakeholders."""
    dry = is_dry_run_action(_dry_run, f"create_status_update incident={args['incident_id']}")
    if dry:
        return dry
    try:
        iid = args["incident_id"]
        body: dict = {"message": args["message"]}
        if args.get("subject"):
            body["subject"] = args["subject"]
        if args.get("html_message"):
            body["html_message"] = args["html_message"]
        resp = pd_client.post(f"incidents/{iid}/status_updates", json=body)
        if resp.status_code < 300:
            return {"success": True, "incident_id": iid, "message": "Status update sent"}
        return {"error": f"HTTP {resp.status_code}: {resp.text}"}
    except Exception as e:
        return {"error": str(e)}


# ── Notification Subscribers ───────────────────────────

@with_retry()
def tool_list_incident_notification_subscribers(args: dict) -> dict:
    """List notification subscribers on an incident."""
    try:
        resp = pd_client.get(f"incidents/{args['incident_id']}/status_updates/subscribers")
        if resp.status_code < 300:
            data = resp.json()
            subs = data.get("subscribers", [])
            return {
                "incident_id": args["incident_id"],
                "subscribers": [
                    {
                        "subscriber_id": s.get("subscriber_id"),
                        "subscriber_type": s.get("subscriber_type"),
                        "has_indirect_subscription": s.get("has_indirect_subscription"),
                        "subscribed_via": [
                            sv.get("name") for sv in s.get("subscribed_via", [])
                        ] if s.get("subscribed_via") else [],
                    }
                    for s in subs
                ],
            }
        return {"error": f"HTTP {resp.status_code}"}
    except Exception as e:
        return {"error": str(e)}


@with_retry()
def tool_add_incident_notification_subscribers(args: dict) -> dict:
    """Add subscribers (users or teams) to receive status updates for an incident."""
    dry = is_dry_run_action(_dry_run, f"add_notification_subscribers incident={args['incident_id']}")
    if dry:
        return dry
    try:
        iid = args["incident_id"]
        subscribers = [
            {"subscriber_id": s["id"], "subscriber_type": s.get("type", "user")}
            for s in args.get("subscribers", [])
        ]
        resp = pd_client.post(
            f"incidents/{iid}/status_updates/subscribers",
            json={"subscribers": subscribers},
        )
        if resp.status_code < 300:
            return {"success": True, "incident_id": iid, "subscribers_added": len(subscribers)}
        return {"error": f"HTTP {resp.status_code}: {resp.text}"}
    except Exception as e:
        return {"error": str(e)}


@with_retry()
def tool_remove_incident_notification_subscriber(args: dict) -> dict:
    """Remove a subscriber from an incident's status updates."""
    dry = is_dry_run_action(_dry_run, f"remove_notification_subscriber incident={args['incident_id']}")
    if dry:
        return dry
    try:
        iid = args["incident_id"]
        resp = pd_client.post(
            f"incidents/{iid}/status_updates/unsubscribe",
            json={
                "subscribers": [{
                    "subscriber_id": args["subscriber_id"],
                    "subscriber_type": args.get("subscriber_type", "user"),
                }]
            },
        )
        if resp.status_code < 300:
            return {"success": True, "incident_id": iid}
        return {"error": f"HTTP {resp.status_code}: {resp.text}"}
    except Exception as e:
        return {"error": str(e)}


# ── Responder Requests ─────────────────────────────────

@with_retry()
def tool_create_responder_request(args: dict) -> dict:
    """Request additional responders for an incident."""
    dry = is_dry_run_action(_dry_run, f"create_responder_request incident={args['incident_id']}")
    if dry:
        return dry
    try:
        iid = args["incident_id"]
        targets = []
        for t in args.get("targets", []):
            targets.append({
                "responder_request_target": {
                    "id": t["id"],
                    "type": t.get("type", "user_reference"),
                }
            })
        body: dict = {
            "requester_id": args["requester_id"],
            "message": args.get("message", "Your help is requested on this incident."),
            "responder_request_targets": targets,
        }
        resp = pd_client.post(f"incidents/{iid}/responder_requests", json=body)
        if resp.status_code < 300:
            data = resp.json().get("responder_request", {})
            return {
                "success": True,
                "incident_id": iid,
                "responder_request_id": data.get("id"),
                "targets_requested": len(targets),
                "message": body["message"],
            }
        return {"error": f"HTTP {resp.status_code}: {resp.text}"}
    except Exception as e:
        return {"error": str(e)}


def tool_list_responder_requests(args: dict) -> dict:
    """List responder requests for an incident."""
    try:
        resp = pd_client.get(f"incidents/{args['incident_id']}/responder_requests")
        if resp.status_code < 300:
            data = resp.json()
            reqs = data.get("responder_requests", [])
            return {
                "incident_id": args["incident_id"],
                "responder_requests": [
                    {
                        "id": r.get("id"),
                        "requester": r.get("requester", {}).get("summary") if r.get("requester") else None,
                        "message": r.get("message"),
                        "requested_at": r.get("requested_at"),
                        "targets": [
                            {
                                "id": t.get("responder_request_target", {}).get("id"),
                                "type": t.get("responder_request_target", {}).get("type"),
                                "summary": t.get("responder_request_target", {}).get("summary"),
                            }
                            for t in r.get("responder_request_targets", [])
                        ],
                    }
                    for r in reqs
                ],
            }
        return {"error": f"HTTP {resp.status_code}"}
    except Exception as e:
        return {"error": str(e)}