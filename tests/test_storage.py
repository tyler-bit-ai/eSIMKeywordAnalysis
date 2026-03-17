from __future__ import annotations

import csv
from pathlib import Path

from keyword_analysis.storage import Observation, Storage


def _make_observation(run_id: str, signal_type: str, rank: int, raw_text: str) -> Observation:
    return Observation(
        run_id=run_id,
        observed_at_utc="2026-03-17T00:00:00+00:00",
        seed_keyword="south korea esim",
        query_keyword="south korea esim",
        signal_type=signal_type,
        locale_gl="us",
        language_hl="en",
        login_state="logged_out",
        browser_profile="default_desktop",
        device_class="desktop",
        rank_position=rank,
        raw_text=raw_text,
        source_url="https://example.com",
        collector_version="0.1.0",
        notes="test",
    )


def test_export_run_to_csv_keeps_single_run_behavior(tmp_path: Path) -> None:
    storage = Storage(tmp_path / "keyword_analysis.sqlite3")
    output_path = tmp_path / "single.csv"

    storage.insert_observations([
        _make_observation("run-a", "autocomplete", 1, "alpha"),
        _make_observation("run-b", "trends_related", 1, "beta"),
    ])

    storage.export_run_to_csv("run-a", output_path)

    with output_path.open(newline="", encoding="utf-8") as file:
        rows = list(csv.DictReader(file))

    assert [row["run_id"] for row in rows] == ["run-a"]
    assert [row["signal_type"] for row in rows] == ["autocomplete"]


def test_export_runs_to_csv_aggregates_multiple_runs(tmp_path: Path) -> None:
    storage = Storage(tmp_path / "keyword_analysis.sqlite3")
    output_path = tmp_path / "multi.csv"

    storage.insert_observations([
        _make_observation("run-a", "autocomplete", 2, "beta"),
        _make_observation("run-b", "trends_related", 1, "alpha"),
    ])

    storage.export_runs_to_csv(["run-a", "run-b"], output_path)

    with output_path.open(newline="", encoding="utf-8") as file:
        rows = list(csv.DictReader(file))

    assert [row["signal_type"] for row in rows] == ["autocomplete", "trends_related"]
    assert [row["run_id"] for row in rows] == ["run-a", "run-b"]
