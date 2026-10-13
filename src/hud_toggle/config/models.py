"""Pydantic models for the config schema.

Every field has a default so a user can ship a two-line config and still
get a working tool. `hud_rules` is the only section without a default —
an empty rule list means the tool does nothing, which we treat as a
config error, not a valid state.
"""
from __future__ import annotations

import re
from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator


class HudRule(BaseModel):
    name: str = Field(..., min_length=1, max_length=64)
    process: str = Field(default="", max_length=128)
    title_re: str = Field(..., min_length=1, max_length=256)
    action: Literal["hide", "minimize", "ignore"] = "hide"

    @field_validator("title_re")
    @classmethod
    def _compile_title_re(cls, v: str) -> str:
        try:
            re.compile(v)
        except re.error as exc:
            raise ValueError(f"invalid regex {v!r}: {exc}") from exc
        return v

    @field_validator("process")
    @classmethod
    def _strip_exe(cls, v: str) -> str:
        return v[:-4] if v.lower().endswith(".exe") else v


class GuardConfig(BaseModel):
    hold_seconds: float = Field(default=3.0, ge=0.0, le=600.0)
    restore_on_exit: bool = True
    poll_ms: int = Field(default=250, ge=50, le=5000)


class HotkeyConfig(BaseModel):
    toggle: str = "ctrl+alt+h"
    toggle_once: str = "ctrl+alt+s"
    quit: str = "ctrl+alt+q"

    @property
    def bindings(self) -> dict[str, str]:
        return {"toggle": self.toggle, "toggle_once": self.toggle_once, "quit": self.quit}


class AppConfig(BaseModel):
    guard: GuardConfig = GuardConfig()
    hotkeys: HotkeyConfig = HotkeyConfig()
    hud_rules: list[HudRule]

    @model_validator(mode="after")
    def _require_rules(self) -> "AppConfig":
        if not self.hud_rules:
            raise ValueError("hud_rules must contain at least one rule")
        seen: set[str] = set()
        for rule in self.hud_rules:
            if rule.name in seen:
                raise ValueError(f"duplicate hud rule name: {rule.name}")
            seen.add(rule.name)
        return self