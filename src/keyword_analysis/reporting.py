"""Reporting utilities for ranked keyword outputs."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from keyword_analysis.scoring import (
    HIGH_PRIORITY_THRESHOLD,
    MEDIUM_PRIORITY_THRESHOLD,
    load_observation_frame,
    score_keywords,
)


def extract_korea_follow_on_modifier(keyword: str) -> str:
    normalized = str(keyword).lower().strip()
    for pattern in (
        "korea esim",
        "south korea esim",
        "esim for korea",
        "best esim for korea",
        "best esim for south korea",
    ):
        if normalized == pattern:
            return "root" if pattern in ("korea esim", "esim for korea", "south korea esim") else "best"
        if normalized.startswith(pattern + " "):
            return normalized.removeprefix(pattern).strip()
    return "variant"


def build_korea_marketing_targets(frame: pd.DataFrame, scored_keywords: pd.DataFrame) -> pd.DataFrame:
    if frame.empty or scored_keywords.empty:
        return pd.DataFrame()

    korea_frame = frame[
        frame["seed_keyword"].str.contains("korea", case=False, na=False)
        | frame["canonical_keyword"].str.contains("korea", case=False, na=False)
    ].copy()
    if korea_frame.empty:
        return pd.DataFrame()

    origins = (
        korea_frame.groupby("canonical_keyword", dropna=False)
        .agg(
            origin_seeds=("seed_keyword", lambda values: ",".join(sorted(set(values)))),
            observed_signals=("signal_type", lambda values: ",".join(sorted(set(values)))),
            raw_variants=("raw_text", lambda values: " | ".join(sorted(set(map(str, values)))[:5])),
        )
        .reset_index()
    )

    targets = scored_keywords.merge(origins, how="inner", on="canonical_keyword")
    targets["marketing_priority"] = targets["priority_score"].apply(
        lambda score: "high" if score >= HIGH_PRIORITY_THRESHOLD else "medium" if score >= MEDIUM_PRIORITY_THRESHOLD else "test"
    )
    targets["follow_on_modifier"] = targets["canonical_keyword"].apply(extract_korea_follow_on_modifier)
    targets["target_reason"] = (
        "Observed from Korea-focused root queries and supported by Google-native signals"
    )
    return targets.sort_values("priority_score", ascending=False)


def build_cluster_summary(scored_keywords: pd.DataFrame) -> pd.DataFrame:
    if scored_keywords.empty:
        return pd.DataFrame()

    summary = (
        scored_keywords.groupby(["keyword_family", "keyword_bucket"], dropna=False)
        .agg(
            keyword_count=("canonical_keyword", "count"),
            avg_priority_score=("priority_score", "mean"),
        )
        .reset_index()
        .sort_values("avg_priority_score", ascending=False)
    )
    return summary


def export_reports(
    output_dir: Path = Path("outputs/reports"),
    database_path: Path = Path("outputs/keyword_analysis.sqlite3"),
) -> dict[str, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    frame = load_observation_frame(database_path)
    scored = score_keywords(frame)
    summary = build_cluster_summary(scored)
    korea_targets = build_korea_marketing_targets(frame, scored)

    keyword_path = output_dir / "ranked_keywords.csv"
    summary_path = output_dir / "cluster_summary.csv"
    korea_target_path = output_dir / "korea_marketing_targets.csv"
    markdown_path = output_dir / "report_summary.md"

    scored.to_csv(keyword_path, index=False)
    summary.to_csv(summary_path, index=False)
    korea_targets.to_csv(korea_target_path, index=False)
    markdown_path.write_text(build_markdown_summary(scored, summary, korea_targets), encoding="utf-8")

    return {
        "ranked_keywords": keyword_path,
        "cluster_summary": summary_path,
        "korea_marketing_targets": korea_target_path,
        "report_summary": markdown_path,
    }


def build_markdown_summary(
    scored: pd.DataFrame,
    summary: pd.DataFrame,
    korea_targets: pd.DataFrame,
) -> str:
    lines = ["# Keyword Report", "", "## Top Keywords"]
    if scored.empty:
        lines.append("- No observations available.")
    else:
        for row in scored.head(10).itertuples():
            lines.append(
                f"- `{row.canonical_keyword}` | score={row.priority_score} | "
                f"bucket={row.keyword_bucket} | evidence={row.evidence_signals}"
            )

    lines.extend(["", "## Cluster Summary"])
    if summary.empty:
        lines.append("- No cluster summary available.")
    else:
        for row in summary.head(10).itertuples():
            lines.append(
                f"- family={row.keyword_family} | bucket={row.keyword_bucket} | "
                f"keywords={row.keyword_count} | avg_score={round(row.avg_priority_score, 2)}"
            )

    lines.extend(["", "## Korea Marketing Targets"])
    if korea_targets.empty:
        lines.append("- No Korea-focused targets available.")
    else:
        for row in korea_targets.head(10).itertuples():
            lines.append(
                f"- `{row.canonical_keyword}` | priority={row.marketing_priority} | "
                f"score={row.priority_score} | modifier={row.follow_on_modifier} | seeds={row.origin_seeds}"
            )

    lines.extend(
        [
            "",
            "## Interpretation Notes",
            "- Scores are signal-based priorities, not true search volume.",
            "- Higher confidence comes from repeated presence across multiple Google-native signals.",
            "- Korea marketing targets are keywords discovered from `korea esim`-family roots and should be treated as SEO/landing-page targets, not guaranteed-volume terms.",
        ]
    )
    return "\n".join(lines) + "\n"
