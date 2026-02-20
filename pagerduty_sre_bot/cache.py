"""TTL cache for slow-changing PagerDuty resources."""

import time
from typing import Any, Optional

_store: dict[str, Any] = {}
_expiry: dict[str, float] = {}
_default_ttl: float = 300.0


def configure(ttl_seconds: float) -> None:
    global _default_ttl
    _default_ttl = ttl_seconds


def cache_get(key: str) -> Optional[Any]:
    if key in _store and time.time() < _expiry[key]:
        return _store[key]
    return None


def cache_set(key: str, value: Any, ttl: float | None = None) -> None:
    _store[key] = value
    _expiry[key] = time.time() + (ttl or _default_ttl)


def cache_clear(pattern: str | None = None) -> None:
    if pattern is None:
        _store.clear()
        _expiry.clear()
    else:
        for k in list(_store):
            if pattern in k:
                del _store[k]
                del _expiry[k]


def cache_size() -> int:
    return len(_store)