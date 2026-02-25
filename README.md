# 🚀 PagerDuty SRE AI Assistant

> **A full-featured, AI-powered command-line assistant for PagerDuty operations.**
> Powered by [Anthropic Claude](https://www.anthropic.com/) + PagerDuty REST API v2 + Events API v2.

[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

---

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Quick Start (First Time Setup)](#quick-start-first-time-setup)
- [Architecture](#architecture)
- [Project Structure](#project-structure)
- [Configuration Reference](#configuration-reference)
- [Usage](#usage)
- [Supported Operations](#supported-operations)
- [Tool Routing](#tool-routing)
- [Dry-Run Mode](#dry-run-mode)
- [Proactive Monitoring](#proactive-monitoring)
- [Conversation Persistence](#conversation-persistence)
- [Example Interactions](#example-interactions)
- [Extending the Bot](#extending-the-bot)
- [Troubleshooting](#troubleshooting)
- [License](#license)

---

## Overview

This is a professional-grade CLI assistant that lets you manage your entire PagerDuty account through natural language. Ask questions, run analyses, manage incidents, create schedules, trigger events — all by chatting.

The bot uses Groq's blazing-fast LLM inference with function calling to translate your natural language requests into precise PagerDuty API calls, then presents the results in a clean, formatted output.

**Coverage:** ~105 tool functions covering ~55% of the PagerDuty REST API v2 surface area, including all commonly used endpoints.

---

## Features

### Core Capabilities
- **Natural Language Interface** — Ask in plain English, get real PagerDuty data
- **105+ Tool Functions** — Full CRUD across incidents, services, users, teams, schedules, escalation policies, and more
- **Events API v2** — Trigger, acknowledge, and resolve alerts; submit change events
- **Alerts Management** — List, update, and bulk-manage alerts independently
- **Status Updates** — Send incident status updates to stakeholders
- **Responder Requests** — Page additional responders onto incidents
- **Schedule CRUD** — Create, update, and delete on-call schedules with layers and rotations
- **Incident Custom Fields** — Manage field schemas and read/write field values on incidents
- **Automation Actions** — List, create, invoke, and manage automation actions and runners
- **Event Orchestration** — Full CRUD for global orchestrations, routing rules, and service orchestrations

### Advanced Analysis
- **Full Incident Analysis** — MTTA, MTTR, escalation counts, service distribution
- **Pattern Analysis** — Noisy services, recurring titles, time-of-day clusters
- **SLA Breach Detection** — Find incidents that exceeded MTTA/MTTR targets
- **On-Call Burnout Report** — Page frequency per user, after-hours pages, risk scoring
- **Postmortem Generation** — Auto-generate structured markdown postmortems

### Infrastructure
- **Streaming Responses** — Final LLM answers stream token-by-token
- **Exponential Backoff Retry** — All API calls retry on transient failures (429, connection errors)
- **TTL Caching** — Slow-changing resources (services, users) are cached to reduce API calls
- **Natural Language Time Parsing** — "yesterday", "last Monday 9am", "3 hours ago" → ISO-8601
- **Smart Context Compression** — Summarizes old conversation turns instead of discarding them
- **Model Fallback** — Automatic fallback from primary to secondary model on failure
- **Dynamic Tool Routing** — Only sends relevant tools per query (keeps within token limits)
- **Conversation Persistence** — Chat history saved/loaded across sessions
- **Proactive Monitoring Daemon** — Background polling for new high-urgency incidents
- **Dry-Run Mode** — Preview destructive operations without executing them
- **Rich CLI Output** — Tables, panels, markdown rendering via Rich (graceful plain-text fallback)
- **YAML Configuration** — All settings configurable via `config.yml`

---

## Quick Start (First Time Setup)

Follow these steps to go from zero to running in under 5 minutes.

### Step 1: Clone & Enter the Project

```bash
git clone https://github.com/your-org/pagerduty-sre-bot.git
cd pagerduty-sre-bot
```

Or if you already have the files:

```bash
cd ~/Desktop/PD_AI_Final
```

### Step 2: Verify Folder Structure

Your project **must** look like this. The `pagerduty_sre_bot/` folder is the Python package — all `.py` files go inside it, not at the root.

```
PD_AI_Final/                    ← project root (you run commands from here)
├── pyproject.toml
├── README.md
├── .env                        ← your API keys (you create this)
├── config.yml                  ← auto-created on first run
└── pagerduty_sre_bot/          ← Python package (all code here)
    ├── __init__.py
    ├── __main__.py
    ├── cli.py
    ├── clients.py
    ├── config.py
    ├── ... (other .py files)
    └── tools/
        ├── __init__.py
        ├── incidents.py
        ├── ... (other tool files)
```

> **⚠️ Common mistake:** Do NOT put `.py` files at the project root alongside `pyproject.toml`. They must be inside `pagerduty_sre_bot/`.

### Step 3: Create a Virtual Environment (Recommended)

```bash
python -m venv .venv
source .venv/bin/activate       # macOS / Linux
# .venv\Scripts\activate        # Windows
```

### Step 4: Install Dependencies

```bash
pip install -e .
```

This installs the package in editable mode plus all dependencies:
- `anthropic` — Claude LLM (tool use + generation)
- `pagerduty` — REST API v2 client
- `httpx` — Events API v2 client
- `python-dotenv` — `.env` file loading
- `pyyaml` — config parsing
- `dateparser` — natural language time parsing
- `rich` — formatted CLI output

### Step 5: Get Your API Keys

You need **two** API keys:

#### Anthropic API Key
1. Go to [console.anthropic.com](https://console.anthropic.com)
2. Sign up / log in
3. Navigate to **API Keys** → **Create Key**
4. Copy the key (starts with `sk-ant-`)

#### PagerDuty API Key
1. Log in to your PagerDuty account
2. Go to **Integrations** → **API Access Keys**
3. Click **Create New API Key**
4. Give it a description, click **Create Key**
5. Copy the key
6. Also note the **email address** of the user who created the key

> **Tip:** User-level API keys (created from your profile → User Settings → API Access) work too and don't require the `PAGERDUTY_EMAIL` setting.

### Step 6: Create Your `.env` File

In the **project root** (same folder as `pyproject.toml`):

```bash
cat > .env << 'EOF'
ANTHROPIC_API_KEY=sk-ant-paste_your_key_here
PAGERDUTY_API_KEY=paste_your_pagerduty_key_here
PAGERDUTY_EMAIL=your.email@company.com
EOF
```

Or create it manually with any text editor. Replace the placeholder values with your real keys.

> **⚠️ Never commit `.env` to git.** Add it to `.gitignore`:
> ```bash
> echo ".env" >> .gitignore
> ```

### Step 7: Run It!

```bash
python -m pagerduty_sre_bot
```

You should see:

```
🚀 PagerDuty Full-Feature SRE AI Assistant — Enhanced Edition
──────────────────────────────────────────────────────────────
  Model   : claude-sonnet-4-20250514 (fallback: claude-haiku-4-5-20251001)
  Dry-run : disabled
  Monitor : off
  Config  : config.yml
  Type help for capabilities, exit to quit

You: 
```

**That's it! Try your first query:**

```
You: who is on call right now?
```

```
You: show incidents from last 24 hours
```

```
You: list all services
```

### Step 8: (Optional) Enable Extra Features

```bash
# Safe mode — see what write operations would do without executing them
python -m pagerduty_sre_bot --dry-run

# Background monitoring — get alerted about new incidents while chatting
python -m pagerduty_sre_bot --monitor

# Both together
python -m pagerduty_sre_bot --monitor --dry-run
```

### First Time Checklist

- [ ] Python 3.10+ installed (`python --version`)
- [ ] Project folder structure is correct (code inside `pagerduty_sre_bot/`)
- [ ] Virtual environment created and activated
- [ ] `pip install -e .` ran successfully
- [ ] `.env` file created at project root with both API keys
- [ ] Running from project root: `cd ~/Desktop/PD_AI_Final && python -m pagerduty_sre_bot`
- [ ] First query returned real data

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    User (CLI)                           │
└──────────────────────┬──────────────────────────────────┘
                       │ natural language
                       ▼
┌─────────────────────────────────────────────────────────┐
│              __main__.py (Entry Point)                   │
│  ┌─────────────┐  ┌──────────────┐  ┌───────────────┐  │
│  │   cli.py    │  │  config.py   │  │  output.py    │  │
│  └─────────────┘  └──────────────┘  └───────────────┘  │
└──────────────────────┬──────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────┐
│             conversation.py (LLM Loop)                  │
│                                                         │
│  1. Build messages (system + history + user query)      │
│  2. Select relevant tools via tool_router.py            │
│  3. Call Groq LLM with function-calling                 │
│  4. Execute tool calls via tool_registry.py             │
│  5. Loop until final answer                             │
│  6. Stream response to user                             │
└───────┬──────────────────────┬──────────────────────────┘
        │                      │
        ▼                      ▼
┌───────────────┐    ┌─────────────────────────────────────┐
│  Claude API   │    │        tool_registry.py             │
│  (Anthropic)  │    │  Maps 105+ tool names → functions   │
└───────────────┘    └──────────────┬──────────────────────┘
                                    │
                     ┌──────────────┼──────────────┐
                     ▼              ▼              ▼
              ┌────────────┐ ┌───────────┐ ┌────────────┐
              │ tools/     │ │ tools/    │ │ tools/     │
              │ incidents  │ │ services  │ │ alerts     │
              │ events     │ │ users     │ │ automation │
              │ schedules  │ │ teams     │ │ orchestr.  │
              │ custom_fld │ │ analytics │ │ status_upd │
              │ analysis   │ │ audit     │ │ ...        │
              └─────┬──────┘ └─────┬─────┘ └─────┬──────┘
                    │              │              │
                    ▼              ▼              ▼
              ┌─────────────────────────────────────────┐
              │           clients.py                    │
              │  PagerDuty REST API v2 + Events API v2  │
              └─────────────────────────────────────────┘
```

---

## Project Structure

```
pagerduty-sre-bot/
├── pyproject.toml                  # Package config, dependencies, entry point
├── README.md                       # This file
├── .env                            # API keys (never commit this)
├── .env.example                    # Template for .env
├── .gitignore
├── config.yml                      # Runtime config (auto-created on first run)
│
└── pagerduty_sre_bot/              # ← All Python code lives here
    ├── __init__.py                 # Package version
    ├── __main__.py                 # Entry point + main chat loop
    ├── cli.py                      # Argument parsing (--monitor, --dry-run, etc.)
    ├── config.py                   # YAML config loading with defaults
    ├── clients.py                  # Groq + PagerDuty REST + Events API v2 clients
    ├── cache.py                    # TTL cache for slow-changing resources
    ├── retry.py                    # Exponential backoff decorator
    ├── time_utils.py               # NL time parsing, ISO helpers
    ├── output.py                   # Rich console output with plain-text fallback
    ├── helpers.py                  # Shared PD helpers (safe_list, unwrap, etc.)
    ├── schemas.py                  # All 105+ Groq function-calling JSON schemas
    ├── tool_registry.py            # Tool name → function dispatch map
    ├── tool_router.py              # Dynamic tool selection per query
    ├── conversation.py             # LLM conversation loop (tool rounds → answer)
    ├── compression.py              # Smart context compression via summarization
    ├── history.py                  # Conversation persistence (load/save/sanitize)
    ├── monitoring.py               # Background incident polling daemon
    ├── system_prompt.py            # System prompt template
    │
    └── tools/                      # Tool implementations (one file per domain)
        ├── __init__.py             # Re-exports all tool functions
        ├── incidents.py            # Incident CRUD + management
        ├── services.py             # Service CRUD + integrations
        ├── users.py                # User CRUD + contact methods + notification rules
        ├── teams.py                # Team CRUD + membership
        ├── escalation.py           # Escalation policy CRUD
        ├── schedules.py            # Schedule CRUD + overrides + on-call users
        ├── oncalls.py              # On-call listings
        ├── analytics.py            # Analytics + full incident analysis
        ├── maintenance.py          # Maintenance window management
        ├── notifications.py        # Notifications + log entries
        ├── audit.py                # Audit records
        ├── config_resources.py     # Tags, vendors, webhooks, extensions, etc.
        ├── analysis.py             # Patterns, SLA breaches, burnout, postmortem
        ├── utility.py              # resolve_time (NL → ISO-8601)
        ├── events.py               # Events API v2 (trigger/ack/resolve + change)
        ├── alerts.py               # Alerts management (list/get/update/bulk)
        ├── status_updates.py       # Status updates + subscribers + responders
        ├── custom_fields.py        # Custom field schemas + incident field values
        ├── automation.py           # Automation actions + runners + invocations
        └── orchestration.py        # Event orchestration full CRUD
```

---

## Configuration Reference

### API Keys (`.env`)

| Variable | Required | Description |
|----------|----------|-------------|
| `ANTHROPIC_API_KEY` | **Yes** | Anthropic API key (starts with `sk-ant-`) |
| `PAGERDUTY_API_KEY` | **Yes** | PagerDuty API token |
| `PAGERDUTY_EMAIL` | For writes* | Email of PD user (needed for account-level API keys) |
| `DRY_RUN` | No | Set to `true` to enable dry-run via environment |

> *If using a **user-level** API key, `PAGERDUTY_EMAIL` is not required — the user is derived from the key itself.

### Runtime Config (`config.yml`)

Auto-created on first run with sensible defaults. Full reference:

```yaml
model:
  primary: claude-sonnet-4-20250514             # Primary Claude model
  fallback: claude-haiku-4-5-20251001           # Faster/cheaper fallback

defaults:
  time_window_hours: 24       # Default lookback for queries
  max_results: 50             # Max items returned per API call

sla:
  mtta_minutes: 5             # Mean Time To Acknowledge target
  mttr_minutes: 60            # Mean Time To Resolve target

monitoring:
  poll_interval_seconds: 60   # How often the monitor daemon polls PD
  urgency_filter: high        # Only alert on "high" urgency incidents

cache:
  ttl_seconds: 300            # How long to cache services/users (5 min)

history:
  file: conversation_history.json   # Where chat history is saved
  max_messages: 40                  # Hard cap on history size
  compress_at: 30                   # Summarize oldest messages at this count

output:
  rich_tables: true           # Use Rich formatting (auto-disabled if not installed)

dry_run: false                # Global dry-run toggle
```

---

## Usage

### Running the Bot

```bash
# Always run from the project root (where .env and pyproject.toml are)
cd ~/Desktop/PD_AI_Final

# Standard mode
python -m pagerduty_sre_bot

# Or use the installed shortcut (after pip install -e .)
pd-sre-bot
```

### Command-Line Options

| Flag | Description |
|------|-------------|
| `--monitor` | Start background daemon that alerts on new high-urgency incidents |
| `--dry-run` | Simulate destructive operations without executing them |
| `--config path` | Use a custom config file (default: `config.yml`) |
| `--no-persist` | Don't save/load conversation history |
| `--history path` | Custom path for conversation history JSON |

```bash
# Examples
python -m pagerduty_sre_bot --monitor --dry-run
python -m pagerduty_sre_bot --config production.yml
python -m pagerduty_sre_bot --no-persist
```

### In-Chat Commands

| Command | Description |
|---------|-------------|
| `help` | Show capabilities and example queries |
| `clear` | Reset conversation history |
| `status` | Show current config, dry-run status, cache info |
| `cache clear` | Flush the TTL cache |
| `exit` / `quit` / `q` | Exit the assistant |

---

## Supported Operations

### Incidents (Full CRUD + Management)

```
"show incidents from last 24 hours"
"high-urgency triggered incidents since yesterday"
"details of incident P1ABC23"
"acknowledge incident P1ABC23"
"resolve incident P1ABC23"
"reassign P1ABC23 to user PXYZ"
"snooze P1ABC23 for 2 hours"
"merge incidents P1ABC, P2DEF into P3GHI"
"add note to P1ABC23: investigating DB pool"
"create incident on service PABC: database offline"
"timeline of incident P1ABC23"
```

### Events API v2

```
"send a critical trigger event to routing key abc123"
"acknowledge alert with dedup key xyz789"
"resolve event with dedup key xyz789"
"send a change event: deployed v2.5.0 to production"
```

### Alerts

```
"show all triggered alerts"
"get alert PABC on incident P123"
"resolve alert PABC on incident P123"
"resolve all alerts on incident P123"
```

### Status Updates & Responder Requests

```
"send status update on P123: we identified the root cause"
"show status updates on incident P123"
"subscribe the SRE team to incident P123 updates"
"page user PXYZ onto incident P123"
"who was requested on incident P123?"
```

### Services

```
"list all services"
"find services matching 'payment'"
"show service PABC with integrations"
"create service 'Auth API' with escalation policy PDEF"
"put service PABC in maintenance for 2 hours"
```

### Schedules (Full CRUD)

```
"show all schedules"
"create a weekly rotation schedule with users P1, P2, P3"
"change schedule PABC timezone to US/Eastern"
"delete schedule PABC"
"create override: user PXYZ on schedule PABC tomorrow"
"who is on call on schedule PABC?"
```

### Users, Teams, Escalation Policies

```
"list all users"
"find user john@example.com"
"add user PXYZ to team PABC as responder"
"show team members of team PABC"
"list escalation policies"
"show escalation policy PABC details"
```

### Custom Fields

```
"list all custom fields"
"create custom field 'Environment' of type string"
"what are the custom field values on incident P123?"
"set Environment to 'production' on incident P123"
```

### Automation Actions

```
"list all automation actions"
"show automation action PABC"
"create automation action 'Restart Nginx'"
"run automation action PABC on incident P123"
"list automation runners"
```

### Event Orchestration

```
"list all event orchestrations"
"create orchestration 'Production Alerts'"
"show routing rules for orchestration PABC"
"show service orchestration rules for service PDEF"
"delete orchestration PABC"
```

### Analysis & Reports

```
"operational summary for last 24 hours"
"analyze incident patterns for last 7 days"
"check SLA breaches this week"
"on-call burnout report for last month"
"generate postmortem for incident P1ABC23"
"MTTA/MTTR report for this week"
```

### Other

```
"who is on call right now?"
"who was paged in the last 6 hours?"
"audit log for today"
"what config changes were made this week?"
"list priority levels"
"list business services"
"service dependencies for PABC"
"find Datadog vendor"
"list webhook subscriptions"
"what features are enabled on this account?"
```

---

## Tool Routing

The bot has **105+ tools** but only sends a relevant subset to the LLM per query. This keeps requests within token limits and improves response speed.

**How it works:**

1. Your query is scanned for keywords
2. Matching keyword groups activate relevant tool sets
3. Only 5–20 tools are sent per request (instead of 105+)

**Example routing:**
| Query | Groups Activated | Tools Sent |
|-------|-----------------|------------|
| "who is on call?" | `oncall`, `utility` | ~10 |
| "resolve incident P123" | `incident`, `utility` | ~9 |
| "check SLA breaches" | `analytics`, `incident`, `utility` | ~14 |
| "run automation action" | `automation`, `utility` | ~6 |
| "show orchestration rules" | `orchestration`, `service`, `utility` | ~16 |

---

## Dry-Run Mode

Prevents any destructive operations from executing. Logs what *would* happen instead.

```bash
# Enable via CLI flag
python -m pagerduty_sre_bot --dry-run

# Or via environment variable
DRY_RUN=true python -m pagerduty_sre_bot

# Or via config.yml
# dry_run: true
```

**Output example:**
```
🔒 DRY-RUN: Would have executed → delete_service PABC123
🔒 DRY-RUN: Would have executed → manage_incident P1ABC23 → resolve
```

---

## Proactive Monitoring

A background daemon polls PagerDuty for new triggered incidents and alerts you inline.

```bash
python -m pagerduty_sre_bot --monitor
```

```
🔔 Monitoring daemon started (polling every 60s for high-urgency triggered incidents)

🚨 NEW INCIDENT [HIGH] P1ABC23 │ Database connection pool exhausted │ service=Payment API │ 2025-01-15T10:30:45Z
```

Configure in `config.yml`:
```yaml
monitoring:
  poll_interval_seconds: 60   # poll frequency
  urgency_filter: high        # "high" or "low"
```

---

## Conversation Persistence

Chat history saves after each turn and reloads on startup, giving the bot memory across sessions.

- Only user messages and final answers are saved (tool intermediates stripped)
- When history exceeds 30 messages, the oldest half is summarized into one context message
- History file: `conversation_history.json` (configurable)

```bash
# Disable persistence
python -m pagerduty_sre_bot --no-persist

# Custom history file
python -m pagerduty_sre_bot --history /tmp/pd_chat.json
```

---

## Example Interactions

### Quick Status Check
```
You: what's happening right now?

  Tool routing: analytics, incident, utility → 14 tools
  ⚙  resolve_time({"expression":"24 hours ago"…})
  ⚙  list_incidents({"since":"2025-01-14T10:00:00Z","until":"2025-01-15T10:00:00Z"…})

🤖 Assistant:
Here's your current operational status:
- **3 triggered incidents** (2 high urgency)
- **1 acknowledged incident** being worked on
- **12 incidents resolved** in the last 24 hours
- Average MTTA: 2.3 minutes | Average MTTR: 34.7 minutes
```

### Acknowledge + Note in One Request
```
You: acknowledge incident P1ABC23 and add a note saying I'm investigating the database

  ⚙  manage_incident({"incident_id":"P1ABC23","action":"acknowledge"})
  ⚙  manage_incident({"incident_id":"P1ABC23","action":"add_note","note_content":"I'm investigating the database"})

🤖 Assistant:
Done! Incident P1ABC23 has been acknowledged and I've added the note
"I'm investigating the database".
```

### Page Additional Responders
```
You: page the DBA team onto incident P1ABC23

  ⚙  list_users({"query":"DBA"})
  ⚙  create_responder_request({"incident_id":"P1ABC23","requester_id":"PSELF","targets":[...]})

🤖 Assistant:
I've paged the DBA team onto incident P1ABC23. They'll receive
notifications based on their notification rules.
```

### Create an On-Call Schedule
```
You: create a weekly rotation schedule called "Backend On-Call" with users P1USER, P2USER starting next Monday

  ⚙  resolve_time({"expression":"next Monday"})
  ⚙  create_schedule({"name":"Backend On-Call","schedule_layers":[{"start":"2025-01-20T00:00:00Z","rotation_turn_length_seconds":604800,"user_ids":["P1USER","P2USER"]}]})

🤖 Assistant:
Created schedule "Backend On-Call":
- Weekly rotation: P1USER → P2USER (7-day turns)
- Starting: 2025-01-20T00:00:00Z (UTC)
- URL: https://your-account.pagerduty.com/schedules/PNEW123
```

---

## Extending the Bot

### Adding a New Tool (4 Steps)

**1. Create the function** in the appropriate `tools/*.py` file:

```python
# In tools/my_domain.py
from pagerduty_sre_bot.clients import pd_client
from pagerduty_sre_bot.retry import with_retry

@with_retry()
def tool_my_new_tool(args: dict) -> dict:
    try:
        result = pd_client.rget(f"my_endpoint/{args['id']}")
        return {"success": True, "data": result}
    except Exception as e:
        return {"error": str(e)}
```

**2. Add the JSON schema** to `schemas.py`:

```python
{
    "type": "function",
    "function": {
        "name": "my_new_tool",
        "description": "What this tool does.",
        "parameters": {
            "type": "object",
            "properties": {"id": {"type": "string"}},
            "required": ["id"],
        },
    },
},
```

**3. Register** in `tool_registry.py`:

```python
from pagerduty_sre_bot.tools.my_domain import tool_my_new_tool

TOOL_DISPATCH = {
    ...
    "my_new_tool": tool_my_new_tool,
}
```

**4. Add routing** in `tool_router.py`:

```python
TOOL_GROUPS = {
    ...
    "my_group": ["my_new_tool"],
}

_KEYWORD_RULES = [
    ...
    ({"my keyword", "another keyword"}, ["my_group", "utility"]),
]
```

---

## Troubleshooting

### Common Errors

| Error | Cause | Fix |
|-------|-------|-----|
| `ModuleNotFoundError: No module named 'pagerduty_sre_bot'` | Running from wrong directory or not installed | `cd` to project root, run `pip install -e .`, then `python -m pagerduty_sre_bot` |
| `ValueError: Missing required API keys` | `.env` not found or missing keys | Create `.env` at project root with `ANTHROPIC_API_KEY` and `PAGERDUTY_API_KEY` |
| `ImportError: cannot import name 'xyz'` | File has old version without new functions | Replace file content with latest version from the artifacts |
| `SyntaxError` in a `.py` file | Shell commands or markers pasted into Python file | Open file and ensure it contains only Python code, no `cat >`, `PYEOF`, etc. |
| `HTTP 400` on write operations | Missing `PAGERDUTY_EMAIL` | Add `PAGERDUTY_EMAIL=you@company.com` to `.env` |
| `HTTP 429 Rate Limited` | Too many API calls | Bot auto-retries with backoff; if persistent, reduce `max_results` in config |
| `Tool routing missed my query` | Keywords not matched | Add your keywords to `_KEYWORD_RULES` in `tool_router.py` |
| `Context too long` error | History too big for model | Use `clear` command, or reduce `history.max_messages` in config |

### Key Rules

1. **Always run from the project root** (where `.env` lives): `cd ~/Desktop/PD_AI_Final`
2. **Always use `python -m pagerduty_sre_bot`** — not `python __main__.py`
3. **After editing files**, no reinstall needed if you used `pip install -e .`
4. **Use `status` command** in the chat to verify config, cache, and history

### Debug Tips

- The bot prints each tool call as it executes: `⚙  tool_name({args...})`
- Use `--dry-run` to test destructive operations safely
- Check `conversation_history.json` for saved context
- Use `cache clear` if you're getting stale data

---

## API Coverage Summary

| Category | Tools | Coverage |
|----------|-------|----------|
| Incidents (CRUD + manage) | 7 | ✅ 100% |
| Events API v2 | 2 | ✅ 100% |
| Alerts Management | 4 | ✅ 100% |
| Status Updates + Responders | 5 | ✅ 100% |
| Services (CRUD + integrations) | 7 | ✅ 100% |
| Users (CRUD + contacts) | 7 | ✅ 100% |
| Teams (CRUD + membership) | 7 | ✅ 100% |
| Escalation Policies | 5 | ✅ 100% |
| Schedules (CRUD + overrides) | 9 | ✅ 100% |
| On-Calls | 1 | ✅ 100% |
| Custom Fields | 7 | ✅ 100% |
| Automation Actions | 5 | ✅ ~80% |
| Event Orchestration | 9 | ✅ ~85% |
| Analytics | 4 | 🟡 ~50% |
| Maintenance Windows | 3 | ✅ 100% |
| Notifications + Logs | 2 | ✅ 100% |
| Audit Records | 1 | ✅ 100% |
| Config (tags, vendors, webhooks) | 15 | 🟡 ~70% |
| Analysis (patterns, SLA, burnout) | 5 | ✅ 100% |
| **Total** | **~105** | **~55%** |

Remaining gaps (lower priority): SCIM v2, Slack Connections, Jira Integration, full Extension CRUD, Notification Subscriptions, Session Management. See the gap analysis document for the complete list.

---

## License

MIT License. See [LICENSE](LICENSE) for details.

---

<p align="center">
  <b>Built for SRE teams who prefer the terminal over clicking through UIs.</b><br>
  <sub>If this helps your on-call life, give it a ⭐</sub>
</p>
