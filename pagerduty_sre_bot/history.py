"""Conversation persistence: load, save, and sanitize history."""

import json
from pathlib import Path
from typing import List

from pagerduty_sre_bot.output import cprint


def history_path(args, config: dict) -> Path:
    if args.history:
        return Path(args.history)
    return Path(config["history"]["file"])


def sanitize_history(history: list) -> list:
    """
    Keep only user text turns and final assistant text turns.
    Drop tool-call assistant turns (content is a list with tool_use blocks)
    and tool-result user turns (content is a list with tool_result blocks).

    Works with both Anthropic format (content can be str or list of blocks)
    and OpenAI format (tool_calls field on assistant messages).
    """
    clean = []
    for m in history:
        if not isinstance(m, dict):
            continue
        role = m.get("role")
        content = m.get("content")

        if role == "user":
            # Skip tool_result user messages (Anthropic format)
            if isinstance(content, list):
                # Check if this is a tool_result message
                if content and isinstance(content[0], dict) and content[0].get("type") == "tool_result":
                    continue
            # Keep normal user text messages
            if isinstance(content, str) and content.strip():
                clean.append({"role": "user", "content": content})

        elif role == "assistant":
            # Skip tool-call turns (OpenAI format)
            if m.get("tool_calls"):
                continue
            # Skip tool_use turns (Anthropic format — content is a list with tool_use blocks)
            if isinstance(content, list):
                has_tool_use = any(
                    isinstance(b, dict) and b.get("type") == "tool_use"
                    for b in content
                )
                if has_tool_use:
                    continue
                # Extract just text from list-format content
                text_parts = [
                    b.get("text", "") for b in content
                    if isinstance(b, dict) and b.get("type") == "text"
                ]
                text = "\n".join(text_parts).strip()
                if text:
                    clean.append({"role": "assistant", "content": text})
            elif isinstance(content, str) and content.strip():
                clean.append({"role": "assistant", "content": content})

    return clean


def load_history(args, config: dict) -> List[dict]:
    if args.no_persist:
        return []
    p = history_path(args, config)
    if p.exists():
        try:
            raw = json.loads(p.read_text())
            data = sanitize_history(raw)
            dropped = len(raw) - len(data)
            suffix = f" ({dropped} intermediate tool messages stripped)" if dropped else ""
            cprint(f"[dim]Loaded {len(data)} messages from {p}{suffix}[/dim]")
            return data
        except Exception:
            pass
    return []


def save_history(history: List[dict], args, config: dict) -> None:
    if args.no_persist:
        return
    p = history_path(args, config)
    try:
        p.write_text(json.dumps(history, indent=2, default=str))
    except Exception as e:
        cprint(f"[yellow]⚠  Could not save history: {e}[/yellow]")