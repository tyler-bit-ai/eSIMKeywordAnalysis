"""High-level pipeline helpers for dashboard dataset refresh."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from keyword_analysis.collect import collect_korea_focus_seed_set
from keyword_analysis.intent_classifier import classify_keyword
from keyword_analysis.reporting import export_reports
from keyword_analysis.storage import Storage


DEFAULT_DATABASE_PATH = Path("outputs/keyword_analysis.sqlite3")
DEFAULT_REPORT_DIR = Path("outputs/reports_korea_focus")
DEFAULT_COLLECTION_EXPORT_DIR = Path("outputs/reports")
DEFAULT_FAILURE_LOG_PATH = DEFAULT_COLLECTION_EXPORT_DIR / "collection_failures.log"


class PipelineError(RuntimeError):
    """Raised when the dashboard refresh pipeline cannot complete."""


@dataclass(frozen=True)
class RefreshArtifacts:
    database_path: Path
    report_dir: Path
    collection_export_dir: Path
    ranked_keywords: Path
    cluster_summary: Path
    korea_marketing_targets: Path
    report_summary: Path
    normalized_keyword_count: int
    intent_assignment_count: int
    failure_log_path: Path


def refresh_korea_dashboard_dataset(
    database_path: Path = DEFAULT_DATABASE_PATH,
    report_dir: Path = DEFAULT_REPORT_DIR,
    collection_export_dir: Path = DEFAULT_COLLECTION_EXPORT_DIR,
    seed_limit: int | None = None,
) -> RefreshArtifacts:
    storage = Storage(database_path)
    collection_export_dir.mkdir(parents=True, exist_ok=True)
    report_dir.mkdir(parents=True, exist_ok=True)

    try:
        collect_korea_focus_seed_set(
            limit=seed_limit,
            database_path=database_path,
            export_dir=collection_export_dir,
        )
        normalized_keyword_count, intent_assignment_count = rebuild_keyword_metadata(storage)
        report_paths = export_reports(output_dir=report_dir, database_path=database_path)
    except Exception as error:
        raise PipelineError(str(error)) from error

    return RefreshArtifacts(
        database_path=database_path,
        report_dir=report_dir,
        collection_export_dir=collection_export_dir,
        ranked_keywords=report_paths["ranked_keywords"],
        cluster_summary=report_paths["cluster_summary"],
        korea_marketing_targets=report_paths["korea_marketing_targets"],
        report_summary=report_paths["report_summary"],
        normalized_keyword_count=normalized_keyword_count,
        intent_assignment_count=intent_assignment_count,
        failure_log_path=DEFAULT_FAILURE_LOG_PATH,
    )


def rebuild_keyword_metadata(storage: Storage) -> tuple[int, int]:
    normalized_keywords = []
    assignments = []

    for keyword in storage.list_distinct_raw_keywords():
        normalized_keyword, matched_assignments = classify_keyword(keyword)
        normalized_keywords.append(normalized_keyword)
        assignments.extend(matched_assignments)

    storage.insert_normalized_keywords(normalized_keywords)
    storage.replace_intent_assignments(assignments)
    return len(normalized_keywords), len(assignments)
