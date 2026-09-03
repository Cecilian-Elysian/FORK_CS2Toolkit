# CS2 Death Switch

CS2 Death Switch is a Windows desktop utility that listens to Counter-Strike 2 Game State Integration (GSI). When the local player dies, it switches to a configured web page or local application. When the player respawns or a new round starts, it pauses the current Windows media session and returns to CS2.

This is a Rust rewrite of the original CS2Toolkit. The former resource replacement, sound event, visual overlay, desktop pet, preset, update, and customisation features were intentionally removed.

## Requirements

- Windows 10 version 1809 or newer
- Counter-Strike 2
- Rust 1.85 or newer for building from source

## Build and run

```powershell
cargo run --release
```

The application stores its new independent configuration at:

```text
%LOCALAPPDATA%\CS2DeathSwitch\config.json
```

It never reads, migrates, or deletes `%LOCALAPPDATA%\CS2Toolkit` data.

## Setup

1. Start the application.
2. Enter a web URL or select a local application.
3. Select or detect the CS2 installation directory.
4. Select `Generate GSI config`.
5. Restart CS2 after generating the configuration.

The generated file is `game\csgo\cfg\gamestate_integration_cs2deathswitch.cfg` under the CS2 installation directory. The local receiver binds only to `127.0.0.1` and uses port `3000` by default.

## Behaviour

- The first GSI update establishes a state baseline and never triggers a switch.
- A transition from positive health to zero triggers one switch.
- GSI updates received while spectating another player are ignored.
- Respawning or entering a new round pauses the current media session and restores CS2 to the foreground.
- If a return occurs while a delayed switch is pending, the pending switch is cancelled.
- Browser sessions are reused where Windows exposes a standard browser window.
- Media control uses the current Windows system media session. Windows does not provide a reliable cross-browser API for selecting one individual tab.

## License

This repository remains licensed under GPL-3.0-only. See [LICENSE](LICENSE).
