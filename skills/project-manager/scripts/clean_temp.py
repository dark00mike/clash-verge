#!/usr/bin/env python3
"""Delete only explicitly disposable project temporary files; preserve active work."""

import argparse
import ctypes
import json
from pathlib import Path
import shutil


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", required=True, type=Path)
    args = parser.parse_args()
    if not args.root.is_absolute():
        parser.error("--root must be an absolute project path.")
    root = args.root.resolve()
    if not root.is_dir():
        parser.error("Project directory does not exist; no files were deleted.")
    temporary = root / ".tmp"
    target = temporary / "disposable"
    if not target.exists():
        print(json.dumps({"deleted_entries": 0, "status": "nothing_to_clean"}))
        return
    # Check the actual destructive target before any recursive operation on Windows.
    if temporary.resolve() != temporary or target.resolve() != target or not target.is_dir():
        parser.error("Disposable directory must be a real directory inside this project.")
    entries = list(target.iterdir())
    for entry in entries:
        if not entry.resolve().is_relative_to(target):
            parser.error("A disposable entry resolves outside its directory; no files were deleted.")
    if hasattr(ctypes, "windll"):
        kernel = ctypes.windll.kernel32
        attributes = kernel.GetFileAttributesW(str(temporary))
        if attributes == -1 or not kernel.SetFileAttributesW(str(temporary), attributes | 2):
            raise ctypes.WinError()
    deleted = 0
    for entry in entries:
        if entry.is_symlink() or not entry.is_dir():
            entry.unlink()
        else:
            shutil.rmtree(entry)
        deleted += 1
    print(json.dumps({"deleted_entries": deleted, "status": "cleaned"}))


if __name__ == "__main__":
    main()
