"""Scans the desktop for windows matching configured HUD rules."""
from __future__ import annotations

from hud_toggle.adapters.win32_window import Win32WindowAdapter
from hud_toggle.config.models import HudRule
from hud_toggle.core.entities import HudCandidate
from hud_toggle.core.matcher import match_window
from hud_toggle.utils.logging import get_logger

log = get_logger(__name__)


class HudDetector:
    def __init__(self, adapter: Win32WindowAdapter, rules: list[HudRule]) -> None:
        self._adapter = adapter
        self._rules = rules

    def scan(self) -> list[HudCandidate]:
        candidates: list[HudCandidate] = []
        for window in self._adapter.list_windows():
            hit = match_window(window, self._rules)
            if hit is not None:
                candidates.append(hit)
        if candidates:
            log.debug("detector.hits", count=len(candidates),
                      names=[c.rule_name for c in candidates])
        return candidates

    def scan_by_rule(self, rule_name: str) -> list[HudCandidate]:
        return [c for c in self.scan() if c.rule_name == rule_name]