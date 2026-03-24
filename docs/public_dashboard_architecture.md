# Public Dashboard Architecture

## Goal

- Keep the existing Streamlit dashboard as the local operator console.
- Add a separate read-only dashboard for GitHub Pages so other people can view published results without running Python or Streamlit.
- Reuse existing report-generation and dashboard data-shaping logic where possible.

## Current Facts

### Local Dashboard Runtime

- `src/keyword_analysis/dashboard.py` is a Streamlit application.
- The dashboard loads report files from `outputs/reports_korea_focus/` by default.
- The dashboard can trigger `refresh_korea_dashboard_dataset(...)` from `src/keyword_analysis/pipeline.py`.
- The refresh path collects signals, rebuilds metadata, and exports reports.

### Existing Report Sources

- `src/keyword_analysis/reporting.py` writes:
  - `ranked_keywords.csv`
  - `cluster_summary.csv`
  - `korea_marketing_targets.csv`
  - `report_summary.md`
- `src/keyword_analysis/dashboard_data.py` builds:
  - KPI aggregates
  - modifier summary
  - seed lineage summary
  - signal summary
  - snapshot change tables

## Dashboard Role Split

### Local Streamlit Dashboard

- Primary audience:
  - project operator on a personal PC
- Responsibilities:
  - run refresh pipeline
  - inspect local file paths
  - compare snapshots from arbitrary local CSV paths
  - troubleshoot data collection issues
- Allowed dependencies:
  - Python runtime
  - Streamlit
  - local filesystem
  - SQLite database

### Public GitHub Pages Dashboard

- Primary audience:
  - external viewers who only need to read published results
- Responsibilities:
  - render prebuilt data only
  - show published KPIs, tables, summaries, and snapshot deltas
  - provide lightweight filters and sorting for exploration
- Explicit non-goals:
  - do not run collection
  - do not run refresh pipeline
  - do not expose local filesystem inputs
  - do not depend on Python server execution
  - do not expose SQLite or internal logs directly

## Excluded From GitHub Pages

The following local-only features must not be carried into the public dashboard:

- `Refresh Market Signals` button
  - reason: it executes collection and reporting code, which GitHub Pages cannot host
- `Report directory` input
  - reason: GitHub Pages has no access to the operator's local filesystem
- `Database path` input
  - reason: SQLite path selection is a local operational concern
- free-form `Previous snapshot CSV` and `Current snapshot CSV` path inputs
  - reason: public viewers should consume published snapshot data, not arbitrary local files
- collector failure log references such as `outputs/reports/collection_failures.log`
  - reason: this is an internal operational artifact

## Recommended Publish Flow

1. Run collection and analysis locally.
2. Export the standard report CSV and Markdown files.
3. Build a public data bundle from the report outputs.
4. Build or copy the static site assets.
5. Publish the static site and public data bundle to GitHub Pages.

## Public Data Contract

### File Location

- Recommended output directory:
  - `outputs/published_dashboard/`
- Recommended primary data file:
  - `outputs/published_dashboard/dashboard_data.json`
- Recommended multi-dataset manifest file:
  - `outputs/published_dashboard/dashboard_manifest.json`

### Top-Level Schema

Single-dataset mode reads one JSON document with this top-level structure:

```json
{
  "generated_at": "2026-03-18T10:00:00Z",
  "source_report_dir": "outputs/reports_korea_focus",
  "dataset_version": "v1",
  "kpis": {
    "high_priority_targets": 0,
    "rising_keywords": 0,
    "new_keywords": 0,
    "manual_review_terms": 0,
    "tracked_targets": 0
  },
  "target_table": [],
  "modifier_summary": [],
  "seed_lineage": [],
  "signal_summary": [],
  "snapshot_changes": {
    "new_keywords": [],
    "disappeared_keywords": [],
    "rank_changes": [],
    "bucket_changes": []
  },
  "metadata": {
    "has_previous_snapshot": false,
    "has_current_snapshot": false,
    "notes": []
  }
}
```

### Multi-Dataset Manifest

When multiple published datasets must be retained side by side, the static site may read a manifest first and then lazy-load the selected dataset JSON.

```json
{
  "generated_at": "2026-03-24T00:00:00Z",
  "default_dataset_id": "current",
  "datasets": [
    {
      "dataset_id": "current",
      "label": "Current Crawl",
      "path": "current.json",
      "generated_at": "2026-03-24T00:00:00Z",
      "source_report_dir": "outputs/reports_korea_focus",
      "dataset_version": "v1",
      "has_previous_snapshot": false,
      "has_current_snapshot": false
    }
  ]
}
```

The static site should:

- try `dashboard_manifest.json` first
- populate a dataset selector from `datasets`
- fetch only the selected dataset JSON
- fall back to `dashboard_data.json` when the manifest is missing

## Field Definitions

### Top-Level Fields

| Field | Type | Required | Source | Notes |
| --- | --- | --- | --- | --- |
| `generated_at` | string | yes | export step | ISO 8601 UTC timestamp |
| `source_report_dir` | string | yes | export step input | path used to load CSV reports |
| `dataset_version` | string | yes | export step constant | schema version for future compatibility |
| `kpis` | object | yes | `build_kpi_frame(...)` output | single published KPI object |
| `target_table` | array<object> | yes | `korea_marketing_targets.csv` plus `dashboard_data.py` enrichments | primary comparison table |
| `modifier_summary` | array<object> | yes | `build_modifier_summary(...)` | group summary for modifier view |
| `seed_lineage` | array<object> | yes | `build_seed_lineage_summary(...)` | seed performance summary |
| `signal_summary` | array<object> | yes | `build_signal_summary(...)` | signal coverage summary |
| `snapshot_changes` | object | yes | `build_snapshot_changes(...)` | published delta tables |
| `metadata` | object | yes | export step | publication and snapshot availability metadata |

### KPI Object

| Field | Type |
| --- | --- |
| `high_priority_targets` | integer |
| `rising_keywords` | integer |
| `new_keywords` | integer |
| `manual_review_terms` | integer |
| `tracked_targets` | integer |

### Target Table Row

| Field | Type | Source |
| --- | --- | --- |
| `canonical_keyword` | string | `korea_marketing_targets.csv` |
| `follow_on_modifier` | string | `korea_marketing_targets.csv` |
| `marketing_priority` | string | `korea_marketing_targets.csv` |
| `priority_score` | number | `korea_marketing_targets.csv` |
| `keyword_bucket` | string | `korea_marketing_targets.csv` |
| `observed_signals` | array<string> | split from `observed_signals` |
| `origin_seeds` | array<string> | split from `origin_seeds` |
| `raw_variants` | array<string> | split from `raw_variants` |
| `is_noisy` | boolean | `dashboard_data.py` enrichment |
| `origin_seed_count` | integer | `dashboard_data.py` enrichment |
| `target_reason` | string | `korea_marketing_targets.csv` |

### Modifier Summary Row

| Field | Type | Source |
| --- | --- | --- |
| `follow_on_modifier` | string | `build_modifier_summary(...)` |
| `keyword_count` | integer | `build_modifier_summary(...)` |
| `avg_priority_score` | number | `build_modifier_summary(...)` |
| `top_keywords` | string | `build_modifier_summary(...)` |

### Seed Lineage Row

| Field | Type | Source |
| --- | --- | --- |
| `origin_seed` | string | `build_seed_lineage_summary(...)` |
| `keyword_count` | integer | `build_seed_lineage_summary(...)` |
| `avg_priority_score` | number | `build_seed_lineage_summary(...)` |
| `modifiers` | string | `build_seed_lineage_summary(...)` |

### Signal Summary Row

| Field | Type | Source |
| --- | --- | --- |
| `signal` | string | `build_signal_summary(...)` |
| `keyword_count` | integer | `build_signal_summary(...)` |
| `avg_priority_score` | number | `build_signal_summary(...)` |

### Snapshot Changes

The `snapshot_changes` object must contain all four keys even when there is no snapshot data:

- `new_keywords`
- `disappeared_keywords`
- `rank_changes`
- `bucket_changes`

Each key maps to an array of row objects derived from `compare_snapshots(...)`.

## Null And Empty Rules

- Missing collections must be serialized as empty arrays, not `null`.
- Missing object sections must be serialized as empty objects only when the schema explicitly allows it.
- For this contract, `kpis` must always exist with numeric defaults.
- String list fields stored as comma-separated or pipe-separated values in CSV must be published as arrays.
- Empty strings in list-like fields must become `[]`.
- Numeric fields should remain numeric in JSON, not stringified.
- `generated_at` must always be present.

## Mapping From Existing Data Sources

| Public JSON Field | Existing Source |
| --- | --- |
| `kpis.high_priority_targets` | `build_kpi_frame(...).high_priority_targets` |
| `kpis.rising_keywords` | `build_kpi_frame(...).rising_keywords` |
| `kpis.manual_review_terms` | `build_kpi_frame(...).manual_review_terms` |
| `kpis.tracked_targets` | `build_kpi_frame(...).tracked_targets` |
| `kpis.new_keywords` | `len(snapshot_changes['new_keywords'])` |
| `target_table` | `DashboardDataset.korea_marketing_targets` after public serialization |
| `modifier_summary` | `DashboardDataset.modifier_summary` |
| `seed_lineage` | `DashboardDataset.seed_lineage` |
| `signal_summary` | `DashboardDataset.signal_summary` |
| `snapshot_changes.*` | `DashboardDataset.snapshot_changes` |

## Reuse Guidance

- Reuse `load_dashboard_dataset(...)` as the main assembly point when possible.
- Reuse `build_kpi_frame(...)`, `build_modifier_summary(...)`, `build_seed_lineage_summary(...)`, and `build_signal_summary(...)` instead of recomputing published summaries in a separate code path.
- Keep UI-only concerns inside Streamlit and later inside the static frontend.
- Keep data shaping and serialization in Python export code.

## Implementation Boundary

- Python remains responsible for collection, scoring, report export, and public JSON generation.
- The public dashboard frontend remains responsible only for rendering, filter state, and client-side sorting.
- The public site consumes published files only and does not import Python modules at runtime.
- SQLite persistence keeps `collection_runs` history per execution and should deduplicate identical `observations` payloads so repeated crawls do not inflate reporting outputs.
