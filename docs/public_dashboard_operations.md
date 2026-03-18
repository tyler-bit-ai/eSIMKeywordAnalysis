# Public Dashboard Operations

## Purpose

- Document the repeatable operating procedure for publishing the public dashboard.
- Separate publish-safe artifacts from local-only operational artifacts.
- Define what to do when collection, export, or deployment fails.

## Operating Model

- Local PC:
  - runs collection and analysis
  - refreshes reports
  - generates the publish-safe JSON bundle
- GitHub Pages:
  - serves the static dashboard only
  - does not run collection or Python logic at request time

## Standard Publishing Sequence

1. Refresh or validate the local source data.
2. Rebuild report outputs.
3. Generate the public dashboard JSON bundle.
4. Validate the static site against the generated JSON.
5. Merge into `main` or trigger the Pages workflow.
6. Confirm the published page is serving the latest artifact.

## Repeatable Runbook

### 1. Refresh Local Reports

- If fresh collection is needed:
  - run the local collection and reporting workflow
- If reports are already current:
  - verify that `outputs/reports_korea_focus/` contains the latest CSV files

### 2. Generate Public Data

- Generate the public JSON bundle:
  - `python -c "from pathlib import Path; from keyword_analysis.pipeline import export_korea_public_dashboard; export_korea_public_dashboard(output_dir=Path('site/data'))"`
- Expected output:
  - `site/data/dashboard_data.json`

### 3. Validate Before Publish

- Start a local static HTTP server from the repository root.
- Open `site/` through the server.
- Confirm:
  - the page loads without JavaScript errors
  - `Published dashboard data loaded.` appears
  - KPI cards render
  - target table rows render
  - modifier, seed, signal, and snapshot sections render or show empty-state messages

### 4. Publish

- Preferred path:
  - push reviewed changes to `main`
  - let GitHub Actions deploy GitHub Pages
- Do not manually upload ad hoc files to Pages outside the repository workflow.

## Publish Cadence

- Recommended default cadence:
  - weekly publish after a verified local refresh
- Faster cadence is acceptable only if:
  - collection quality is stable
  - the published change is intentional
- The public dashboard should be described as a latest published snapshot, not as real-time data.

## Publish-Safe Artifacts

These are safe to publish as part of the Pages artifact:

- `site/index.html`
- `site/styles.css`
- `site/app.js`
- `site/data/dashboard_data.json`

## Non-Public Artifacts

These should remain local-only unless there is an explicit review decision:

- `outputs/*.sqlite3`
- `outputs/reports/collection_failures.log`
- arbitrary local snapshot file paths
- local database path settings
- internal troubleshooting notes

## Key Risks And Responses

### Collection Failure

- Symptom:
  - refreshed reports look incomplete or stale
- Check:
  - `outputs/reports/collection_failures.log`
- Response:
  - do not publish a broken refresh by default
  - keep the previous published artifact until collection quality is acceptable

### Missing Or Empty Reports

- Symptom:
  - generated `dashboard_data.json` contains empty arrays across major sections
- Check:
  - whether `ranked_keywords.csv`, `cluster_summary.csv`, and `korea_marketing_targets.csv` exist under `outputs/reports_korea_focus/`
- Response:
  - stop the publish attempt
  - rebuild reports locally before retrying

### Wrong Base Path Or Missing Data File

- Symptom:
  - static page loads but shows fetch errors or empty content
- Check:
  - whether the Pages artifact includes `site/data/dashboard_data.json`
  - whether the published page is serving the `site/` artifact root
- Response:
  - rerun the Pages workflow
  - confirm repository Pages settings still point to `GitHub Actions`

### Stale Data

- Symptom:
  - published view does not match the latest local analysis
- Check:
  - `generated_at` in `dashboard_data.json`
  - the commit SHA used by the most recent Pages deployment
- Response:
  - regenerate the JSON bundle
  - redeploy from the intended `main` commit

## Fallback And Rollback

- Preferred fallback:
  - keep the previously published Pages artifact rather than publishing uncertain data
- If a bad deployment reaches Pages:
  - revert the source commit on `main` or redeploy a known-good commit
- Do not patch the live Pages output manually unless the repository is in emergency fallback mode.

## Operator Notes

- The public dashboard is a communication layer, not the source of truth.
- The source of truth remains the local collection, local reports, and reviewed source code in `main`.
