from __future__ import annotations

from pathlib import Path

from keyword_analysis.config import load_collection_profile


def test_load_collection_profile_merges_defaults(tmp_path: Path) -> None:
    config_path = tmp_path / "collection_profiles.yaml"
    config_path.write_text(
        """
default_profile:
  locale_gl: ca
  viewport:
    width: 1280
  autocomplete_expansion:
    max_expansions: 4
    include_numbers: false
""".strip(),
        encoding="utf-8",
    )

    profile = load_collection_profile(config_path=config_path)

    assert profile["locale_gl"] == "ca"
    assert profile["language_hl"] == "en"
    assert profile["viewport"]["width"] == 1280
    assert profile["viewport"]["height"] == 900
    assert profile["collect_related_searches"] is True
    assert profile["autocomplete_expansion"]["max_expansions"] == 4
    assert profile["autocomplete_expansion"]["include_numbers"] is False
    assert profile["autocomplete_expansion"]["include_modifiers"] is True
