"""Configuration helpers for collection profiles."""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any

import yaml


DEFAULT_CONFIG_PATH = Path("config/collection_profiles.yaml")
DEFAULT_PROFILE: dict[str, Any] = {
    "locale_gl": "us",
    "language_hl": "en",
    "google_domain": "www.google.com",
    "login_state": "logged_out",
    "device_class": "desktop",
    "user_agent_mode": "default_desktop",
    "viewport": {
        "width": 1440,
        "height": 900,
    },
    "request_spacing_seconds": 4,
    "retry_limit": 2,
    "collect_serp_context": False,
    "collect_related_searches": True,
    "autocomplete_expansion": {
        "enabled": True,
        "max_expansions": 16,
        "include_letters": True,
        "include_numbers": True,
        "include_modifiers": True,
        "letters": "abcdefghijklmnopqrstuvwxyz",
        "numbers": "0123456789",
        "modifiers": [
            "best",
            "buy",
            "review",
            "reddit",
            "unlimited",
            "for travel",
            "with phone number",
        ],
    },
}


def load_collection_profile(
    profile_name: str = "default_profile",
    config_path: Path = DEFAULT_CONFIG_PATH,
) -> dict[str, Any]:
    with config_path.open("r", encoding="utf-8") as file:
        profiles = yaml.safe_load(file) or {}

    if profile_name not in profiles:
        raise KeyError(f"Missing collection profile: {profile_name}")

    return _merge_profile(DEFAULT_PROFILE, profiles[profile_name])


def _merge_profile(defaults: dict[str, Any], overrides: dict[str, Any]) -> dict[str, Any]:
    merged = deepcopy(defaults)
    for key, value in overrides.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = _merge_profile(merged[key], value)
            continue
        merged[key] = value
    return merged
