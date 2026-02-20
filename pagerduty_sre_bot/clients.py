"""Groq, PagerDuty REST API v2, and Events API v2 client initialization."""

import os
import httpx
from dotenv import load_dotenv
from groq import Client
import pagerduty

load_dotenv(".env")

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
PAGERDUTY_API_KEY = os.getenv("PAGERDUTY_API_KEY")
PAGERDUTY_EMAIL = os.getenv("PAGERDUTY_EMAIL", "")

if not GROQ_API_KEY or not PAGERDUTY_API_KEY:
    raise ValueError(
        "Missing required API keys. Set GROQ_API_KEY and PAGERDUTY_API_KEY in .env"
    )

groq_client = Client(api_key=GROQ_API_KEY)
pd_client = pagerduty.RestApiV2Client(PAGERDUTY_API_KEY, default_from=PAGERDUTY_EMAIL)

# ── Events API v2 ────────────────────────────────────
# The Events API uses a different base URL and auth model (routing_key per-request).
# We use a plain httpx client for it.
EVENTS_API_URL = "https://events.pagerduty.com/v2/enqueue"
CHANGE_EVENTS_API_URL = "https://events.pagerduty.com/v2/change/enqueue"

_events_http = httpx.Client(timeout=30.0)


def send_event_v2(routing_key: str, payload: dict) -> dict:
    """Send an event to the PagerDuty Events API v2."""
    resp = _events_http.post(EVENTS_API_URL, json={**payload, "routing_key": routing_key})
    return {"status_code": resp.status_code, "body": resp.json() if resp.status_code < 500 else resp.text}


def send_change_event(routing_key: str, payload: dict) -> dict:
    """Send a change event to the PagerDuty Events API v2."""
    resp = _events_http.post(CHANGE_EVENTS_API_URL, json={**payload, "routing_key": routing_key})
    return {"status_code": resp.status_code, "body": resp.json() if resp.status_code < 500 else resp.text}