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

## Dashboard

- Install dependencies from `pyproject.toml`.
- Launch the Korea keyword dashboard with:
  - `streamlit run src/keyword_analysis/dashboard.py`
- The dashboard reads existing outputs from `outputs/reports_korea_focus/` by default.
