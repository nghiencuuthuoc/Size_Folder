#!/usr/bin/env python3
import os
import sys
import csv
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from fnmatch import fnmatch

def win_long(path: str) -> str:
    """Enable long-path support on Windows."""
    if os.name == "nt":
        path = os.path.normpath(path)
        if not path.startswith("\\\\?\\"):
            return "\\\\?\\" + path
    return path

def format_size(size_bytes: int) -> str:
    # Human-readable formatting
    for unit in ("bytes", "KB", "MB", "GB", "TB", "PB"):
        if size_bytes < 1024 or unit == "PB":
            return f"{size_bytes:.0f} {unit}" if unit == "bytes" else f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0

def should_exclude(name: str, patterns: list[str]) -> bool:
    return any(fnmatch(name, p) for p in patterns)

def get_folder_size(
    root: str,
    max_depth: int | None = None,
    exclude_patterns: list[str] | None = None,
    dedupe_hardlinks: bool = True,
) -> int:
    """
    Compute total byte size for all files under `root`.
    - Does not follow symlinks (avoids loops).
    - Optionally deduplicates files with multiple hardlinks.
    - Can limit recursion depth (0 means only `root` itself; 1 includes its direct children; etc.).
    """
    root = win_long(root)
    exclude_patterns = exclude_patterns or []
    total = 0
    seen_inodes: set[tuple[int, int]] = set()  # (st_dev, st_ino)

    def _walk(path: str, depth: int) -> None:
        nonlocal total
        try:
            with os.scandir(path) as it:
                for entry in it:
                    name = entry.name
                    if should_exclude(name, exclude_patterns):
                        continue
                    try:
                        if entry.is_symlink():
                            # Skip symlinks entirely to avoid cycles/double counting
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
                    except Exception as e:
                        print(f"⚠️ Cannot access {entry.path}: {e}", file=sys.stderr)
        except Exception as e:
            print(f"⚠️ Cannot open {path}: {e}", file=sys.stderr)

    _walk(root, 0)
    return total

def list_immediate_subdirs(root: str) -> list[str]:
    root = win_long(root)
    try:
        with os.scandir(root) as it:
            return [e.path for e in it if e.is_dir(follow_symlinks=False)]
    except FileNotFoundError:
        raise
    except Exception as e:
        print(f"⚠️ Cannot list {root}: {e}", file=sys.stderr)
        return []

def main():
    ap = argparse.ArgumentParser(
        description="Compute sizes of immediate subfolders under a root folder.")
    ap.add_argument("--root", "-r", default=".", help="Root folder (default: current directory)")
    ap.add_argument("--max-depth", type=int, default=None,
                    help="Max recursion depth relative to each subfolder (e.g., 2). Default: unlimited.")
    ap.add_argument("--exclude", "-x", action="append", default=[],
                    help="Glob patterns to exclude (e.g., -x .git -x node_modules -x '*.tmp'). Can repeat.")
    ap.add_argument("--threads", type=int, default=max(4, (os.cpu_count() or 4) * 2),
                    help="Number of worker threads (default: ~2x CPU).")
    ap.add_argument("--top", type=int, default=0,
                    help="Show only top-N largest subfolders (0 = show all).")
    ap.add_argument("--csv", metavar="OUT.csv", help="Write results to CSV file as well.")
    args = ap.parse_args()

    root = os.path.abspath(args.root)
    if not os.path.exists(root):
        print(f"❌ Folder not found: {root}", file=sys.stderr)
        sys.exit(1)

    subdirs = list_immediate_subdirs(root)
    if not subdirs:
        print(f"📁 No subdirectories under: {root}")
        return

    print(f"📁 Checking sizes in: {root}")
    results: list[tuple[str, int]] = []

    with ThreadPoolExecutor(max_workers=args.threads) as ex:
        fut2name = {
            ex.submit(
                get_folder_size,
                sd,
                max_depth=args.max_depth,
                exclude_patterns=args.exclude,
                dedupe_hardlinks=True,
            ): sd
            for sd in subdirs
        }
        for fut in as_completed(fut2name):
            sd = fut2name[fut]
            try:
                size = fut.result()
            except Exception as e:
                print(f"⚠️ Failed on {sd}: {e}", file=sys.stderr)
                size = 0
            results.append((sd, size))

    # Sort by size desc
    results.sort(key=lambda x: x[1], reverse=True)

    # Optionally trim to top-N
    display = results[: args.top] if args.top and args.top > 0 else results

    # Print nicely
    for path, size in display:
        folder_name = os.path.basename(path.rstrip("/\\"))
        print(f"📂 {folder_name}: {format_size(size)}")

    # CSV export
    if args.csv:
        try:
            with open(args.csv, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["folder", "bytes", "human_readable", "absolute_path"])
                for path, size in results:
                    writer.writerow([os.path.basename(path.rstrip('/\\')), size, format_size(size), path])
            print(f"💾 Saved CSV: {args.csv}")
        except Exception as e:
            print(f"⚠️ Cannot write CSV {args.csv}: {e}", file=sys.stderr)

if __name__ == "__main__":
    main()

# 
#  https://chatgpt.com/c/68fc31cd-9fcc-8320-8508-ebe83c288984
#  python size_folders.py --root "E:\DDD"


