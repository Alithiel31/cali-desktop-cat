# Roadmap

[Français](../ROADMAP.md) · English

Sorted from most urgent to most anecdotal. `[x]` = done. Within a level, the order is the recommended order.
Last updated: 20/10/2026, version 0.4.1 (about 240 tests). The weak point remains whatever has never run on a real
Windows machine (`winapi.py`, the global shortcut, the executable). Test coverage needs measuring again (the last
measurement, 85 %, dates from the 19/10/2026 review).

## Done — basic reliability
- [x] Instance lock taken over after a crash (verified: it is not taken over while the 1st instance is running).
- [x] Time actually elapsed and capped: a sleep no longer skews statistics or gifts.
- [x] Focus reward conditioned on presence (≥ 50 %).
- [x] Bubble readable whatever the Windows theme; its tail points at the cat's head.
- [x] Cat fully visible while working, moved back if a screen is unplugged.
- [x] Error log (`desktopcat/log.py`), see [TROUBLESHOOTING.md](TROUBLESHOOTING.md).
- [x] No more teleporting when landing on a window moved during the jump.
- [x] Save file: timestamped copies, daily copy with restore, format version and migrations.
- [x] Machine-independent tests (fake screens, fake mouse, guard against real screens).
- [x] GitHub Actions CI (Windows + Ubuntu, Python 3.12 and 3.13); CD: exe build and Release on a `v*` tag.
- [x] `CHANGELOG.md`, `CONTRIBUTING.md` and project documentation.

## Level 1 — Urgent: signing, then v0.4.x
- [ ] **Code signing (SignPath Foundation)**: Smart App Control blocks the unsigned exe with no way around, including on
  the dev machine. Preparation done in v0.4.1 (Code signing policy, metadata, commented block in `release.yml`);
  remaining: 2FA, application, activation. Details: [DISTRIBUTION.md](DISTRIBUTION.md#signing-signpath-foundation).
- [x] **Validate on a real Windows**: Windows tests in CI and on the dev machine (236 tests), manual checklist
  ([MANUAL-TESTING.md](MANUAL-TESTING.md)) run with Python on 19/10/2026.
- [ ] **Test the exe** on a machine without Smart App Control (or once signed): startup, log, save file, launch with
  Windows, Task Manager.
- [x] **Privacy**: "Noter les applications utilisées" setting + "Effacer mes statistiques" button (readable backups
  included).
- [x] **Battery**: no more `timeBeginPeriod(1)`; loop at 10 iterations/s when the cat is hidden or asleep (user away).
- [x] **Stackable gifts**: the focus reward is no longer lost if a gift was waiting (save v2).
- [x] **Save file**: daily copy also when the app runs for several days; `fsync` and retries.
- [x] **Invisible windows**: overlays, non-activatable or zero-opacity windows excluded from perching; titles read
  without a message (no freeze on a blocked window). *To verify on a real Windows with Steam/Discord open.*
- [ ] **CPU measurement** on the real machine (idle, asleep, walking) to decide what next: per-pid `exe` cache, less
  frequent window scan.

## Level 2 — Important: rest of the 0.4.x
- [x] **Launch with Windows**: the registry is the source of truth (including `StartupApproved`, written by Task
  Manager); path rewritten at startup; re-ticking the box re-enables startup.
- [ ] **Fake full screen**: check that a maximized window with a hidden taskbar does not hide the cat (`IsZoomed` /
  `WS_CAPTION` in `is_fullscreen`).
- [ ] **Full screen and video**: only the active window is examined (a full-screen video on the other screen does not
  hide the cat if it goes there). And a film watched without touching the mouse puts the cat to sleep: lead,
  `CallNtPowerInformation(SystemExecutionState)` and the `ES_DISPLAY_REQUIRED` flag set by video players.
- [ ] **Reproducible builds**: pinned versions (PySide6, PyInstaller), versioned `.spec`; consider `--onedir` (faster
  startup, fewer antivirus false positives, and maybe required for Smart App Control).
  Icon and version number: done (v0.4.1).

## Level 3 — Medium
- [ ] **Visible second launch**: the "already running" message goes to `print()`, invisible without a console. Open the
  running instance's panel instead (`QLocalServer`).
- [ ] **Consistent focus statistics**: focus time also counts absence, whereas the reward requires presence.
- [x] **Kibble**: feeding the cat (mood, gift bonus when full). Hat shop: later.
- [x] Seasonal hat (Halloween), mouse hunting, Pomodoro break, Ctrl+Alt+C shortcut.
  *To verify on a real Windows: the shortcut (`RegisterHotKey` + native filter) and multi-screen hunting.*
- [ ] Gift pace: 20 min passive versus 10 min in focus, to revisit with the "full" bonus (+25 %).
- [ ] Long-term goal: complete collection, achievements, other seasons (Christmas...), shop.
- [ ] Code quality: keep splitting `pet.py` (~700 lines; physics, layout, input and reactions have already been moved
  out), make `winapi` injectable into `Game`, gradual typing and ruff.

## Level 4 — Anecdotal
- [x] `.gitignore`: global `*.png` rule removed (`tools/out/` stays excluded).
- [x] Empty `framerate test/` folder deleted. [ ] The README's "Executable" section should point to the Releases.
- [ ] Screenshots or GIFs in the README.
- [x] Documentation translated into English (`README.en.md`, `docs/en/`).
- [ ] Quiet hours; text size independent of the cat's size.
- [ ] Optional sounds, new phrases, cat name editable from the cat; several cats, new coats.
- [ ] Fallback emoji font if Segoe UI Emoji is missing.
- [ ] Panel: only rebuild the hat cards that change (if the catalog grows).
