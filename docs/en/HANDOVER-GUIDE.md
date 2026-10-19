# Handover guide

[Français](../GUIDE-DE-REPRISE.md) · English

[Back to the README](../../README.en.md)

Desktop Cat has a single real maintainer (**Jacques Duchamplecheval**, GitHub alias `Alithiel31`). This document exists
so that another person — or Jacques himself after a long break — can take the project over without having to
reconstruct everything. It points to the existing documentation rather than duplicating it.

The project is deliberately light: a local application, no server, no database, no mandatory third-party account.
Taking it over is therefore much simpler than for a hosted service.

---

## 1. Understanding the project — recommended reading order

1. [README.en.md](../../README.en.md) — what the cat does, how to run it
2. [docs/en/GAMEPLAY.md](./GAMEPLAY.md) — the game rules (gifts, rarities, focus)
3. [docs/en/ARCHITECTURE.md](./ARCHITECTURE.md) — modules, loops, coordinates, extension points
4. [docs/en/DEVELOPMENT.md](./DEVELOPMENT.md) — run, test, conventions
5. [docs/en/DISTRIBUTION.md](./DISTRIBUTION.md) — build and publish the executable
6. [docs/en/ROADMAP.md](./ROADMAP.md) — what is done, what remains, in the recommended order
7. [docs/en/MANUAL-TESTING.md](./MANUAL-TESTING.md) — the checklist to run on a real Windows machine before a Release
8. [docs/en/TROUBLESHOOTING.md](./TROUBLESHOOTING.md), [SECURITY.md](./SECURITY.md),
   [CONTRIBUTING.md](./CONTRIBUTING.md)
9. [docs/en/DEPENDENCY-WATCH.md](./DEPENDENCY-WATCH.md), [docs/en/ACCESSIBILITY.md](./ACCESSIBILITY.md)
10. [CHANGELOG.md](./CHANGELOG.md) — history of decisions

The documentation also exists in French (`docs/`, `*.md`): both versions go together.

---

## 2. What exists, and where

| Component | Where | How to access it |
|---|---|---|
| Source code | GitHub, [`Alithiel31/cali-desktop-cat`](https://github.com/Alithiel31/cali-desktop-cat) (public) | The maintainer's GitHub account |
| Continuous integration | `.github/workflows/ci.yml` | Triggered on push to `main` and on PRs |
| Releases | `.github/workflows/release.yml` | Triggered on a `v*` tag; no secret required (`GITHUB_TOKEN` is enough) |
| User data | `%APPDATA%\DesktopCat\` on each user's machine | Local, never centralized |

No hosting, no domain, no database, no third-party service: there is nothing to "keep running" on the server side.

---

## 3. Secrets and access needed to act

No real secret is needed for the project to work or stored in the repository.

- **Administrator access to the GitHub repository** (branch settings, Releases, Dependabot).
- The release workflow only uses the automatically provided `GITHUB_TOKEN`.

Code signing (SignPath Foundation) is in preparation (see [DISTRIBUTION.md](./DISTRIBUTION.md)). Once the project is
accepted, the repository's `SIGNPATH_API_TOKEN` secret and `SIGNPATH_ORGANIZATION_ID` variable, as well as the SignPath
account (which approves every Release), will become the **critical** items of this list — to be recorded here at that
point.

---

## 4. Getting the project running again from scratch

1. Clone the repository, create a Python 3.12 or 3.13 environment, `pip install -r requirements.txt`.
2. `python -m unittest discover -s tests` — everything must pass.
3. `python main.py` on a Windows machine to validate by hand (preferably via `tools\run_test_instance.bat`, then the
   checklist in [MANUAL-TESTING.md](./MANUAL-TESTING.md)).
4. To publish: see [DISTRIBUTION.md](./DISTRIBUTION.md).

---

## 5. Known risks to keep in mind

- **Single maintainer** — this document reduces the risk but does not remove it.
- **Written without access to Windows at first**: the real Windows API (`winapi.py`) and mixed display scales are only
  validated by hand (see the README, "Known limitations").
- **Dependence on PySide6/Qt**: an upgrade may change rendering or break on certain Python versions (already happened
  with Python 3.10). See [DEPENDENCY-WATCH.md](./DEPENDENCY-WATCH.md).
- **Save format**: any change goes through `SCHEMA_VERSION` + a migration (see
  [ARCHITECTURE.md](./ARCHITECTURE.md#extension-points)); forgetting the migration means losing users' progress.

---

## To be completed by the maintainer

These fields are deliberately left empty — they involve personal information that has no place in a public repository:

- [ ] Where the GitHub account is kept (password manager, two-factor authentication) and who else has access in an emergency
- [ ] Trusted person(s) to contact in case of prolonged unavailability of the maintainer
- [ ] Where the local backups of the working folder are (other than GitHub), if any
