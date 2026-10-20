# Troubleshooting

[Français](../TROUBLESHOOTING.md) · English

This document grows with the project: every problem encountered and solved has its place here.

## Where are the files?

Everything is in `%APPDATA%\DesktopCat\` (in Git Bash: `$APPDATA/DesktopCat/`).

| File | Content |
|---|---|
| `save.json` | Your progress: hats, kibble, settings, statistics for the last 60 days. |
| `save.json.YYYY-MM-DD_HH-MM-SS.bak` | An unreadable `save.json`, set aside automatically (the 3 most recent are kept). |
| `backups/save-YYYY-MM-DD.json` | Daily copy, made at the first launch of the day (the 7 most recent are kept). |
| `save.json.vN.bak` | Copy made before a format migration (or if the save comes from a newer version of the app). Never overwritten. |
| `desktopcat.log` | The log: startups, warnings, errors. 1 MB maximum, 2 old files kept (`.log.1`, `.log.2`). |
| `desktopcat.log.crash` | Trace of a fatal interpreter crash (very rare). Empty if all is well. |

The lock that prevents running two cats is `%TEMP%\desktopcat.lock`.

## Reading the log

- Right-click the tray icon, then **Ouvrir le journal** ("Open the log").
- Or on the command line: `notepad "$APPDATA/DesktopCat/desktopcat.log"` / `tail -50 "$APPDATA/DesktopCat/desktopcat.log"`.

Each line has the form `date level module: message`. The useful levels:
`WARNING` (something abnormal but handled), `ERROR` (an action failed, for example a save),
`CRITICAL` (unhandled exception, with the full trace).

Lines starting with `Qt :` are messages from the graphics library. The log's messages are in French.

## Reporting a bug

Attach, if possible:
1. the last lines of `desktopcat.log` (and `desktopcat.log.crash` if it is not empty);
2. your Windows and Python versions (the first `Démarrage : ...` line of the log contains them);
3. your screen setup (number, display scale) if the bug concerns the cat's movement;
4. what you were doing just before.

Repository: https://github.com/Alithiel31/cali-desktop-cat/issues

---

## The cat does not start

### "Desktop Cat est déjà lancé" (already running)
An instance is already running: look for the icon in the notification area (the ^ arrow if it is hidden).
Otherwise, end the `pythonw.exe` / `DesktopCat.exe` process in Task Manager.

After a crash or a hard shutdown, the lock is taken over automatically after **30 seconds**.
If that is not enough: delete `%TEMP%\desktopcat.lock`.

### Nothing shows up, no error
Open the log. Launched with `pythonw` or without a console, the app never displays its errors on screen: they are all in
`desktopcat.log`. To see startup errors live, run `python main.py` in a console.

## The cat is invisible

- Tray icon menu: if the entry is **Afficher le chat** ("Show the cat"), you had hidden it. Click it.
- An app in **full screen** (game, video) hides the cat, but only on its own screen.
- A screen was just plugged or unplugged: the cat repositions itself within moments.

## The cat does not perch on my windows

- Check the settings: "Il marche sur le bord haut des fenêtres" ("It walks on the top edge of windows") must be ticked.
- Ignored: **maximized**, **minimized**, **untitled** windows, windows smaller than 250 × 120 px, tool windows, and
  windows on another virtual desktop.
- There must be room above the window for the cat to stand.
- Also ignored are look-alike windows: click-through transparent overlays (Steam, NVIDIA, Discord), windows that cannot
  be activated, stacked zero-opacity windows. If the cat walks "in mid-air" above one of these windows, it is a bug:
  attach the log and the application's name.

## No gift after a focus session

A session earns nothing if:
- it lasts **less than 10 minutes**;
- you were **present less than half of the time** (no keyboard or mouse), or the PC was asleep;
- the app was closed and the session ended during the absence.

When the session ends with the app open, a notification explains why (if "Notifications de fin de session" is ticked).
See [GAMEPLAY.md](GAMEPLAY.md).

## The cat falls asleep while I watch a film

It falls asleep after 5 minutes without keyboard or mouse (setting "Il s'endort après", "It falls asleep after", from 1
to 60 min). Watching a video without touching anything counts as absence. Known limitation, see the
[roadmap](ROADMAP.md).

## Ctrl+Alt+C does nothing

- Settings: the keyboard shortcut setting must be ticked; the tray menu then shows "Cacher le chat   Ctrl+Alt+C".
- If another application already uses this shortcut, it stays inactive; the log says so ("Raccourci Ctrl+Alt+C
  indisponible …").
- On a keyboard where AltGr+C types a character, that character is captured: untick the setting.

## No notifications

Panel, Settings tab: "Notifications de fin de session" must be ticked.

## Launch with Windows no longer works

The command is registered in `HKCU\Software\Microsoft\Windows\CurrentVersion\Run` (value `DesktopCat`) and refreshed at
every launch. If Windows refuses the change, check that your account can modify this key, then try enabling
"Lancer avec Windows" again in the panel.

The registry is the source of truth: if you disable Desktop Cat in Task Manager (Startup tab), the panel's checkbox
unticks itself; re-ticking it re-enables it. If you move or replace the exe, the path is rewritten at the next launch.

## My save file is lost or unreadable

- If `save.json` is corrupted, the app sets it aside (`save.json.<date>.bak`) then **automatically restores the most
  recent daily copy** and notifies you. You lose at most the day's progress.
- If no copy is usable, it starts from a fresh save; the unreadable file remains recoverable by hand.
- Restoring by hand: quit the app, copy a file from `backups/` over `save.json`, relaunch.
- The log tells everything (`Sauvegarde illisible`, `Sauvegarde restaurée depuis la copie du jour`).
- To deliberately start over: quit the app, delete `save.json`.
- `Sauvegarde impossible` in the log: the disk is full or the folder is write-protected.

## Emojis show up as squares

Windows' emoji font (Segoe UI Emoji) cannot be found. On a recent Windows it is always present; on another system
(tests, Linux), this is normal.

## The tests fail

- The tests are validated in CI with **Python 3.12 and 3.13** and PySide6 6.x: use one of these versions (3.10 crashes).
- Run them from the project root: `python -m unittest discover -s tests`.
- On Linux, you need Qt's system libraries (for example `libegl1`).
- The tests depend neither on your screens nor on your mouse (fake screens, fake mouse). If a test fails for you and not
  elsewhere, that is a serious lead: attach the test's name and the complete output.
