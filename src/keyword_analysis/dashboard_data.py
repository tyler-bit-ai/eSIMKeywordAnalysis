"""Dashboard data loaders and dataframe preparation helpers."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from keyword_analysis.monitoring import compare_snapshots


NOISE_MARKERS = ("reddit", "klook", "health insurance")


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
