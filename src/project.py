"""Project-level skill operations."""

import json
import os
import shutil
import stat
from pathlib import Path

from .config import get_archive_path, get_registry_path
from .github import download_skills
from .linker import create_junction, get_junction_target, is_junction, remove_junction


def _force_rmtree(path: Path) -> None:
    def _on_error(_func, _path, _exc_info):
        os.chmod(_path, stat.S_IWRITE)
        os.unlink(_path)
    shutil.rmtree(path, onexc=_on_error)

# Known tool directories: (marker_files/dirs, skills_subdir)
TOOL_SIGNATURES = [
    ([".claude", "CLAUDE.md"], ".claude/skills"),
    ([".agents", "AGENTS.md"], ".agents/skills"),
]

SKILLS_JSON = ".skills.json"


def _find_project_root() -> Path:
    """Return the current working directory as project root."""
    return Path.cwd()


def detect_targets(root: Path | None = None) -> list[Path]:
    """Auto-detect skill target directories in the project."""
    root = root or _find_project_root()
    targets = []

    for markers, skills_dir in TOOL_SIGNATURES:
        for marker in markers:
            if (root / marker).exists():
                targets.append(root / skills_dir)
                break

    return targets


def _load_skills_json(root: Path) -> dict:
    f = root / SKILLS_JSON
    if f.exists():
        return json.loads(f.read_text(encoding="utf-8"))
    return {"skills": {}}


def _save_skills_json(root: Path, data: dict) -> None:
    f = root / SKILLS_JSON
    f.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def init() -> None:
    """Scan existing skills in the project and initialize .skills.json."""
    root = _find_project_root()
    targets = detect_targets(root)

    if not targets:
        print("Error: No AI tool directory detected (.claude/ or .agents/).")
        return

    skills_json_path = root / SKILLS_JSON
    if skills_json_path.exists():
        print(f".skills.json already exists. Use 'skm status' to view.")
        return

    registry = get_registry_path()
    found: dict[str, dict] = {}

    for target_dir in targets:
        if not target_dir.exists():
            continue
        for item in sorted(target_dir.iterdir()):
            if not item.is_dir() or item.name.startswith("."):
                continue
            name = item.name
            if name in found:
                continue

            if is_junction(item):
                # junction → check if it points to the global registry
                target = get_junction_target(item)
                if target and registry.as_posix() in target.replace("\\", "/"):
                    found[name] = {"type": "global"}
                    print(f"  [global] {name}")
                else:
                    found[name] = {"type": "local", "source": ""}
                    print(f"  [local]  {name} (junction to external)")
            else:
                found[name] = {"type": "local", "source": ""}
                print(f"  [local]  {name}")

    if not found:
        print("No skills found in project.")
        return

    data = {"skills": found}
    _save_skills_json(root, data)
    print(f"\nInitialized .skills.json with {len(found)} skill(s).")


def use(skill_name: str) -> None:
    """Link a skill from the global registry into the project."""
    root = _find_project_root()
    targets = detect_targets(root)

    if not targets:
        print("Error: No AI tool directory detected (.claude/ or .agents/).")
        print("Create one first, or specify manually.")
        return

    skill_path = get_registry_path() / skill_name
    if not skill_path.is_dir():
        print(f"Error: Skill '{skill_name}' not found in registry.")
        print(f"  Registry: {get_registry_path()}")
        print(f"  Use 'sk list' to see available skills.")
        return

    for target_dir in targets:
        target_dir.mkdir(parents=True, exist_ok=True)
        link = target_dir / skill_name
        create_junction(skill_path, link)
        print(f"  + {skill_name} -> {target_dir.relative_to(root)}/")

    # Record in .skills.json
    data = _load_skills_json(root)
    data["skills"][skill_name] = {"type": "global"}
    _save_skills_json(root, data)


def unuse(skill_name: str) -> None:
    """Remove a skill link from the project."""
    root = _find_project_root()
    targets = detect_targets(root)

    for target_dir in targets:
        link = target_dir / skill_name
        if link.exists() or is_junction(link):
            remove_junction(link)
            print(f"  - {skill_name} from {target_dir.relative_to(root)}/")

    # Remove from .skills.json
    data = _load_skills_json(root)
    data["skills"].pop(skill_name, None)
    _save_skills_json(root, data)


def add(url: str) -> None:
    """Download a skill directly into the project (not via registry)."""
    root = _find_project_root()
    targets = detect_targets(root)

    if not targets:
        print("Error: No AI tool directory detected (.claude/ or .agents/).")
        return

    skills, ref, tmp = download_skills(url)

    for name, src_path in skills.items():
        for target_dir in targets:
            target_dir.mkdir(parents=True, exist_ok=True)
            dest = target_dir / name
            if dest.exists():
                _force_rmtree(dest)
            shutil.copytree(src_path, dest)
            # Remove .git if present
            git_dir = dest / ".git"
            if git_dir.exists():
                _force_rmtree(git_dir)
            print(f"  + {name} -> {target_dir.relative_to(root)}/")

        # Record in .skills.json as local
        data = _load_skills_json(root)
        data["skills"][name] = {"type": "local", "source": ref.display}
        _save_skills_json(root, data)

    _force_rmtree(tmp)


def sync() -> None:
    """Rebuild global skill links based on .skills.json. Skip local skills."""
    root = _find_project_root()
    targets = detect_targets(root)

    if not targets:
        print("Error: No AI tool directory detected.")
        return

    data = _load_skills_json(root)
    skills = data.get("skills", {})
    global_skills = {k: v for k, v in skills.items() if v.get("type") == "global"}
    local_skills = {k: v for k, v in skills.items() if v.get("type") == "local"}

    if not global_skills:
        print("No global skills to sync.")
        return

    registry = get_registry_path()
    synced = 0

    for name in global_skills:
        skill_path = registry / name
        if not skill_path.is_dir():
            print(f"  ! {name}: not found in registry, skipping")
            continue

        for target_dir in targets:
            target_dir.mkdir(parents=True, exist_ok=True)
            link = target_dir / name
            create_junction(skill_path, link)
            print(f"  ~ {name} -> {target_dir.relative_to(root)}/")
        synced += 1

    if local_skills:
        print(f"\nSkipped {len(local_skills)} local skill(s): {', '.join(local_skills)}")

    print(f"\nSynced {synced} global skill(s) to {len(targets)} target(s).")


def status() -> None:
    """Show skills linked in the current project."""
    root = _find_project_root()
    targets = detect_targets(root)
    data = _load_skills_json(root)
    skills = data.get("skills", {})

    if not targets:
        print("No AI tool directory detected in this project.")
        return

    print(f"Project: {root}\n")

    for target_dir in targets:
        print(f"  Target: {target_dir.relative_to(root)}/")
        if not target_dir.exists():
            print("    (directory does not exist)")
            continue

        for item in sorted(target_dir.iterdir()):
            if not item.is_dir():
                continue
            name = item.name
            info = skills.get(name, {})
            stype = info.get("type", "unknown")

            if is_junction(item):
                target = get_junction_target(item) or "?"
                print(f"    {name:<25} [global] -> {target}")
            else:
                if stype == "temp":
                    created = info.get("created", "")
                    print(f"    {name:<25} [temp]   {created}")
                elif stype == "local":
                    source = info.get("source", "")
                    print(f"    {name:<25} [local]  {source}")
                else:
                    print(f"    {name:<25} [untracked]")

    if not skills:
        print("\n  No skills in .skills.json")


def mark(skill_name: str, skill_type: str) -> None:
    """Change a skill's type in .skills.json."""
    root = _find_project_root()
    data = _load_skills_json(root)
    skills = data.get("skills", {})

    if skill_name not in skills:
        # Check if skill exists on disk but not in .skills.json
        targets = detect_targets(root)
        found = False
        for target_dir in targets:
            if (target_dir / skill_name).exists():
                found = True
                break
        if not found:
            print(f"Error: Skill '{skill_name}' not found in project.")
            return
        # Add it
        skills[skill_name] = {}

    entry = skills[skill_name]
    old_type = entry.get("type", "unknown")

    if skill_type == "temp":
        from datetime import date
        entry["type"] = "temp"
        entry.setdefault("created", str(date.today()))
    else:
        entry["type"] = skill_type
        entry.pop("created", None)

    data["skills"] = skills
    _save_skills_json(root, data)
    print(f"  {skill_name}: {old_type} -> {skill_type}")


def archive(skill_name: str) -> None:
    """Move a skill from the project to the archive directory."""
    root = _find_project_root()
    targets = detect_targets(root)
    archive_path = get_archive_path()
    archive_path.mkdir(parents=True, exist_ok=True)

    dest = archive_path / skill_name
    if dest.exists():
        _force_rmtree(dest)

    moved = False
    for target_dir in targets:
        src = target_dir / skill_name
        if src.exists() and not is_junction(src):
            if not moved:
                shutil.copytree(src, dest)
                moved = True
            _force_rmtree(src)
            print(f"  - {skill_name} from {target_dir.relative_to(root)}/")
        elif is_junction(src):
            remove_junction(src)
            print(f"  - {skill_name} (junction) from {target_dir.relative_to(root)}/")

    if moved:
        print(f"  -> archived to {archive_path}/")
    elif not moved and not any(is_junction(t / skill_name) for t in targets if (t / skill_name).exists()):
        print(f"Error: Skill '{skill_name}' not found in project.")
        return

    # Remove from .skills.json
    data = _load_skills_json(root)
    data["skills"].pop(skill_name, None)
    _save_skills_json(root, data)


def archive_all_temp() -> None:
    """Archive all skills marked as temp."""
    root = _find_project_root()
    data = _load_skills_json(root)
    skills = data.get("skills", {})
    temp_skills = [name for name, info in skills.items() if info.get("type") == "temp"]

    if not temp_skills:
        print("No temp skills to archive.")
        return

    for name in temp_skills:
        print(f"Archiving {name}...")
        archive(name)


def list_archived() -> None:
    """List all skills in the archive directory."""
    archive_path = get_archive_path()

    if not archive_path.exists():
        print("No archive directory. Nothing archived yet.")
        return

    items = [d for d in sorted(archive_path.iterdir()) if d.is_dir()]
    if not items:
        print("Archive is empty.")
        return

    print(f"Archive: {archive_path}\n")
    for item in items:
        print(f"  {item.name}")
    print(f"\nTotal: {len(items)} skill(s)")


def restore(skill_name: str) -> None:
    """Restore a skill from the archive to the project."""
    root = _find_project_root()
    targets = detect_targets(root)

    if not targets:
        print("Error: No AI tool directory detected (.claude/ or .agents/).")
        return

    archive_path = get_archive_path()
    src = archive_path / skill_name

    if not src.exists():
        print(f"Error: Skill '{skill_name}' not found in archive.")
        print(f"  Archive: {archive_path}")
        return

    for target_dir in targets:
        target_dir.mkdir(parents=True, exist_ok=True)
        dest = target_dir / skill_name
        if dest.exists():
            _force_rmtree(dest)
        shutil.copytree(src, dest)
        print(f"  + {skill_name} -> {target_dir.relative_to(root)}/")

    # Record in .skills.json as local
    data = _load_skills_json(root)
    data["skills"][skill_name] = {"type": "local", "source": "archive"}
    _save_skills_json(root, data)

    # Remove from archive
    _force_rmtree(src)
    print(f"  <- restored from archive")
