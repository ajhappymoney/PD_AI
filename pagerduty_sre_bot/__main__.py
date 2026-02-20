#!/usr/bin/env python3
"""Entry point: python -m pagerduty_sre_bot"""

import signal
import sys

from pagerduty_sre_bot.cli import parse_args
from pagerduty_sre_bot.config import load_config, is_dry_run
from pagerduty_sre_bot.output import cprint, print_rule
from pagerduty_sre_bot.history import load_history, save_history
from pagerduty_sre_bot.compression import compress_history
from pagerduty_sre_bot.monitoring import start_monitoring, stop_monitoring
from pagerduty_sre_bot.conversation import run_conversation
from pagerduty_sre_bot.cache import cache_clear

HELP_TEXT = """
╔══════════════════════════════════════════════════════════════════════════╗
║          PagerDuty SRE AI Assistant — Enhanced Edition                  ║
╠══════════════════════════════════════════════════════════════════════════╣
║  INCIDENTS                                                               ║
║    "show incidents from last 24 hours"                                   ║
║    "acknowledge / resolve incident P1ABC23"                              ║
║    "generate postmortem for P1ABC23"                                     ║
║  ANALYSIS                                                                ║
║    "analyze patterns for last 7 days"                                    ║
║    "check SLA breaches this week"                                        ║
║    "on-call burnout report for last month"                               ║
║  ON-CALL & SCHEDULES                                                     ║
║    "who is on call right now?"                                           ║
║  SERVICES / USERS / TEAMS / ESCALATION                                   ║
║    "list all services" / "list users" / "list teams"                     ║
║  AUDIT & NOTIFICATIONS                                                   ║
║    "audit log for today" / "who was paged last 6 hours?"                 ║
║  COMMANDS                                                                ║
║    help / clear / status / cache clear / exit                            ║
╚══════════════════════════════════════════════════════════════════════════╝
"""


def print_status(args, config):
    from pagerduty_sre_bot.cache import cache_size
    from pagerduty_sre_bot.history import history_path

    dry = "[bold red]ENABLED[/bold red]" if is_dry_run(args, config) else "[green]disabled[/green]"
    mon = "[green]active[/green]" if args.monitor else "[dim]off[/dim]"
    cprint(
        f"[bold]Config:[/bold] {args.config} | "
        f"[bold]Model:[/bold] {config['model']['primary']} | "
        f"[bold]Dry-run:[/bold] {dry} | "
        f"[bold]Monitor:[/bold] {mon} | "
        f"[bold]Cached:[/bold] {cache_size()} | "
        f"[bold]History:[/bold] {'disabled' if args.no_persist else str(history_path(args, config))}"
    )


def main():
    args = parse_args()
    config = load_config(args.config)
    dry_run = is_dry_run(args, config)

    model_primary = config["model"]["primary"]
    model_fallback = config["model"]["fallback"]

    cprint("\n[bold blue]🚀 PagerDuty Full-Feature SRE AI Assistant — Enhanced Edition[/bold blue]")
    print_rule()
    cprint(f"  Model   : [cyan]{model_primary}[/cyan] (fallback: {model_fallback})")
    cprint(f"  Dry-run : {'[bold red]ENABLED[/bold red]' if dry_run else '[green]disabled[/green]'}")
    cprint(f"  Monitor : {'[bold yellow]active[/bold yellow]' if args.monitor else '[dim]off[/dim]'}")
    cprint(f"  Config  : [dim]{args.config}[/dim]")
    cprint("  Type [bold]help[/bold] for capabilities, [bold]exit[/bold] to quit\n")

    conversation_history = load_history(args, config)

    if args.monitor:
        start_monitoring(config)

    def _shutdown(sig, frame):
        cprint("\n[yellow]Shutting down…[/yellow]")
        stop_monitoring()
        save_history(conversation_history, args, config)
        sys.exit(0)

    signal.signal(signal.SIGINT, _shutdown)
    signal.signal(signal.SIGTERM, _shutdown)

    try:
        from rich.console import Console
        console = Console()
        use_rich_input = True
    except ImportError:
        use_rich_input = False

    while True:
        try:
            if use_rich_input:
                query = console.input("\n[bold green]You:[/bold green] ").strip()
            else:
                query = input("\nYou: ").strip()
        except (EOFError, KeyboardInterrupt):
            _shutdown(None, None)
            break

        if not query:
            continue

        q = query.lower()

        if q in ("exit", "quit", "q"):
            cprint("[bold]Goodbye! 👋[/bold]")
            stop_monitoring()
            save_history(conversation_history, args, config)
            break

        if q in ("help", "?", "h"):
            cprint(HELP_TEXT)
            continue

        if q == "clear":
            conversation_history = []
            save_history([], args, config)
            cprint("[green]Conversation history cleared.[/green]")
            continue

        if q == "status":
            print_status(args, config)
            continue

        if q == "cache clear":
            cache_clear()
            cprint("[green]Cache cleared.[/green]")
            continue

        try:
            print_rule()
            answer, conversation_history = run_conversation(
                query, conversation_history, config, dry_run
            )
            print_rule()
            conversation_history = compress_history(conversation_history, config)
            save_history(conversation_history, args, config)
        except KeyboardInterrupt:
            cprint("\n[yellow]Interrupted.[/yellow]")
        except Exception as e:
            cprint(f"\n[bold red]❌ Error:[/bold red] {e}")
            import traceback
            cprint(f"[dim]{traceback.format_exc()}[/dim]")


if __name__ == "__main__":
    main()