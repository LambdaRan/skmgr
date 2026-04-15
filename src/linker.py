"""Windows directory junction operations."""

import os
import subprocess
import sys
from pathlib import Path


def is_junction(path: Path) -> bool:
    """Check if path is a directory junction (reparse point)."""
    if not path.exists() and not path.is_symlink():
        return False
    if sys.platform == "win32":
        import ctypes
        FILE_ATTRIBUTE_REPARSE_POINT = 0x400
        attrs = ctypes.windll.kernel32.GetFileAttributesW(str(path))
        return attrs != -1 and bool(attrs & FILE_ATTRIBUTE_REPARSE_POINT)
    return path.is_symlink()


def create_junction(target: Path, link: Path) -> None:
    """Create a junction/symlink from link -> target."""
    target = target.resolve()
    if not target.exists():
        raise FileNotFoundError(f"Target does not exist: {target}")

    link.parent.mkdir(parents=True, exist_ok=True)

    if link.exists() or is_junction(link):
        remove_junction(link)

    if sys.platform == "win32":
        result = subprocess.run(
            ["cmd", "/c", "mklink", "/J", str(link), str(target)],
            capture_output=True, text=True,
        )
        if result.returncode != 0:
            raise OSError(f"Failed to create junction: {result.stderr.strip()}")
    else:
        link.symlink_to(target)


def remove_junction(path: Path) -> None:
    """Remove a junction/symlink."""
    if not path.exists() and not is_junction(path):
        return
    if sys.platform == "win32" and is_junction(path):
        # rmdir removes junction without deleting target contents
        subprocess.run(["cmd", "/c", "rmdir", str(path)], capture_output=True)
    elif path.is_symlink():
        path.unlink()
    elif path.is_dir():
        import shutil
        shutil.rmtree(path)


def get_junction_target(path: Path) -> str | None:
    """Get the target of a junction/symlink, or None."""
    if not is_junction(path):
        return None
    if sys.platform == "win32":
        result = subprocess.run(
            ["cmd", "/c", "dir", str(path.parent), "/AL"],
            capture_output=True, text=True,
        )
        for line in result.stdout.splitlines():
            name = path.name
            if name in line and "[" in line:
                start = line.index("[") + 1
                end = line.index("]")
                return line[start:end]
    else:
        return str(path.resolve())
    return None
