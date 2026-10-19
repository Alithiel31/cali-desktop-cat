# Security

[Français](SECURITY.md) · English

## Reporting a vulnerability

Please **do not** open a public issue to report a security flaw — a regular GitHub issue exposes it to everyone before a
fix exists.

Two ways to report, in order of preference:

1. **[Report a vulnerability](https://github.com/Alithiel31/cali-desktop-cat/security/advisories/new)** through the
   repository's Security tab (GitHub Security Advisories) — the report stays private between you and the maintainer.
2. By email to [contact@alithiel31.dev](mailto:contact@alithiel31.dev), with `SECURITY` in the subject and, if possible:
   the affected component, steps to reproduce and the expected impact.

### What we can promise

- Acknowledgement within **72 hours**.
- The project is maintained by one person in their spare time: no formal SLA beyond the acknowledgement, but a
  confirmed flaw with real impact goes ahead of everything else.
- Credit in [`CHANGELOG.en.md`](./CHANGELOG.en.md) once the fix is published, unless you prefer otherwise.
- No bug bounty program — this is a personal project.

## What is exposed (threat model)

Desktop Cat is a **local** application: no server, no account, no network communication. The surfaces to consider are
therefore different from a web service:

| Surface | Detail |
|---|---|
| Local data | `%APPDATA%\DesktopCat\`: JSON save file, log. The statistics contain the **executable names** of the active windows (40 per day, 60 days), unless tracking is turned off in the settings. "Effacer mes statistiques" ("Erase my statistics") also removes them from readable backups. Nothing is sent anywhere. |
| Windows calls | `winapi.py` reads the window list, the active window and the idle time through `ctypes`. Read-only. |
| Registry | A single value written: `HKCU\Software\Microsoft\Windows\CurrentVersion\Run\DesktopCat` (launch with Windows, can be turned off). The `StartupApproved` key (Task Manager) is read; its value is only deleted when you re-tick the box. |
| Global hotkey | `RegisterHotKey` for Ctrl+Alt+C (can be turned off): the app reads no other keystroke. |
| Save file | Read and cleaned at startup (`store.py`): a damaged or malicious file is discarded, never executed. |
| Distributed executable | `DesktopCat.exe` (PyInstaller) published in the Releases, with its SHA256 hash. **Unsigned** (a SignPath Foundation application is in preparation): Windows SmartScreen will show a warning. |

## Scope

In scope: the code in `desktopcat/` and `main.py`, the GitHub Actions workflows (`.github/workflows/`, in particular
`release.yml`, which produces the executable), the published executable.

Out of scope: a flaw in PySide6/Qt, Python or PyInstaller themselves (report it upstream), already-privileged access to
the user's machine, social engineering.

## What is already in place

- **No network**: no outgoing request in the application code.
- **SHA256 hash** published with every executable (`DesktopCat.exe.sha256`).
- **Tests before packaging**: `release.yml` replays the test suite before building the executable; only the publishing
  job has write access (`contents: write`).
- **Tag and version aligned**: the Release fails if the tag does not match `desktopcat.__version__`.

## Draft — to be completed

- [ ] Enable Dependabot and the repository's security alerts (see [`.github/dependabot.yml`](./.github/dependabot.yml)).
- [ ] Add secret scanning (gitleaks) and CodeQL (Python) to CI, as on QcWeather.
- [ ] Sign the executable (code-signing certificate) — currently unsigned.
- [ ] Pin GitHub Actions by SHA once the release pipeline is stable.

## Supported versions

Only the latest published version (and `main`) receives fixes.
