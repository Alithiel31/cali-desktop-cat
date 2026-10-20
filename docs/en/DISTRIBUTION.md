# Distribution (Windows executable)

[Français](../DISTRIBUTION.md) · English

[Back to the README](../../README.en.md)

Desktop Cat is distributed as a single executable, `DesktopCat.exe`, built by **PyInstaller** in GitHub Actions
(`.github/workflows/release.yml`).

## Building the executable locally

```bash
pip install pyinstaller
python tools/make_version_file.py
pyinstaller --noconsole --onefile --name DesktopCat --icon assets/desktopcat.ico --version-file build/version_info.txt main.py
```

Result: `dist/DesktopCat.exe`. `build/`, `dist/` and `*.spec` are ignored by Git.
`tools/make_version_file.py` writes the Windows metadata (product name, version taken from `desktopcat.__version__`,
author) shown in Properties > Details. Quit the cat before rebuilding: a running exe cannot be replaced
("Access denied").

## Publishing a version

1. Update `__version__` in `desktopcat/__init__.py` (e.g. `"0.4.2"`).
2. Move the content of `[Non publié]` in the [CHANGELOG](./CHANGELOG.md) (and in
   [CHANGELOG.md](../../CHANGELOG.md)) under a new `[0.4.2] - YYYY-MM-DD` heading.
3. Commit to `main`; CI must be green.
4. Create and push the tag:

   ```bash
   git tag v0.4.2
   git push --tags
   ```

The `release.yml` workflow:

| Step | What it does |
|---|---|
| Check tag/version | Fails if the tag (`v0.4.2`) does not match `desktopcat.__version__` (`0.4.2`). |
| Tests | Replays the whole suite before packaging. |
| Metadata | `tools/make_version_file.py` -> `build/version_info.txt`. |
| Build | `pyinstaller --noconsole --onefile --name DesktopCat --icon assets/desktopcat.ico --version-file build/version_info.txt main.py` on `windows-latest`. |
| Hash | Writes `DesktopCat.exe.sha256`. |
| Publication | Separate job, the only one with `contents: write`: `gh release create` with the exe, the hash and generated notes. |

On a PR that touches `main.py`, `requirements.txt`, `desktopcat/**` or the workflow, the build runs **as a dry run**
(no publication) to catch a packaging regression before the merge.

## Verifying a download

```powershell
(Get-FileHash .\DesktopCat.exe -Algorithm SHA256).Hash.ToLower()
```

Compare with the content of `DesktopCat.exe.sha256` published in the same Release.

## Known limitations

- **The executable is not signed**: Windows SmartScreen shows "Windows protected your PC". Click *More info* then
  *Run anyway*. **Smart App Control** (Windows 11), if enabled, blocks it with no way around ("blocked by Device Guard
  policy"), including an exe built locally. Antivirus products may also wrongly flag a PyInstaller executable (a common
  false positive with `--onefile`). The chosen remedy is the Microsoft Store (see below).
- Launch with Windows updates the registered path at every launch. If Windows refuses the change, the option goes back
  to its previous state and the panel shows a warning.
  (To verify with the packaged version, see "Draft" below.)

## Signing and Microsoft Store

The SignPath Foundation application (free signing for open source) was **rejected** in October 2026: the project is
not well known enough yet (few interactions on the repository). It can be tried again once it has more traction.

Chosen route: the **Microsoft Store**. Packages published on the Store are signed by the Store, which should remove
the SmartScreen warning and the Smart App Control block (to verify on a machine where Smart App Control is active,
once the package is available). The GitHub Releases keep providing the unsigned exe.

To do (nothing is committed yet):
- [ ] Create a Microsoft developer account (Partner Center) and reserve the name "Desktop Cat".
- [ ] Study the package: MSIX built from the PyInstaller exe (or from `--onedir`), required icons and metadata.
- [ ] Automate the package build in `release.yml`, or define a manual submission procedure.
- [ ] Prepare the Store listing (description, screenshots, privacy policy: no data transmitted, see
  [SECURITY.md](./SECURITY.md)).
- [ ] Verify inside the package environment: launch with Windows (`Run` key), global hotkey, `%APPDATA%\DesktopCat`
  folder (save file, log).
- [ ] Go through certification, then test on a machine with Smart App Control active. If it still blocks, the Event
  Viewer (Microsoft > Windows > CodeIntegrity > Operational, event 3077) names the refused file.

## Draft — to be completed

- [x] First Releases `v0.4.0` and `v0.4.1` published (tested with Python; the exe is blocked by Smart App Control on the
  dev machine).
- [x] Executable icon (`assets/desktopcat.ico`, see `tools/make_icon.py`).
- [x] Version number shown in the panel, the tray icon's tooltip and the exe's metadata.
- [ ] Versioned `.spec` file instead of the command line (today `*.spec` is in `.gitignore`; the local
  `DesktopCat.spec` is a PyInstaller leftover).
- [ ] Launch with Windows verified with the packaged executable (path in the registry).
- [x] SignPath application: rejected (October 2026); chosen route: Microsoft Store (see above). SmartScreen / Smart App Control note in the README: done.
- [ ] Pinned dependencies (`pyproject.toml` + lock file) for reproducible builds.
- [ ] Updates: decide whether the app notifies about a new Release (today, no network access — not to be broken
  lightly, cf. [SECURITY.md](./SECURITY.md)).
