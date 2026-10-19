# Development tools

[Français](README.md) · English

| File | Purpose |
|---|---|
| `run_test_instance.bat` | Runs the app with an isolated temporary save (meows off, 50 kibble, hungry cat): your real save is not touched. See [docs/en/MANUAL-TESTING.md](../docs/en/MANUAL-TESTING.md). |
| `make_icon.py` | Regenerates `assets/desktopcat.ico` (the exe's icon) from the cat sprite. Re-run it if the drawing changes. |
| `make_version_file.py` | Writes the Windows metadata of the exe (`build/version_info.txt`) from `desktopcat.__version__`. Used by the build, see [docs/en/DISTRIBUTION.md](../docs/en/DISTRIBUTION.md). |
| `preview_panel.py` | Generates screenshots of the panel in `tools/out/` (headless, Qt `offscreen` mode). |
| `demo_backups.py` | Replays the "damaged save" scenario in a temporary folder: set aside, daily copy, restore. |
| `spikes/` | Historical prototypes used to choose the technology (smoothness, transparency, perching). Kept for the record, **not maintained**. |

`spike_pywebview.py` is the first lead (Python + pywebview); `spike_qt.py` is the one that was kept (PySide6).
