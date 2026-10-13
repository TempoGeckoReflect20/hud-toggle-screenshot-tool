# Security Policy

## Supported versions

| Version | Supported |
|---------|-----------|
| 0.4.x   | yes       |
| 0.3.x   | security fixes only |
| < 0.3   | no        |

## Reporting a vulnerability

Email `security@hud-toggle.local` with subject line
`[hud-toggle] <short description>`. Do not open a public issue for
anything that could be exploited before a fix ships.

Include:
- Windows version and build number
- Python version
- Whether the tool was running elevated
- Steps to reproduce
- Whether it involves the Win32 window-enumeration adapter, the
  hotkey hook, or the config loader

Expect an acknowledgement within 72 hours and a fix or mitigation
within 14 days for anything rated medium or higher.

## Threat model

This tool runs with the privileges of the user who launched it. It
does not request elevation on its own. It reads window titles and
process names from the local desktop session to identify HUD windows.
It does not phone home, does not collect telemetry, and does not
transmit anything off the machine.

Known non-issues:
- The tool can enumerate windows belonging to other processes on the
  same desktop. That is required to find HUD overlays. It does not
  read their memory.
- The config file is plain TOML and is user-editable by design.
- Hotkeys are registered via `RegisterHotKey` and are global to the
  session. That is a Windows platform behavior, not a bug.

Out of scope:
- Anything that requires the attacker to already have code execution
  as the same user.
- Antivirus false positives on the PyInstaller one-file build. Report
  those upstream to PyInstaller.