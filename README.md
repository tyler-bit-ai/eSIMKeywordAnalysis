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
