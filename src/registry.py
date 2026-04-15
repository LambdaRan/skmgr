"""Global skill registry operations."""

import json
import os
import shutil
import stat
from datetime import date
from pathlib import Path


def _force_rmtree(path: Path) -> None:
    """rmtree that handles Windows read-only files (e.g. .git objects)."""
    def _on_error(_func, _path, _exc_info):
        os.chmod(_path, stat.S_IWRITE)
        os.unlink(_path)
    shutil.rmtree(path, onexc=_on_error)

from .config import get_registry_path
from .github import download_skills


def _registry_file() -> Path:
    return get_registry_path() / "registry.json"


def _load_registry() -> dict:
    f = _registry_file()
    if f.exists():
        return json.loads(f.read_text(encoding="utf-8"))
    return {"skills": {}}


def _save_registry(data: dict) -> None:
    f = _registry_file()
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def install(url: str) -> list[str]:
    """Install skills from a GitHub URL into the global registry.

    Returns list of installed skill names.
    """
    skills, ref, tmp = download_skills(url)
    registry_path = get_registry_path()
    registry_path.mkdir(parents=True, exist_ok=True)
    reg = _load_registry()
    installed = []

    for name, src_path in skills.items():
        dest = registry_path / name
        if dest.exists():
            _force_rmtree(dest)
        shutil.copytree(src_path, dest, dirs_exist_ok=True)

        # Remove .git inside copied skill if present
        git_dir = dest / ".git"
        if git_dir.exists():
            _force_rmtree(git_dir)

        reg["skills"][name] = {
            "source": ref.display,
            "installed": str(date.today()),
        }
        installed.append(name)
        print(f"  + {name}")

    _save_registry(reg)
    _force_rmtree(tmp)

    print(f"\nInstalled {len(installed)} skill(s) to {registry_path}")
    return installed


def update(skill_name: str | None = None) -> None:
    """Update skills by re-installing from their source."""
    reg = _load_registry()

    if skill_name:
        if skill_name not in reg["skills"]:
            print(f"Skill not found in registry: {skill_name}")
            return
        entries = {skill_name: reg["skills"][skill_name]}
    else:
        entries = reg["skills"]

    if not entries:
        print("No skills in registry.")
        return

    # Group by source to avoid cloning the same repo multiple times
    by_source: dict[str, list[str]] = {}
    for name, info in entries.items():
        src = info["source"]
        by_source.setdefault(src, []).append(name)

    for source, names in by_source.items():
        print(f"Updating from {source}...")
        try:
            install(source)
        except Exception as e:
            print(f"  Failed: {e}")


def list_skills() -> None:
    """Print all skills in the global registry."""
    reg = _load_registry()
    skills = reg.get("skills", {})

    if not skills:
        print("No skills installed. Use 'sk install <url>' to add some.")
        return

    print(f"Registry: {get_registry_path()}\n")
    for name, info in sorted(skills.items()):
        source = info.get("source", "unknown")
        installed = info.get("installed", "?")
        print(f"  {name:<30} {source:<40} ({installed})")
    print(f"\nTotal: {len(skills)} skill(s)")


def get_skill_path(name: str) -> Path | None:
    """Return the path to a skill in the registry, or None."""
    path = get_registry_path() / name
    if path.is_dir():
        return path
    return None
