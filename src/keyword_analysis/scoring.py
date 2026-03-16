"""Keyword scoring and prioritization from public Google signals."""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pandas as pd


SIGNAL_WEIGHTS: dict[str, int] = {
    "autocomplete": 5,
    "related_search": 3,
    "trends_related": 4,
    "serp_context": 1,
}

COMMERCIAL_MARKERS = ("best", "cheap", "price", "plan", "prepaid", "unlimited")


def load_observation_frame(
    database_path: Path = Path("outputs/keyword_analysis.sqlite3"),
) -> pd.DataFrame:
    with sqlite3.connect(database_path) as connection:
        observations = pd.read_sql_query("SELECT * FROM observations", connection)
        normalized = pd.read_sql_query("SELECT * FROM normalized_keywords", connection)

    if observations.empty:
        return observations

    frame = observations.merge(
        normalized,
        how="left",
        left_on="raw_text",
        right_on="raw_keyword",
    )
    frame["canonical_keyword"] = frame["canonical_keyword"].fillna(frame["raw_text"].str.lower())
    return frame


def score_keywords(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty:
        return pd.DataFrame()

    frame = frame.copy()
    frame["signal_weight"] = frame["signal_type"].map(SIGNAL_WEIGHTS).fillna(1)
    frame["commercial_flag"] = frame["canonical_keyword"].apply(
        lambda keyword: int(any(marker in str(keyword) for marker in COMMERCIAL_MARKERS))
    )
    frame["rank_bonus"] = frame["rank_position"].fillna(10).rsub(11).clip(lower=0)

    aggregated = (
        frame.groupby("canonical_keyword", dropna=False)
        .agg(
            keyword_family=("keyword_family", "first"),
            destination=("destination", "first"),
            signal_count=("signal_type", "nunique"),
            observation_count=("id", "count"),
            weighted_signal_score=("signal_weight", "sum"),
            avg_rank_bonus=("rank_bonus", "mean"),
            commercial_intent=("commercial_flag", "max"),
            evidence_signals=("signal_type", lambda values: ",".join(sorted(set(values)))),
            evidence_notes=("notes", lambda values: ",".join(sorted({str(v) for v in values if v}))),
        )
        .reset_index()
    )

    aggregated["priority_score"] = (
        aggregated["weighted_signal_score"]
        + aggregated["signal_count"] * 4
        + aggregated["avg_rank_bonus"].fillna(0)
        + aggregated["commercial_intent"] * 3
        + aggregated["observation_count"]
    ).round(2)

    aggregated["keyword_bucket"] = aggregated.apply(classify_keyword_bucket, axis=1)
    aggregated["confidence_note"] = aggregated.apply(build_confidence_note, axis=1)
    return aggregated.sort_values(["priority_score", "signal_count"], ascending=[False, False])


def classify_keyword_bucket(row: pd.Series) -> str:
    if row["signal_count"] >= 3 and row["priority_score"] >= 18:
        return "core_stable"
    if "trends_related" in str(row["evidence_signals"]) and row["priority_score"] >= 10:
        return "rising"
    return "niche_long_tail"


def build_confidence_note(row: pd.Series) -> str:
    return (
        f"signals={row['evidence_signals']};"
        f"count={row['observation_count']};"
        f"commercial={row['commercial_intent']}"
    )
