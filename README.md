# KeywordAnalysis

Python workflow for estimating how U.S. users search Google for eSIM topics using only public Google signals.

## Scope

- Google Search only
- Public signals only
- U.S. English assumptions: `hl=en`, `gl=us`
- No Google internal query logs
- Focus on eSIM, travel eSIM, and destination-specific eSIM demand patterns

## Initial Layout

- `docs/`: research framing, roadmap, and signal notes
- `src/keyword_analysis/`: collection and analysis package
- `site/`: GitHub Pages static dashboard assets
- `config/`: collection profiles and runtime settings
- `outputs/`: generated exports and reports

## Planned Workflow

1. Define seed keywords.
2. Collect Google autocomplete, related searches, and Trends data.
3. Normalize discovered keywords and cluster intents.
4. Score keywords and monitor changes over time.

## Collection Notes

- Seed exports now aggregate observations from every collector run triggered for the seed, rather than only the autocomplete run.
- Autocomplete collection can fan out into modifier, alphabet, and numeric expansions using `config/collection_profiles.yaml` under `autocomplete_expansion`.
- `related_search` remains an optional, best-effort Google SERP signal. Selector misses or Google anti-bot responses are recorded as failed runs instead of leaving a `started` status behind.
- Deterministic pytest coverage is available for export aggregation, query expansion, config defaults, and related-search failure handling.

## Dashboard

- Install dependencies from `pyproject.toml`.
- Launch the Korea keyword dashboard with:
  - `streamlit run src/keyword_analysis/dashboard.py`
- The dashboard reads existing outputs from `outputs/reports_korea_focus/` by default.

## Public Dashboard

- The local Streamlit dashboard remains the operator console.
- The public dashboard is a separate read-only static site under `site/`.
- Generate the published data bundle with:
  - `python -c "from keyword_analysis.pipeline import export_korea_public_dashboard; export_korea_public_dashboard()"`
- For a local preview of the published site, place `dashboard_data.json` under `site/data/` and serve the repository with a static HTTP server.

## Branch Strategy

- Use a feature branch such as `feature/public-dashboard` for public dashboard work.
- Keep `main` as the source-of-truth branch for Python code, static site assets, and docs.
- Do not manually edit deployment output on a long-lived `gh-pages` branch unless Actions-based deployment is unavailable.
- Preferred flow:
  - develop and test on a feature branch
  - open a pull request into `main`
  - let GitHub Actions publish the Pages artifact from `main`

## GitHub Pages Deployment

- Preferred deployment mode:
  - GitHub Pages with `GitHub Actions` as the source
- The workflow should:
  - install the Python package
  - generate `site/data/dashboard_data.json`
  - upload `site/` as the Pages artifact
- See `docs/github_pages_deployment.md` for the full setup and operating steps.

## Publish Safety

- Treat the public dashboard as a read-only published view, not a live analytics system.
- Publish only the generated JSON bundle and static site assets.
- Do not publish:
  - `outputs/*.sqlite3`
  - `outputs/reports/collection_failures.log`
  - arbitrary local snapshot paths or local filesystem settings
- See `docs/public_dashboard_operations.md` for the runbook, publish cadence, and rollback guidance.
