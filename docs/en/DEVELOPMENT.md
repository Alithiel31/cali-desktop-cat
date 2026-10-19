# Local development

[Français](../DEVELOPPEMENT.md) · English

[Back to the README](../../README.en.md)

## Requirements

- **Python 3.12 or 3.13** (3.10 crashes with PySide6 6.12). Validated in CI on these two versions.
- **Windows** to actually run the app (`winapi.py` only makes sense there). The tests run anywhere.
- Git. PyInstaller only to build the executable.

## Install and run

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

`requirements.txt` has a single line: `PySide6-Essentials>=6.6,<7` (Qt without the modules we do not need).

## Tests

```bash
python -m unittest discover -s tests -v
```

| Environment | Detail |
|---|---|
| Windows | `set QT_QPA_PLATFORM=offscreen` if you do not want any window to show. |
| Linux | System libraries needed: `libegl1 libgl1 libxkbcommon0 libdbus-1-3 libfontconfig1 libglib2.0-0`. |
| CI | `ci.yml`: Windows + Ubuntu 24.04 × Python 3.12 and 3.13. |

Description of the test files and of the "no real screens" guard: [ARCHITECTURE.md](./ARCHITECTURE.md#tests).

## Testing by hand without risking your save

`tools\run_test_instance.bat` redirects `APPDATA` to `%TEMP%\desktopcat_test`, writes a fresh save there (meows and
notifications off) and launches the app. Your real save is not touched.
Details of the other tools: [tools/README.en.md](../../tools/README.en.md).

## Where the app writes

| What | Where |
|---|---|
| Save file, copies, log | `%APPDATA%\DesktopCat\` (elsewhere: `$XDG_DATA_HOME` or `~/.local/share`) |
| Instance lock | `%TEMP%\desktopcat.lock` |
| Launch with Windows | `HKCU\Software\Microsoft\Windows\CurrentVersion\Run`, value `DesktopCat` |

See [TROUBLESHOOTING.md](./TROUBLESHOOTING.md#where-are-the-files) for the detail of the files.

## Environment variables

The app has **no configuration variable** of its own. The ones that matter are system variables:

| Variable | Effect |
|---|---|
| `APPDATA` | Save folder (redefined by `run_test_instance.bat`). |
| `XDG_DATA_HOME` | Same outside Windows. |
| `QT_QPA_PLATFORM` | `offscreen` for the tests and `tools/preview_panel.py`. |

## Conventions

- Commit messages: `type: description` (`fix:`, `feat:`, `docs:`, `ci:`, `test:`, `chore:`), in French.
- Documentation: every file has an English version (`docs/en/`, `README.en.md`); changing one means updating the other.
- Line endings: LF for `.py` and `.md`, CRLF for `.bat` (see `.gitattributes`).
- Randomness and time are passed as parameters whenever possible (cf. `phrases.py`) so they stay testable.
- Any new pure logic goes in a module with no Qt and no Windows (like `screens.py`, `surfaces.py`, `hats.py`): that is
  what makes it testable everywhere.

## Draft — to be completed

- [ ] Linter / formatter (ruff) and gradual typing — planned at level 3 of the [roadmap](./ROADMAP.md).
- [ ] Pre-commit or pre-push hook that replays the tests (equivalent of QcWeather's Husky hook).
- [ ] Test coverage measurement.
- [ ] Procedure to validate the real Windows API and mixed display scales (today: by hand, on a real dual-screen setup).
