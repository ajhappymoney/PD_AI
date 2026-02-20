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
    Keep only user turns and final assistant text turns.
    Drop tool-call assistant turns and raw tool results.
    """
    clean = []
    for m in history:
        if not isinstance(m, dict):
            continue
        role = m.get("role")
        if role == "user":
            clean.append(m)
        elif role == "assistant" and not m.get("tool_calls"):
            clean.append(m)
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