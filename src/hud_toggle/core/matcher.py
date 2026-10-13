"""Rule matching. Pure function — no I/O, no logging side effects."""
from __future__ import annotations

import re
from functools import lru_cache

from hud_toggle.config.models import HudRule
from hud_toggle.core.entities import HudAction, HudCandidate, WindowHandle


@lru_cache(maxsize=256)
def _compiled(pattern: str) -> re.Pattern[str]:
    return re.compile(pattern)


def match_window(
    window: WindowHandle,
    rules: list[HudRule],
) -> HudCandidate | None:
    """Return the first rule that matches `window`, or None.

    Matching order: process (exact, case-insensitive) then title regex.
    An empty `process` on the rule matches any process. Rules are tried
    in list order so users control precedence.
    """
    proc = window.process_name.lower()
    for rule in rules:
        if rule.process and rule.process.lower() != proc:
            continue
        if not _compiled(rule.title_re).search(window.window_title):
            continue
        return HudCandidate(
            handle=window,
            rule_name=rule.name,
            action=HudAction(rule.action),
        )
    return None