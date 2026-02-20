"""Groq function-calling tool schemas (JSON definitions).

All tool schemas live in this single file. TOOLS is the complete list
used by the LLM conversation loop and tool router.
"""

TOOLS: list[dict] = [
    # ── Incidents ─────────────────────────────────────
    {
        "type": "function",
        "function": {
            "name": "list_incidents",
            "description": "List incidents within a time window, optionally filtered by status, urgency, service, or team.",
            "parameters": {
                "type": "object",
                "properties": {
                    "since":       {"type": "string", "description": "ISO8601 start time"},
                    "until":       {"type": "string", "description": "ISO8601 end time"},
                    "statuses":    {"type": "array", "items": {"type": "string", "enum": ["triggered","acknowledged","resolved"]}},
                    "urgencies":   {"type": "array", "items": {"type": "string", "enum": ["high","low"]}},
                    "service_ids": {"type": "array", "items": {"type": "string"}},
                    "team_ids":    {"type": "array", "items": {"type": "string"}},
                    "sort_by":     {"type": "string", "enum": ["created_at","resolved_at","urgency"]},
                    "limit":       {"type": "integer"},
                },
                "required": ["since", "until"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_incident",
            "description": "Get full details of a single incident by ID.",
            "parameters": {
                "type": "object",
                "properties": {"incident_id": {"type": "string"}},
                "required": ["incident_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_incident_timeline",
            "description": "Get the full log-entry timeline for an incident.",
            "parameters": {
                "type": "object",
                "properties": {"incident_id": {"type": "string"}},
                "required": ["incident_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_incident_notes",
            "description": "Get notes/annotations added to an incident.",
            "parameters": {
                "type": "object",
                "properties": {"incident_id": {"type": "string"}},
                "required": ["incident_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_incident_alerts",
            "description": "Get alerts associated with an incident.",
            "parameters": {
                "type": "object",
                "properties": {"incident_id": {"type": "string"}},
                "required": ["incident_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "manage_incident",
            "description": "Update an incident: acknowledge, resolve, reassign, change urgency, merge, snooze, or add a note.",
            "parameters": {
                "type": "object",
                "properties": {
                    "incident_id":     {"type": "string"},
                    "action":          {"type": "string", "enum": ["acknowledge","resolve","reassign","change_urgency","snooze","add_note","merge"]},
                    "assignee_id":     {"type": "string"},
                    "assignee_type":   {"type": "string", "enum": ["user_reference","escalation_policy_reference"]},
                    "urgency":         {"type": "string", "enum": ["high","low"]},
                    "snooze_duration": {"type": "integer", "description": "Snooze duration in seconds."},
                    "note_content":    {"type": "string"},
                    "merge_ids":       {"type": "array", "items": {"type": "string"}},
                },
                "required": ["incident_id", "action"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "create_incident",
            "description": "Create a new incident on a service.",
            "parameters": {
                "type": "object",
                "properties": {
                    "title":                {"type": "string"},
                    "service_id":           {"type": "string"},
                    "urgency":              {"type": "string", "enum": ["high","low"]},
                    "body":                 {"type": "string"},
                    "escalation_policy_id": {"type": "string"},
                    "priority_id":          {"type": "string"},
                },
                "required": ["title", "service_id"],
            },
        },
    },
    # ── Services ──────────────────────────────────────
    {
        "type": "function",
        "function": {
            "name": "list_services",
            "description": "List all services, optionally filtered by team or name.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query":    {"type": "string"},
                    "team_ids": {"type": "array", "items": {"type": "string"}},
                    "include":  {"type": "array", "items": {"type": "string", "enum": ["escalation_policies","teams","integrations"]}},
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_service",
            "description": "Get details of a single service by ID.",
            "parameters": {
                "type": "object",
                "properties": {
                    "service_id": {"type": "string"},
                    "include":    {"type": "array", "items": {"type": "string", "enum": ["escalation_policies","teams","integrations"]}},
                },
                "required": ["service_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "create_service",
            "description": "Create a new PagerDuty service.",
            "parameters": {
                "type": "object",
                "properties": {
                    "name":                 {"type": "string"},
                    "description":          {"type": "string"},
                    "escalation_policy_id": {"type": "string"},
                    "urgency_rule":         {"type": "string", "enum": ["high","low","severity_based"]},
                    "alert_creation":       {"type": "string", "enum": ["create_incidents","create_alerts_and_incidents"]},
                },
                "required": ["name", "escalation_policy_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "update_service",
            "description": "Update an existing service.",
            "parameters": {
                "type": "object",
                "properties": {
                    "service_id":           {"type": "string"},
                    "name":                 {"type": "string"},
                    "description":          {"type": "string"},
                    "escalation_policy_id": {"type": "string"},
                    "status":               {"type": "string", "enum": ["active","warning","critical","maintenance","disabled"]},
                },
                "required": ["service_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "delete_service",
            "description": "Delete a service by ID. WARNING: irreversible.",
            "parameters": {
                "type": "object",
                "properties": {"service_id": {"type": "string"}},
                "required": ["service_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_service_integrations",
            "description": "List integrations for a service.",
            "parameters": {
                "type": "object",
                "properties": {"service_id": {"type": "string"}},
                "required": ["service_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "create_service_integration",
            "description": "Create a new integration on a service.",
            "parameters": {
                "type": "object",
                "properties": {
                    "service_id": {"type": "string"},
                    "name":       {"type": "string"},
                    "type":       {"type": "string"},
                    "vendor_id":  {"type": "string"},
                },
                "required": ["service_id", "name", "type"],
            },
        },
    },
    # ── Users ─────────────────────────────────────────
    {
        "type": "function",
        "function": {
            "name": "list_users",
            "description": "List users in the account.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query":    {"type": "string"},
                    "team_ids": {"type": "array", "items": {"type": "string"}},
                    "include":  {"type": "array", "items": {"type": "string", "enum": ["contact_methods","notification_rules","teams"]}},
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_user",
            "description": "Get detailed profile info for a user by ID.",
            "parameters": {
                "type": "object",
                "properties": {
                    "user_id": {"type": "string"},
                    "include": {"type": "array", "items": {"type": "string", "enum": ["contact_methods","notification_rules","teams"]}},
                },
                "required": ["user_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "create_user",
            "description": "Create a new user in PagerDuty.",
            "parameters": {
                "type": "object",
                "properties": {
                    "name":      {"type": "string"},
                    "email":     {"type": "string"},
                    "role":      {"type": "string", "enum": ["admin","limited_user","observer","owner","read_only_limited_user","read_only_user","restricted_access","user"]},
                    "time_zone": {"type": "string"},
                    "job_title": {"type": "string"},
                },
                "required": ["name", "email"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "update_user",
            "description": "Update a user's profile.",
            "parameters": {
                "type": "object",
                "properties": {
                    "user_id":   {"type": "string"},
                    "name":      {"type": "string"},
                    "email":     {"type": "string"},
                    "role":      {"type": "string"},
                    "job_title": {"type": "string"},
                    "time_zone": {"type": "string"},
                },
                "required": ["user_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "delete_user",
            "description": "Delete a user. WARNING: irreversible.",
            "parameters": {
                "type": "object",
                "properties": {"user_id": {"type": "string"}},
                "required": ["user_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_user_contact_methods",
            "description": "Get contact methods for a user.",
            "parameters": {
                "type": "object",
                "properties": {"user_id": {"type": "string"}},
                "required": ["user_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_user_notification_rules",
            "description": "Get notification rules for a user.",
            "parameters": {
                "type": "object",
                "properties": {"user_id": {"type": "string"}},
                "required": ["user_id"],
            },
        },
    },
    # ── Teams ─────────────────────────────────────────
    {
        "type": "function",
        "function": {
            "name": "list_teams",
            "description": "List all teams.",
            "parameters": {
                "type": "object",
                "properties": {"query": {"type": "string"}},
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_team",
            "description": "Get details of a team by ID.",
            "parameters": {
                "type": "object",
                "properties": {"team_id": {"type": "string"}},
                "required": ["team_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "create_team",
            "description": "Create a new team.",
            "parameters": {
                "type": "object",
                "properties": {
                    "name":        {"type": "string"},
                    "description": {"type": "string"},
                },
                "required": ["name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "update_team",
            "description": "Update an existing team.",
            "parameters": {
                "type": "object",
                "properties": {
                    "team_id":     {"type": "string"},
                    "name":        {"type": "string"},
                    "description": {"type": "string"},
                },
                "required": ["team_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "delete_team",
            "description": "Delete a team. WARNING: irreversible.",
            "parameters": {
                "type": "object",
                "properties": {"team_id": {"type": "string"}},
                "required": ["team_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "manage_team_membership",
            "description": "Add or remove a user from a team.",
            "parameters": {
                "type": "object",
                "properties": {
                    "team_id": {"type": "string"},
                    "user_id": {"type": "string"},
                    "action":  {"type": "string", "enum": ["add","remove"]},
                    "role":    {"type": "string", "enum": ["manager","responder","observer"]},
                },
                "required": ["team_id", "user_id", "action"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_team_members",
            "description": "List all members of a team.",
            "parameters": {
                "type": "object",
                "properties": {"team_id": {"type": "string"}},
                "required": ["team_id"],
            },
        },
    },
    # ── Escalation Policies ───────────────────────────
    {
        "type": "function",
        "function": {
            "name": "list_escalation_policies",
            "description": "List escalation policies.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query":    {"type": "string"},
                    "team_ids": {"type": "array", "items": {"type": "string"}},
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_escalation_policy",
            "description": "Get full details of an escalation policy.",
            "parameters": {
                "type": "object",
                "properties": {"policy_id": {"type": "string"}},
                "required": ["policy_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "create_escalation_policy",
            "description": "Create a new escalation policy.",
            "parameters": {
                "type": "object",
                "properties": {
                    "name":             {"type": "string"},
                    "description":      {"type": "string"},
                    "num_loops":        {"type": "integer"},
                    "escalation_rules": {"type": "array", "items": {"type": "object"}},
                    "team_id":          {"type": "string"},
                },
                "required": ["name", "escalation_rules"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "update_escalation_policy",
            "description": "Update an escalation policy.",
            "parameters": {
                "type": "object",
                "properties": {
                    "policy_id":        {"type": "string"},
                    "name":             {"type": "string"},
                    "description":      {"type": "string"},
                    "num_loops":        {"type": "integer"},
                    "escalation_rules": {"type": "array", "items": {"type": "object"}},
                },
                "required": ["policy_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "delete_escalation_policy",
            "description": "Delete an escalation policy.",
            "parameters": {
                "type": "object",
                "properties": {"policy_id": {"type": "string"}},
                "required": ["policy_id"],
            },
        },
    },
    # ── Schedules ─────────────────────────────────────
    {
        "type": "function",
        "function": {
            "name": "list_schedules",
            "description": "List all on-call schedules.",
            "parameters": {
                "type": "object",
                "properties": {"query": {"type": "string"}},
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_schedule",
            "description": "Get details of a schedule including rendered on-call entries.",
            "parameters": {
                "type": "object",
                "properties": {
                    "schedule_id": {"type": "string"},
                    "since":       {"type": "string"},
                    "until":       {"type": "string"},
                },
                "required": ["schedule_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_schedule_overrides",
            "description": "List overrides on a schedule.",
            "parameters": {
                "type": "object",
                "properties": {
                    "schedule_id": {"type": "string"},
                    "since":       {"type": "string"},
                    "until":       {"type": "string"},
                },
                "required": ["schedule_id", "since", "until"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "create_schedule_override",
            "description": "Create an override on a schedule (swap on-call).",
            "parameters": {
                "type": "object",
                "properties": {
                    "schedule_id": {"type": "string"},
                    "user_id":     {"type": "string"},
                    "start":       {"type": "string"},
                    "end":         {"type": "string"},
                },
                "required": ["schedule_id", "user_id", "start", "end"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "delete_schedule_override",
            "description": "Delete a schedule override.",
            "parameters": {
                "type": "object",
                "properties": {
                    "schedule_id": {"type": "string"},
                    "override_id": {"type": "string"},
                },
                "required": ["schedule_id", "override_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_schedule_users_on_call",
            "description": "List users currently on call for a schedule.",
            "parameters": {
                "type": "object",
                "properties": {
                    "schedule_id": {"type": "string"},
                    "since":       {"type": "string"},
                    "until":       {"type": "string"},
                },
                "required": ["schedule_id"],
            },
        },
    },
    # ── On-Calls ──────────────────────────────────────
    {
        "type": "function",
        "function": {
            "name": "list_oncalls",
            "description": "List current on-call entries across all or specific escalation policies/schedules.",
            "parameters": {
                "type": "object",
                "properties": {
                    "schedule_ids":          {"type": "array", "items": {"type": "string"}},
                    "escalation_policy_ids": {"type": "array", "items": {"type": "string"}},
                    "user_ids":              {"type": "array", "items": {"type": "string"}},
                    "since":                 {"type": "string"},
                    "until":                 {"type": "string"},
                    "earliest":              {"type": "boolean"},
                },
                "required": [],
            },
        },
    },
    # ── Priorities ────────────────────────────────────
    {
        "type": "function",
        "function": {
            "name": "list_priorities",
            "description": "List all incident priority levels.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    # ── Maintenance Windows ───────────────────────────
    {
        "type": "function",
        "function": {
            "name": "list_maintenance_windows",
            "description": "List maintenance windows.",
            "parameters": {
                "type": "object",
                "properties": {
                    "service_ids": {"type": "array", "items": {"type": "string"}},
                    "team_ids":    {"type": "array", "items": {"type": "string"}},
                    "filter":      {"type": "string", "enum": ["past","future","ongoing","open","all"]},
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "create_maintenance_window",
            "description": "Create a maintenance window on one or more services.",
            "parameters": {
                "type": "object",
                "properties": {
                    "start_time":  {"type": "string"},
                    "end_time":    {"type": "string"},
                    "description": {"type": "string"},
                    "service_ids": {"type": "array", "items": {"type": "string"}},
                },
                "required": ["start_time", "end_time", "service_ids"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "delete_maintenance_window",
            "description": "Delete/end a maintenance window.",
            "parameters": {
                "type": "object",
                "properties": {"window_id": {"type": "string"}},
                "required": ["window_id"],
            },
        },
    },
    # ── Log Entries ───────────────────────────────────
    {
        "type": "function",
        "function": {
            "name": "list_log_entries",
            "description": "List account-wide log entries (audit trail).",
            "parameters": {
                "type": "object",
                "properties": {
                    "since":       {"type": "string"},
                    "until":       {"type": "string"},
                    "is_overview": {"type": "boolean"},
                },
                "required": [],
            },
        },
    },
    # ── Notifications ─────────────────────────────────
    {
        "type": "function",
        "function": {
            "name": "list_notifications",
            "description": "List notifications that were sent.",
            "parameters": {
                "type": "object",
                "properties": {
                    "since":   {"type": "string"},
                    "until":   {"type": "string"},
                    "filter":  {"type": "string", "enum": ["sms_notification","email_notification","phone_notification","push_notification"]},
                    "include": {"type": "array", "items": {"type": "string", "enum": ["users"]}},
                },
                "required": ["since", "until"],
            },
        },
    },
    # ── Analytics ─────────────────────────────────────
    {
        "type": "function",
        "function": {
            "name": "get_analytics_incidents",
            "description": "Get raw analytics data for incidents (MTTA, MTTR, etc.).",
            "parameters": {
                "type": "object",
                "properties": {
                    "since":       {"type": "string"},
                    "until":       {"type": "string"},
                    "service_ids": {"type": "array", "items": {"type": "string"}},
                    "team_ids":    {"type": "array", "items": {"type": "string"}},
                    "urgencies":   {"type": "array", "items": {"type": "string", "enum": ["high","low"]}},
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_analytics_services",
            "description": "Get aggregated analytics per service.",
            "parameters": {
                "type": "object",
                "properties": {
                    "since":       {"type": "string"},
                    "until":       {"type": "string"},
                    "service_ids": {"type": "array", "items": {"type": "string"}},
                    "team_ids":    {"type": "array", "items": {"type": "string"}},
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_analytics_teams",
            "description": "Get aggregated analytics per team.",
            "parameters": {
                "type": "object",
                "properties": {
                    "since":    {"type": "string"},
                    "until":    {"type": "string"},
                    "team_ids": {"type": "array", "items": {"type": "string"}},
                },
                "required": [],
            },
        },
    },
    # ── Tags ──────────────────────────────────────────
    {
        "type": "function",
        "function": {
            "name": "list_tags",
            "description": "List all tags.",
            "parameters": {
                "type": "object",
                "properties": {"query": {"type": "string"}},
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "manage_tags",
            "description": "Add or remove tags from a resource.",
            "parameters": {
                "type": "object",
                "properties": {
                    "resource_type": {"type": "string", "enum": ["users","teams","escalation_policies"]},
                    "resource_id":   {"type": "string"},
                    "add_tags":      {"type": "array", "items": {"type": "object"}},
                    "remove_tags":   {"type": "array", "items": {"type": "object"}},
                },
                "required": ["resource_type", "resource_id"],
            },
        },
    },
    # ── Vendors ───────────────────────────────────────
    {
        "type": "function",
        "function": {
            "name": "list_vendors",
            "description": "List available integration vendors.",
            "parameters": {
                "type": "object",
                "properties": {"query": {"type": "string"}},
                "required": [],
            },
        },
    },
    # ── Response Plays ────────────────────────────────
    {
        "type": "function",
        "function": {
            "name": "list_response_plays",
            "description": "List response plays.",
            "parameters": {
                "type": "object",
                "properties": {"query": {"type": "string"}},
                "required": [],
            },
        },
    },
    # ── Business Services ─────────────────────────────
    {
        "type": "function",
        "function": {
            "name": "list_business_services",
            "description": "List business services.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_business_service",
            "description": "Get a business service by ID.",
            "parameters": {
                "type": "object",
                "properties": {"business_service_id": {"type": "string"}},
                "required": ["business_service_id"],
            },
        },
    },
    # ── Service Dependencies ──────────────────────────
    {
        "type": "function",
        "function": {
            "name": "get_service_dependencies",
            "description": "Get upstream/downstream service dependencies.",
            "parameters": {
                "type": "object",
                "properties": {
                    "service_id":   {"type": "string"},
                    "service_type": {"type": "string", "enum": ["technical","business"]},
                },
                "required": ["service_id", "service_type"],
            },
        },
    },
    # ── Status Dashboard ──────────────────────────────
    {
        "type": "function",
        "function": {
            "name": "list_status_dashboards",
            "description": "List status dashboards.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    # ── Audit Records ─────────────────────────────────
    {
        "type": "function",
        "function": {
            "name": "list_audit_records",
            "description": "List audit records (who changed what).",
            "parameters": {
                "type": "object",
                "properties": {
                    "since":               {"type": "string"},
                    "until":               {"type": "string"},
                    "root_resource_types": {"type": "array", "items": {"type": "string", "enum": ["users","services","teams","escalation_policies","schedules"]}},
                },
                "required": [],
            },
        },
    },
    # ── Event Orchestration / Rulesets ────────────────
    {
        "type": "function",
        "function": {
            "name": "list_event_orchestrations",
            "description": "List global event orchestration rules.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_rulesets",
            "description": "List rulesets (legacy event rules).",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    # ── Webhooks ──────────────────────────────────────
    {
        "type": "function",
        "function": {
            "name": "list_webhook_subscriptions",
            "description": "List V3 webhook subscriptions.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "create_webhook_subscription",
            "description": "Create a new V3 webhook subscription.",
            "parameters": {
                "type": "object",
                "properties": {
                    "delivery_method_url": {"type": "string"},
                    "description":         {"type": "string"},
                    "events":              {"type": "array", "items": {"type": "string"}},
                    "filter_type":         {"type": "string", "enum": ["service_reference","team_reference","account_reference"]},
                    "filter_id":           {"type": "string"},
                },
                "required": ["delivery_method_url", "events", "filter_type"],
            },
        },
    },
    # ── Abilities / Extensions / Workflows ────────────
    {
        "type": "function",
        "function": {
            "name": "list_abilities",
            "description": "List the account's enabled abilities/features.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_extensions",
            "description": "List extensions (Slack channels, webhooks, etc.).",
            "parameters": {
                "type": "object",
                "properties": {
                    "query":               {"type": "string"},
                    "extension_schema_id": {"type": "string"},
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_incident_workflows",
            "description": "List incident workflows.",
            "parameters": {
                "type": "object",
                "properties": {"query": {"type": "string"}},
                "required": [],
            },
        },
    },
    # ── Compound Analysis ─────────────────────────────
    {
        "type": "function",
        "function": {
            "name": "full_incident_analysis",
            "description": "Run a full analysis: MTTA, MTTR, escalation counts, service distribution.",
            "parameters": {
                "type": "object",
                "properties": {
                    "since":       {"type": "string"},
                    "until":       {"type": "string"},
                    "service_ids": {"type": "array", "items": {"type": "string"}},
                    "team_ids":    {"type": "array", "items": {"type": "string"}},
                },
                "required": ["since", "until"],
            },
        },
    },
    # ── Utility: resolve_time ─────────────────────────
    {
        "type": "function",
        "function": {
            "name": "resolve_time",
            "description": "Convert natural-language time to ISO-8601 UTC. Use for 'yesterday', 'last Monday', '3 hours ago'.",
            "parameters": {
                "type": "object",
                "properties": {
                    "expression": {"type": "string", "description": "Natural-language time expression."},
                },
                "required": ["expression"],
            },
        },
    },
    # ── Postmortem generator ──────────────────────────
    {
        "type": "function",
        "function": {
            "name": "generate_postmortem",
            "description": "Auto-generate a structured postmortem for a resolved incident.",
            "parameters": {
                "type": "object",
                "properties": {
                    "incident_id": {"type": "string"},
                    "output_file": {"type": "string"},
                },
                "required": ["incident_id"],
            },
        },
    },
    # ── Pattern analysis ──────────────────────────────
    {
        "type": "function",
        "function": {
            "name": "analyze_patterns",
            "description": "Find recurring incident patterns: noisy services, repeated titles, time-of-day clusters.",
            "parameters": {
                "type": "object",
                "properties": {
                    "since":       {"type": "string"},
                    "until":       {"type": "string"},
                    "service_ids": {"type": "array", "items": {"type": "string"}},
                    "team_ids":    {"type": "array", "items": {"type": "string"}},
                    "top_n":       {"type": "integer"},
                },
                "required": ["since", "until"],
            },
        },
    },
    # ── SLA breach detector ───────────────────────────
    {
        "type": "function",
        "function": {
            "name": "check_sla_breaches",
            "description": "Find incidents that breached MTTA or MTTR SLA targets.",
            "parameters": {
                "type": "object",
                "properties": {
                    "since":                  {"type": "string"},
                    "until":                  {"type": "string"},
                    "mtta_threshold_seconds": {"type": "integer"},
                    "mttr_threshold_seconds": {"type": "integer"},
                    "service_ids":            {"type": "array", "items": {"type": "string"}},
                    "team_ids":               {"type": "array", "items": {"type": "string"}},
                },
                "required": ["since", "until"],
            },
        },
    },
    # ── On-call burnout report ────────────────────────
    {
        "type": "function",
        "function": {
            "name": "oncall_load_report",
            "description": "Analyse paging frequency to detect on-call burnout risk.",
            "parameters": {
                "type": "object",
                "properties": {
                    "since":    {"type": "string"},
                    "until":    {"type": "string"},
                    "team_ids": {"type": "array", "items": {"type": "string"}},
                },
                "required": ["since", "until"],
            },
        },
    },
    # ═══════════════════════════════════════════════════
    # NEW FEATURE SCHEMAS (Events, Alerts, Status Updates,
    # Responders, Schedule CRUD, Custom Fields, Automation,
    # Orchestration Full CRUD)
    # ═══════════════════════════════════════════════════
    # ── Events API v2 ─────────────────────────────────
    {
        "type": "function",
        "function": {
            "name": "send_event",
            "description": "Send a trigger/acknowledge/resolve event via Events API v2. Requires a routing_key (integration key).",
            "parameters": {
                "type": "object",
                "properties": {
                    "routing_key":    {"type": "string", "description": "Integration key from a PD service."},
                    "event_action":   {"type": "string", "enum": ["trigger","acknowledge","resolve"]},
                    "dedup_key":      {"type": "string", "description": "Dedup key for correlating events."},
                    "summary":        {"type": "string", "description": "Alert summary (trigger only)."},
                    "source":         {"type": "string"},
                    "severity":       {"type": "string", "enum": ["critical","error","warning","info"]},
                    "component":      {"type": "string"},
                    "group":          {"type": "string"},
                    "event_class":    {"type": "string"},
                    "custom_details": {"type": "object"},
                    "client":         {"type": "string"},
                    "client_url":     {"type": "string"},
                },
                "required": ["routing_key", "event_action"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "send_change_event",
            "description": "Submit a change event (deployment, config change) via Events API v2.",
            "parameters": {
                "type": "object",
                "properties": {
                    "routing_key":    {"type": "string"},
                    "summary":        {"type": "string"},
                    "source":         {"type": "string"},
                    "timestamp":      {"type": "string"},
                    "custom_details": {"type": "object"},
                    "links":          {"type": "array", "items": {"type": "object"}},
                },
                "required": ["routing_key", "summary"],
            },
        },
    },
    # ── Alerts Management ─────────────────────────────
    {
        "type": "function",
        "function": {
            "name": "list_alerts",
            "description": "List alerts account-wide, optionally filtered by status, service, or time.",
            "parameters": {
                "type": "object",
                "properties": {
                    "since":       {"type": "string"},
                    "until":       {"type": "string"},
                    "statuses":    {"type": "array", "items": {"type": "string", "enum": ["triggered","resolved"]}},
                    "service_ids": {"type": "array", "items": {"type": "string"}},
                    "sort_by":     {"type": "string"},
                    "limit":       {"type": "integer"},
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_alert",
            "description": "Get a single alert by incident ID and alert ID.",
            "parameters": {
                "type": "object",
                "properties": {
                    "incident_id": {"type": "string"},
                    "alert_id":    {"type": "string"},
                },
                "required": ["incident_id", "alert_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "update_alert",
            "description": "Update an alert (e.g. resolve it).",
            "parameters": {
                "type": "object",
                "properties": {
                    "incident_id": {"type": "string"},
                    "alert_id":    {"type": "string"},
                    "status":      {"type": "string", "enum": ["triggered","resolved"]},
                },
                "required": ["incident_id", "alert_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "manage_incident_alerts",
            "description": "Bulk-update (e.g. resolve) multiple alerts on an incident.",
            "parameters": {
                "type": "object",
                "properties": {
                    "incident_id": {"type": "string"},
                    "alert_ids":   {"type": "array", "items": {"type": "string"}},
                    "status":      {"type": "string", "enum": ["triggered","resolved"]},
                },
                "required": ["incident_id", "alert_ids"],
            },
        },
    },
    # ── Status Updates ────────────────────────────────
    {
        "type": "function",
        "function": {
            "name": "list_incident_status_updates",
            "description": "List status updates posted on an incident.",
            "parameters": {
                "type": "object",
                "properties": {"incident_id": {"type": "string"}},
                "required": ["incident_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "create_incident_status_update",
            "description": "Send a status update on an incident to notify stakeholders.",
            "parameters": {
                "type": "object",
                "properties": {
                    "incident_id":  {"type": "string"},
                    "message":      {"type": "string", "description": "Status update text."},
                    "subject":      {"type": "string"},
                    "html_message": {"type": "string"},
                },
                "required": ["incident_id", "message"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "add_incident_notification_subscribers",
            "description": "Add subscribers (users/teams) to receive status updates for an incident.",
            "parameters": {
                "type": "object",
                "properties": {
                    "incident_id": {"type": "string"},
                    "subscribers": {"type": "array", "items": {"type": "object",
                                                               "properties": {"id": {"type": "string"}, "type": {"type": "string", "enum": ["user","team"]}},
                                                               "required": ["id"]
                                                               }},
                },
                "required": ["incident_id", "subscribers"],
            },
        },
    },
    # ── Responder Requests ────────────────────────────
    {
        "type": "function",
        "function": {
            "name": "create_responder_request",
            "description": "Request additional responders (users/escalation policies) for an incident.",
            "parameters": {
                "type": "object",
                "properties": {
                    "incident_id":  {"type": "string"},
                    "requester_id": {"type": "string", "description": "User ID of the person making the request."},
                    "message":      {"type": "string"},
                    "targets":      {"type": "array", "items": {"type": "object",
                                                                "properties": {
                                                                    "id": {"type": "string"},
                                                                    "type": {"type": "string", "enum": ["user_reference","escalation_policy_reference"]},
                                                                }, "required": ["id"]
                                                                }},
                },
                "required": ["incident_id", "requester_id", "targets"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_responder_requests",
            "description": "List responder requests for an incident.",
            "parameters": {
                "type": "object",
                "properties": {"incident_id": {"type": "string"}},
                "required": ["incident_id"],
            },
        },
    },
    # ── Schedule Create / Update / Delete ─────────────
    {
        "type": "function",
        "function": {
            "name": "create_schedule",
            "description": "Create a new on-call schedule with layers and rotations.",
            "parameters": {
                "type": "object",
                "properties": {
                    "name":        {"type": "string"},
                    "description": {"type": "string"},
                    "time_zone":   {"type": "string", "description": "IANA timezone. Default: UTC."},
                    "schedule_layers": {"type": "array", "items": {"type": "object",
                                                                   "properties": {
                                                                       "name": {"type": "string"},
                                                                       "start": {"type": "string", "description": "ISO8601 start time."},
                                                                       "end": {"type": "string"},
                                                                       "rotation_turn_length_seconds": {"type": "integer"},
                                                                       "user_ids": {"type": "array", "items": {"type": "string"}},
                                                                   }, "required": ["start", "user_ids"]
                                                                   }},
                    "teams": {"type": "array", "items": {"type": "string"}},
                },
                "required": ["name", "schedule_layers"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "update_schedule",
            "description": "Update an existing on-call schedule.",
            "parameters": {
                "type": "object",
                "properties": {
                    "schedule_id": {"type": "string"},
                    "name":        {"type": "string"},
                    "description": {"type": "string"},
                    "time_zone":   {"type": "string"},
                    "schedule_layers": {"type": "array", "items": {"type": "object"}},
                    "teams":       {"type": "array", "items": {"type": "string"}},
                },
                "required": ["schedule_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "delete_schedule",
            "description": "Delete a schedule. WARNING: irreversible.",
            "parameters": {
                "type": "object",
                "properties": {"schedule_id": {"type": "string"}},
                "required": ["schedule_id"],
            },
        },
    },
    # ── Custom Fields ─────────────────────────────────
    {
        "type": "function",
        "function": {
            "name": "list_custom_fields",
            "description": "List incident custom field definitions.",
            "parameters": {"type": "object", "properties": {"include": {"type": "array", "items": {"type": "string"}}}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_custom_field",
            "description": "Get a single custom field schema by ID.",
            "parameters": {"type": "object", "properties": {"field_id": {"type": "string"}}, "required": ["field_id"]},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "create_custom_field",
            "description": "Create a new incident custom field definition.",
            "parameters": {
                "type": "object",
                "properties": {
                    "name":          {"type": "string"},
                    "display_name":  {"type": "string"},
                    "description":   {"type": "string"},
                    "data_type":     {"type": "string", "enum": ["string","integer","float","boolean","datetime","url"]},
                    "field_type":    {"type": "string", "enum": ["single_value","single_value_fixed","multi_value","multi_value_fixed"]},
                    "fixed_options": {"type": "boolean"},
                },
                "required": ["name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "update_custom_field",
            "description": "Update a custom field schema.",
            "parameters": {
                "type": "object",
                "properties": {"field_id": {"type": "string"}, "display_name": {"type": "string"}, "description": {"type": "string"}},
                "required": ["field_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "delete_custom_field",
            "description": "Delete a custom field schema.",
            "parameters": {"type": "object", "properties": {"field_id": {"type": "string"}}, "required": ["field_id"]},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_incident_custom_field_values",
            "description": "Get custom field values set on a specific incident.",
            "parameters": {"type": "object", "properties": {"incident_id": {"type": "string"}}, "required": ["incident_id"]},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "set_incident_custom_field_values",
            "description": "Set custom field values on an incident.",
            "parameters": {
                "type": "object",
                "properties": {
                    "incident_id": {"type": "string"},
                    "fields": {"type": "array", "items": {"type": "object",
                                                          "properties": {"id": {"type": "string"}, "value": {}}, "required": ["id", "value"]
                                                          }},
                },
                "required": ["incident_id", "fields"],
            },
        },
    },
    # ── Automation Actions ────────────────────────────
    {
        "type": "function",
        "function": {
            "name": "list_automation_actions",
            "description": "List automation actions, optionally filtered by query or service.",
            "parameters": {
                "type": "object",
                "properties": {"query": {"type": "string"}, "service_id": {"type": "string"}},
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_automation_action",
            "description": "Get details of a single automation action.",
            "parameters": {"type": "object", "properties": {"action_id": {"type": "string"}}, "required": ["action_id"]},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "create_automation_action",
            "description": "Create a new automation action.",
            "parameters": {
                "type": "object",
                "properties": {
                    "name":                  {"type": "string"},
                    "description":           {"type": "string"},
                    "action_type":           {"type": "string", "enum": ["process_automation","script"]},
                    "runner_id":             {"type": "string"},
                    "action_data_reference": {"type": "object"},
                    "services":              {"type": "array", "items": {"type": "string"}},
                },
                "required": ["name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "invoke_automation_action",
            "description": "Invoke (run) an automation action on an incident.",
            "parameters": {
                "type": "object",
                "properties": {
                    "action_id":   {"type": "string"},
                    "incident_id": {"type": "string"},
                    "alert_id":    {"type": "string"},
                },
                "required": ["action_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_automation_runners",
            "description": "List automation action runners.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    # ── Event Orchestration Full CRUD ─────────────────
    {
        "type": "function",
        "function": {
            "name": "get_event_orchestration",
            "description": "Get details of a single event orchestration.",
            "parameters": {"type": "object", "properties": {"orchestration_id": {"type": "string"}}, "required": ["orchestration_id"]},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "create_event_orchestration",
            "description": "Create a new global event orchestration.",
            "parameters": {
                "type": "object",
                "properties": {"name": {"type": "string"}, "description": {"type": "string"}, "team_id": {"type": "string"}},
                "required": ["name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "update_event_orchestration",
            "description": "Update a global event orchestration.",
            "parameters": {
                "type": "object",
                "properties": {
                    "orchestration_id": {"type": "string"}, "name": {"type": "string"},
                    "description": {"type": "string"}, "team_id": {"type": "string"},
                },
                "required": ["orchestration_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "delete_event_orchestration",
            "description": "Delete a global event orchestration.",
            "parameters": {"type": "object", "properties": {"orchestration_id": {"type": "string"}}, "required": ["orchestration_id"]},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_orchestration_router",
            "description": "Get the global routing rules for an orchestration.",
            "parameters": {"type": "object", "properties": {"orchestration_id": {"type": "string"}}, "required": ["orchestration_id"]},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "update_orchestration_router",
            "description": "Update the global routing rules for an orchestration.",
            "parameters": {
                "type": "object",
                "properties": {
                    "orchestration_id": {"type": "string"},
                    "orchestration_path": {"type": "object", "description": "Full orchestration_path object with sets/rules."},
                },
                "required": ["orchestration_id", "orchestration_path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_service_orchestration",
            "description": "Get the event orchestration rules for a service.",
            "parameters": {"type": "object", "properties": {"service_id": {"type": "string"}}, "required": ["service_id"]},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "update_service_orchestration",
            "description": "Update the event orchestration rules for a service.",
            "parameters": {
                "type": "object",
                "properties": {
                    "service_id": {"type": "string"},
                    "orchestration_path": {"type": "object"},
                },
                "required": ["service_id", "orchestration_path"],
            },
        },
    },
]