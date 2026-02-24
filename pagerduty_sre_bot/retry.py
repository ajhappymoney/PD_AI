"""Exponential-backoff retry decorator for transient API errors."""

import time
from functools import wraps

from anthropic import APIConnectionError, APIStatusError, RateLimitError

from pagerduty_sre_bot.output import cprint

RETRYABLE_EXCEPTIONS = (APIConnectionError, RateLimitError)


def with_retry(max_retries: int = 3, base_delay: float = 1.0):
    """Retry on transient errors with exponential back-off."""

    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            last_exc = None
            for attempt in range(max_retries):
                try:
                    return fn(*args, **kwargs)
                except RETRYABLE_EXCEPTIONS as e:
                    last_exc = e
                    delay = base_delay * (2 ** attempt)
                    cprint(
                        f"[yellow]⚠  Transient error ({type(e).__name__}), "
                        f"retrying in {delay:.1f}s… (attempt {attempt + 1}/{max_retries})[/yellow]"
                    )
                    time.sleep(delay)
                except APIStatusError as e:
                    if e.status_code == 429:
                        last_exc = e
                        delay = base_delay * (2 ** attempt)
                        cprint(f"[yellow]⚠  Rate-limited (429), retrying in {delay:.1f}s…[/yellow]")
                        time.sleep(delay)
                    elif e.status_code == 529:  # Anthropic overloaded
                        last_exc = e
                        delay = base_delay * (2 ** attempt) * 2
                        cprint(f"[yellow]⚠  API overloaded (529), retrying in {delay:.1f}s…[/yellow]")
                        time.sleep(delay)
                    else:
                        raise
            raise last_exc

        return wrapper

    return decorator