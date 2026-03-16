"""Small runner for prototype collection."""

from __future__ import annotations
from pathlib import Path

from keyword_analysis.collectors.google_autocomplete import GoogleAutocompleteCollector
from keyword_analysis.collectors.google_related_searches import GoogleRelatedSearchesCollector
from keyword_analysis.collectors.google_trends import GoogleTrendsCollector
from keyword_analysis.seeds import list_korea_focus_seed_keywords, list_seed_keywords
from keyword_analysis.storage import Storage


def collect_small_seed_set(limit: int = 3, database_path: Path = Path("outputs/keyword_analysis.sqlite3")) -> None:
    storage = Storage(database_path)
    seeds = list_seed_keywords()[:limit]
    _collect_seeds(storage, seeds)


def collect_korea_focus_seed_set(
    limit: int = 3,
    database_path: Path = Path("outputs/keyword_analysis.sqlite3"),
) -> None:
    storage = Storage(database_path)
    seeds = list_korea_focus_seed_keywords()[:limit]
    _collect_seeds(storage, seeds)


def _collect_seeds(storage: Storage, seeds: list[str]) -> None:
    failure_log = []

    for seed in seeds:
        autocomplete = GoogleAutocompleteCollector(storage=storage)
        related = GoogleRelatedSearchesCollector(storage=storage)
        trends = GoogleTrendsCollector(storage=storage)

        for collector_name, action in (
            ("autocomplete", lambda: autocomplete.collect(seed)),
            ("related_search", lambda: related.collect(seed)),
            ("trends_related", lambda: trends.collect_related_queries(seed)),
        ):
            try:
                action()
            except Exception as error:
                failure_log.append(f"{seed}|{collector_name}|{error}")

        storage.export_run_to_csv(
            autocomplete.context.run_id,
            Path("outputs/reports") / f"{seed.replace(' ', '_')}_{autocomplete.context.run_id}.csv",
        )

    if failure_log:
        Path("outputs/reports/collection_failures.log").write_text(
            "\n".join(failure_log) + "\n",
            encoding="utf-8",
        )


if __name__ == "__main__":
    collect_korea_focus_seed_set()
