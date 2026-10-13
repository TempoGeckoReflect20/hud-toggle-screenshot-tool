"""Applies hide/minimize/restore to a set of HUD candidates."""
from __future__ import annotations

from hud_toggle.adapters.win32_window import Win32WindowAdapter
from hud_toggle.core.entities import HudAction, HudCandidate, ToggleState
from hud_toggle.utils.logging import get_logger

log = get_logger(__name__)


class HudToggler:
    def __init__(self, adapter: Win32WindowAdapter) -> None:
        self._adapter = adapter

    def hide_all(self, candidates: list[HudCandidate]) -> ToggleState:
        state = ToggleState()
        for c in candidates:
            if c.action is HudAction.IGNORE:
                continue
            if c.action is HudAction.HIDE:
                if self._adapter.hide(c.handle.value):
                    state.hidden_handles.append(c.handle.value)
            elif c.action is HudAction.MINIMIZE:
                if self._adapter.minimize(c.handle.value):
                    state.minimized_handles.append(c.handle.value)
            else:
                state.visible_handles.append(c.handle.value)
        log.info("toggler.hidden", hidden=len(state.hidden_handles),
                 minimized=len(state.minimized_handles))
        return state

    def restore(self, state: ToggleState) -> int:
        restored = 0
        for hwnd in (*state.hidden_handles, *state.minimized_handles):
            if not self._adapter.is_alive(hwnd):
                log.debug("toggler.skip_dead", hwnd=hex(hwnd))
                continue
            if self._adapter.restore(hwnd):
                restored += 1
        log.info("toggler.restored", count=restored)
        return restored