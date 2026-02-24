"""LLM conversation loop using Anthropic Claude API with tool use."""

import json

from anthropic import APIStatusError, APIConnectionError

from pagerduty_sre_bot.clients import anthropic_client
from pagerduty_sre_bot.schemas import TOOLS
from pagerduty_sre_bot.system_prompt import SYSTEM_PROMPT
from pagerduty_sre_bot.tool_registry import execute_tool
from pagerduty_sre_bot.tool_router import select_tools_for_query
from pagerduty_sre_bot.history import sanitize_history
from pagerduty_sre_bot.time_utils import now_utc
from pagerduty_sre_bot.output import cprint, RICH_AVAILABLE, console

try:
    from rich.markdown import Markdown
except ImportError:
    Markdown = None


# ── Schema Converter ──────────────────────────────────
# Our schemas.py uses OpenAI/Groq format. Anthropic needs a different shape.

def _convert_tools_to_anthropic(tools: list[dict]) -> list[dict]:
    """
    Convert OpenAI-style tool schemas to Anthropic format.

    OpenAI:  {"type":"function","function":{"name":"x","description":"y","parameters":{...}}}
    Anthropic: {"name":"x","description":"y","input_schema":{...}}
    """
    converted = []
    for t in tools:
        fn = t.get("function", {})
        converted.append({
            "name": fn["name"],
            "description": fn.get("description", ""),
            "input_schema": fn.get("parameters", {"type": "object", "properties": {}}),
        })
    return converted


# ── LLM Call ──────────────────────────────────────────

def _call_claude(
        system: str,
        messages: list,
        model: str,
        fallback_model: str | None = None,
        tools: list | None = None,
        max_tokens: int = 4096,
):
    """
    Call Anthropic Claude API with tool use.
    Falls back to fallback_model on failure.
    """
    kwargs = dict(
        model=model,
        system=system,
        messages=messages,
        max_tokens=max_tokens,
    )
    if tools:
        kwargs["tools"] = tools
        kwargs["tool_choice"] = {"type": "auto"}

    try:
        return anthropic_client.messages.create(**kwargs)
    except (APIStatusError, APIConnectionError) as e:
        if fallback_model and model != fallback_model:
            cprint(f"[yellow]⚠  Primary model failed ({e}), falling back to {fallback_model}…[/yellow]")
            kwargs["model"] = fallback_model
            return anthropic_client.messages.create(**kwargs)
        raise


def _extract_text(response) -> str:
    """Extract all text content from a Claude response."""
    parts = []
    for block in response.content:
        if block.type == "text":
            parts.append(block.text)
    return "\n".join(parts)


def _has_tool_use(response) -> bool:
    """Check if the response contains any tool_use blocks."""
    return any(block.type == "tool_use" for block in response.content)


def _response_to_assistant_message(response) -> dict:
    """
    Convert Claude response to a message dict for the conversation history.
    Preserves both text and tool_use blocks.
    """
    content = []
    for block in response.content:
        if block.type == "text":
            content.append({"type": "text", "text": block.text})
        elif block.type == "tool_use":
            content.append({
                "type": "tool_use",
                "id": block.id,
                "name": block.name,
                "input": block.input,
            })
    return {"role": "assistant", "content": content}


def run_conversation(
        user_query: str,
        conversation_history: list,
        config: dict,
        dry_run: bool = False,
) -> tuple[str, list]:
    """
    Run one conversation turn using Claude.
    Returns (answer_text, updated_history).
    """
    # Propagate dry_run to all tool modules that have destructive operations
    from pagerduty_sre_bot.tools import (
        incidents, services, users, teams, escalation, schedules,
        maintenance, config_resources, events, alerts, status_updates,
        custom_fields, automation, orchestration,
    )
    for mod in (
            incidents, services, users, teams, escalation, schedules,
            maintenance, config_resources, events, alerts, status_updates,
            custom_fields, automation, orchestration,
    ):
        mod.set_dry_run(dry_run)

    now = now_utc()
    model_primary = config["model"]["primary"]
    model_fallback = config["model"]["fallback"]

    system = SYSTEM_PROMPT.format(
        current_time=now.strftime("%Y-%m-%dT%H:%M:%SZ"),
        dry_run_status="ENABLED" if dry_run else "disabled",
    )

    # Build messages — Claude uses system separately, not as a message
    messages = list(conversation_history)
    messages.append({"role": "user", "content": user_query})

    # Select and convert tools for this query
    active_tools_openai = select_tools_for_query(user_query)
    active_tools = _convert_tools_to_anthropic(active_tools_openai)

    rounds = 0
    answer = ""

    while rounds < 10:
        rounds += 1

        response = _call_claude(
            system=system,
            messages=messages,
            model=model_primary,
            fallback_model=model_fallback,
            tools=active_tools,
        )

        if not _has_tool_use(response):
            # Final answer — no more tool calls
            answer = _extract_text(response)
            messages.append({"role": "assistant", "content": answer})

            cprint("\n[bold blue]🤖 Assistant:[/bold blue]")
            if answer:
                if RICH_AVAILABLE and Markdown:
                    console.print(Markdown(answer))
                else:
                    print(answer)
            break

        # ── Process tool calls ──────────────────────────
        # Add the full assistant response (with tool_use blocks) to messages
        messages.append(_response_to_assistant_message(response))

        # Collect all tool results into a single user message
        tool_results = []
        for block in response.content:
            if block.type != "tool_use":
                continue

            fn_name = block.name
            fn_args = block.input or {}
            tool_use_id = block.id

            preview = json.dumps(fn_args, default=str)[:120]
            cprint(f"  [cyan]⚙  {fn_name}[/cyan]([dim]{preview}…[/dim])")

            result = execute_tool(fn_name, fn_args)
            result_str = json.dumps(result, indent=2, default=str)

            # Truncate very large results
            if len(result_str) > 28000:
                result_str = result_str[:28000] + "\n…[result truncated to fit context]"

            tool_results.append({
                "type": "tool_result",
                "tool_use_id": tool_use_id,
                "content": result_str,
            })

        # Anthropic requires tool results as a user message
        messages.append({"role": "user", "content": tool_results})

    else:
        answer = "I reached the maximum tool-call rounds. Please try a more specific question."

    # Sanitize for persistence: keep only user text + assistant text
    updated_history = sanitize_history(messages)
    return answer, updated_history