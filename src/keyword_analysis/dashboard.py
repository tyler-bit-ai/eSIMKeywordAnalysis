"""Streamlit dashboard for Korea eSIM keyword comparison."""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import streamlit as st

PROJECT_SRC = Path(__file__).resolve().parents[1]
if str(PROJECT_SRC) not in sys.path:
    sys.path.insert(0, str(PROJECT_SRC))

from keyword_analysis.dashboard_help import build_help_payload, get_section_spec
from keyword_analysis.dashboard_data import DashboardDataset, load_dashboard_dataset
from keyword_analysis.pipeline import DEFAULT_DATABASE_PATH, PipelineError, refresh_korea_dashboard_dataset


DEFAULT_REPORT_DIR = Path("outputs/reports_korea_focus")
DEFAULT_COLLECTION_EXPORT_DIR = Path("outputs/reports")


def main() -> None:
    st.set_page_config(
        page_title="Korea eSIM Keyword Dashboard",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    title_col, action_col = st.columns([4, 2])
    with title_col:
        st.title("Korea eSIM Keyword Dashboard")
        st.caption("Compare Korea-focused Google keyword targets, modifiers, seed lineage, and snapshot changes.")
    with action_col:
        help_clicked = st.button("Help", use_container_width=True)
        refresh_clicked = st.button("Refresh Market Signals", type="primary", use_container_width=True)

    report_dir = st.sidebar.text_input("Report directory", str(DEFAULT_REPORT_DIR))
    database_path = st.sidebar.text_input("Database path", str(DEFAULT_DATABASE_PATH))
    previous_snapshot = st.sidebar.text_input("Previous snapshot CSV", "")
    current_snapshot = st.sidebar.text_input("Current snapshot CSV", "")

    if help_clicked:
        render_help_dialog()

    if refresh_clicked:
        run_refresh_pipeline(Path(database_path), Path(report_dir), DEFAULT_COLLECTION_EXPORT_DIR)
        st.rerun()

    dataset = load_dashboard_dataset(
        report_dir=Path(report_dir),
        previous_snapshot=Path(previous_snapshot) if previous_snapshot else None,
        current_snapshot=Path(current_snapshot) if current_snapshot else None,
    )

    targets = dataset.korea_marketing_targets.copy()
    filtered_targets = apply_filters(targets)

    render_kpis(dataset, filtered_targets)
    render_action_views(filtered_targets)
    render_export_candidates(filtered_targets)
    render_main_table(filtered_targets)

    left_col, right_col = st.columns([1, 1])
    with left_col:
        render_modifier_summary(dataset, filtered_targets)
        render_signal_summary(dataset)
    with right_col:
        render_seed_lineage(dataset)
        render_snapshot_changes(dataset)


@st.dialog("Dashboard Help", width="large")
def render_help_dialog() -> None:
    payload = build_help_payload()
    score_rule = payload["score_rule"]
    sections = payload["sections"]

    st.subheader(score_rule.title)
    st.write(score_rule.summary)
    st.markdown("**Score formula**")
    for step in score_rule.formula_steps:
        st.write(f"- {step}")

    st.markdown("**Signal weights**")
    signal_frame = pd.DataFrame(
        [{"signal": signal, "weight": weight} for signal, weight in score_rule.signal_weights.items()]
    )
    st.dataframe(signal_frame, use_container_width=True, hide_index=True)

    st.markdown("**Marketing priority**")
    for rule in score_rule.marketing_priority_rules:
        st.write(f"- {rule}")

    st.markdown("**Keyword buckets**")
    for rule in score_rule.bucket_rules:
        st.write(f"- {rule}")

    st.subheader("Section Guide")
    for section in sections:
        with st.expander(section.title, expanded=False):
            st.write(f"**What it means:** {section.business_meaning}")
            st.write(f"**How to use it:** {section.how_to_use}")
            st.write(f"**What drives it:** {section.scoring_note}")


def run_refresh_pipeline(database_path: Path, report_dir: Path, collection_export_dir: Path) -> None:
    try:
        with st.status("Refreshing current market dataset...", expanded=True) as status:
            st.write("Collecting fresh Korea-focused Google signals.")
            st.write("Rebuilding normalized keywords and intent assignments.")
            st.write("Exporting refreshed dashboard reports.")
            artifacts = refresh_korea_dashboard_dataset(
                database_path=database_path,
                report_dir=report_dir,
                collection_export_dir=collection_export_dir,
            )
            status.update(label="Refresh completed", state="complete")
        st.success(
            "Dataset refresh completed. "
            f"Normalized keywords: {artifacts.normalized_keyword_count}, "
            f"intent assignments: {artifacts.intent_assignment_count}"
        )
        st.caption(
            f"Updated reports: {artifacts.ranked_keywords}, {artifacts.cluster_summary}, "
            f"{artifacts.korea_marketing_targets}"
        )
        if artifacts.failure_log_path.exists():
            st.warning(f"Collector warnings were logged to {artifacts.failure_log_path}.")
    except PipelineError as error:
        st.error(f"Dataset refresh failed: {error}")
        failure_log = collection_export_dir / "collection_failures.log"
        if failure_log.exists():
            st.caption(f"Check collector failures: {failure_log}")


def apply_filters(targets: pd.DataFrame) -> pd.DataFrame:
    st.sidebar.header("Filters")
    if targets.empty:
        return targets

    seeds = sorted(extract_unique_items(targets["origin_seeds"]))
    modifiers = sorted(targets["follow_on_modifier"].dropna().astype(str).unique().tolist())
    buckets = sorted(targets["keyword_bucket"].dropna().astype(str).unique().tolist())
    priorities = sorted(targets["marketing_priority"].dropna().astype(str).unique().tolist())
    signals = sorted(extract_unique_items(targets["observed_signals"]))

    selected_seeds = st.sidebar.multiselect("Origin seed", seeds)
    selected_modifiers = st.sidebar.multiselect("Modifier", modifiers)
    selected_buckets = st.sidebar.multiselect("Bucket", buckets)
    selected_priorities = st.sidebar.multiselect("Marketing priority", priorities)
    selected_signals = st.sidebar.multiselect("Observed signal", signals)
    hide_noisy = st.sidebar.checkbox("Hide noisy/manual-review terms", value=False)

    frame = targets.copy()
    if selected_seeds:
        frame = frame[frame["origin_seeds"].fillna("").apply(lambda value: contains_any(value, selected_seeds))]
    if selected_modifiers:
        frame = frame[frame["follow_on_modifier"].isin(selected_modifiers)]
    if selected_buckets:
        frame = frame[frame["keyword_bucket"].isin(selected_buckets)]
    if selected_priorities:
        frame = frame[frame["marketing_priority"].isin(selected_priorities)]
    if selected_signals:
        frame = frame[frame["observed_signals"].fillna("").apply(lambda value: contains_any(value, selected_signals))]
    if hide_noisy and "is_noisy" in frame.columns:
        frame = frame[~frame["is_noisy"]]

    return frame.sort_values("priority_score", ascending=False)


def render_kpis(dataset: DashboardDataset, filtered_targets: pd.DataFrame) -> None:
    st.subheader(get_section_spec("kpi").title)
    kpi_source = dataset.kpi_frame.iloc[0].to_dict() if not dataset.kpi_frame.empty else {}
    new_keywords = len(dataset.snapshot_changes.get("new_keywords", pd.DataFrame()))

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("High Priority Targets", kpi_source.get("high_priority_targets", 0))
    col2.metric("Rising Keywords", kpi_source.get("rising_keywords", 0))
    col3.metric("New Since Last Snapshot", new_keywords)
    col4.metric("Manual Review Terms", kpi_source.get("manual_review_terms", 0))
    st.caption(f"Visible targets after filters: {len(filtered_targets)}")


def render_main_table(filtered_targets: pd.DataFrame) -> None:
    st.subheader(get_section_spec("target_comparison").title)
    if filtered_targets.empty:
        st.info("No targets available for the current filter set.")
        return

    display_columns = [
        "canonical_keyword",
        "follow_on_modifier",
        "marketing_priority",
        "priority_score",
        "keyword_bucket",
        "observed_signals",
        "origin_seeds",
        "raw_variants",
    ]
    st.dataframe(
        filtered_targets[display_columns],
        use_container_width=True,
        hide_index=True,
    )


def render_action_views(filtered_targets: pd.DataFrame) -> None:
    st.subheader(get_section_spec("action_views").title)
    tabs = st.tabs(["Target Now", "Watch", "Review Manually"])
    target_now = filtered_targets[
        (filtered_targets["marketing_priority"] == "high")
        & (~filtered_targets.get("is_noisy", pd.Series(False, index=filtered_targets.index)))
    ]
    watch = filtered_targets[
        (filtered_targets["marketing_priority"].isin(["high", "medium"]))
        & (filtered_targets["keyword_bucket"].isin(["rising", "niche_long_tail"]))
    ]
    review = filtered_targets[filtered_targets.get("is_noisy", pd.Series(False, index=filtered_targets.index))]

    for tab, frame in zip(tabs, [target_now, watch, review], strict=True):
        with tab:
            if frame.empty:
                st.info("No keywords available.")
            else:
                st.dataframe(
                    frame[
                        [
                            "canonical_keyword",
                            "follow_on_modifier",
                            "marketing_priority",
                            "priority_score",
                            "observed_signals",
                            "origin_seeds",
                        ]
                    ],
                    use_container_width=True,
                    hide_index=True,
                )


def render_export_candidates(filtered_targets: pd.DataFrame) -> None:
    st.subheader(get_section_spec("marketing_exports").title)
    if filtered_targets.empty:
        st.info("No export candidates available.")
        return

    landing_page_candidates = filtered_targets[
        filtered_targets["follow_on_modifier"].isin(
            ["root", "best", "unlimited data", "with phone number", "tourist", "data only"]
        )
    ]
    content_brief_candidates = filtered_targets[
        filtered_targets["follow_on_modifier"].isin(["best", "tourist", "with phone number", "data only"])
    ]

    col1, col2 = st.columns(2)
    with col1:
        st.caption("Landing Page Candidates")
        st.dataframe(
            landing_page_candidates[
                ["canonical_keyword", "follow_on_modifier", "priority_score", "origin_seeds"]
            ].head(15),
            use_container_width=True,
            hide_index=True,
        )
    with col2:
        st.caption("Content Brief Candidates")
        st.dataframe(
            content_brief_candidates[
                ["canonical_keyword", "follow_on_modifier", "priority_score", "origin_seeds"]
            ].head(15),
            use_container_width=True,
            hide_index=True,
        )


def render_modifier_summary(dataset: DashboardDataset, filtered_targets: pd.DataFrame) -> None:
    st.subheader(get_section_spec("modifier_comparison").title)
    if filtered_targets.empty:
        st.info("No modifier summary available.")
        return

    summary = (
        filtered_targets.groupby("follow_on_modifier", dropna=False)
        .agg(
            keyword_count=("canonical_keyword", "count"),
            avg_priority_score=("priority_score", "mean"),
        )
        .reset_index()
        .sort_values("avg_priority_score", ascending=False)
    )
    summary["avg_priority_score"] = summary["avg_priority_score"].round(2)
    st.dataframe(summary, use_container_width=True, hide_index=True)


def render_signal_summary(dataset: DashboardDataset) -> None:
    st.subheader(get_section_spec("signal_summary").title)
    if dataset.signal_summary.empty:
        st.info("No signal summary available.")
        return
    st.dataframe(dataset.signal_summary, use_container_width=True, hide_index=True)


def render_seed_lineage(dataset: DashboardDataset) -> None:
    st.subheader(get_section_spec("seed_lineage").title)
    if dataset.seed_lineage.empty:
        st.info("No seed lineage summary available.")
        return
    st.dataframe(dataset.seed_lineage, use_container_width=True, hide_index=True)


def render_snapshot_changes(dataset: DashboardDataset) -> None:
    st.subheader(get_section_spec("snapshot_delta").title)
    tabs = st.tabs(["New", "Disappeared", "Rank Changes", "Bucket Changes"])
    names = ["new_keywords", "disappeared_keywords", "rank_changes", "bucket_changes"]
    for tab, name in zip(tabs, names, strict=True):
        with tab:
            frame = dataset.snapshot_changes.get(name, pd.DataFrame())
            if frame.empty:
                st.info("No data available.")
            else:
                st.dataframe(frame, use_container_width=True, hide_index=True)


def extract_unique_items(series: pd.Series) -> set[str]:
    values: set[str] = set()
    for raw in series.dropna().astype(str):
        for part in raw.split(","):
            cleaned = part.strip()
            if cleaned:
                values.add(cleaned)
    return values


def contains_any(raw_value: str, expected_values: list[str]) -> bool:
    values = {item.strip() for item in str(raw_value).split(",") if item.strip()}
    return any(expected in values for expected in expected_values)


if __name__ == "__main__":
    main()
