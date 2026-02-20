"""Shared PagerDuty API helpers used across tool modules."""

from typing import Any

from pagerduty_sre_bot.clients import pd_client
from pagerduty_sre_bot.retry import with_retry
from pagerduty_sre_bot.output import cprint

MAX_RESULTS = 50


def set_max_results(n: int) -> None:
    global MAX_RESULTS
    MAX_RESULTS = n


@with_retry(max_retries=3)
def safe_list(endpoint: str, params: dict | None = None, limit: int | None = None) -> dict | list:
    if limit is None:
        limit = MAX_RESULTS
    results = []
    truncated = False
    try:
        for item in pd_client.iter_all(endpoint, params=params or {}):
            results.append(item)
            if len(results) >= limit:
                truncated = True
                break
    except Exception as e:
        return {"error": str(e)}
    if truncated:
        return {
            "items": results,
            "truncated": True,
            "note": f"Results truncated at {limit}. Refine your query for complete data.",
        }
    return results


def unwrap(result: Any) -> list:
    if isinstance(result, dict):
        if "error" in result:
            return []
        if "items" in result:
            return result["items"]
        return []
    return result if isinstance(result, list) else []


def is_dry_run_action(dry_run: bool, action_desc: str) -> dict:
    if dry_run:
        cprint(f"[yellow]🔒 DRY-RUN: Would have executed → {action_desc}[/yellow]")
        return {"dry_run": True, "would_execute": action_desc}
    return {}