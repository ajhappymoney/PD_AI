"""Tool dispatch registry — maps tool names to implementations."""

# ── Existing tools ────────────────────────────────────
from pagerduty_sre_bot.tools.incidents import (
    tool_list_incidents, tool_get_incident, tool_get_incident_timeline,
    tool_get_incident_notes, tool_get_incident_alerts,
    tool_manage_incident, tool_create_incident,
)
from pagerduty_sre_bot.tools.services import (
    tool_list_services, tool_get_service, tool_create_service,
    tool_update_service, tool_delete_service,
    tool_list_service_integrations, tool_create_service_integration,
)
from pagerduty_sre_bot.tools.users import (
    tool_list_users, tool_get_user, tool_create_user,
    tool_update_user, tool_delete_user,
    tool_get_user_contact_methods, tool_get_user_notification_rules,
)
from pagerduty_sre_bot.tools.teams import (
    tool_list_teams, tool_get_team, tool_create_team,
    tool_update_team, tool_delete_team,
    tool_manage_team_membership, tool_list_team_members,
)
from pagerduty_sre_bot.tools.escalation import (
    tool_list_escalation_policies, tool_get_escalation_policy,
    tool_create_escalation_policy, tool_update_escalation_policy,
    tool_delete_escalation_policy,
)
from pagerduty_sre_bot.tools.schedules import (
    tool_list_schedules, tool_get_schedule,
    tool_create_schedule, tool_update_schedule, tool_delete_schedule,
    tool_list_schedule_overrides, tool_create_schedule_override,
    tool_delete_schedule_override, tool_list_schedule_users_on_call,
)
from pagerduty_sre_bot.tools.oncalls import tool_list_oncalls
from pagerduty_sre_bot.tools.analytics import (
    tool_get_analytics_incidents, tool_get_analytics_services,
    tool_get_analytics_teams, tool_full_incident_analysis,
)
from pagerduty_sre_bot.tools.maintenance import (
    tool_list_maintenance_windows, tool_create_maintenance_window,
    tool_delete_maintenance_window,
)
from pagerduty_sre_bot.tools.notifications import tool_list_log_entries, tool_list_notifications
from pagerduty_sre_bot.tools.audit import tool_list_audit_records
from pagerduty_sre_bot.tools.config_resources import (
    tool_list_tags, tool_manage_tags, tool_list_vendors,
    tool_list_response_plays, tool_list_business_services,
    tool_get_business_service, tool_get_service_dependencies,
    tool_list_status_dashboards,
    tool_list_rulesets, tool_list_webhook_subscriptions,
    tool_create_webhook_subscription, tool_list_abilities,
    tool_list_extensions, tool_list_incident_workflows,
    tool_list_priorities,
)
from pagerduty_sre_bot.tools.analysis import (
    tool_generate_postmortem, tool_analyze_patterns,
    tool_check_sla_breaches, tool_oncall_load_report,
)
from pagerduty_sre_bot.tools.utility import tool_resolve_time

# ── NEW: 7 feature areas ─────────────────────────────
from pagerduty_sre_bot.tools.events import tool_send_event, tool_send_change_event
from pagerduty_sre_bot.tools.alerts import (
    tool_list_alerts, tool_get_alert, tool_update_alert, tool_manage_incident_alerts,
)
from pagerduty_sre_bot.tools.status_updates import (
    tool_list_incident_status_updates, tool_create_incident_status_update,
    tool_add_incident_notification_subscribers,
    tool_create_responder_request, tool_list_responder_requests,
)
from pagerduty_sre_bot.tools.custom_fields import (
    tool_list_custom_fields, tool_get_custom_field,
    tool_create_custom_field, tool_update_custom_field, tool_delete_custom_field,
    tool_get_incident_custom_field_values, tool_set_incident_custom_field_values,
)
from pagerduty_sre_bot.tools.automation import (
    tool_list_automation_actions, tool_get_automation_action,
    tool_create_automation_action, tool_invoke_automation_action,
    tool_list_automation_runners,
)
from pagerduty_sre_bot.tools.orchestration import (
    tool_list_event_orchestrations,
    tool_get_event_orchestration, tool_create_event_orchestration,
    tool_update_event_orchestration, tool_delete_event_orchestration,
    tool_get_orchestration_router, tool_update_orchestration_router,
    tool_get_service_orchestration, tool_update_service_orchestration,
)


TOOL_DISPATCH: dict[str, callable] = {
    # Incidents
    "list_incidents":              tool_list_incidents,
    "get_incident":                tool_get_incident,
    "get_incident_timeline":       tool_get_incident_timeline,
    "get_incident_notes":          tool_get_incident_notes,
    "get_incident_alerts":         tool_get_incident_alerts,
    "manage_incident":             tool_manage_incident,
    "create_incident":             tool_create_incident,
    # Services
    "list_services":               tool_list_services,
    "get_service":                 tool_get_service,
    "create_service":              tool_create_service,
    "update_service":              tool_update_service,
    "delete_service":              tool_delete_service,
    "list_service_integrations":   tool_list_service_integrations,
    "create_service_integration":  tool_create_service_integration,
    # Users
    "list_users":                  tool_list_users,
    "get_user":                    tool_get_user,
    "create_user":                 tool_create_user,
    "update_user":                 tool_update_user,
    "delete_user":                 tool_delete_user,
    "get_user_contact_methods":    tool_get_user_contact_methods,
    "get_user_notification_rules": tool_get_user_notification_rules,
    # Teams
    "list_teams":                  tool_list_teams,
    "get_team":                    tool_get_team,
    "create_team":                 tool_create_team,
    "update_team":                 tool_update_team,
    "delete_team":                 tool_delete_team,
    "manage_team_membership":      tool_manage_team_membership,
    "list_team_members":           tool_list_team_members,
    # Escalation Policies
    "list_escalation_policies":    tool_list_escalation_policies,
    "get_escalation_policy":       tool_get_escalation_policy,
    "create_escalation_policy":    tool_create_escalation_policy,
    "update_escalation_policy":    tool_update_escalation_policy,
    "delete_escalation_policy":    tool_delete_escalation_policy,
    # Schedules (now with create/update/delete)
    "list_schedules":              tool_list_schedules,
    "get_schedule":                tool_get_schedule,
    "create_schedule":             tool_create_schedule,
    "update_schedule":             tool_update_schedule,
    "delete_schedule":             tool_delete_schedule,
    "list_schedule_overrides":     tool_list_schedule_overrides,
    "create_schedule_override":    tool_create_schedule_override,
    "delete_schedule_override":    tool_delete_schedule_override,
    "list_schedule_users_on_call": tool_list_schedule_users_on_call,
    # On-Calls
    "list_oncalls":                tool_list_oncalls,
    # Priorities / Maintenance / Notifications / Logs
    "list_priorities":             tool_list_priorities,
    "list_maintenance_windows":    tool_list_maintenance_windows,
    "create_maintenance_window":   tool_create_maintenance_window,
    "delete_maintenance_window":   tool_delete_maintenance_window,
    "list_log_entries":            tool_list_log_entries,
    "list_notifications":          tool_list_notifications,
    # Analytics
    "get_analytics_incidents":     tool_get_analytics_incidents,
    "get_analytics_services":      tool_get_analytics_services,
    "get_analytics_teams":         tool_get_analytics_teams,
    "full_incident_analysis":      tool_full_incident_analysis,
    # Config resources
    "list_tags":                   tool_list_tags,
    "manage_tags":                 tool_manage_tags,
    "list_vendors":                tool_list_vendors,
    "list_response_plays":         tool_list_response_plays,
    "list_business_services":      tool_list_business_services,
    "get_business_service":        tool_get_business_service,
    "get_service_dependencies":    tool_get_service_dependencies,
    "list_status_dashboards":      tool_list_status_dashboards,
    "list_audit_records":          tool_list_audit_records,
    "list_rulesets":               tool_list_rulesets,
    "list_webhook_subscriptions":  tool_list_webhook_subscriptions,
    "create_webhook_subscription": tool_create_webhook_subscription,
    "list_abilities":              tool_list_abilities,
    "list_extensions":             tool_list_extensions,
    "list_incident_workflows":     tool_list_incident_workflows,
    # Analysis
    "resolve_time":                tool_resolve_time,
    "generate_postmortem":         tool_generate_postmortem,
    "analyze_patterns":            tool_analyze_patterns,
    "check_sla_breaches":          tool_check_sla_breaches,
    "oncall_load_report":          tool_oncall_load_report,
    # ═══ NEW: Events API v2 ══════════════════════════
    "send_event":                  tool_send_event,
    "send_change_event":           tool_send_change_event,
    # ═══ NEW: Alerts Management ══════════════════════
    "list_alerts":                 tool_list_alerts,
    "get_alert":                   tool_get_alert,
    "update_alert":                tool_update_alert,
    "manage_incident_alerts":      tool_manage_incident_alerts,
    # ═══ NEW: Status Updates & Responders ════════════
    "list_incident_status_updates":           tool_list_incident_status_updates,
    "create_incident_status_update":          tool_create_incident_status_update,
    "add_incident_notification_subscribers":  tool_add_incident_notification_subscribers,
    "create_responder_request":               tool_create_responder_request,
    "list_responder_requests":                tool_list_responder_requests,
    # ═══ NEW: Custom Fields ══════════════════════════
    "list_custom_fields":                 tool_list_custom_fields,
    "get_custom_field":                   tool_get_custom_field,
    "create_custom_field":                tool_create_custom_field,
    "update_custom_field":                tool_update_custom_field,
    "delete_custom_field":                tool_delete_custom_field,
    "get_incident_custom_field_values":   tool_get_incident_custom_field_values,
    "set_incident_custom_field_values":   tool_set_incident_custom_field_values,
    # ═══ NEW: Automation Actions ═════════════════════
    "list_automation_actions":       tool_list_automation_actions,
    "get_automation_action":         tool_get_automation_action,
    "create_automation_action":      tool_create_automation_action,
    "invoke_automation_action":      tool_invoke_automation_action,
    "list_automation_runners":       tool_list_automation_runners,
    # ═══ NEW: Event Orchestration Full CRUD ══════════
    "list_event_orchestrations":     tool_list_event_orchestrations,
    "get_event_orchestration":       tool_get_event_orchestration,
    "create_event_orchestration":    tool_create_event_orchestration,
    "update_event_orchestration":    tool_update_event_orchestration,
    "delete_event_orchestration":    tool_delete_event_orchestration,
    "get_orchestration_router":      tool_get_orchestration_router,
    "update_orchestration_router":   tool_update_orchestration_router,
    "get_service_orchestration":     tool_get_service_orchestration,
    "update_service_orchestration":  tool_update_service_orchestration,
}


def execute_tool(name: str, args: dict) -> dict:
    """Dispatch a tool call with safe error handling."""
    fn = TOOL_DISPATCH.get(name)
    if not fn:
        return {"error": f"Unknown tool: {name}"}
    try:
        return fn(args)
    except Exception as e:
        return {"error": f"Tool '{name}' execution failed: {e}"}