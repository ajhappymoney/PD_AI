"""LLM conversation loop: tool rounds (non-streaming) → streaming final answer."""

import json

from groq import APIStatusError, APIConnectionError

from pagerduty_sre_bot.clients import groq_client
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


def _msg_to_dict(msg) -> dict:
    """Convert a Groq ChatCompletionMessage (Pydantic) to a plain dict."""
    d: dict = {"role": msg.role}
    if msg.content is not None:
        d["content"] = msg.content
    if getattr(msg, "tool_calls", None):
        d["tool_calls"] = [
            {
                "id": tc.id,
                "type": "function",
                "function": {
                    "name": tc.function.name,
                    "arguments": tc.function.arguments,
                },
            }
            for tc in msg.tool_calls
        ]
    return d


def _call_llm(
        messages: list,
        use_tools: bool = True,
        stream: bool = False,
        model: str | None = None,
        fallback_model: str | None = None,
        tools: list | None = None,
):
    """Call Groq with optional tool subset and streaming. Falls back on failure."""
    kwargs = dict(model=model, messages=messages, max_tokens=4096)
    if use_tools:
        kwargs["tools"] = tools if tools is not None else TOOLS
        kwargs["tool_choice"] = "auto"
    if stream:
        kwargs["stream"] = True

    try:
        return groq_client.chat.completions.create(**kwargs)
    except (APIStatusError, APIConnectionError) as e:
        if fallback_model and model != fallback_model:
            cprint(f"[yellow]⚠  Primary model failed ({e}), falling back to {fallback_model}…[/yellow]")
            kwargs["model"] = fallback_model
            return groq_client.chat.completions.create(**kwargs)
        raise


def run_conversation(
        user_query: str,
        conversation_history: list,
        config: dict,
        dry_run: bool = False,
) -> tuple[str, list]:
    """
    Run one conversation turn.
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

    messages = [{"role": "system", "content": system}] + conversation_history
    messages.append({"role": "user", "content": user_query})

    active_tools = select_tools_for_query(user_query)

    rounds = 0
    answer = ""

    while rounds < 10:
        rounds += 1

        response = _call_llm(
            messages, use_tools=True, stream=False,
            model=model_primary, fallback_model=model_fallback,
            tools=active_tools,
        )
        msg = response.choices[0].message

        if not msg.tool_calls:
            # Final answer
            messages.append({"role": "assistant", "content": msg.content or ""})
            cprint("\n[bold blue]🤖 Assistant:[/bold blue]")
            if msg.content:
                if RICH_AVAILABLE and Markdown:
                    console.print(Markdown(msg.content))
                else:
                    print(msg.content)
            answer = msg.content or ""
            break

        # Process tool calls
        messages.append(_msg_to_dict(msg))

        for tc in msg.tool_calls:
            fn_name = tc.function.name
            try:
                fn_args = json.loads(tc.function.arguments)
            except (json.JSONDecodeError, TypeError) as e:
                cprint(f"[red]⚠  Could not parse args for {fn_name}: {e}[/red]")
                fn_args = {}

            preview = json.dumps(fn_args, default=str)[:120]
            cprint(f"  [cyan]⚙  {fn_name}[/cyan]([dim]{preview}…[/dim])")

            result = execute_tool(fn_name, fn_args)
            result_str = json.dumps(result, indent=2, default=str)

            if len(result_str) > 28000:
                result_str = result_str[:28000] + "\n…[result truncated to fit context]"

            messages.append({
                "role": "tool",
                "tool_call_id": tc.id,
                "content": result_str,
            })
    else:
        answer = "I reached the maximum tool-call rounds. Please try a more specific question."

    updated_history = sanitize_history(messages[1:])
    return answer, updated_history