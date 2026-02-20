"""Incident Custom Fields — schema management and value read/write."""

from pagerduty_sre_bot.clients import pd_client
from pagerduty_sre_bot.helpers import safe_list, unwrap, is_dry_run_action
from pagerduty_sre_bot.retry import with_retry

_dry_run = False


def set_dry_run(v: bool) -> None:
    global _dry_run
    _dry_run = v


# ── Field Schema CRUD ─────────────────────────────────

def tool_list_custom_fields(args: dict) -> dict:
    """List incident custom field definitions."""
    params = {}
    if args.get("include"):
        params["include[]"] = args["include"]
    raw = safe_list("incidents/custom_fields", params)
    if isinstance(raw, dict) and "error" in raw:
        return raw
    items = unwrap(raw) if isinstance(raw, dict) else raw
    return {
        "total": len(items),
        "custom_fields": [
            {
                "id": f["id"], "name": f.get("name"),
                "display_name": f.get("display_name"),
                "description": f.get("description"),
                "field_type": f.get("field_type"),
                "data_type": f.get("data_type"),
                "fixed_options": f.get("fixed_options"),
            }
            for f in items
        ],
    }


@with_retry()
def tool_get_custom_field(args: dict) -> dict:
    """Get a single custom field schema by ID."""
    try:
        return pd_client.rget(f"incidents/custom_fields/{args['field_id']}")
    except Exception as e:
        return {"error": str(e)}


@with_retry()
def tool_create_custom_field(args: dict) -> dict:
    """Create a new incident custom field definition."""
    dry = is_dry_run_action(_dry_run, f"create_custom_field name='{args.get('name')}'")
    if dry:
        return dry
    try:
        body: dict = {
            "data_type": args.get("data_type", "string"),
            "field_type": args.get("field_type", "single_value"),
            "name": args["name"],
            "display_name": args.get("display_name", args["name"]),
        }
        if args.get("description"):
            body["description"] = args["description"]
        if args.get("fixed_options") is not None:
            body["fixed_options"] = args["fixed_options"]
        if args.get("default_value"):
            body["default_value"] = args["default_value"]

        field = pd_client.rpost("incidents/custom_fields", json=body)
        return {"success": True, "custom_field": {"id": field["id"], "name": field.get("name")}}
    except Exception as e:
        return {"error": str(e)}


@with_retry()
def tool_update_custom_field(args: dict) -> dict:
    """Update a custom field schema."""
    dry = is_dry_run_action(_dry_run, f"update_custom_field {args['field_id']}")
    if dry:
        return dry
    try:
        fid = args["field_id"]
        payload: dict = {"id": fid, "type": "custom_field"}
        for k in ("name", "display_name", "description", "field_type", "fixed_options"):
            if args.get(k) is not None:
                payload[k] = args[k]
        updated = pd_client.rput(f"incidents/custom_fields/{fid}", json=payload)
        return {"success": True, "custom_field": {"id": updated["id"], "name": updated.get("name")}}
    except Exception as e:
        return {"error": str(e)}


@with_retry()
def tool_delete_custom_field(args: dict) -> dict:
    """Delete a custom field schema."""
    dry = is_dry_run_action(_dry_run, f"delete_custom_field {args['field_id']}")
    if dry:
        return dry
    try:
        pd_client.delete(f"incidents/custom_fields/{args['field_id']}")
        return {"success": True, "deleted_field_id": args["field_id"]}
    except Exception as e:
        return {"error": str(e)}


# ── Field Options (for select/dropdown fields) ────────

@with_retry()
def tool_create_field_option(args: dict) -> dict:
    """Create a dropdown option for a custom field."""
    dry = is_dry_run_action(_dry_run, f"create_field_option field={args['field_id']}")
    if dry:
        return dry
    try:
        body = {"data": {"type": "field_option", "value": args["value"]}}
        resp = pd_client.post(
            f"incidents/custom_fields/{args['field_id']}/field_options", json=body
        )
        if resp.status_code < 300:
            data = resp.json().get("field_option", {})
            return {"success": True, "field_option": {"id": data.get("id"), "value": data.get("value")}}
        return {"error": f"HTTP {resp.status_code}: {resp.text}"}
    except Exception as e:
        return {"error": str(e)}


# ── Field Values on Incidents ──────────────────────────

@with_retry()
def tool_get_incident_custom_field_values(args: dict) -> dict:
    """Get custom field values set on a specific incident."""
    try:
        inc = pd_client.rget(f"incidents/{args['incident_id']}")
        fields = inc.get("custom_fields", [])
        return {
            "incident_id": args["incident_id"],
            "custom_fields": [
                {
                    "id": f.get("id"),
                    "name": f.get("name"),
                    "display_name": f.get("display_name"),
                    "value": f.get("value"),
                    "field_type": f.get("field_type"),
                    "data_type": f.get("data_type"),
                }
                for f in fields
            ],
        }
    except Exception as e:
        return {"error": str(e)}


@with_retry()
def tool_set_incident_custom_field_values(args: dict) -> dict:
    """Set custom field values on an incident."""
    dry = is_dry_run_action(_dry_run, f"set_custom_field_values incident={args['incident_id']}")
    if dry:
        return dry
    try:
        iid = args["incident_id"]
        custom_fields = [
            {"id": f["id"], "value": f["value"]}
            for f in args.get("fields", [])
        ]
        payload = {
            "id": iid,
            "type": "incident",
            "custom_fields": custom_fields,
        }
        updated = pd_client.rput(f"incidents/{iid}", json=payload)
        return {
            "success": True,
            "incident_id": iid,
            "fields_updated": len(custom_fields),
        }
    except Exception as e:
        return {"error": str(e)}