"""Dashboard data loaders and dataframe preparation helpers."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pandas as pd

from keyword_analysis.dashboard_help import build_help_payload
from keyword_analysis.monitoring import compare_snapshots


NOISE_MARKERS = ("reddit", "klook", "health insurance")
DEFAULT_PUBLISHED_DASHBOARD_DIR = Path("outputs/published_dashboard")
DEFAULT_PUBLISHED_DASHBOARD_FILENAME = "dashboard_data.json"
DEFAULT_PUBLISHED_DASHBOARD_MANIFEST_FILENAME = "dashboard_manifest.json"
PUBLIC_DASHBOARD_DATASET_VERSION = "v1"


@dataclass(frozen=True)
class DashboardDataset:
    ranked_keywords: pd.DataFrame
    cluster_summary: pd.DataFrame
    korea_marketing_targets: pd.DataFrame
    kpi_frame: pd.DataFrame
    modifier_summary: pd.DataFrame
    seed_lineage: pd.DataFrame
    signal_summary: pd.DataFrame
    noisy_terms: pd.DataFrame
    snapshot_changes: dict[str, pd.DataFrame]


@dataclass(frozen=True)
class PublishedDashboardSpec:
    dataset_id: str
    label: str
    report_dir: Path
    output_filename: str | None = None
    previous_snapshot: Path | None = None
    current_snapshot: Path | None = None


def load_dashboard_dataset(
    report_dir: Path = Path("outputs/reports_korea_focus"),
    previous_snapshot: Path | None = None,
    current_snapshot: Path | None = None,
) -> DashboardDataset:
    ranked_keywords = _load_csv(report_dir / "ranked_keywords.csv")
    cluster_summary = _load_csv(report_dir / "cluster_summary.csv")
    korea_marketing_targets = _load_csv(report_dir / "korea_marketing_targets.csv")

    if not korea_marketing_targets.empty:
        korea_marketing_targets["is_noisy"] = korea_marketing_targets["canonical_keyword"].apply(is_noisy_keyword)
        korea_marketing_targets["origin_seed_count"] = (
            korea_marketing_targets["origin_seeds"].fillna("").str.split(",").apply(
                lambda values: len([value for value in values if value])
            )
        )

    kpi_frame = build_kpi_frame(korea_marketing_targets)
    modifier_summary = build_modifier_summary(korea_marketing_targets)
    seed_lineage = build_seed_lineage_summary(korea_marketing_targets)
    signal_summary = build_signal_summary(korea_marketing_targets)
    noisy_terms = korea_marketing_targets[korea_marketing_targets["is_noisy"]] if not korea_marketing_targets.empty else pd.DataFrame()
    snapshot_changes = build_snapshot_changes(previous_snapshot, current_snapshot)

    return DashboardDataset(
        ranked_keywords=ranked_keywords,
        cluster_summary=cluster_summary,
        korea_marketing_targets=korea_marketing_targets,
        kpi_frame=kpi_frame,
        modifier_summary=modifier_summary,
        seed_lineage=seed_lineage,
        signal_summary=signal_summary,
        noisy_terms=noisy_terms,
        snapshot_changes=snapshot_changes,
    )


def _load_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path)


def is_noisy_keyword(keyword: str) -> bool:
    normalized = str(keyword).lower()
    return any(marker in normalized for marker in NOISE_MARKERS)


def build_kpi_frame(targets: pd.DataFrame) -> pd.DataFrame:
    if targets.empty:
        return pd.DataFrame(
            [{"high_priority_targets": 0, "rising_keywords": 0, "manual_review_terms": 0, "tracked_targets": 0}]
        )

    return pd.DataFrame(
        [
            {
                "high_priority_targets": int((targets["marketing_priority"] == "high").sum()),
                "rising_keywords": int((targets["keyword_bucket"] == "rising").sum()),
                "manual_review_terms": int(targets["is_noisy"].sum()),
                "tracked_targets": int(len(targets)),
            }
        ]
    )


def build_modifier_summary(targets: pd.DataFrame) -> pd.DataFrame:
    if targets.empty:
        return pd.DataFrame()

    summary = (
        targets.groupby("follow_on_modifier", dropna=False)
        .agg(
            keyword_count=("canonical_keyword", "count"),
            avg_priority_score=("priority_score", "mean"),
            top_keywords=("canonical_keyword", lambda values: " | ".join(list(values)[:3])),
        )
        .reset_index()
        .sort_values(["avg_priority_score", "keyword_count"], ascending=[False, False])
    )
    summary["avg_priority_score"] = summary["avg_priority_score"].round(2)
    return summary


def build_seed_lineage_summary(targets: pd.DataFrame) -> pd.DataFrame:
    if targets.empty:
        return pd.DataFrame()

    exploded = targets.assign(origin_seed=targets["origin_seeds"].fillna("").str.split(",")).explode("origin_seed")
    exploded["origin_seed"] = exploded["origin_seed"].str.strip()
    exploded = exploded[exploded["origin_seed"] != ""]
    if exploded.empty:
        return pd.DataFrame()

    summary = (
        exploded.groupby("origin_seed", dropna=False)
        .agg(
            keyword_count=("canonical_keyword", "count"),
            avg_priority_score=("priority_score", "mean"),
            modifiers=("follow_on_modifier", lambda values: ",".join(sorted(set(map(str, values))))),
        )
        .reset_index()
        .sort_values("avg_priority_score", ascending=False)
    )
    summary["avg_priority_score"] = summary["avg_priority_score"].round(2)
    return summary


def build_signal_summary(targets: pd.DataFrame) -> pd.DataFrame:
    if targets.empty:
        return pd.DataFrame()

    exploded = targets.assign(signal=targets["observed_signals"].fillna("").str.split(",")).explode("signal")
    exploded["signal"] = exploded["signal"].str.strip()
    exploded = exploded[exploded["signal"] != ""]
    if exploded.empty:
        return pd.DataFrame()

    summary = (
        exploded.groupby("signal")
        .agg(
            keyword_count=("canonical_keyword", "count"),
            avg_priority_score=("priority_score", "mean"),
        )
        .reset_index()
        .sort_values("keyword_count", ascending=False)
    )
    summary["avg_priority_score"] = summary["avg_priority_score"].round(2)
    return summary


def build_snapshot_changes(
    previous_snapshot: Path | None,
    current_snapshot: Path | None,
) -> dict[str, pd.DataFrame]:
    if not previous_snapshot or not current_snapshot:
        empty = pd.DataFrame()
        return {
            "new_keywords": empty,
            "disappeared_keywords": empty,
            "rank_changes": empty,
            "bucket_changes": empty,
        }
    return compare_snapshots(previous_snapshot, current_snapshot)


def export_public_dashboard_bundle(
    report_dir: Path = Path("outputs/reports_korea_focus"),
    output_dir: Path = DEFAULT_PUBLISHED_DASHBOARD_DIR,
    previous_snapshot: Path | None = None,
    current_snapshot: Path | None = None,
    generated_at: datetime | None = None,
) -> Path:
    payload = _build_dashboard_payload(
        report_dir=report_dir,
        previous_snapshot=previous_snapshot,
        current_snapshot=current_snapshot,
        generated_at=generated_at,
    )
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / DEFAULT_PUBLISHED_DASHBOARD_FILENAME
    _write_dashboard_payload(output_path, payload)
    return output_path


def export_public_dashboard_manifest(
    dataset_specs: list[PublishedDashboardSpec],
    output_dir: Path = DEFAULT_PUBLISHED_DASHBOARD_DIR,
    generated_at: datetime | None = None,
    default_dataset_id: str | None = None,
) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    timestamp = generated_at or datetime.now(UTC)
    if not dataset_specs:
        manifest_path = output_dir / DEFAULT_PUBLISHED_DASHBOARD_MANIFEST_FILENAME
        manifest_path.write_text(
            json.dumps(
                {
                    "generated_at": timestamp.astimezone(UTC).isoformat().replace("+00:00", "Z"),
                    "default_dataset_id": None,
                    "datasets": [],
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
        return manifest_path

    default_id = default_dataset_id or dataset_specs[0].dataset_id
    manifest_entries: list[dict[str, Any]] = []
    default_payload: dict[str, Any] | None = None

    for spec in dataset_specs:
        filename = spec.output_filename or f"{spec.dataset_id}.json"
        payload = _build_dashboard_payload(
            report_dir=spec.report_dir,
            previous_snapshot=spec.previous_snapshot,
            current_snapshot=spec.current_snapshot,
            generated_at=timestamp,
        )
        output_path = output_dir / filename
        _write_dashboard_payload(output_path, payload)
        if spec.dataset_id == default_id:
            default_payload = payload
        manifest_entries.append(
            {
                "dataset_id": spec.dataset_id,
                "label": spec.label,
                "path": output_path.name,
                "generated_at": payload["generated_at"],
                "source_report_dir": str(spec.report_dir),
                "dataset_version": payload["dataset_version"],
                "has_previous_snapshot": payload["metadata"]["has_previous_snapshot"],
                "has_current_snapshot": payload["metadata"]["has_current_snapshot"],
            }
        )

    if default_payload is not None:
        _write_dashboard_payload(output_dir / DEFAULT_PUBLISHED_DASHBOARD_FILENAME, default_payload)

    manifest_path = output_dir / DEFAULT_PUBLISHED_DASHBOARD_MANIFEST_FILENAME
    manifest_path.write_text(
        json.dumps(
            {
                "generated_at": timestamp.astimezone(UTC).isoformat().replace("+00:00", "Z"),
                "default_dataset_id": default_id,
                "datasets": manifest_entries,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    return manifest_path


def build_public_dashboard_payload(
    dataset: DashboardDataset,
    source_report_dir: Path,
    previous_snapshot: Path | None = None,
    current_snapshot: Path | None = None,
    generated_at: datetime | None = None,
) -> dict[str, Any]:
    timestamp = generated_at or datetime.now(UTC)
    kpis = _build_public_kpis(dataset)
    return {
        "generated_at": timestamp.astimezone(UTC).isoformat().replace("+00:00", "Z"),
        "source_report_dir": str(source_report_dir),
        "dataset_version": PUBLIC_DASHBOARD_DATASET_VERSION,
        "help": _serialize_help_payload(),
        "kpis": kpis,
        "target_table": _serialize_target_table(dataset.korea_marketing_targets),
        "modifier_summary": _serialize_frame_records(dataset.modifier_summary),
        "seed_lineage": _serialize_frame_records(dataset.seed_lineage),
        "signal_summary": _serialize_frame_records(dataset.signal_summary),
        "snapshot_changes": {
            "new_keywords": _serialize_frame_records(dataset.snapshot_changes.get("new_keywords", pd.DataFrame())),
            "disappeared_keywords": _serialize_frame_records(
                dataset.snapshot_changes.get("disappeared_keywords", pd.DataFrame())
            ),
            "rank_changes": _serialize_frame_records(dataset.snapshot_changes.get("rank_changes", pd.DataFrame())),
            "bucket_changes": _serialize_frame_records(dataset.snapshot_changes.get("bucket_changes", pd.DataFrame())),
        },
        "metadata": {
            "has_previous_snapshot": bool(previous_snapshot),
            "has_current_snapshot": bool(current_snapshot),
            "notes": [],
        },
    }


def _build_dashboard_payload(
    report_dir: Path,
    previous_snapshot: Path | None,
    current_snapshot: Path | None,
    generated_at: datetime | None,
) -> dict[str, Any]:
    dataset = load_dashboard_dataset(
        report_dir=report_dir,
        previous_snapshot=previous_snapshot,
        current_snapshot=current_snapshot,
    )
    return build_public_dashboard_payload(
        dataset=dataset,
        source_report_dir=report_dir,
        previous_snapshot=previous_snapshot,
        current_snapshot=current_snapshot,
        generated_at=generated_at,
    )


def _write_dashboard_payload(output_path: Path, payload: dict[str, Any]) -> None:
    output_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def _serialize_help_payload() -> dict[str, Any]:
    payload = build_help_payload()
    score_rule = payload["score_rule"]
    sections = payload["sections"]
    return {
        "score_rule": {
            "title": score_rule.title,
            "summary": score_rule.summary,
            "formula_steps": list(score_rule.formula_steps),
            "signal_weights": score_rule.signal_weights,
            "marketing_priority_rules": list(score_rule.marketing_priority_rules),
            "bucket_rules": list(score_rule.bucket_rules),
        },
        "sections": [
            {
                "id": section.id,
                "title": section.title,
                "business_meaning": section.business_meaning,
                "how_to_use": section.how_to_use,
                "scoring_note": section.scoring_note,
            }
            for section in sections
        ],
    }


def _build_public_kpis(dataset: DashboardDataset) -> dict[str, int]:
    defaults = {
        "high_priority_targets": 0,
        "rising_keywords": 0,
        "new_keywords": 0,
        "manual_review_terms": 0,
        "tracked_targets": 0,
    }
    if dataset.kpi_frame.empty:
        return defaults

    source = {
        key: int(value)
        for key, value in dataset.kpi_frame.iloc[0].to_dict().items()
        if key in defaults
    }
    source["new_keywords"] = len(dataset.snapshot_changes.get("new_keywords", pd.DataFrame()))
    return {**defaults, **source}


def _serialize_target_table(frame: pd.DataFrame) -> list[dict[str, Any]]:
    if frame.empty:
        return []

    records: list[dict[str, Any]] = []
    for row in frame.to_dict(orient="records"):
        record = _normalize_record(row)
        record["observed_signals"] = _split_string_values(record.get("observed_signals"))
        record["origin_seeds"] = _split_string_values(record.get("origin_seeds"))
        record["raw_variants"] = _split_string_values(record.get("raw_variants"), delimiter="|")
        records.append(record)
    return records


def _serialize_frame_records(frame: pd.DataFrame) -> list[dict[str, Any]]:
    if frame.empty:
        return []
    return [_normalize_record(row) for row in frame.to_dict(orient="records")]


def _normalize_record(row: dict[str, Any]) -> dict[str, Any]:
    return {str(key): _normalize_scalar(value) for key, value in row.items()}


def _normalize_scalar(value: Any) -> Any:
    if pd.isna(value):
        return None
    if hasattr(value, "item"):
        return value.item()
    return value


def _split_string_values(raw_value: Any, delimiter: str = ",") -> list[str]:
    if raw_value in (None, ""):
        return []
    return [
        part.strip()
        for part in str(raw_value).split(delimiter)
        if part.strip()
    ]
