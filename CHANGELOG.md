# Changelog

All notable changes to CS2 Death Switch are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Changed

- Repository rewritten in Rust as **CS2 Death Switch**, replacing the previous
  Python/PySide6-based CS2Toolkit.
- Application identity, configuration directory and persisted state migrated
  to `CS2DeathSwitch` (under `%LOCALAPPDATA%\CS2DeathSwitch`).
- The new release does not read, migrate or delete any data left behind by
  the previous Python-based CS2Toolkit.

### Removed

- Resource replacement (custom startup movie, sound, font).
- GSI-driven sound events and presets.
- In-game visual replacements (flash, kill icons, death media).
- `GO桌宠` desktop pet overlay.
- Preset import/export and the public/private update channels.
- All Python source, build scripts and PySide6 dependencies.

### Added

- GSI listener bound only to `127.0.0.1` with a configurable port.
- Automatic Steam library detection (multiple Steam install roots, all
  `libraryfolders.vdf` entries, environment-variable override).
- `gamestate_integration_cs2deathswitch.cfg` generator.
- Death → switch, respawn/round start → pause media + return to CS2.
- Optional close-to-tray with system tray menu (pause, show, exit).
- Standalone JSON configuration persisted per-user.
- Fully Chinese user interface (window, controls, tray menu, logs).
- Automatic loading of a system CJK font at startup (Microsoft YaHei,
  SimHei, SimSun or DengXian from `%WINDIR%\Fonts`); no fonts are
  bundled with the binary.