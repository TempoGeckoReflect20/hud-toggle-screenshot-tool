"""Top-level application object.

Wires the platform adapter to the HUD services and owns the hotkey
listener. This is the only place that knows about all three layers at
once — handlers stay thin, services stay pure, adapters stay dumb.
"""
from __future__ import annotations

import time

from hud_toggle.adapters.win32_window import Win32WindowAdapter
from hud_toggle.config.models import AppConfig
from hud_toggle.core.hotkey import HotkeyBinder
from hud_toggle.services.hud_detector import HudDetector
from hud_toggle.services.hud_toggler import HudToggler
from hud_toggle.services.screenshot_guard import ScreenshotGuard
from hud_toggle.utils.logging import get_logger

log = get_logger(__name__)


class App:
    """Owns the runtime graph: adapter -> detector -> toggler -> guard."""

    def __init__(self, config: AppConfig) -> None:
        self._config = config
        self._adapter = Win32WindowAdapter()
        self._detector = HudDetector(self._adapter, config.hud_rules)
        self._toggler = HudToggler(self._adapter)
        self._guard = ScreenshotGuard(self._detector, self._toggler, config.guard)
        self._hotkeys = HotkeyBinder(config.hotkeys)

    def detect_candidates(self):
        return self._detector.scan()

    def toggle_once(self, hold_seconds: float) -> None:
        """Hide HUDs, sleep, restore. Used by --toggle-once."""
        state = self._guard.arm()
        log.info("toggle_once.armed", hidden=len(state.hidden_handles))
        time.sleep(max(0.0, hold_seconds))
        self._guard.disarm(state)
        log.info("toggle_once.restored", restored=len(state.hidden_handles))

    def run_forever(self) -> int:
        self._hotkeys.on("toggle", self._guard.flip)
        self._hotkeys.on("toggle_once", lambda: self.toggle_once(self._config.guard.hold_seconds))
        self._hotkeys.on("quit", self._hotkeys.stop)
        log.info("app.running", hotkeys=list(self._config.hotkeys.bindings))
        self._hotkeys.block_until_stopped()
        return 0