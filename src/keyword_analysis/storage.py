"""SQLite persistence for collection runs and raw observations."""

from __future__ import annotations

import csv
import sqlite3
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable

from keyword_analysis.schemas import IntentAssignment, NormalizedKeyword


@dataclass(frozen=True)
class CollectionRun:
    run_id: str
    started_at_utc: str
    collector_name: str
    profile_name: str
    locale_gl: str
    language_hl: str
    login_state: str
    browser_profile: str
    device_class: str
    status: str
    notes: str = ""


@dataclass(frozen=True)
class Observation:
    run_id: str
    observed_at_utc: str
    seed_keyword: str
    query_keyword: str
    signal_type: str
    locale_gl: str
    language_hl: str
    login_state: str
    browser_profile: str
    device_class: str
    rank_position: int | None
    raw_text: str
    source_url: str
    collector_version: str
    notes: str = ""


class Storage:
    def __init__(self, database_path: Path = Path("outputs/keyword_analysis.sqlite3")) -> None:
        self.database_path = database_path
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.database_path)
        connection.row_factory = sqlite3.Row
        return connection

    def _initialize(self) -> None:
        with self._connect() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS collection_runs (
                    run_id TEXT PRIMARY KEY,
                    started_at_utc TEXT NOT NULL,
                    collector_name TEXT NOT NULL,
                    profile_name TEXT NOT NULL,
                    locale_gl TEXT NOT NULL,
                    language_hl TEXT NOT NULL,
                    login_state TEXT NOT NULL,
                    browser_profile TEXT NOT NULL,
                    device_class TEXT NOT NULL,
                    status TEXT NOT NULL,
                    notes TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS observations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    run_id TEXT NOT NULL,
                    observed_at_utc TEXT NOT NULL,
                    seed_keyword TEXT NOT NULL,
                    query_keyword TEXT NOT NULL,
                    signal_type TEXT NOT NULL,
                    locale_gl TEXT NOT NULL,
                    language_hl TEXT NOT NULL,
                    login_state TEXT NOT NULL,
                    browser_profile TEXT NOT NULL,
                    device_class TEXT NOT NULL,
                    rank_position INTEGER,
                    raw_text TEXT NOT NULL,
                    source_url TEXT NOT NULL,
                    collector_version TEXT NOT NULL,
                    notes TEXT NOT NULL,
                    FOREIGN KEY (run_id) REFERENCES collection_runs (run_id)
                );

                CREATE TABLE IF NOT EXISTS normalized_keywords (
                    raw_keyword TEXT PRIMARY KEY,
                    canonical_keyword TEXT NOT NULL,
                    destination TEXT,
                    keyword_family TEXT NOT NULL,
                    clusters TEXT NOT NULL,
                    normalization_notes TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS intent_assignments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    canonical_keyword TEXT NOT NULL,
                    cluster TEXT NOT NULL,
                    reason TEXT NOT NULL
                );
                """
            )

    def insert_run(self, run: CollectionRun) -> None:
        payload = asdict(run)
        columns = ", ".join(payload)
        placeholders = ", ".join(f":{key}" for key in payload)
        with self._connect() as connection:
            connection.execute(
                f"INSERT OR REPLACE INTO collection_runs ({columns}) VALUES ({placeholders})",
                payload,
            )

    def insert_observations(self, observations: Iterable[Observation]) -> None:
        rows = [asdict(observation) for observation in observations]
        if not rows:
            return

        columns = ", ".join(rows[0])
        placeholders = ", ".join(f":{key}" for key in rows[0])
        with self._connect() as connection:
            connection.executemany(
                f"INSERT INTO observations ({columns}) VALUES ({placeholders})",
                rows,
            )

    def list_distinct_raw_keywords(self) -> list[str]:
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT DISTINCT raw_text FROM observations WHERE raw_text != '' ORDER BY raw_text"
            ).fetchall()
        return [str(row["raw_text"]) for row in rows]

    def export_run_to_csv(self, run_id: str, output_path: Path) -> None:
        self.export_runs_to_csv([run_id], output_path)

    def export_runs_to_csv(self, run_ids: Iterable[str], output_path: Path) -> None:
        run_id_list = [run_id for run_id in run_ids]
        if not run_id_list:
            return

        output_path.parent.mkdir(parents=True, exist_ok=True)
        placeholders = ", ".join("?" for _ in run_id_list)
        with self._connect() as connection:
            rows = connection.execute(
                (
                    "SELECT * FROM observations "
                    f"WHERE run_id IN ({placeholders}) "
                    "ORDER BY signal_type, rank_position"
                ),
                run_id_list,
            ).fetchall()

        if not rows:
            return

        with output_path.open("w", newline="", encoding="utf-8") as file:
            writer = csv.DictWriter(file, fieldnames=rows[0].keys())
            writer.writeheader()
            for row in rows:
                writer.writerow(dict(row))

    def insert_normalized_keywords(self, normalized_keywords: Iterable[NormalizedKeyword]) -> None:
        rows = []
        for normalized in normalized_keywords:
            payload = asdict(normalized)
            payload["clusters"] = ",".join(normalized.clusters)
            rows.append(payload)

        if not rows:
            return

        with self._connect() as connection:
            connection.executemany(
                """
                INSERT OR REPLACE INTO normalized_keywords (
                    raw_keyword,
                    canonical_keyword,
                    destination,
                    keyword_family,
                    clusters,
                    normalization_notes
                ) VALUES (
                    :raw_keyword,
                    :canonical_keyword,
                    :destination,
                    :keyword_family,
                    :clusters,
                    :normalization_notes
                )
                """,
                rows,
            )

    def insert_intent_assignments(self, assignments: Iterable[IntentAssignment]) -> None:
        rows = [asdict(assignment) for assignment in assignments]
        if not rows:
            return

        with self._connect() as connection:
            connection.executemany(
                """
                INSERT INTO intent_assignments (canonical_keyword, cluster, reason)
                VALUES (:canonical_keyword, :cluster, :reason)
                """,
                rows,
            )

    def replace_intent_assignments(self, assignments: Iterable[IntentAssignment]) -> None:
        rows = [asdict(assignment) for assignment in assignments]
        with self._connect() as connection:
            connection.execute("DELETE FROM intent_assignments")
            if rows:
                connection.executemany(
                    """
                    INSERT INTO intent_assignments (canonical_keyword, cluster, reason)
                    VALUES (:canonical_keyword, :cluster, :reason)
                    """,
                    rows,
                )
