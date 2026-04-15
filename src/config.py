"""Global configuration management (~/.skrc.json)."""

import json
from pathlib import Path

CONFIG_PATH = Path.home() / ".skrc.json"
DEFAULT_REGISTRY = Path.home() / ".skills-registry"
DEFAULT_ARCHIVE = Path.home() / ".skills-archive"


def load_config() -> dict:
    if CONFIG_PATH.exists():
        return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    return {}


def save_config(cfg: dict) -> None:
    CONFIG_PATH.write_text(json.dumps(cfg, indent=2, ensure_ascii=False), encoding="utf-8")


def get_registry_path() -> Path:
    cfg = load_config()
    raw = cfg.get("registry", "")
    if raw:
        return Path(raw).expanduser().resolve()
    return DEFAULT_REGISTRY.resolve()


def set_registry_path(path_str: str) -> None:
    cfg = load_config()
    cfg["registry"] = str(Path(path_str).expanduser().resolve())
    save_config(cfg)
    print(f"Registry set to: {cfg['registry']}")


def get_archive_path() -> Path:
    cfg = load_config()
    raw = cfg.get("archive", "")
    if raw:
        return Path(raw).expanduser().resolve()
    return DEFAULT_ARCHIVE.resolve()


def set_archive_path(path_str: str) -> None:
    cfg = load_config()
    cfg["archive"] = str(Path(path_str).expanduser().resolve())
    save_config(cfg)
    print(f"Archive set to: {cfg['archive']}")
