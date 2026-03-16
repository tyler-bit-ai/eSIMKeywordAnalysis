"""Configuration helpers for collection profiles."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


DEFAULT_CONFIG_PATH = Path("config/collection_profiles.yaml")


def load_collection_profile(
    profile_name: str = "default_profile",
    config_path: Path = DEFAULT_CONFIG_PATH,
) -> dict[str, Any]:
    with config_path.open("r", encoding="utf-8") as file:
        profiles = yaml.safe_load(file) or {}

    if profile_name not in profiles:
        raise KeyError(f"Missing collection profile: {profile_name}")

    return profiles[profile_name]

