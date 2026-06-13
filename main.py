"""Entry point for the FIFA World Cup 2026 WhatsApp notifier.

Usage:
    python main.py preview   # 9 PM IST  — tonight's slate
    python main.py recap     # 11 AM IST — last night's results
"""

from __future__ import annotations

import argparse

from src import log
from src.config import get_settings
from src.pipeline import Notifier


def main() -> None:
    """Parse the mode argument and run one notification."""
    parser = argparse.ArgumentParser(description="FIFA World Cup 2026 WhatsApp notifier")
    parser.add_argument("mode", choices=("preview", "recap"), help="which daily update to send")
    parser.add_argument(
        "--dry-run", action="store_true", help="print the message instead of sending it"
    )
    args = parser.parse_args()

    log.setup()
    Notifier(get_settings(), dry_run=args.dry_run).run(args.mode)


if __name__ == "__main__":
    main()
