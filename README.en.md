# Desktop Cat 🐱

[Français](README.md) · English

[![CI](https://github.com/Alithiel31/cali-desktop-cat/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/Alithiel31/cali-desktop-cat/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](./LICENSE)
[![Python](https://img.shields.io/badge/Python-3.12%20|%203.13-blue?logo=python)](https://www.python.org/)
[![Qt](https://img.shields.io/badge/PySide6-Qt%206-green?logo=qt)](https://doc.qt.io/qtforpython-6/)
[![Windows](https://img.shields.io/badge/Windows-10%20|%2011-0078D6?logo=windows)](https://github.com/Alithiel31/cali-desktop-cat/releases)

A tortoiseshell cat that lives on your Windows desktop: it wanders around, perches on window edges, falls when
the window disappears, jumps from one window to another, falls asleep when you are away, meows in a speech bubble now
and then, stalks your mouse, gets hungry (you feed it kibble), brings you gifts (hats in 6 rarities, including a seasonal
one at Halloween) and works alongside you during your focus sessions, followed by a Pomodoro break. It roams all of
your screens, and **Ctrl+Alt+C** shows or hides it.

> **Note on language.** The app's interface is in French. In these English docs, French labels are quoted as they
> appear on screen, with a translation in parentheses the first time they come up.

## Install
Download `DesktopCat.exe` from the [Releases](https://github.com/Alithiel31/cali-desktop-cat/releases) page and run it:
no installer, no administrator rights. The SHA256 hash is published next to the exe.

> The exe is **not signed yet**: SmartScreen shows a warning ("Informations complémentaires" > "Exécuter quand même",
> i.e. "More info" > "Run anyway"), and **Smart App Control** (Windows 11), if enabled, blocks it with no way around.
> A free code-signing application is in progress (see [Code signing policy](#code-signing-policy)).
> Meanwhile, you can run the app from source (below).

## Uninstall
1. Panel > Settings (Réglages): untick **Lancer avec Windows** ("Launch with Windows"; this removes the startup registry entry).
2. Quit the cat (right-click the tray icon > Quitter / Quit).
3. Delete `DesktopCat.exe`, then the `%APPDATA%\DesktopCat` folder (save file, backups, log).

No other file or registry key is created. If the exe was deleted without unticking the box, remove the **DesktopCat**
entry in Task Manager > Startup apps (or the `DesktopCat` value under
`HKCU\Software\Microsoft\Windows\CurrentVersion\Run`).

## Run from source
    pip install -r requirements.txt
    python main.py

## Tests
    python -m unittest discover -s tests -v
They also run outside Windows (Qt in `offscreen` mode, fake desktop and fake screens).

Tray icon: panel, 25-minute focus session (or stop it), skip the break, give kibble, hide the cat (Ctrl+Alt+C),
open the log, quit.
Double-click the cat = panel; right-click = menu (including "Donner des croquettes", "Give kibble"); you can pick it up and drop it.

## Panel
Header: kibble count (🐟), the cat's mood and a **Nourrir** ("Feed") button. Tabs: Garde-robe (wardrobe: wear hats,
sell duplicates), Concentration (focus, and break), Statistiques (7 days + apps of the day), Réglages (settings,
including "Il miaule de temps en temps", "It meows from time to time").

## Multiple screens
One floor per screen (the bottom of its work area, taskbar excluded). Adjacent screens whose bottoms are less than
80 px apart are crossed on foot; otherwise the cat jumps or falls from one to the other. It perches on windows
on every screen, even with different display scales. A full-screen app only hides the cat on its own screen.
Plugging or unplugging a screen is handled live.

## Focus
A session shorter than 10 min earns neither a gift nor kibble. It survives an app restart (if it ended in the
meantime, it is dropped without reward).

## Known limitations
- Mixed display scales (100 % / 125 % on two screens) are tested with fake screens, little on real hardware.
- A window straddling two screens with different scales is converted using the scale of only one of them.
- Save file: `%APPDATA%/DesktopCat/save.json`.

## Executable
    pip install pyinstaller
    python tools/make_version_file.py
    pyinstaller --noconsole --onefile --name DesktopCat --icon assets/desktopcat.ico --version-file build/version_info.txt main.py

## Project structure
    main.py          entry point
    desktopcat/      the app's code (see docs/en/ARCHITECTURE.md)
    tests/           unit tests (Qt offscreen)
    docs/            documentation in French; docs/en/: the English version
    assets/          executable icon
    tools/           development tools (icon, exe metadata, panel screenshots, test launcher)
    .github/         CI/CD, issue and PR templates, Dependabot

## Privacy
Everything stays on your computer: the app sends nothing anywhere and makes no network access. For statistics, it
records every second the **executable name** of the active window (40 apps per day, 60 days) in
`%APPDATA%/DesktopCat/save.json`. This tracking can be turned off in **Réglages** ("Noter les applications utilisées",
"Record the apps used"), and the **Effacer mes statistiques** ("Erase my statistics") button on the Statistics tab
erases the whole history, backups included.
Details: [SECURITY.en.md](SECURITY.en.md).

## Code signing policy
Free code signing provided by [SignPath.io](https://about.signpath.io/), certificate by
[SignPath Foundation](https://signpath.org/) *(application in progress: current releases are not signed yet)*.

- **Product:** Desktop Cat — repository [Alithiel31/cali-desktop-cat](https://github.com/Alithiel31/cali-desktop-cat), MIT License.
- **What is signed:** only `DesktopCat.exe` attached to the GitHub Releases of this repository, built from this
  source code by GitHub Actions (`.github/workflows/release.yml`). Nothing else is signed.
- **Committers and reviewers:** [Jacques Duchamplecheval (alithiel31)](https://github.com/Alithiel31)
- **Approvers:** [Jacques Duchamplecheval (alithiel31)](https://github.com/Alithiel31) — every release is approved
  manually before signing.
- **Privacy policy:** this program will not transfer any information to other networked systems unless specifically
  requested by the user or the person installing or operating it. See [Privacy](#privacy) for what it stores
  locally.

## Documentation
Every document exists in French and English; the English versions live in [docs/en/](docs/en/) and in `*.en.md` files.
- [Architecture](docs/en/ARCHITECTURE.md): modules, loops, coordinates, extension points.
- [Game rules](docs/en/GAMEPLAY.md): gifts, rarities, focus, statistics.
- [Development](docs/en/DEVELOPMENT.md): install, test, conventions.
- [Manual testing](docs/en/MANUAL-TESTING.md): the checklist to run on a real Windows machine before a Release.
- [Distribution](docs/en/DISTRIBUTION.md): building the executable, publishing a Release, SmartScreen.
- [Troubleshooting](docs/en/TROUBLESHOOTING.md): where the files are, reading the log, common problems.
- [Roadmap](docs/en/ROADMAP.md): what is done and what remains, from most critical to most anecdotal.
- [Accessibility](docs/en/ACCESSIBILITY.md) *(draft)*.
- [Dependency watch](docs/en/DEPENDENCY-WATCH.md): PySide6, PyInstaller, Windows API.
- [Handover guide](docs/en/HANDOVER-GUIDE.md): taking over the project without the maintainer.
- [Tools](tools/README.en.md): isolated test launcher, panel screenshots.
- [Changelog](CHANGELOG.en.md).

## Development
- Test without touching your real save: `tools\run_test_instance.bat`.
- Panel screenshots: `python tools/preview_panel.py` (written to `tools/out/`).

## Contributing
Environment, tests, commit convention: [CONTRIBUTING.en.md](CONTRIBUTING.en.md). Help: [SUPPORT.en.md](SUPPORT.en.md).
Code of conduct: [CODE_OF_CONDUCT.en.md](CODE_OF_CONDUCT.en.md).

## Security
To report a vulnerability, see [SECURITY.en.md](SECURITY.en.md) — no public issue.

## License
MIT, see [LICENSE](LICENSE).

---

Made by **Jacques Duchamplecheval** ([alithiel31](https://github.com/Alithiel31)) — [alithiel31.dev](https://alithiel31.dev) · [contact@alithiel31.dev](mailto:contact@alithiel31.dev)
