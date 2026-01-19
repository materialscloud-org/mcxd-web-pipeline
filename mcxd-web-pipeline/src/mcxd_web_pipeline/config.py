from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent

ENV_VAR = "MCXD_WEB_PIPELINE_CONFIG"


def _repo_root_config_path() -> Path:
    # .../src/mcxd_web_pipeline/config.py -> parents[2] == project root in editable installs
    return Path(__file__).resolve().parents[2] / "config.yaml"


def _load_yaml(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if data is None:
        return {}
    if not isinstance(data, dict):
        raise ValueError(f"Top-level YAML must be a mapping: {path}")
    return data


def _pick_config_file() -> Path:
    p = os.getenv(ENV_VAR)
    if p:
        return Path(p).expanduser()

    repo = _repo_root_config_path()
    if repo.is_file():
        return repo

    raise FileNotFoundError(
        f"No config found. In editable installs, reads from {repo}, otherwise set {ENV_VAR}."
    )


@lru_cache(maxsize=1)
def get_config() -> dict[str, Any]:
    path = _pick_config_file()
    return _load_yaml(path)


def config_path() -> Path:
    """Where config is currently loaded from."""
    return _pick_config_file()


# Eager load:
CONFIG_PATH = _pick_config_file()
CONFIG = _load_yaml(CONFIG_PATH)
