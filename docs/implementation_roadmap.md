# Implementation Roadmap

## Phase 1: Research Framing And Signal Validation

- Objectives:
  - lock project scope to Google-only public signals
  - confirm U.S. locale controls and metadata requirements
- Outputs:
  - research specification
  - collection profile defaults
  - signal usage guardrails
- Dependencies:
  - none
- Success Criteria:
  - scope excludes non-Google sources and internal logs
  - metadata schema is defined for every observation

## Phase 2: Seed Keyword Design And Collection Prototype

- Objectives:
  - establish seed taxonomy
  - build first-pass collectors for autocomplete, related searches, and Trends
- Outputs:
  - seed library
  - Playwright collectors
  - SQLite raw observation storage
- Dependencies:
  - Phase 1
- Success Criteria:
  - small seed set can be collected repeatedly with `hl=en` and `gl=us`
  - raw outputs are stored with run metadata

## Phase 3: Normalization And Intent Clustering

- Objectives:
  - canonicalize keyword variants
  - assign transparent rule-based intent clusters
- Outputs:
  - normalization rules
  - intent classifier
  - normalized tables and mappings
- Dependencies:
  - Phase 2
- Success Criteria:
  - `esim`, `eSIM`, and destination variants are grouped consistently
  - cluster assignments can be explained from deterministic rules

## Phase 4: Scoring And Reporting

- Objectives:
  - rank discovered keywords using public-signal evidence
  - produce report exports for review
- Outputs:
  - scoring model
  - ranked keyword tables
  - summary reports
- Dependencies:
  - Phase 3
- Success Criteria:
  - reports distinguish stable, rising, and niche terms
  - reports show evidence signals instead of claiming true search volume

## Phase 5: Monitoring And Maintenance

- Objectives:
  - detect changes over time
  - maintain validation and risk controls
- Outputs:
  - snapshot comparison logic
  - validation playbook
  - operational cadence
- Dependencies:
  - Phase 4
- Success Criteria:
  - daily or weekly snapshots can be compared for keyword changes
  - new/disappeared keywords and bucket shifts are reviewable

## Recommended MVP Scope

- Focus on 10 to 20 seed keywords centered on generic travel eSIM and Korea-specific travel eSIM.
- Collect autocomplete daily and related searches plus Trends weekly.
- Use rule-based normalization only.
- Export ranked keyword CSV plus one Markdown summary after each weekly batch.
- Keep SERP context optional and sample only a few top results per keyword.

## Recommended Version 2 Scope

- Expand beyond Korea into a broader destination library driven by discovered patterns.
- Add stronger scheduling, snapshot retention, and anomaly alerts.
- Improve network/carrier compatibility parsing and duration extraction.
- Add confidence calibration based on multi-week persistence and cross-signal overlap.
- Add a richer dashboard with historical keyword trend lines, saved views, and manual review workflow states.

## Dashboard MVP

- Streamlit-based local dashboard
- Korea marketing target comparison table
- Modifier summary, root-seed lineage, and signal summary
- Snapshot delta tabs driven by saved ranked-keyword snapshots
- `Target Now`, `Watch`, and `Review Manually` action views

## Dashboard Version 2

- Historical trend charting per keyword and modifier
- Automatic snapshot discovery and date switching
- Reviewer notes and action status tracking
- Stronger export workflows for landing-page and content-brief pipelines
