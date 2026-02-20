"""Command-line argument parsing."""

import argparse


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="PagerDuty SRE AI Assistant",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m pagerduty_sre_bot
  python -m pagerduty_sre_bot --monitor
  python -m pagerduty_sre_bot --dry-run
  python -m pagerduty_sre_bot --config my_config.yml --no-persist
        """,
    )
    parser.add_argument(
        "--monitor", action="store_true",
        help="Start proactive monitoring daemon alongside the chat loop",
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Print what destructive operations *would* do without executing them",
    )
    parser.add_argument(
        "--config", default="config.yml",
        help="Path to YAML config file (default: config.yml)",
    )
    parser.add_argument(
        "--no-persist", action="store_true",
        help="Do not load or save conversation history",
    )
    parser.add_argument(
        "--history", default=None,
        help="Path to conversation history JSON (overrides config)",
    )
    return parser.parse_args()