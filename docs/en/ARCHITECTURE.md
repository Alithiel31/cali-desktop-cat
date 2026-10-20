# Architecture

[Français](../ARCHITECTURE.md) · English

Desktop Cat is a PySide6 (Qt 6) app for Windows. One rule guides the split:
**pure logic (math, game rules) is separated from whatever touches Qt and Windows**, which makes it possible to test
most of the code on any system.

## Overview

```
main.py ── creates and wires ──►  Store ──► Game ──► Pet ◄── Bubble / GiftBox / FxLayer
                                          │        │
                                          │        ├── motion.py, pet_layout.py, pet_input.py, pet_companion.py
                                          │        ├── hunt.py      (mouse hunting)
                                          │        ├── screens.py   (multi-screen geometry)
                                          │        ├── surfaces.py  (walkable window edges)
                                          │        └── sprite.py    (pixel-art drawing) ◄── hats.py
                                          ├── winapi.py             (everything that talks to Windows)
                                          ├── autostart.py          (launch with Windows)
                                          └── hotkey.py             (global Ctrl+Alt+C shortcut)
                                   Panel (control window) ◄── Game
```

## Modules (`desktopcat/`)

| Module | Role | Depends on Qt? | Depends on Windows? |
|---|---|---|---|
| `store.py` | JSON save file (`%APPDATA%/DesktopCat/save.json`), defaults, cleaning of a damaged file, per-day statistics. Atomic write (`.tmp` then `os.replace`). Backup copies, daily copy with automatic restore, format migrations. | no | no |
| `game.py` | Game rules: one-second timer, gifts, hats, focus, screen time, validated settings (`SETTING_RULES`). Emits signals; no interface. | yes (`QObject`, signals) | via `winapi` |
| `pet.py` | The cat: transparent window, states (idle, walk, nap, sleep, work, wait, drag, fall, jump), mouse, bubble, gift and movement orchestration. | yes | via `world.py` |
| `motion.py` | Physics of walking, jumping and falling, independent of Qt and Windows. | no | no |
| `world.py` | Converts Windows windows into walkable surfaces in Qt coordinates. | no | via `winapi` |
| `pet_layout.py` | Computes the position of the cat, the gift and the bubble in the visible area, without Qt. | no | no |
| `pet_input.py` | Translates mouse events and the context menu into actions on the cat. | yes | no |
| `pet_companion.py` | Expressive reactions to gifts, bubbles, sleep and focus sessions. | yes | no |
| `screens.py` | Multi-screen geometry (physical ↔ logical pixel conversion, floors, chains of adjacent screens). Pure functions. | no | no |
| `surfaces.py` | Computes the top window edges the cat can walk on, removing the parts hidden by windows above. Pure functions. | no | no |
| `winapi.py` | `ctypes` to `user32`/`dwmapi`/`kernel32`: window list, active window, idle time, full screen. On another system it returns neutral values. | no | yes (isolated here) |
| `sprite.py` | Drawing of the cat and the gift, cell by cell, on a grid. Coats, poses, eyes, hats. | yes | no |
| `hats.py` | Hat catalog, rarities, weighted draw. | no | no |
| `hunt.py` | Rules of mouse hunting (resting mouse, within reach). Pure functions. | no | no |
| `hotkey.py` | Global Ctrl+Alt+C shortcut (`RegisterHotKey` + Qt native event filter). | yes | yes |
| `phrases.py` | Meow texts and random delay (the randomness is passed as a parameter). | no | no |
| `widgets.py` | `Bubble` (speech bubble), `GiftBox` (gift), `FxLayer` (hearts, stars, "z"). | yes | no |
| `panel.py` | Control window: wardrobe, focus, statistics, settings. | yes | no |
| `log.py` | Error log: rotating file, capture of exceptions (including those in Qt slots), Qt messages and fatal crashes. | yes (Qt messages) | no |
| `autostart.py` | `HKCU\...\Run` registry key (and `StartupApproved`). | no | yes |

## Loops and time

- **`Game.tick(dt)`**: about once per second. The time counted is the time actually elapsed (monotonic clock), capped at
  5 s per iteration: a sleep or a freeze of the app therefore skews neither the statistics nor gift progress. It counts
  activity, advances progress toward the next gift, per-application screen time, the focus session, and detects absence
  (falling asleep) and full screen. It saves every 30 s.
- **`Pet.step(dt)`**: about 60 times per second (16 ms timer, `LOOP_MS`). When the cat is hidden or asleep because the
  user is away, the timer drops to 100 ms (`LOOP_SLOW_MS`, 10 iterations per second) to spare the battery; the nap
  ("nap") keeps the normal rate. `dt` is capped (2.5 times the timer interval). This is the method the tests call
  directly.
- **Window scan**: every 0.2 s inside `step` (`_refresh_surfaces`), which rebuilds the list of surfaces.
- **Animation**: repaint every 80 ms.

## Coordinates

Two systems coexist:

- **physical**: native Windows pixels (window rectangles, full-screen detection);
- **logical**: Qt pixels (positions of the cat's widgets).

`screens.to_logical` converts screen by screen from the origin of the reference screen (middle of the window's top
edge). The cat only works in logical coordinates; only `winapi` and `screens` see physical ones.

## The cat's physics model

The cat has a position `(fx, fy)`: `fx` is the left edge of the sprite, `fy` the y of the feet. It stands on a
**surface**: the floor of a screen (the bottom of its work area) or the top edge of a window. Floors of adjacent
screens (horizontal gap ≤ 2 px, height difference ≤ 80 px) form a **chain** it crosses on foot; otherwise it jumps or
falls. If the surface disappears (window closed, minimized, moved), it falls to the next one.

## Data flow

1. `Game.tick` updates `Store.data` then emits `changed`.
2. `Pet` and `Panel` listen to `changed` and refresh.
3. The cat's actions (menu, double-click) go up through signals (`open_panel`, `start_focus`, ...) wired in `main.py`,
   which is the only place where everything is connected.

## Tests

`python -m unittest discover -s tests -v`. The tests use Qt in `offscreen` mode, fake screens and a fake desktop.

| File | Covers |
|---|---|
| `test_logic.py` | Store, game rules, hats, surfaces. |
| `test_screens.py` | Multi-screen geometry. |
| `test_features.py` | Cat and panel behavior (states, jumps, full screen, meows, bubble...). |
| `test_log.py` | Error log: exceptions, Qt slots, threads, Qt messages, save failures. |
| `test_gameplay.py` | Seasonal hats, mood and kibble, breaks, mouse hunting, shortcut. |
| `test_store_backups.py` | Save file: timestamped copies, daily copy, restore, format migrations. |
| `test_autostart.py` | Launch with Windows, on a fake registry (the real one is never touched). |
| `test_motion.py` | Jump and fall trajectories, walking (no Qt). |
| `test_pet_layout.py` | Visual placement of the cat, gift and bubble (no Qt). |
| `test_world.py` | Bridge between native windows and walkable surfaces. |
| `test_tools.py` | Build tools: the exe's Windows metadata. |

The tests are **machine-independent**: fake screens (`ScreenInfo`), fake mouse (`FixedCursor`), fake desktop. A guard in
`GameTestCase` fails any test that would read the real screens.

Real Windows API calls (`winapi.py`) are only tested on Windows (the CI's Windows jobs); mixed display scales, the
global shortcut and perching with Steam/Discord are validated by hand: [MANUAL-TESTING.md](MANUAL-TESTING.md) and
`tools/run_test_instance.bat`.

## Extension points

- **New hat**: add an entry to `HATS` (`hats.py`). No other file to change.
- **New setting**: default value in `store.DEFAULTS["settings"]`, validation rule in `game.SETTING_RULES`, control in
  `Panel._build_settings`.
- **Changing the save format**: increment `store.SCHEMA_VERSION` and add to `store.MIGRATIONS` the function
  `{old_version: function(dict) -> dict}` that transforms the old format. The file is copied to `save.json.v<N>.bak`
  before migration. Add a test in `tests/test_store_backups.py`.
- **New phrase**: `phrases.MEOWS`.
- **New cat state**: see `Pet.step` / `_step_stand`; remember the matching pose in `paintEvent`.
