"""TOML config loader.

Search order when `path` is None:
1. $HUD_TOGGLE_CONFIG
2. %APPDATA%/hud-toggle/config.toml
3. packaged defaults.toml
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

import tomllib
from pydantic import ValidationError

from hud_toggle.config.models import AppConfig
from hud_toggle.utils.logging import get_logger

log = get_logger(__name__)

_ENV_VAR = "HUD_TOGGLE_CONFIG"
_APPDATA_SUBPATH = Path("hud-toggle") / "config.toml"


def _packaged_defaults() -> Path:
    return Path(__file__).parent / "defaults.toml"


def _user_config_path() -> Path | None:
    appdata = os.environ.get("APPDATA")
    if not appdata:
        return None
    candidate = Path(appdata) / _APPDATA_SUBPATH
    return candidate if candidate.is_file() else None


def resolve_config_path(path: str | os.PathLike[str] | None) -> Path:
    if path is not None:
        p = Path(path)
        if not p.is_file():
            raise FileNotFoundError(f"config not found: {p}")
        return p

    env = os.environ.get(_ENV_VAR)
    if env:
        p = Path(env)
        if not p.is_file():
            raise FileNotFoundError(f"{_ENV_VAR} points at missing file: {p}")
        return p

    user = _user_config_path()
    if user is not None:
        return user

    return _packaged_defaults()


def load_config(path: str | os.PathLike[str] | None = None) -> AppConfig:
    resolved = resolve_config_path(path)
    log.debug("config.resolve", path=str(resolved))

    with resolved.open("rb") as fh:
        raw = tomllib.load(fh)

    try:
        return AppConfig.model_validate(raw)
    except ValidationError as exc:
        print(f"invalid config at {resolved}:\n{exc}", file=sys.stderr)
        raise SystemExit(2) from exc