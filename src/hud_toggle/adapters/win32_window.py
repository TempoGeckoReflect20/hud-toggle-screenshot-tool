"""Win32 window enumeration and visibility control.

Uses EnumWindows + GetWindowThreadProcessId to build WindowHandle
records, and ShowWindow / SetWindowPos to hide and restore. Skips
cloaked UWP windows — those are not real HUDs and hiding them does
nothing visible.
"""
from __future__ import annotations

import ctypes
from ctypes import wintypes

from hud_toggle.core.entities import WindowHandle
from hud_toggle.utils.logging import get_logger

log = get_logger(__name__)

_user32 = ctypes.WinDLL("user32", use_last_error=True)
_kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)

_SW_HIDE = 0
_SW_SHOW = 5
_SW_MINIMIZE = 6
_SW_RESTORE = 9

_GWL_EXSTYLE = -20
_WS_EX_TOOLWINDOW = 0x00000080
_DWMWA_CLOAKED = 14


class Win32WindowAdapter:
    """Enumerates top-level windows and toggles their visibility."""

    def __init__(self) -> None:
        self._proc_cache: dict[int, str] = {}
        self._saved_placement: dict[int, int] = {}

    def list_windows(self) -> list[WindowHandle]:
        handles: list[WindowHandle] = []
        seen: set[int] = set()

        @ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
        def _cb(hwnd: int, _lparam: int) -> bool:
            if hwnd in seen:
                return True
            if not _user32.IsWindowVisible(hwnd):
                return True
            if self._is_cloaked(hwnd):
                return True
            title = self._title(hwnd)
            if not title:
                return True
            proc = self._process_name(hwnd)
            if not proc:
                return True
            seen.add(hwnd)
            handles.append(WindowHandle(value=hwnd, process_name=proc, window_title=title))
            return True

        _user32.EnumWindows(_cb, 0)
        return handles

    def hide(self, handle: int) -> bool:
        self._saved_placement.setdefault(handle, _SW_SHOW)
        ok = bool(_user32.ShowWindow(handle, _SW_HIDE))
        if not ok:
            log.warning("win32.hide_failed", hwnd=hex(handle), err=ctypes.get_last_error())
        return ok

    def minimize(self, handle: int) -> bool:
        self._saved_placement.setdefault(handle, _SW_RESTORE)
        ok = bool(_user32.ShowWindow(handle, _SW_MINIMIZE))
        if not ok:
            log.warning("win32.minimize_failed", hwnd=hex(handle), err=ctypes.get_last_error())
        return ok

    def restore(self, handle: int) -> bool:
        prev = self._saved_placement.pop(handle, _SW_SHOW)
        ok = bool(_user32.ShowWindow(handle, prev))
        if not ok:
            log.warning("win32.restore_failed", hwnd=hex(handle), err=ctypes.get_last_error())
        return ok

    def is_alive(self, handle: int) -> bool:
        return bool(_user32.IsWindow(handle))

    # -- internals -----------------------------------------------------

    def _title(self, hwnd: int) -> str:
        length = _user32.GetWindowTextLengthW(hwnd)
        if length <= 0:
            return ""
        buf = ctypes.create_unicode_buffer(length + 1)
        _user32.GetWindowTextW(hwnd, buf, length + 1)
        return buf.value

    def _process_name(self, hwnd: int) -> str:
        pid = wintypes.DWORD()
        _user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        if pid.value in self._proc_cache:
            return self._proc_cache[pid.value]

        PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
        hproc = _kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid.value)
        if not hproc:
            return ""
        try:
            size = wintypes.DWORD(260)
            buf = ctypes.create_unicode_buffer(size.value)
            if not _kernel32.QueryFullProcessImageNameW(hproc, 0, buf, ctypes.byref(size)):
                return ""
            name = buf.value.rsplit("\\", 1)[-1]
            if name.lower().endswith(".exe"):
                name = name[:-4]
            self._proc_cache[pid.value] = name
            return name
        finally:
            _kernel32.CloseHandle(hproc)

    def _is_cloaked(self, hwnd: int) -> bool:
        try:
            dwmapi = ctypes.WinDLL("dwmapi", use_last_error=True)
        except OSError:
            return False
        cloaked = wintypes.DWORD(0)
        hr = dwmapi.DwmGetWindowAttribute(
            wintypes.HWND(hwnd),
            wintypes.DWORD(_DWMWA_CLOAKED),
            ctypes.byref(cloaked),
            ctypes.sizeof(cloaked),
        )
        return hr == 0 and cloaked.value != 0