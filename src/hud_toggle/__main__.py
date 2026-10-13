"""CLI entry point.

Usage:
    python -m hud_toggle                 # run with default config
    python -m hud_toggle --config PATH   # run with a specific config
    python -m hud_toggle --list          # list detected HUD candidates
    python -m hud_toggle --toggle-once   # hide, wait, restore, exit
"""
from __future__ import annotations

import argparse
import sys

from hud_toggle.bootstrap.app import App
from hud_toggle.config.loader import load_config
from hud_toggle.utils.logging import configure_logging, get_logger

log = get_logger(__name__)


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="hud-toggle",
        description="Toggle HUD overlays on and off for clean screenshots.",
    )
    p.add_argument("--config", metavar="PATH", help="path to config TOML")
    p.add_argument("--list", action="store_true", help="list detected HUD candidates and exit")
    p.add_argument(
        "--toggle-once",
        action="store_true",
        help="hide HUDs, hold for --hold seconds, restore, exit",
    )
    p.add_argument(
        "--hold",
        type=float,
        default=3.0,
        metavar="SECONDS",
        help="seconds to keep HUDs hidden in --toggle-once mode (default: 3.0)",
    )
    p.add_argument("--verbose", "-v", action="count", default=0)
    return p


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    configure_logging(verbosity=args.verbose)

    cfg = load_config(args.config)
    log.info("config.loaded", path=args.config or "<default>", huds=len(cfg.hud_rules))

    app = App(cfg)

    if args.list:
        for candidate in app.detect_candidates():
            print(f"{candidate.process_name:32} {candidate.window_title}")
        return 0

    if args.toggle_once:
        app.toggle_once(hold_seconds=args.hold)
        return 0

    return app.run_forever()


if __name__ == "__main__":
    sys.exit(main())