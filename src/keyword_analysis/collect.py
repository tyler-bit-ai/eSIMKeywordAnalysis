"""Small runner for prototype collection."""

from __future__ import annotations
from pathlib import Path

from keyword_analysis.collectors.google_autocomplete import GoogleAutocompleteCollector
from keyword_analysis.collectors.google_related_searches import GoogleRelatedSearchesCollector
from keyword_analysis.collectors.google_trends import GoogleTrendsCollector
from keyword_analysis.config import load_collection_profile
from keyword_analysis.query_expansion import build_autocomplete_queries
from keyword_analysis.seeds import list_korea_focus_seed_keywords, list_seed_keywords
from keyword_analysis.storage import Storage


DEFAULT_EXPORT_DIR = Path("outputs/reports")


def collect_small_seed_set(
    limit: int | None = 3,
    database_path: Path = Path("outputs/keyword_analysis.sqlite3"),
    export_dir: Path = DEFAULT_EXPORT_DIR,
) -> None:
    storage = Storage(database_path)
    all_seeds = list_seed_keywords()
    seeds = all_seeds[:limit] if limit is not None else all_seeds
    _collect_seeds(storage, seeds, export_dir)


def collect_korea_focus_seed_set(
    limit: int | None = None,
    database_path: Path = Path("outputs/keyword_analysis.sqlite3"),
    export_dir: Path = DEFAULT_EXPORT_DIR,
) -> None:
    storage = Storage(database_path)
    all_seeds = list_korea_focus_seed_keywords()
    seeds = all_seeds[:limit] if limit is not None else all_seeds
    _collect_seeds(storage, seeds, export_dir)


def _collect_seeds(storage: Storage, seeds: list[str], export_dir: Path) -> None:
    failure_log = []
    export_dir.mkdir(parents=True, exist_ok=True)
    profile = load_collection_profile()
    expansion_config = profile.get("autocomplete_expansion", {})
    collect_related_searches = bool(profile.get("collect_related_searches", True))

    for seed in seeds:
        autocomplete = GoogleAutocompleteCollector(storage=storage)
        related = GoogleRelatedSearchesCollector(storage=storage)
        trends = GoogleTrendsCollector(storage=storage)
        run_ids = [autocomplete.context.run_id, trends.context.run_id]
        if collect_related_searches:
            run_ids.append(related.context.run_id)
        expanded_queries = build_autocomplete_queries(seed, expansion_config)

        collector_actions = [
            ("autocomplete", lambda: autocomplete.collect(seed, expanded_queries=expanded_queries)),
            ("trends_related", lambda: trends.collect_related_queries(seed)),
        ]
        if collect_related_searches:
            collector_actions.insert(1, ("related_search", lambda: related.collect(seed)))

        for collector_name, action in collector_actions:
            try:
                action()
            except Exception as error:
                failure_log.append(f"{seed}|{collector_name}|{error}")

        storage.export_runs_to_csv(
            run_ids,
            export_dir / f"{seed.replace(' ', '_')}_{autocomplete.context.run_id}.csv",
        )

    if failure_log:
        (export_dir / "collection_failures.log").write_text(
            "\n".join(failure_log) + "\n",
            encoding="utf-8",
        )


if __name__ == "__main__":
    collect_korea_focus_seed_set()
