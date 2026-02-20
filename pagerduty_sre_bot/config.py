"""YAML configuration loading with defaults."""

import os
from pathlib import Path

import yaml

DEFAULT_CONFIG: dict = {
    "model": {
        "primary": "moonshotai/kimi-k2-instruct-0905",
        "fallback": "llama-3.3-70b-versatile",
    },
    "defaults": {
        "time_window_hours": 24,
        "max_results": 50,
    },
    "sla": {
        "mtta_minutes": 5,
        "mttr_minutes": 60,
    },
    "monitoring": {
        "poll_interval_seconds": 60,
        "urgency_filter": "high",
    },
    "cache": {
        "ttl_seconds": 300,
    },
    "history": {
        "file": "conversation_history.json",
        "max_messages": 40,
        "compress_at": 30,
    },
    "output": {
        "rich_tables": True,
    },
    "dry_run": False,
}


def _deep_merge(base: dict, override: dict) -> dict:
    result = dict(base)
    for k, v in override.items():
        if isinstance(v, dict) and isinstance(result.get(k), dict):
            result[k] = _deep_merge(result[k], v)
        else:
            result[k] = v
    return result


def load_config(path: str) -> dict:
    """Load config from YAML, creating defaults if file is absent."""
    cfg = DEFAULT_CONFIG.copy()
    p = Path(path)
    if p.exists():
        with open(p) as f:
            user_cfg = yaml.safe_load(f) or {}
        cfg = _deep_merge(cfg, user_cfg)
    else:
        with open(p, "w") as f:
            yaml.dump(DEFAULT_CONFIG, f, default_flow_style=False)
        print(f"[INFO] Created default config at {p}")
    return cfg


def is_dry_run(args, config: dict) -> bool:
    """Resolve dry-run from CLI flag, env var, or config."""
    return (
            args.dry_run
            or os.getenv("DRY_RUN", "false").lower() == "true"
            or config.get("dry_run", False)
    )