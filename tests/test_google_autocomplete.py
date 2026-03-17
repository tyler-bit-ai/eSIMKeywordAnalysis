from __future__ import annotations

from pathlib import Path

from keyword_analysis.collectors.google_autocomplete import GoogleAutocompleteCollector
from keyword_analysis.query_expansion import ExpandedQuery
from keyword_analysis.storage import Observation, Storage


def _make_observation(raw_text: str, query_keyword: str) -> Observation:
    return Observation(
        run_id="run-1",
        observed_at_utc="2026-03-17T00:00:00+00:00",
        seed_keyword="korea esim",
        query_keyword=query_keyword,
        signal_type="autocomplete",
        locale_gl="us",
        language_hl="en",
        login_state="logged_out",
        browser_profile="default_desktop",
        device_class="desktop",
        rank_position=1,
        raw_text=raw_text,
        source_url="https://example.com",
        collector_version="0.1.0",
        notes="test",
    )


def test_collect_dedupes_observations_across_expanded_queries(tmp_path: Path, monkeypatch) -> None:
    storage = Storage(tmp_path / "keyword_analysis.sqlite3")
    collector = GoogleAutocompleteCollector(storage=storage)

    def fake_collect_query(seed_keyword: str, query_keyword: str, expansion_source: str) -> list[Observation]:
        if query_keyword == "korea esim":
            return [_make_observation("alpha", query_keyword)]
        return [
            _make_observation("alpha", query_keyword),
            _make_observation("beta", query_keyword),
        ]

    monkeypatch.setattr(collector, "_collect_query", fake_collect_query)

    observations = collector.collect(
        "korea esim",
        expanded_queries=[
            ExpandedQuery(query_keyword="korea esim", source="seed"),
            ExpandedQuery(query_keyword="korea esim best", source="modifier:best"),
        ],
    )

    assert [observation.raw_text for observation in observations] == ["alpha", "beta"]
    assert [observation.query_keyword for observation in observations] == [
        "korea esim",
        "korea esim best",
    ]
