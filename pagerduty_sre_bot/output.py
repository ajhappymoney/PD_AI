"""Rich-formatted CLI output helpers with graceful plain-text fallback."""

import re

try:
    from rich.console import Console
    from rich.markdown import Markdown
    from rich.rule import Rule

    RICH_AVAILABLE = True
    console = Console()
except ImportError:
    RICH_AVAILABLE = False
    console = None
    print("[WARNING] 'rich' not installed. Run: pip install rich  (plain text mode active)")


def cprint(msg: str, **kwargs) -> None:
    """Print with Rich markup, falling back to plain text."""
    if RICH_AVAILABLE:
        console.print(msg, **kwargs)
    else:
        plain = re.sub(r"\[.*?\]", "", str(msg))
        print(plain)


def print_rule(title: str = "") -> None:
    if RICH_AVAILABLE:
        console.print(Rule(title))
    else:
        sep = f"\n{'─' * 50} {title} {'─' * 50}\n" if title else "─" * 100
        print(sep)


def render_markdown(text: str) -> None:
    if RICH_AVAILABLE:
        console.print(Markdown(text))
    else:
        print(text)