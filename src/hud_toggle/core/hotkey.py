"""Global hotkey binder. Wraps the `keyboard` package.

Registered hotkeys are global to the Windows session — they fire even
when the tool isn't focused. That's intentional: you're usually in a
game or a full-screen app when you want to toggle the HUD.
"""
from __future__ import annotations

import threading
from collections.abc import Callable

import keyboard

from hud_toggle.config.models import HotkeyConfig
from hud_toggle.utils.logging import get_logger

log = get_logger(__name__)


class HotkeyBinder:
    def __init__(self, config: HotkeyConfig) -> None:
        self._config = config
        self._callbacks: dict[str, Callable[[], None]] = {}
        self._handles: list[object] = []
        self._stopped = threading.Event()

    def on(self, name: str, callback: Callable[[], None]) -> None:
        if name not in self._config.bindings:
            raise KeyError(f"unknown hotkey slot: {name}")
        self._callbacks[name] = callback

    def start(self) -> None:
        for name, combo in self._config.bindings.items():
            cb = self._callbacks.get(name)
            if cb is None:
                continue
            handle = keyboard.add_hotkey(combo, self._wrap(name, cb), suppress=False)
            self._handles.append(handle)
            log.info("hotkey.bound", name=name, combo=combo)

    def _wrap(self, name: str, cb: Callable[[], None]) -> Callable[[], None]:
        def _run() -> None:
            try:
                cb()
            except Exception:  # noqa: BLE001 - hotkey thread must not die
                log.exception("hotkey.callback_failed", name=name)
        return _run

    def stop(self) -> None:
        for handle in self._handles:
            try:
                keyboard.remove_hotkey(handle)
            except (KeyError, ValueError):
                pass
        self._handles.clear()
        self._stopped.set()

    def block_until_stopped(self) -> None:
        self.start()
        try:
            self._stopped.wait()
        except KeyboardInterrupt:
            log.info("hotkey.interrupted")
        finally:
            self.stop()