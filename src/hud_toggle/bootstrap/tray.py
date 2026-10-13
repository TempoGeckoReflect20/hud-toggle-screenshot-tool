"""System-tray wrapper. Optional — the CLI works without it.

Uses pywin32's shell notify icon directly rather than pystray so we
don't drag in a second GUI stack. Menu is built from the same hotkey
bindings the CLI uses.
"""
from __future__ import annotations

import sys

from hud_toggle.bootstrap.app import App
from hud_toggle.config.loader import load_config
from hud_toggle.utils.logging import configure_logging, get_logger

log = get_logger(__name__)


def main() -> int:
    configure_logging(verbosity=1)
    cfg = load_config(None)
    app = App(cfg)

    try:
        import win32gui  # type: ignore[import-not-found]
        import win32con  # type: ignore[import-not-found]
    except ImportError:
        log.error("tray.pywin32_missing")
        print("pywin32 is required for the tray build. pip install pywin32", file=sys.stderr)
        return 2

    # Minimal hidden window to receive the tray callbacks.
    wc = win32gui.WNDCLASS()
    wc.lpszClassName = "HudToggleTray"
    wc.hInstance = win32gui.GetModuleHandle(None)
    wc.lpfnWndProc = _wnd_proc  # type: ignore[assignment]
    win32gui.RegisterClass(wc)

    hwnd = win32gui.CreateWindow(
        wc.lpszClassName, "hud-toggle", win32con.WS_OVERLAPPED,
        0, 0, 0, 0, 0, 0, wc.hInstance, None,
    )

    nid = (hwnd, 0, win32gui.NIF_ICON | win32gui.NIF_MESSAGE | win32gui.NIF_TIP,
           win32con.WM_USER + 20, win32gui.LoadIcon(0, win32con.IDI_APPLICATION),
           "hud-toggle")
    win32gui.Shell_NotifyIcon(win32gui.NIM_ADD, nid)
    log.info("tray.ready")

    app._hotkeys.on("quit", lambda: win32gui.PostMessage(hwnd, win32con.WM_CLOSE, 0, 0))
    try:
        app.run_forever()
    finally:
        win32gui.Shell_NotifyIcon(win32gui.NIM_DELETE, nid)
    return 0


def _wnd_proc(hwnd, msg, wparam, lparam):  # pragma: no cover - Win32 callback
    import win32con
    import win32gui
    if msg == win32con.WM_CLOSE:
        win32gui.DestroyWindow(hwnd)
        win32gui.PostQuitMessage(0)
        return 0
    return win32gui.DefWindowProc(hwnd, msg, wparam, lparam)


if __name__ == "__main__":
    sys.exit(main())