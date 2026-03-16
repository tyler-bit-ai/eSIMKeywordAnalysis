# Google-Only eSIM Keyword Research Plan

## Problem Definition

- Define "how U.S. users search on Google" as a public-signal estimate of likely query wording, modifiers, and intent patterns shown in Google surfaces visible to U.S. English users.
- Prioritize the Korea travel eSIM use case: U.S. users preparing to visit Korea and searching for eSIM purchase options on Google.
- Treat Google internal query logs as unavailable ground truth.
- Treat this project as an estimation exercise based on repeated observations of Google autocomplete, related searches, Google Trends, and optional SERP title/snippet context.
- Count a keyword insight as useful when it can support one or more of these outcomes:
  - identify a plausible search phrase used by U.S. consumers planning a Korea trip
  - identify follow-on keywords that appear after root searches such as `korea esim`
  - identify a repeatable modifier pattern such as destination, duration, unlimited data, or phone number
  - identify intent clusters that can be tracked over time
  - identify changes in visibility across public Google signals
  - identify target keywords where product-page SEO or paid/organic marketing should aim to appear

## In-Scope Signals

- Google autocomplete suggestions
- Google related searches from Google Search results pages
- Google Trends interest patterns and related queries
- Optional Google Search result titles/snippets for intent interpretation only

## Out-Of-Scope Sources

- Amazon, Qoo10, or any ecommerce platform
- Google Ads private tooling
- Google Search Console data not owned by the project
- Google internal search logs
- Third-party keyword databases used as a substitute for Google-native public signals

## Locale And Personalization Controls

- Use U.S.-oriented Google settings with `hl=en` and `gl=us`.
- Run collectors in a logged-out browser profile.
- Keep browser, viewport, user agent, and collection cadence consistent across runs.
- Store collection metadata that captures locale, language, login state, browser profile, device class, timestamp, and collector version.
- Re-run the same seeds on a schedule to separate persistent patterns from temporary noise.

## Collection Metadata Schema

Every observation row should preserve:

| Field | Description |
| --- | --- |
| `run_id` | Unique ID for a single collection run |
| `observed_at_utc` | UTC timestamp for the observation |
| `seed_keyword` | Original seed that triggered the collection |
| `query_keyword` | Actual query sent to Google or Trends |
| `signal_type` | `autocomplete`, `related_search`, `trends_related`, `trends_timeseries`, `serp_context` |
| `locale_gl` | Country parameter, expected `us` |
| `language_hl` | Language parameter, expected `en` |
| `login_state` | `logged_out` by default |
| `browser_profile` | Named profile or automation preset used for the run |
| `device_class` | `desktop` or `mobile` |
| `rank_position` | Position within the observed signal when available |
| `raw_text` | Raw suggestion, related search text, snippet, or title |
| `source_url` | URL or endpoint used to retrieve the signal |
| `collector_version` | Version string of the collecting code |
| `notes` | Optional exception or parsing notes |

## Deliverables

- Python project scaffold for data collection and analysis
- Google-only collection modules
- Normalized keyword taxonomy and clustering rules
- Scoring model for stable, rising, and niche terms
- Korea-focused marketing target report for follow-on keywords discovered from `korea esim`-family seeds
- Time-series monitoring process
- Risk and validation framework

## Success Criteria

- The workflow can collect repeatable Google public signals for a controlled U.S. locale setup.
- Raw observations are preserved with enough metadata for auditability.
- Keyword outputs distinguish between canonical terms, modifiers, and intent clusters.
- Reports make a clear distinction between observed public signals and inferred real-world search behavior.
- Reports highlight which Korea-focused follow-on queries are actionable marketing targets.
