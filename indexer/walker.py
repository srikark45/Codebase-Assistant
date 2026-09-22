"""
walker.py
Walks a repository and yields paths to source files worth indexing.
"""

import os
from pathlib import Path

DEFAULT_EXTENSIONS = {".py", ".js", ".ts", ".java", ".c", ".cpp", ".h", ".go", ".rb"}

DEFAULT_IGNORE_DIRS = {
    ".git", "node_modules", "__pycache__", "venv", ".venv",
    "dist", "build", ".mypy_cache", ".pytest_cache",
}


def find_source_files(root: str, extensions=None, ignore_dirs=None):
    """
    Walk `root` and yield absolute paths to files matching `extensions`.

    Args:
        root: path to the repository root.
        extensions: set of file extensions to include (default: DEFAULT_EXTENSIONS).
        ignore_dirs: set of directory names to skip entirely.

    Yields:
        str: absolute file path.
    """
    extensions = extensions or DEFAULT_EXTENSIONS
    ignore_dirs = ignore_dirs or DEFAULT_IGNORE_DIRS

    root_path = Path(root).resolve()
    if not root_path.exists():
        raise FileNotFoundError(f"Path does not exist: {root}")

    for dirpath, dirnames, filenames in os.walk(root_path):
        # prune ignored directories in-place so os.walk doesn't descend into them
        dirnames[:] = [d for d in dirnames if d not in ignore_dirs]

        for filename in filenames:
            if Path(filename).suffix in extensions:
                yield str(Path(dirpath) / filename)


def read_file_safely(path: str):
    """
    Read a file's text content, returning None on decode/permission errors
    instead of crashing the whole indexing run.
    """
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()
    except (OSError, UnicodeDecodeError):
        return None
