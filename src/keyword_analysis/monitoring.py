"""Monitoring helpers for keyword snapshot comparison."""

from __future__ import annotations

from pathlib import Path

import pandas as pd


def load_snapshot(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path)


def compare_snapshots(previous_path: Path, current_path: Path) -> dict[str, pd.DataFrame]:
    previous = load_snapshot(previous_path)
    current = load_snapshot(current_path)

    if previous.empty:
        return {
            "new_keywords": current,
            "disappeared_keywords": pd.DataFrame(),
            "rank_changes": pd.DataFrame(),
            "bucket_changes": pd.DataFrame(),
        }

    prev = previous.copy()
    curr = current.copy()
    prev["prior_rank"] = range(1, len(prev) + 1)
    curr["current_rank"] = range(1, len(curr) + 1)

    merged = curr.merge(
        prev[["canonical_keyword", "priority_score", "keyword_bucket", "prior_rank"]],
        on="canonical_keyword",
        how="outer",
        suffixes=("_current", "_previous"),
        indicator=True,
    )

    new_keywords = merged[merged["_merge"] == "left_only"]
    disappeared_keywords = merged[merged["_merge"] == "right_only"]
    persisted = merged[merged["_merge"] == "both"].copy()
    persisted["rank_delta"] = persisted["prior_rank"] - persisted["current_rank"]
    persisted["score_delta"] = (
        persisted["priority_score_current"] - persisted["priority_score_previous"]
    ).round(2)

    rank_changes = persisted[
        (persisted["rank_delta"] != 0) | (persisted["score_delta"].abs() >= 1)
    ].sort_values("rank_delta", ascending=False)
    bucket_changes = persisted[
        persisted["keyword_bucket_current"] != persisted["keyword_bucket_previous"]
    ]

    return {
        "new_keywords": new_keywords,
        "disappeared_keywords": disappeared_keywords,
        "rank_changes": rank_changes,
        "bucket_changes": bucket_changes,
    }

