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
  false positive with `--onefile`).
- Launch with Windows updates the registered path at every launch. If Windows refuses the change, the option goes back
  to its previous state and the panel shows a warning.
  (To verify with the packaged version, see "Draft" below.)

## Signing (SignPath Foundation)

Free signing for open-source projects: the certificate is in the name of SignPath Foundation (that is the publisher
Windows displays), which already has a reputation with SmartScreen and Smart App Control.

Conditions met (see <https://signpath.org/terms>): MIT license, no proprietary code, published project (v0.4.0, then
v0.4.1), how it works described in the README, no data transmitted, uninstall documented, **Code signing policy**
section in the README, builds made by GitHub Actions from the repository, product name and version in the exe's
metadata (`tools/make_version_file.py`).

Steps:
1. 2FA enabled on GitHub (and on SignPath when creating the account).
2. Apply at <https://signpath.org/apply>: repository, latest Release (v0.4.1), license, link to the Code signing policy.
3. Once accepted: create the `SIGNPATH_API_TOKEN` secret and the `SIGNPATH_ORGANIZATION_ID` variable in the repository,
   then uncomment the "Signature" block of `release.yml` (check the project and policy names).
4. For every Release: approve the signing request on signpath.io.
5. Verify on a machine with Smart App Control active. If it still blocks (unsigned Qt DLLs extracted by `--onefile`),
   the Event Viewer (Microsoft > Windows > CodeIntegrity > Operational, event 3077) names the refused file; consider
   `--onedir` then.

## Draft — to be completed

- [x] First Releases `v0.4.0` and `v0.4.1` published (tested with Python; the exe is blocked by Smart App Control on the
  dev machine).
- [x] Executable icon (`assets/desktopcat.ico`, see `tools/make_icon.py`).
- [x] Version number shown in the panel, the tray icon's tooltip and the exe's metadata.
- [ ] Versioned `.spec` file instead of the command line (today `*.spec` is in `.gitignore`; the local
  `DesktopCat.spec` is a PyInstaller leftover).
- [ ] Launch with Windows verified with the packaged executable (path in the registry).
- [ ] Code signing: SignPath application (see above). SmartScreen / Smart App Control note in the README: done.
- [ ] Pinned dependencies (`pyproject.toml` + lock file) for reproducible builds.
- [ ] Updates: decide whether the app notifies about a new Release (today, no network access — not to be broken
  lightly, cf. [SECURITY.md](./SECURITY.md)).
