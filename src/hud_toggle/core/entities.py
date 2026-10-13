"""Domain entities. Frozen dataclasses — nothing in core mutates these."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class HudAction(str, Enum):
    HIDE = "hide"
    MINIMIZE = "minimize"
    IGNORE = "ignore"


@dataclass(frozen=True, slots=True)
class WindowHandle:
    """Opaque wrapper around a platform window handle.

    The integer value is meaningful only to the adapter that produced it.
    Core code treats it as an identity token.
    """
    value: int
    process_name: str
    window_title: str


@dataclass(frozen=True, slots=True)
class HudCandidate:
    handle: WindowHandle
    rule_name: str
    action: HudAction

    @property
    def process_name(self) -> str:
        return self.handle.process_name

    @property
    def window_title(self) -> str:
        return self.handle.window_title


@dataclass(slots=True)
class ToggleState:
    """Snapshot returned by HudToggler so the guard can restore later."""
    hidden_handles: list[int] = field(default_factory=list)
    minimized_handles: list[int] = field(default_factory=list)
    visible_handles: list[int] = field(default_factory=list)

    @property
    def any_changed(self) -> bool:
        return bool(self.hidden_handles or self.minimized_handles)