# Contributing to hud-toggle-screenshot-tool

Thanks for wanting to help. This project is a Windows desktop tool that
toggles HUD overlays on and off so screenshots come out clean. It's a
small tool with a small surface — patches stay small too.

## Ground rules

- Python 3.11+ is the floor. 3.12 is what CI runs.
- One feature per PR. If it touches `core/`, `services/`, and `adapters/`
  in the same diff, split it.
- Every new service gets a test in `tests/`. No exceptions.
- No new runtime dependency without a note in the PR body explaining
  what the stdlib alternative was and why it didn't work.

## Dev setup

```
git clone https://github.com/<you>/hud-toggle-screenshot-tool
cd hud-toggle-screenshot-tool
python -m venv .venv
.venv\Scripts\activate
pip install -e .[dev]
```

Run the tool:

```
python -m hud_toggle
```

Run tests:

```
pytest -q
```

## Style

- `ruff` for lint, `black` for format. Both run in pre-commit.
- Type hints on every public function. `mypy --strict` on `core/` and
  `services/` only — adapters talk to Win32, they get a pass.
- Logging via `hud_toggle.utils.logging.get_logger(__name__)`. Never
  `print` in shipped code.

## Reporting bugs

Open an issue with: Windows build (`winver`), Python version, the exact
HUD you were trying to toggle, and whether you were on a single monitor
or multi. Multi-monitor bugs are 80% of the tracker, so always say.

## Scope

This tool toggles HUD overlays for screenshots. It is not a screenshot
tool itself, not a screen recorder, not a stream overlay. If your PR
adds capture, recording, or streaming, it's out of scope.