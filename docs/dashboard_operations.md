# Dashboard Operations

## Upstream Dependencies

- `outputs/reports_korea_focus/ranked_keywords.csv`
- `outputs/reports_korea_focus/cluster_summary.csv`
- `outputs/reports_korea_focus/korea_marketing_targets.csv`
- optional snapshot CSV files for delta comparison

## Refresh Workflow

1. Run Korea-focused seed collection.
2. Normalize and classify newly collected raw keywords.
3. Rebuild report outputs with `export_reports(...)`.
4. Save the current `ranked_keywords.csv` as a dated snapshot if you want delta comparison.
5. Launch or refresh the Streamlit dashboard.

## Suggested Snapshot Convention

- Store ranked snapshots under a dated path such as:
  - `outputs/snapshots/2026-03-16_ranked_keywords.csv`
- Compare the most recent pair in the dashboard sidebar by setting:
  - `Previous snapshot CSV`
  - `Current snapshot CSV`

## Run Instructions

- Launch dashboard:
  - `python -m streamlit run src/keyword_analysis/dashboard.py`
- Default report directory:
  - `outputs/reports_korea_focus`
- If report files live elsewhere, change the report directory in the sidebar.
- Default database path for refresh:
  - `outputs/keyword_analysis.sqlite3`

## In-Dashboard Actions

- `Refresh Market Signals`
  - Collects the current Korea-focused seed set again
  - Rebuilds normalized keywords and intent assignments
  - Re-exports `ranked_keywords.csv`, `cluster_summary.csv`, `korea_marketing_targets.csv`, and `report_summary.md`
- `Help`
  - Opens an in-app explanation of score rules, bucket logic, and the marketing meaning of each dashboard section

## Help Synchronization Rule

- Dashboard help content is not treated as a freeform static document.
- Score explanations and section descriptions must be generated from the code metadata under `src/keyword_analysis/`.
- When scoring logic or dashboard sections change, the matching tests must also pass so help text cannot silently drift from the live application.

## Troubleshooting

### Missing Report Files

- Symptom:
  - dashboard loads with empty tables
- Check:
  - whether `export_reports(...)` ran successfully
  - whether the report directory points to the expected output path

### Missing Snapshot Delta

- Symptom:
  - snapshot tabs show no data
- Check:
  - whether both previous and current snapshot CSV paths are set
  - whether the files contain `canonical_keyword`, `priority_score`, and `keyword_bucket`

### Blocked Google Signals

- Symptom:
  - certain signals disappear or the related-search panel seems stale
- Check:
  - `outputs/reports/collection_failures.log`
  - whether Google anti-bot protection blocked SERP collection
- Action:
  - treat missing signals as a collection issue, not as immediate keyword disappearance

## MVP Limits

- MVP relies on precomputed CSV outputs rather than live queries.
- Snapshot comparison depends on manually provided or saved snapshot files.
- Noise heuristics are simple string rules and should not be treated as perfect classification.
- The UI is optimized for quick local decision-making, not for multi-user workflow management.

## Version 2 Ideas

- Historical trend charts per keyword or modifier
- Saved filter presets for SEO, paid search, and landing-page planning
- Manual review state tracking such as `approved`, `ignore`, `needs content`
- Better noise heuristics and brand-term handling
- Snapshot registry automation and auto-discovery of the latest file pair
