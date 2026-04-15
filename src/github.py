"""GitHub repository download and skill extraction."""

import os
import re
import shutil
import stat
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path


def _force_rmtree(path: Path) -> None:
    def _on_error(_func, _path, _exc_info):
        os.chmod(_path, stat.S_IWRITE)
        os.unlink(_path)
    shutil.rmtree(path, onexc=_on_error)


@dataclass
class GitHubRef:
    owner: str
    repo: str
    branch: str | None = None
    subpath: str | None = None

    @property
    def clone_url(self) -> str:
        return f"https://github.com/{self.owner}/{self.repo}.git"

    @property
    def display(self) -> str:
        s = f"github:{self.owner}/{self.repo}"
        if self.subpath:
            s += f"/{self.subpath}"
        return s


def parse_github_url(url: str) -> GitHubRef:
    """Parse various GitHub URL formats into a GitHubRef.

    Supports:
      github:owner/repo
      github:owner/repo/path/to/skill
      https://github.com/owner/repo
      https://github.com/owner/repo/tree/branch/path
    """
    # github:owner/repo[/subpath]
    m = re.match(r"^github:([^/]+)/([^/]+)(?:/(.+))?$", url)
    if m:
        return GitHubRef(owner=m.group(1), repo=m.group(2), subpath=m.group(3))

    # https://github.com/owner/repo/tree/branch/path
    m = re.match(
        r"^https?://github\.com/([^/]+)/([^/]+)/tree/([^/]+)/(.+)$", url
    )
    if m:
        return GitHubRef(
            owner=m.group(1), repo=m.group(2),
            branch=m.group(3), subpath=m.group(4),
        )

    # https://github.com/owner/repo
    m = re.match(r"^https?://github\.com/([^/]+)/([^/]+?)(?:\.git)?$", url)
    if m:
        return GitHubRef(owner=m.group(1), repo=m.group(2))

    raise ValueError(f"Unsupported URL format: {url}")


def clone_repo(ref: GitHubRef, dest: Path) -> Path:
    """Shallow clone a repo to dest. Returns the repo root path."""
    cmd = ["git", "clone", "--depth", "1"]
    if ref.branch:
        cmd += ["-b", ref.branch]
    cmd += [ref.clone_url, str(dest)]

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"git clone failed: {result.stderr.strip()}")
    return dest


def extract_skills(repo_path: Path, subpath: str | None = None) -> dict[str, Path]:
    """Identify skills in a cloned repo.

    A skill is a directory containing at least one .md file.
    Returns {skill_name: skill_dir_path}.
    """
    root = repo_path / subpath if subpath else repo_path
    if not root.is_dir():
        raise FileNotFoundError(f"Path not found in repo: {root}")

    skills: dict[str, Path] = {}

    # If root itself contains .md files, treat it as a single skill
    if any(root.glob("*.md")):
        skills[root.name] = root
        return skills

    # Otherwise scan subdirectories
    for child in sorted(root.iterdir()):
        if child.is_dir() and not child.name.startswith("."):
            if any(child.glob("*.md")):
                skills[child.name] = child

    return skills


def download_skills(url: str) -> tuple[dict[str, Path], GitHubRef, Path]:
    """Download and extract skills from a GitHub URL.

    Returns (skills_dict, github_ref, temp_dir).
    Caller is responsible for cleaning up temp_dir.
    """
    ref = parse_github_url(url)
    tmp = Path(tempfile.mkdtemp(prefix="skmgr_"))
    repo_path = clone_repo(ref, tmp / ref.repo)
    skills = extract_skills(repo_path, ref.subpath)

    if not skills:
        _force_rmtree(tmp)
        raise RuntimeError(f"No skills found in {url}")

    return skills, ref, tmp
