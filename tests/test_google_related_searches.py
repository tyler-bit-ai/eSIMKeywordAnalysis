from __future__ import annotations

import sqlite3
from pathlib import Path

from keyword_analysis.collectors.google_related_searches import GoogleRelatedSearchesCollector
from keyword_analysis.storage import Storage


def test_collect_marks_failed_run_when_selector_lookup_fails(tmp_path: Path, monkeypatch) -> None:
    storage = Storage(tmp_path / "keyword_analysis.sqlite3")
    collector = GoogleRelatedSearchesCollector(storage=storage)

    def fake_run_with_retries(handler):
        raise RuntimeError("related_search_section_not_found")

    monkeypatch.setattr(collector, "run_with_retries", fake_run_with_retries)

    observations = collector.collect("korea esim")

    assert observations == []

    connection = sqlite3.connect(tmp_path / "keyword_analysis.sqlite3")
    row = connection.execute(
        "SELECT status, notes FROM collection_runs WHERE run_id = ?",
        (collector.context.run_id,),
    ).fetchone()
    connection.close()

    assert row == ("failed", "related_search_section_not_found")
