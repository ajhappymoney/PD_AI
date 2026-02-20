"""Proactive monitoring daemon — polls PagerDuty for new high-urgency incidents."""

import threading
import time

from pagerduty_sre_bot.clients import pd_client
from pagerduty_sre_bot.time_utils import iso_hours_ago, iso_now
from pagerduty_sre_bot.output import cprint

_active = threading.Event()
_active.set()


def stop_monitoring() -> None:
    _active.clear()


def _daemon(config: dict) -> None:
    poll = config["monitoring"]["poll_interval_seconds"]
    urgency = config["monitoring"]["urgency_filter"]
    seen: set[str] = set()

    cprint(
        f"\n[bold yellow]🔔 Monitoring daemon started "
        f"(polling every {poll}s for {urgency}-urgency triggered incidents)[/bold yellow]"
    )

    while _active.is_set():
        try:
            window_start = iso_hours_ago(poll / 3600 * 2)
            window_end = iso_now()
            params = {
                "since": window_start,
                "until": window_end,
                "statuses[]": ["triggered"],
                "urgencies[]": [urgency],
                "sort_by": "created_at:desc",
            }
            raw: list = []
            try:
                for item in pd_client.iter_all("incidents", params=params):
                    raw.append(item)
                    if len(raw) >= 20:
                        break
            except Exception:
                pass

            for inc in raw:
                if inc["id"] not in seen:
                    seen.add(inc["id"])
                    svc = inc.get("service", {}).get("summary", "?")
                    ts = inc.get("created_at", "?")
                    url = inc.get("html_url", "")
                    cprint(
                        f"\n[bold red]🚨 NEW INCIDENT [{urgency.upper()}] {inc['id']}[/bold red] "
                        f"│ [white]{inc['title']}[/white] "
                        f"│ service=[cyan]{svc}[/cyan] "
                        f"│ [dim]{ts}[/dim] "
                        f"│ {url}"
                    )

            if len(seen) > 500:
                seen = set(list(seen)[-200:])
        except Exception as e:
            cprint(f"[dim]Monitor error: {e}[/dim]")

        for _ in range(int(poll)):
            if not _active.is_set():
                break
            time.sleep(1)

    cprint("[dim]Monitoring daemon stopped.[/dim]")


def start_monitoring(config: dict) -> threading.Thread:
    _active.set()
    t = threading.Thread(target=_daemon, args=(config,), daemon=True, name="pd-monitor")
    t.start()
    return t