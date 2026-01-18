# SizeFolder GUI (PharmApp Themed)

A cross-platform Tkinter desktop utility that scans the **immediate subfolders** under a chosen root folder and computes total size per subfolder, with **threaded scanning**, **cancellation**, **live progress**, **filtering**, **sortable columns**, and **CSV export**. fileciteturn0file0L1-L9

## Features

- Scan immediate subfolders and compute total sizes (bytes + human-readable). fileciteturn0file0L1-L9  
- Threaded scanning with **Stop** (cancellable). fileciteturn0file0L1-L9  
- **Exclude patterns** (glob, comma-separated): e.g., `.git,node_modules,__pycache__`. fileciteturn0file0L169-L179  
- **Max depth** control (limit recursion). fileciteturn0file0L62-L80  
- Optional **hardlink de-duplication** (avoid double-counting). fileciteturn0file0L62-L80  
- Sortable columns (click header to toggle ▲/▼). fileciteturn0file0L9-L9  
- Inline **filter box** (search by folder name or path). fileciteturn0file0L190-L195  
- Context menu: open folder, reveal in file manager, copy path. fileciteturn0file0L219-L239  
- CSV export (`folder, bytes, human_readable, absolute_path`). fileciteturn0file0L311-L327  
- Windows long-path handling (`\\?\\` prefix). fileciteturn0file0L36-L47  

## Requirements

- Python 3.9+ (recommended)
- No external dependencies (standard library only)

## Run

```bash
python size_folder_gui_gui_v1.py
```

> The app launches a GUI window. Choose a root folder, then click **Scan**.

## Keyboard Shortcuts

- **Ctrl/⌘ + O**: Browse root folder fileciteturn0file0L141-L149  
- **Ctrl/⌘ + R**: Start scan fileciteturn0file0L141-L149  
- **Ctrl/⌘ + S**: Save CSV fileciteturn0file0L141-L149  
- **Ctrl/⌘ + F**: Focus filter box fileciteturn0file0L141-L149  
- **F1**: Open Help tab fileciteturn0file0L141-L149  
- **Esc**: Stop scan fileciteturn0file0L141-L149  

## How it Works

1. Lists immediate subfolders of the selected root. fileciteturn0file0L50-L60  
2. Computes each subfolder size recursively using `os.scandir()` (no symlink following). fileciteturn0file0L62-L114  
3. Runs size computations in parallel using a `ThreadPoolExecutor`. fileciteturn0file0L344-L387  
4. Streams progress/results back to the GUI via a thread-safe queue. fileciteturn0file0L284-L309  

## CSV Output

CSV columns (in this order): fileciteturn0file0L311-L327

- `folder`
- `bytes`
- `human_readable`
- `absolute_path`

## Packaging (PyInstaller)

### Windows (EXE)

```powershell
py -3 -m pip install pyinstaller
py -3 -m PyInstaller --noconfirm --clean --onefile --windowed `
  --name SizeFolderGUI `
  --icon .\nct_logo.ico `
  --add-data "nct_logo.png;." `
  size_folder_gui_gui_v1.py
```

### macOS (.app)

```bash
python3 -m pip install pyinstaller
python3 -m PyInstaller --noconfirm --clean --windowed --name SizeFolderGUI \
  --icon ./nct_logo.icns \
  --add-data "nct_logo.png:." \
  size_folder_gui_gui_v1.py
```

## Branding

- Runtime window icon: `nct_logo.png` fileciteturn0file0L23-L35  
- Theme colors are defined in constants near the top of the file. fileciteturn0file0L17-L28  

### Website

The official project website is: **www.pharmapp.dev**.

If you want the in-app footer to match, update the footer string in the code:

- `self.var_footer = "... | www.pharmapp.dev"` (in the Scan tab footer). fileciteturn0file0L254-L258  

## License

Choose a license for your repository (e.g., MIT). If you haven’t decided yet, add a `LICENSE` file later.

---

© 2026 | PharmApp | www.pharmapp.dev | www.nghiencuuthuoc.com
