"""Read-only scanner for a project directory.

Collects relative file paths and, for eligible text files, lowercased
text content. Binary files and files over 200 KB contribute a path only,
never content. Ignored directories are never descended into.
"""

from __future__ import annotations

import fnmatch
import os
from dataclasses import dataclass, field

IGNORE_DIRS = {".git", "node_modules", "__pycache__", ".venv", "venv", "dist", "build"}
MAX_TEXT_BYTES = 200_000


@dataclass
class ScanResult:
    files: list[str] = field(default_factory=list)
    texts: dict[str, str] = field(default_factory=dict)


def _is_text_file(path: str) -> bool:
    """True only if no chunk of the whole file contains a NUL byte.

    Files are already size-limited to 200 KB before this is called,
    so reading the whole file in chunks is cheap and correct, unlike
    checking only the first chunk.
    """
    try:
        with open(path, "rb") as handle:
            while True:
                chunk = handle.read(8192)
                if not chunk:
                    return True
                if b"\x00" in chunk:
                    return False
    except OSError:
        return False


def scan_project(path: str, exclude=None) -> ScanResult:
    """Scan *path* and return its files and eligible text content.

    *exclude* is an optional list of glob patterns; a file is skipped
    if any pattern matches its relative path or its basename.
    """
    if not os.path.isdir(path):
        raise FileNotFoundError(f"Directory not found: {path}")
    exclude = list(exclude or [])

    result = ScanResult()
    for root, dirs, names in os.walk(path):
        dirs[:] = sorted(d for d in dirs if d not in IGNORE_DIRS)
        for name in sorted(names):
            full = os.path.join(root, name)
            rel = os.path.relpath(full, path).replace(os.sep, "/")
            if any(
                fnmatch.fnmatch(rel, pattern) or fnmatch.fnmatch(name, pattern)
                for pattern in exclude
            ):
                continue
            result.files.append(rel)
            try:
                size = os.path.getsize(full)
            except OSError:
                continue
            if size > MAX_TEXT_BYTES or not _is_text_file(full):
                continue
            try:
                with open(full, encoding="utf-8", errors="ignore") as handle:
                    result.texts[rel] = handle.read().lower()
            except OSError:
                continue
    result.files.sort()
    return result
