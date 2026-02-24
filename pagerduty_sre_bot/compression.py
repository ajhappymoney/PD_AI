"""Smart context compression — summarises old turns to save tokens."""

from typing import List

from pagerduty_sre_bot.clients import anthropic_client
from pagerduty_sre_bot.output import cprint


def compress_history(history: List[dict], config: dict) -> List[dict]:
    """
    When history exceeds compress_at, summarise the oldest half into
    a single assistant message.
    """
    compress_at = config["history"]["compress_at"]
    max_messages = config["history"]["max_messages"]
    fallback_model = config["model"]["fallback"]

    if len(history) < compress_at:
        return history

    half = len(history) // 2
    old_messages = history[:half]
    new_messages = history[half:]

    transcript = "\n".join(
        f"{m['role'].upper()}: {str(m.get('content', ''))[:500]}"
        for m in old_messages
        if m.get("content") and isinstance(m.get("content"), str) and m.get("role") in ("user", "assistant")
    )

    if not transcript.strip():
        return new_messages

    try:
        resp = anthropic_client.messages.create(
            model=fallback_model,
            system=(
                "You are a concise technical summariser. Summarise the following "
                "SRE/PagerDuty conversation into a brief bullet-point memory block "
                "covering: key incidents discussed, actions taken, decisions made, "
                "and any IDs or names that are important. Be terse — max 300 words."
            ),
            messages=[{"role": "user", "content": transcript}],
            max_tokens=400,
        )
        summary_text = resp.content[0].text if resp.content else ""
        summary_message = {
            "role": "assistant",
            "content": f"[CONVERSATION SUMMARY — earlier context]\n{summary_text}",
        }
        compressed = [summary_message] + new_messages
        cprint(f"[dim]Context compressed: {len(old_messages)} messages → 1 summary[/dim]")
        return compressed
    except Exception as e:
        cprint(f"[yellow]⚠  Context compression failed: {e}. Trimming instead.[/yellow]")
        return history[-max_messages:]