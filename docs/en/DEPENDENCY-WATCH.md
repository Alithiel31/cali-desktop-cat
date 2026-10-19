# Dependency watch

[Français](../VEILLE-DEPENDANCES.md) · English

[Back to the README](../../README.en.md)

Desktop Cat calls **no external API** (see [SECURITY.en.md](../../SECURITY.en.md)). What needs watching are its technical
dependencies, which can break rendering or packaging without notice.

## What to watch

| Dependency | Use | Where to look | Detected automatically? |
|---|---|---|---|
| [PySide6](https://pypi.org/project/PySide6-Essentials/) (Qt 6) | The whole interface, transparent windows, multi-screen | [Qt for Python release notes](https://doc.qt.io/qtforpython-6/), PyPI | Partly: CI fails if a test breaks (Dependabot `pip`) |
| Python | Interpreter | [Release calendar](https://devguide.python.org/versions/) | CI on 3.12 and 3.13 |
| [PyInstaller](https://pyinstaller.org) | `DesktopCat.exe` executable | Release notes, antivirus false positives | Dry-run build on PRs (`release.yml`) |
| Windows API (`user32`, `dwmapi`, `kernel32`) | Windows, active window, idle time, full screen (`winapi.py`) | Windows 11 changes | ❌ No automatic test: manual validation |
| GitHub Actions (`checkout`, `setup-python`, `upload-artifact`...) | CI/CD | Dependabot `github-actions` | ✅ Weekly PR |
| Runners (`windows-latest`, `ubuntu-24.04`) | CI/CD | [GitHub images](https://github.com/actions/runner-images) | Partly |

## Incidents already encountered

- **Python 3.10 + PySide6 6.12**: crash. CI moved to 3.12 and 3.13, Ubuntu 24.04 pinned (commit `e94e859`).

## At each check

- [ ] Open Dependabot PRs are reviewed and merged (or closed with a reason, in a comment in `dependabot.yml`).
- [ ] The latest PySide6 passes the tests locally before raising the `<7` bound.
- [ ] The freshly built executable launches on a clean Windows machine.
- [ ] Multi-screen and mixed-DPI behavior is rechecked on a real dual-screen setup after a Qt upgrade.

## Draft — to be completed

- [ ] Chosen check frequency (monthly? at each minor Qt upgrade?).
- [ ] PySide6 and PyInstaller versions validated as "good" for each Release (to note here or in the CHANGELOG).
- [ ] Manual Windows acceptance sheet (see [ACCESSIBILITY.md](./ACCESSIBILITY.md) and [DEVELOPMENT.md](./DEVELOPMENT.md)).
