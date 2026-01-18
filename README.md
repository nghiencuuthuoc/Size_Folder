# SizeFolder GUI (PharmApp themed)

A lightweight, cross‑platform desktop utility to scan the **immediate subfolders** of a chosen root directory and compute their total sizes. It is designed for fast folder triage (find what is consuming disk space), with **threaded scanning**, **stop/cancel**, **filtering**, **sortable columns**, and **CSV export**.

## Key features

- Scans **immediate subfolders** under a selected *Root* folder
- Computes sizes recursively with configurable **Max depth**
- **Threaded** I/O scanning (configurable worker threads)
- **Stop** button (Esc) for cancellable runs
- **Exclude patterns** (glob, comma-separated) such as `.git`, `node_modules`, `__pycache__`
- **Filter** box for quick search in results
- **Sortable columns** (click headers to toggle ▲/▼)
- **Top‑N** view (show only the largest N subfolders)
- **CSV export** (`folder, bytes, human_readable, absolute_path`)
- Cross‑platform: Windows / macOS / Linux (Tkinter)

## Screenshots

Add screenshots here (recommended):
- `./docs/screenshot_scan.png`
- `./docs/screenshot_help.png`

## Requirements

- Python **3.8+**
- Tkinter (bundled with most Python installers; on some Linux distros you may need to install it separately)

No third‑party Python packages are required.

## Quick start

### 1) Run from source

```bash
python size_folder_gui_gui_v1.py
```

If you prefer, rename the script to `size_folder_gui.py` and run:

```bash
python size_folder_gui.py
```

### 2) Use the app

1. Choose a **Root** folder
2. Adjust options if needed:
   - **Exclude**: glob patterns (comma-separated)
   - **Max depth**: recursion depth (0 = only root; 1 = children; 2 = grandchildren; etc.)
   - **Threads**: parallel workers
   - **Top‑N**: show only the largest N results (0 = show all)
   - **De‑dupe hardlinks**: avoids counting hardlinked files multiple times
3. Click **Scan**
4. Optionally **Save CSV**

## Keyboard shortcuts

- **Ctrl/⌘ + O**: Browse root folder
- **Ctrl/⌘ + R**: Start scan
- **Ctrl/⌘ + S**: Save CSV
- **Ctrl/⌘ + F**: Focus filter box
- **F1**: Help tab
- **Esc**: Stop scan

## Output and interpretation

- **Bytes** is the logical file size (`st_size`), not necessarily allocated size on disk.
- On Windows, the tool internally applies the `\\?\` prefix to better support very long paths.
- Symlinks are not followed.

## CSV export format

The exported CSV contains:

| Column | Description |
|---|---|
| `folder` | Subfolder name (basename) |
| `bytes` | Total size in bytes |
| `human_readable` | Formatted size (KB/MB/GB/...) |
| `absolute_path` | Full path of the subfolder |

## Build standalone executables (PyInstaller)

> Optional. Only needed if you want a packaged app.

### Windows (one‑file EXE)

```powershell
py -3 -m pip install pyinstaller
py -3 -m PyInstaller --noconfirm --clean --onefile --windowed `
  --name SizeFolderGUI `
  --icon .\nct_logo.ico `
  --add-data "nct_logo.png;." `
  size_folder_gui_gui_v1.py
```

### macOS (.app bundle)

```bash
python3 -m pip install pyinstaller
python3 -m PyInstaller --noconfirm --clean --windowed \
  --name SizeFolderGUI \
  --icon ./nct_logo.icns \
  --add-data "nct_logo.png:." \
  size_folder_gui_gui_v1.py
```

Notes:
- On macOS, Gatekeeper may block the first run; use right‑click → Open.
- For distribution, consider code signing and notarization.

## Project links

- Product / demo: **www.pharmapp.dev**
- Articles & documentation: **www.nghiencuuthuoc.com**

## License

Choose one:
- MIT (recommended for open source utilities), or
- Proprietary / internal use only

If you select MIT, add a `LICENSE` file at the repo root.
