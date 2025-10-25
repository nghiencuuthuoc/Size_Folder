#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SizeFolder GUI — PharmApp themed
- Scan immediate subfolders under a root and compute total sizes.
- Threaded, cancellable, progress reporting, CSV export.
- Tkinter GUI with vertical space efficiency and resizable layout.
"""

import os
import sys
import csv
import queue
import platform
import threading
import traceback
from concurrent.futures import ThreadPoolExecutor, as_completed
from fnmatch import fnmatch

import tkinter as tk
from tkinter import ttk, filedialog, messagebox

# ------------------------------
# Utilities
# ------------------------------

APP_NAME = "SizeFolder GUI"
APP_VERSION = "v1.0"
PHARM_BG = "#fdf5e6"   # oldlace
PHARM_TXT = "#2a2a2a"
PHARM_ACCENT = "#f4a261"
PHARM_ACCENT2 = "#e76f51"

IS_MAC = (platform.system() == "Darwin")
IS_WIN = (platform.system() == "Windows")

def resource_path(rel: str) -> str:
    """
    Return absolute path to resource, works for dev and PyInstaller.
    """
    if hasattr(sys, "_MEIPASS"):
        base = sys._MEIPASS  # type: ignore[attr-defined]
    else:
        base = os.path.abspath(os.path.dirname(__file__))
    return os.path.join(base, rel)

def win_long(path: str) -> str:
    """Enable long-path support on Windows."""
    if IS_WIN:
        path = os.path.normpath(path)
        if not path.startswith("\\\\?\\"):
            return "\\\\?\\" + path
    return path

def format_size(size_bytes: int) -> str:
    """Human-readable size."""
    units = ("bytes", "KB", "MB", "GB", "TB", "PB")
    size = float(size_bytes)
    for u in units:
        if size < 1024.0 or u == units[-1]:
            return f"{int(size)} {u}" if u == "bytes" else f"{size:.2f} {u}"
        size /= 1024.0

def should_exclude(name: str, patterns: list[str]) -> bool:
    return any(fnmatch(name, p) for p in patterns)

def list_immediate_subdirs(root: str) -> list[str]:
    root = win_long(root)
    try:
        with os.scandir(root) as it:
            return [e.path for e in it if e.is_dir(follow_symlinks=False)]
    except FileNotFoundError:
        raise
    except Exception:
        traceback.print_exc()
        return []

def get_folder_size(
    root: str,
    stop_flag: threading.Event,
    max_depth: int | None = None,
    exclude_patterns: list[str] | None = None,
    dedupe_hardlinks: bool = True,
) -> int:
    """
    Compute total bytes for all files under `root`.
    - No symlink following.
    - Optionally dedupe files with multiple hardlinks.
    - Limit recursion depth (0 means only root itself; 1 includes its direct children; etc.)
    - Stop early if stop_flag is set.
    """
    root = win_long(root)
    exclude_patterns = exclude_patterns or []
    total = 0
    seen_inodes: set[tuple[int, int]] = set()

    def _walk(path: str, depth: int) -> None:
        nonlocal total
        if stop_flag.is_set():
            return
        try:
            with os.scandir(path) as it:
                for entry in it:
                    if stop_flag.is_set():
                        return
                    name = entry.name
                    if should_exclude(name, exclude_patterns):
                        continue
                    try:
                        if entry.is_symlink():
                            continue
                        if entry.is_dir(follow_symlinks=False):
                            if max_depth is None or depth < max_depth:
                                _walk(entry.path, depth + 1)
                        else:
                            st = entry.stat(follow_symlinks=False)
                            if dedupe_hardlinks:
                                key = (st.st_dev, st.st_ino)
                                if key in seen_inodes:
                                    continue
                                seen_inodes.add(key)
                            total += st.st_size
                    except Exception:
                        # Keep going; log to stderr to avoid GUI spam
                        print(f"⚠️ Cannot access {entry.path}", file=sys.stderr)
        except Exception:
            print(f"⚠️ Cannot open {path}", file=sys.stderr)

    _walk(root, 0)
    return total


# ------------------------------
# GUI
# ------------------------------

class SizeFolderApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(f"{APP_NAME} {APP_VERSION}")
        self.minsize(800, 520)
        self.configure(bg=PHARM_BG)
        try:
            # Window icon from PNG
            icon_png = resource_path("nct_logo.png")
            if os.path.exists(icon_png):
                self.iconphoto(True, tk.PhotoImage(file=icon_png))
        except Exception:
            pass

        # ttk style
        self.style = ttk.Style(self)
        # On some Linux distros, 'clam' is friendlier to recolor
        try:
            self.style.theme_use("clam")
        except Exception:
            pass
        self._init_styles()

        # State
        self.results: list[tuple[str, int]] = []  # (path, size_bytes)
        self.filtered_view: list[tuple[str, int]] = []
        self.stop_flag = threading.Event()
        self.scan_running = False
        self.queue = queue.Queue()

        # Build UI
        self._build_ui()

        # Shortcuts
        self._bind_shortcuts()

    # -------- Styles --------
    def _init_styles(self):
        # Basic palette
        self.style.configure("TFrame", background=PHARM_BG)
        self.style.configure("TLabel", background=PHARM_BG, foreground=PHARM_TXT)
        self.style.configure("TCheckbutton", background=PHARM_BG, foreground=PHARM_TXT)
        self.style.configure("TRadiobutton", background=PHARM_BG, foreground=PHARM_TXT)
        self.style.configure("TButton", padding=4)
        # Accent button
        self.style.configure("Accent.TButton", background=PHARM_ACCENT, foreground="#000")
        self.style.map("Accent.TButton",
                       background=[("active", PHARM_ACCENT2)],
                       foreground=[("active", "#fff")])

        # Treeview
        self.style.configure("Treeview",
                             background="white", fieldbackground="white",
                             foreground="#111", rowheight=22)
        self.style.configure("Treeview.Heading", font=("Segoe UI", 9, "bold"))

        # Progressbar
        self.style.configure("Horizontal.TProgressbar", thickness=8)

    # -------- UI Build --------
    def _build_ui(self):
        # Notebook (Scan / Help)
        self.nb = ttk.Notebook(self)
        self.nb.pack(fill="both", expand=True, padx=8, pady=8)

        self.tab_scan = ttk.Frame(self.nb)
        self.tab_help = ttk.Frame(self.nb)

        self.nb.add(self.tab_scan, text="Scan")
        self.nb.add(self.tab_help, text="Help")

        self._build_scan_tab(self.tab_scan)
        self._build_help_tab(self.tab_help)

    def _build_scan_tab(self, parent: ttk.Frame):
        # Top row: root + browse + scan/stop/save (compact)
        top = ttk.Frame(parent)
        top.pack(fill="x", padx=0, pady=(0, 6))

        ttk.Label(top, text="Root:").pack(side="left")
        self.var_root = tk.StringVar(value=os.path.expanduser("~"))
        self.ent_root = ttk.Entry(top, textvariable=self.var_root, width=48)
        self.ent_root.pack(side="left", padx=(4, 4), fill="x", expand=True)

        ttk.Button(top, text="Browse… (Ctrl/⌘+O)", command=self.on_browse).pack(side="left", padx=(0, 6))
        self.btn_scan = ttk.Button(top, text="Scan (Ctrl/⌘+R)", style="Accent.TButton", command=self.on_scan)
        self.btn_scan.pack(side="left", padx=(0, 6))
        self.btn_stop = ttk.Button(top, text="Stop (Esc)", command=self.on_stop, state="disabled")
        self.btn_stop.pack(side="left", padx=(0, 6))
        self.btn_csv = ttk.Button(top, text="Save CSV (Ctrl/⌘+S)", command=self.on_save_csv, state="disabled")
        self.btn_csv.pack(side="left")

        # Second row: options (very compact)
        opts = ttk.Frame(parent)
        opts.pack(fill="x", padx=0, pady=(0, 6))

        ttk.Label(opts, text="Exclude (glob, comma):").pack(side="left")
        self.var_exclude = tk.StringVar(value=".git,node_modules,__pycache__")
        self.ent_exclude = ttk.Entry(opts, textvariable=self.var_exclude, width=36)
        self.ent_exclude.pack(side="left", padx=(4, 16))

        ttk.Label(opts, text="Max depth:").pack(side="left")
        self.var_depth = tk.IntVar(value=2)
        sp_depth = ttk.Spinbox(opts, from_=0, to=99, textvariable=self.var_depth, width=4)
        sp_depth.pack(side="left", padx=(4, 12))

        ttk.Label(opts, text="Threads:").pack(side="left")
        default_threads = max(4, (os.cpu_count() or 4) * 2)
        self.var_threads = tk.IntVar(value=default_threads)
        sp_threads = ttk.Spinbox(opts, from_=1, to=256, textvariable=self.var_threads, width=4)
        sp_threads.pack(side="left", padx=(4, 12))

        ttk.Label(opts, text="Top-N:").pack(side="left")
        self.var_top = tk.IntVar(value=0)
        sp_top = ttk.Spinbox(opts, from_=0, to=1000, textvariable=self.var_top, width=6)
        sp_top.pack(side="left", padx=(4, 12))

        self.var_dedupe = tk.BooleanVar(value=True)
        ttk.Checkbutton(opts, text="De-dupe hardlinks", variable=self.var_dedupe).pack(side="left", padx=(0, 12))

        ttk.Label(opts, text="Filter:").pack(side="left")
        self.var_filter = tk.StringVar(value="")
        ent_filter = ttk.Entry(opts, textvariable=self.var_filter, width=24)
        ent_filter.pack(side="left", padx=(4, 0))
        ent_filter.bind("<KeyRelease>", lambda e: self.apply_filter())

        # Progress
        prog = ttk.Frame(parent)
        prog.pack(fill="x", padx=0, pady=(0, 6))
        self.pb = ttk.Progressbar(prog, mode="determinate")
        self.pb.pack(side="left", fill="x", expand=True)
        self.var_status = tk.StringVar(value="Ready.")
        ttk.Label(prog, textvariable=self.var_status).pack(side="left", padx=(8, 0))

        # Treeview (Folder, Size, Bytes, Path)
        tvf = ttk.Frame(parent)
        tvf.pack(fill="both", expand=True)
        columns = ("folder", "size_h", "bytes", "path")
        self.tv = ttk.Treeview(tvf, columns=columns, show="headings", selectmode="extended")
        self.tv.heading("folder", text="Folder", command=lambda: self.sort_by(0, key=lambda r: os.path.basename(r[0]).lower()))
        self.tv.heading("size_h", text="Size", command=lambda: self.sort_by(1, key=lambda r: r[1], reverse=True))
        self.tv.heading("bytes", text="Bytes", command=lambda: self.sort_by(1, key=lambda r: r[1], reverse=True))
        self.tv.heading("path", text="Path", command=lambda: self.sort_by(0, key=lambda r: r[0].lower()))
        self.tv.column("folder", width=220, anchor="w")
        self.tv.column("size_h", width=120, anchor="e")
        self.tv.column("bytes", width=120, anchor="e")
        self.tv.column("path", width=400, anchor="w")

        vsb = ttk.Scrollbar(tvf, orient="vertical", command=self.tv.yview)
        hsb = ttk.Scrollbar(tvf, orient="horizontal", command=self.tv.xview)
        self.tv.configure(yscroll=vsb.set, xscroll=hsb.set)
        self.tv.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")

        tvf.rowconfigure(0, weight=1)
        tvf.columnconfigure(0, weight=1)

        # Context menu
        self.ctx = tk.Menu(self, tearoff=False)
        self.ctx.add_command(label="Open Folder", command=self.on_open_folder)
        self.ctx.add_command(label="Reveal in File Manager", command=self.on_reveal)
        self.ctx.add_separator()
        self.ctx.add_command(label="Copy Path", command=self.on_copy_path)
        self.tv.bind("<Button-3>", self._show_ctx_menu)  # right click

        # Status bar (1 line)
        self.var_footer = tk.StringVar(value="© 2025 | 🧠 PharmApp | www.nghiencuuthuoc.com | www.pharmapp.vn")
        foot = ttk.Label(parent, textvariable=self.var_footer, anchor="center")
        foot.pack(fill="x", pady=(6, 0))

        # Make entire tab resizable
        parent.rowconfigure(3, weight=1)  # tvf row index in pack order not used; grid handles inside tvf.

    def _build_help_tab(self, parent: ttk.Frame):
        info = tk.Text(parent, wrap="word", height=20, bg="white", fg="#222")
        info.pack(fill="both", expand=True, padx=6, pady=6)

        mod = "⌘" if IS_MAC else "Ctrl"
        help_txt = f"""
{APP_NAME} {APP_VERSION}

What it does
- Scans immediate subfolders under the chosen Root and computes total sizes.
- Fast (os.scandir), no symlink following, optional hardlink de-duplication.
- Threaded with a Stop button, live progress, filter box, sortable columns.
- Exclude patterns support (glob): e.g., .git, node_modules, *.tmp
- Export CSV for downstream analysis.

Keyboard Shortcuts
- {mod}+O : Browse root folder
- {mod}+R : Start Scan
- {mod}+S : Save CSV
- {mod}+F : Focus Filter box
- F1      : Switch to Help tab
- Esc     : Stop current scan

Fields & Options
- Exclude: Comma separated glob patterns; applied to names at each level.
- Max depth: 0 only root; 1 includes its direct children; 2 (default) includes grandchildren; None = unlimited.
- Threads: Parallelize by subfolder (I/O-bound); default ≈ 2×CPU.
- Top-N: 0 = show all; otherwise shows the largest N.

Right-click on results
- Open Folder: open the folder directly.
- Reveal in File Manager: select/reveal the folder in Explorer/Finder.
- Copy Path: copy absolute path to clipboard.

Notes
- On Windows, very long paths are handled using the \\?\\ prefix internally.
- “Bytes” is logical size (st_size). Allocated size on disk may differ.
- CSV columns: folder, bytes, human_readable, absolute_path.

Build & Packaging
- Windows (EXE, one-file, icon):
  py -3 -m pip install pyinstaller
  py -3 -m PyInstaller --noconfirm --clean --onefile --windowed ^
      --name SizeFolderGUI ^
      --icon ./nct_logo.ico ^
      --add-data "nct_logo.png;." ^
      size_folder_gui.py

- macOS (.app):
  python3 -m pip install pyinstaller
  python3 -m PyInstaller --noconfirm --clean --windowed --name SizeFolderGUI \\
      --icon ./nct_logo.icns \\
      --add-data "nct_logo.png:." \\
      size_folder_gui.py
  # First run may require: right-click > Open (Gatekeeper).
  # For notarization/codesign, apply your Apple Developer ID as needed.

Branding
- Window icon: ./nct_logo.png (runtime)
- EXE icon:    ./nct_logo.ico (build-time)
- macOS icon:  ./nct_logo.icns (build-time)

© 2025 | 🧠 PharmApp | www.nghiencuuthuoc.com | www.pharmapp.vn
"""
        info.insert("1.0", help_txt)
        info.config(state="disabled")

    # -------- Shortcuts --------
    def _bind_shortcuts(self):
        mod = "Command" if IS_MAC else "Control"
        self.bind(f"<{mod}-o>", lambda e: self.on_browse())
        self.bind(f"<{mod}-O>", lambda e: self.on_browse())
        self.bind(f"<{mod}-r>", lambda e: self.on_scan())
        self.bind(f"<{mod}-R>", lambda e: self.on_scan())
        self.bind(f"<{mod}-s>", lambda e: self.on_save_csv())
        self.bind(f"<{mod}-S>", lambda e: self.on_save_csv())
        self.bind(f"<{mod}-f>", lambda e: self._focus_filter())
        self.bind(f"<{mod}-F>", lambda e: self._focus_filter())
        self.bind("<F1>", lambda e: self.nb.select(self.tab_help))
        self.bind("<Escape>", lambda e: self.on_stop())

    def _focus_filter(self):
        # Move focus to filter entry
        for w in self.tab_scan.winfo_children():
            # naive search
            pass
        self.focus()  # no-op; we keep it simple
        # Better: we stored the variable; get widget from options frame:
        # (We already bound KeyRelease on the entry; here we just try to set focus explicitly.)
        try:
            self.tab_scan.children  # ensure attribute exists
            # Find entry by variable string name
            for child in self.tab_scan.winfo_children():
                for sub in child.winfo_children():
                    if isinstance(sub, ttk.Entry) and sub.cget("textvariable") == str(self.var_filter):
                        sub.focus_set()
                        sub.selection_range(0, tk.END)
                        return
        except Exception:
            pass

    # -------- Context menu --------
    def _show_ctx_menu(self, event):
        try:
            iid = self.tv.identify_row(event.y)
            if iid:
                self.tv.selection_set(iid)
                self.ctx.tk_popup(event.x_root, event.y_root)
        finally:
            self.ctx.grab_release()

    def _get_selected_paths(self) -> list[str]:
        paths = []
        for iid in self.tv.selection():
            vals = self.tv.item(iid, "values")
            if len(vals) >= 4:
                paths.append(vals[3])
        return paths

    def on_open_folder(self):
        for p in self._get_selected_paths():
            self._open_folder(p)

    def on_reveal(self):
        for p in self._get_selected_paths():
            self._reveal_in_manager(p)

    def on_copy_path(self):
        paths = self._get_selected_paths()
        if not paths:
            return
        self.clipboard_clear()
        self.clipboard_append("\n".join(paths))
        self.update()
        self._set_status(f"Copied {len(paths)} path(s).")

    # -------- Platform helpers --------
    def _open_folder(self, path: str):
        try:
            if IS_WIN:
                os.startfile(path)  # type: ignore[attr-defined]
            elif IS_MAC:
                os.system(f'open "{path}"')
            else:
                os.system(f'xdg-open "{path}"')
        except Exception as e:
            messagebox.showerror("Open Folder", str(e))

    def _reveal_in_manager(self, path: str):
        try:
            if IS_WIN:
                # Reveal/Select in Explorer
                os.system(f'explorer /select,"{path}"')
            elif IS_MAC:
                os.system(f'open -R "{path}"')
            else:
                os.system(f'xdg-open "{os.path.dirname(path)}"')
        except Exception as e:
            messagebox.showerror("Reveal", str(e))

    # -------- Actions --------
    def on_browse(self):
        d = filedialog.askdirectory(initialdir=self.var_root.get() or os.path.expanduser("~"))
        if d:
            self.var_root.set(d)

    def on_scan(self):
        if self.scan_running:
            return
        root = self.var_root.get().strip()
        if not root or not os.path.isdir(root):
            messagebox.showwarning("Scan", "Please select a valid root folder.")
            return

        # Parse excludes
        raw_ex = [x.strip() for x in self.var_exclude.get().split(",") if x.strip()]
        self.excludes = raw_ex

        # Params
        self.max_depth = int(self.var_depth.get()) if self.var_depth.get() >= 0 else None
        self.threads = max(1, int(self.var_threads.get()))
        self.top_n = max(0, int(self.var_top.get()))
        self.dedupe = bool(self.var_dedupe.get())

        # Prepare UI
        self._clear_results()
        self.btn_scan.configure(state="disabled")
        self.btn_stop.configure(state="normal")
        self.btn_csv.configure(state="disabled")
        self.scan_running = True
        self.stop_flag.clear()
        self.pb.configure(mode="determinate", value=0)
        self._set_status("Scanning…")

        # Start background thread
        t = threading.Thread(target=self._scan_worker, args=(root,), daemon=True)
        t.start()
        # Start UI poll
        self.after(100, self._poll_queue)

    def on_stop(self):
        if self.scan_running:
            self.stop_flag.set()
            self._set_status("Stopping…")

    def on_save_csv(self):
        if not self.results:
            messagebox.showinfo("Save CSV", "No results to save.")
            return
        f = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv")],
            initialfile="folder_sizes.csv"
        )
        if not f:
            return
        try:
            with open(f, "w", newline="", encoding="utf-8") as out:
                w = csv.writer(out)
                w.writerow(["folder", "bytes", "human_readable", "absolute_path"])
                for p, sz in self.results:
                    w.writerow([os.path.basename(p.rstrip("/\\")), sz, format_size(sz), p])
            self._set_status(f"Saved CSV: {f}")
        except Exception as e:
            messagebox.showerror("Save CSV", str(e))

    # -------- Worker & Queue --------
    def _scan_worker(self, root: str):
        # List subdirs
        try:
            subdirs = list_immediate_subdirs(root)
        except FileNotFoundError:
            self.queue.put(("error", f"Folder not found: {root}"))
            self.queue.put(("done", None))
            return
        except Exception as e:
            self.queue.put(("error", f"Cannot list: {e}"))
            self.queue.put(("done", None))
            return

        n = len(subdirs)
        self.queue.put(("init", n))

        results_local: list[tuple[str, int]] = []
        # Parallel compute per subdir
        try:
            with ThreadPoolExecutor(max_workers=self.threads) as ex:
                fut_map = {
                    ex.submit(
                        get_folder_size,
                        sd,
                        self.stop_flag,
                        max_depth=self.max_depth,
                        exclude_patterns=self.excludes,
                        dedupe_hardlinks=self.dedupe,
                    ): sd for sd in subdirs
                }
                done_count = 0
                for fut in as_completed(fut_map):
                    sd = fut_map[fut]
                    try:
                        size = fut.result()
                    except Exception:
                        size = 0
                    results_local.append((sd, size))
                    done_count += 1
                    self.queue.put(("progress", done_count))
                    if self.stop_flag.is_set():
                        break
        except Exception as e:
            self.queue.put(("error", str(e)))

        # Sort by size desc
        results_local.sort(key=lambda x: x[1], reverse=True)
        self.queue.put(("results", results_local))
        self.queue.put(("done", None))

    def _poll_queue(self):
        try:
            while True:
                ev, payload = self.queue.get_nowait()
                if ev == "init":
                    total = int(payload)
                    self.pb.configure(maximum=total, value=0)
                elif ev == "progress":
                    v = int(payload)
                    self.pb.configure(value=v)
                    self._set_status(f"Scanning… {int(self.pb['value'])}/{int(self.pb['maximum'])}")
                elif ev == "results":
                    self.results = payload or []
                    self.apply_filter(refresh_tree=True)
                    self.btn_csv.configure(state="normal" if self.results else "disabled")
                elif ev == "error":
                    messagebox.showerror("Error", str(payload))
                elif ev == "done":
                    self.scan_running = False
                    self.btn_scan.configure(state="normal")
                    self.btn_stop.configure(state="disabled")
                    self._set_status("Done." if not self.stop_flag.is_set() else "Stopped.")
        except queue.Empty:
            pass

        if self.scan_running:
            self.after(100, self._poll_queue)

    # -------- Helpers --------
    def _set_status(self, msg: str):
        self.var_status.set(msg)

    def _clear_results(self):
        for iid in self.tv.get_children():
            self.tv.delete(iid)
        self.results = []
        self.filtered_view = []
        self.pb.configure(value=0, maximum=100)
        self._set_status("Ready.")

    def apply_filter(self, refresh_tree: bool = False):
        q = self.var_filter.get().strip().lower()
        data = self.results
        if q:
            data = [(p, sz) for (p, sz) in self.results if q in os.path.basename(p).lower() or q in p.lower()]
        # Trim top N if needed (but keep full data for CSV)
        top_n = self.top_n if hasattr(self, "top_n") else 0
        view = data[: top_n] if top_n and top_n > 0 else data
        self.filtered_view = view
        self._reload_tree()

    def _reload_tree(self):
        self.tv.delete(*self.tv.get_children())
        for p, sz in self.filtered_view:
            folder_name = os.path.basename(p.rstrip("/\\"))
            self.tv.insert("", "end", values=(folder_name, format_size(sz), sz, p))

    def sort_by(self, column_index: int, key, reverse: bool = False):
        """
        column_index: 0 for path, 1 for size
        key: callable mapping (p, sz)-> comparable
        """
        # Sort underlying filtered_view
        self.filtered_view.sort(key=key, reverse=reverse)
        self._reload_tree()

# ------------------------------
# Main
# ------------------------------

def main():
    app = SizeFolderApp()
    app.mainloop()

if __name__ == "__main__":
    main()
