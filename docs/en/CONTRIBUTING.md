# Contributing

[Français](../../CONTRIBUTING.md) · English

Thanks for your interest in this project. Desktop Cat is a Windows desktop companion (PySide6 / Qt 6); any contribution
that fixes a bug, improves reliability, the cat's behavior or the documentation is welcome.

## Before you start

- Open an issue to discuss the change you have in mind, except for trivial fixes (typo, broken link).
- Check the [roadmap](./ROADMAP.md): the topic may already be listed, with a decision still to be made (the
  hat shop, for example).
- Check that the change is not already under way in the `[Non publié]` ("Unreleased") section of
  [`CHANGELOG.md`](./CHANGELOG.md).

## Development environment

```bash
git clone https://github.com/Alithiel31/cali-desktop-cat.git
cd cali-desktop-cat
python -m venv .venv
.venv\Scripts\activate          # Windows; source .venv/bin/activate elsewhere
pip install -r requirements.txt
python main.py
```

Python **3.12 or 3.13** (CI tests both; 3.10 crashes with PySide6 6.12).

## Testing

```bash
python -m unittest discover -s tests -v
```

The tests also run outside Windows: Qt in `offscreen` mode, fake screens, fake mouse, fake desktop. On Linux you need
Qt's system libraries (`libegl1 libgl1 libxkbcommon0 libdbus-1-3 libfontconfig1 libglib2.0-0`).

**Golden rule: a test must never depend on your machine.** A guard in `GameTestCase` fails any test that would read the
real screens. Use `ScreenInfo` and `FixedCursor` (see [docs/en/ARCHITECTURE.md](./ARCHITECTURE.md#tests)).

To test by hand **without touching your real save**: `tools\run_test_instance.bat`.

## Reproducing CI locally

| Job | Command |
|---|---|
| `lint` (`ci.yml`) | `pip install -r requirements-dev.txt` then `ruff check .` (`ruff check --fix .` fixes import order and simple cases) |
| `tests` (`ci.yml`) | `set QT_QPA_PLATFORM=offscreen` then `python -m unittest discover -s tests -v` |
| `build-windows` (`release.yml`) | `pip install -r requirements-build.txt`, `python tools/make_version_file.py`, then `pyinstaller DesktopCat.spec` |

The executable build runs on a PR that touches `main.py`, `requirements.txt`, `requirements-build.txt`, `desktopcat/**` or the workflow itself.

## Opening a Pull Request

1. Create a branch from `main` (`git checkout -b fix/my-change`).
2. Commit with a clear message in the `type: description` format (`fix:`, `feat:`, `docs:`, `ci:`, `test:`, `chore:`).
   The project's own commits are written in French; English messages are fine for contributions.
3. Add or adapt a test for any change in behavior (a fixed bug = a test that would have caught it).
4. Update [`CHANGELOG.md`](../../CHANGELOG.md) and [`CHANGELOG.md`](./CHANGELOG.md) under `[Non publié]` (`Added`,
   `Changed`, `Fixed`, `Security`) if the change is visible to users.
5. If a game rule changes, update [docs/en/GAMEPLAY.md](./GAMEPLAY.md); if the structure changes,
   [docs/en/ARCHITECTURE.md](./ARCHITECTURE.md). Every document has a French counterpart (`docs/`, root `*.md`):
   update that one too (a rough translation is better than an outdated version).
6. Check that the `tests` job passes, then open the PR against `main`.

## Common recipes

See "Extension points" in [docs/en/ARCHITECTURE.md](./ARCHITECTURE.md#extension-points): new hat, new setting,
changing the save format (version + migration), new phrase, new cat state.

## Publishing a release

See [docs/en/DISTRIBUTION.md](./DISTRIBUTION.md).

## Reporting a problem

Open an issue from the Issues tab. Attach the last lines of `desktopcat.log` — see
[docs/en/TROUBLESHOOTING.md](./TROUBLESHOOTING.md#reporting-a-bug).

## Secrets and personal data

Never commit a real save file (`save.json`), a full log, or a screenshot showing private windows. Screenshots generated in `tools/out/` are
ignored by `.gitignore`; adding others (README) is fine, as long as no private window is visible.
