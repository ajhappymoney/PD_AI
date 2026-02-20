"""Dynamic tool selection — routes queries to relevant tool subsets."""

from pagerduty_sre_bot.schemas import TOOLS
from pagerduty_sre_bot.output import cprint

TOOL_GROUPS: dict[str, list[str]] = {
    "incident": [
        "list_incidents", "get_incident", "get_incident_timeline",
        "get_incident_notes", "get_incident_alerts",
        "manage_incident", "create_incident",
    ],
    "service": [
        "list_services", "get_service", "create_service",
        "update_service", "delete_service",
        "list_service_integrations", "create_service_integration",
    ],
    "oncall": [
        "list_oncalls", "list_schedules", "get_schedule",
        "create_schedule", "update_schedule", "delete_schedule",
        "list_schedule_overrides", "create_schedule_override",
        "delete_schedule_override", "list_schedule_users_on_call",
    ],
    "user": [
        "list_users", "get_user", "create_user", "update_user", "delete_user",
        "get_user_contact_methods", "get_user_notification_rules",
    ],
    "team": [
        "list_teams", "get_team", "create_team", "update_team", "delete_team",
        "manage_team_membership", "list_team_members",
    ],
    "escalation": [
        "list_escalation_policies", "get_escalation_policy",
        "create_escalation_policy", "update_escalation_policy",
        "delete_escalation_policy",
    ],
    "analytics": [
        "get_analytics_incidents", "get_analytics_services", "get_analytics_teams",
        "full_incident_analysis", "analyze_patterns",
        "check_sla_breaches", "oncall_load_report",
    ],
    "maintenance": [
        "list_maintenance_windows", "create_maintenance_window",
        "delete_maintenance_window",
    ],
    "notification": ["list_notifications", "list_log_entries"],
    "audit": ["list_audit_records"],
    "postmortem": ["generate_postmortem"],
    "config": [
        "list_tags", "manage_tags", "list_vendors", "list_response_plays",
        "list_business_services", "get_business_service",
        "get_service_dependencies", "list_status_dashboards",
        "list_rulesets", "list_webhook_subscriptions",
        "create_webhook_subscription", "list_abilities",
        "list_extensions", "list_incident_workflows", "list_priorities",
    ],
    "utility": ["resolve_time"],
    # ═══ NEW GROUPS ══════════════════════════════════
    "events_api": [
        "send_event", "send_change_event",
    ],
    "alerts": [
        "list_alerts", "get_alert", "update_alert", "manage_incident_alerts",
    ],
    "status_updates": [
        "list_incident_status_updates", "create_incident_status_update",
        "add_incident_notification_subscribers",
        "create_responder_request", "list_responder_requests",
    ],
    "custom_fields": [
        "list_custom_fields", "get_custom_field",
        "create_custom_field", "update_custom_field", "delete_custom_field",
        "get_incident_custom_field_values", "set_incident_custom_field_values",
    ],
    "automation": [
        "list_automation_actions", "get_automation_action",
        "create_automation_action", "invoke_automation_action",
        "list_automation_runners",
    ],
    "orchestration": [
        "list_event_orchestrations", "get_event_orchestration",
        "create_event_orchestration", "update_event_orchestration",
        "delete_event_orchestration",
        "get_orchestration_router", "update_orchestration_router",
        "get_service_orchestration", "update_service_orchestration",
    ],
}

_KEYWORD_RULES: list[tuple[set[str], list[str]]] = [
    # ── New feature keywords ──
    ({"event api", "send event", "trigger event", "trigger alert", "routing key",
      "dedup", "change event", "deployment event"},
     ["events_api", "service", "utility"]),
    ({"alert", "alerts", "suppressed", "resolve alert", "update alert"},
     ["alerts", "incident", "utility"]),
    ({"status update", "stakeholder", "subscriber", "notify stakeholders",
      "communication", "status report"},
     ["status_updates", "incident", "utility"]),
    ({"responder", "page someone", "add responder", "request help",
      "responder request", "page the"},
     ["status_updates", "incident", "user", "utility"]),
    ({"custom field", "custom fields", "field value", "incident field",
      "set field", "get field"},
     ["custom_fields", "incident", "utility"]),
    ({"automation", "automation action", "runbook", "runner", "invoke",
      "run action", "diagnostics", "remediation"},
     ["automation", "utility"]),
    ({"orchestration", "routing rule", "service orchestration", "event rule",
      "unrouted", "orchestration rule"},
     ["orchestration", "service", "utility"]),
    # ── Existing keywords ──
    ({"postmortem", "post-mortem", "post mortem"}, ["postmortem", "incident", "utility"]),
    ({"incident", "incidents", "page", "ack", "acknowledge",
      "resolve", "trigger", "triggered", "rca", "root cause"},
     ["incident", "utility"]),
    ({"who is on call", "on call", "oncall", "on-call", "schedule", "override",
      "shift", "rotation", "create schedule", "update schedule"},
     ["oncall", "utility"]),
    ({"service", "services", "integration", "integrations", "maintenance", "maint"},
     ["service", "maintenance", "utility"]),
    ({"user", "users", "contact", "notification rule"}, ["user", "utility"]),
    ({"team", "teams", "member", "members", "membership"}, ["team", "utility"]),
    ({"escalation", "policy", "policies"}, ["escalation", "utility"]),
    ({"analytics", "mtta", "mttr", "report", "summary", "sla", "breach",
      "pattern", "patterns", "burnout", "load report", "analysis", "last", "days",
      "hours", "week", "month"},
     ["analytics", "incident", "utility"]),
    ({"notification", "paged", "log entry", "log entries"}, ["notification", "utility"]),
    ({"audit", "audit log", "config change"}, ["audit", "utility"]),
    ({"webhook", "extension", "vendor", "ruleset",
      "workflow", "ability", "feature", "tag", "business service", "dependency"},
     ["config", "utility"]),
]

_TOOL_BY_NAME: dict[str, dict] = {t["function"]["name"]: t for t in TOOLS}


def select_tools_for_query(query: str) -> list[dict]:
    """Return minimal subset of TOOLS relevant to this query."""
    q = query.lower()
    selected_groups: set[str] = {"utility"}

    for keywords, groups in _KEYWORD_RULES:
        if any(kw in q for kw in keywords):
            selected_groups.update(groups)

    if selected_groups == {"utility"}:
        selected_groups.update(["incident", "analytics", "utility"])

    tool_names: set[str] = set()
    for group in selected_groups:
        tool_names.update(TOOL_GROUPS.get(group, []))

    selected = [_TOOL_BY_NAME[n] for n in tool_names if n in _TOOL_BY_NAME]
    cprint(f"  [dim]Tool routing: {', '.join(sorted(selected_groups))} → {len(selected)} tools[/dim]")
    return selected