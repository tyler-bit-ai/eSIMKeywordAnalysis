# Korea eSIM Dashboard Plan

## Dashboard Goal

- Help SEO and marketing users compare Korea eSIM keyword targets at a glance.
- Prioritize keywords discovered from root searches such as `korea esim`, `esim for korea`, and `south korea esim`.
- Make it obvious which follow-on keywords should be targeted now, watched, or reviewed manually.

## Primary User Questions

- Which Korea eSIM follow-on keywords have the highest marketing priority right now?
- Which modifiers appear most often after `korea esim`-family root searches?
- Which keywords are supported by multiple Google-native signals instead of only one signal?
- Which targets came from `korea esim` vs `esim for korea` vs `south korea esim`?
- Which keywords are new, disappearing, or moving in score/rank compared with the previous snapshot?
- Which terms look noisy, off-topic, or manual-review-only?

## Screen Structure

### Header KPI Strip

- `High Priority Targets`
- `Rising Keywords`
- `New Since Last Snapshot`
- `Manual Review Terms`

### Main Comparison Table

- Default sort: `priority_score` descending
- Required columns:
  - `canonical_keyword`
  - `follow_on_modifier`
  - `marketing_priority`
  - `priority_score`
  - `keyword_bucket`
  - `evidence_signals`
  - `origin_seeds`
  - `raw_variants`
- Purpose:
  - give users one screen where they can compare targetability, evidence, and lineage

### Modifier Comparison Panel

- Group keywords by `follow_on_modifier`
- Show keyword count, average score, and top examples per modifier
- Highlight commercially useful modifiers such as:
  - `best`
  - `unlimited data`
  - `with phone number`
  - `tourist`
  - `data only`

### Root-Seed Lineage Panel

- Compare outputs from:
  - `korea esim`
  - `esim for korea`
  - `south korea esim`
- Show how many target keywords came from each root
- Show overlap across roots where the same canonical keyword appears in more than one seed lineage

### Snapshot Delta Panel

- Show:
  - new keywords
  - disappeared keywords
  - biggest upward movers
  - biggest downward movers
  - bucket changes
- Keep this compact and comparison-first rather than chart-heavy

## Comparison Rules

### Priority Cues

- `high`: bold/high-contrast color
- `medium`: neutral warning color
- `test`: low-emphasis color

### Evidence Cues

- Render `autocomplete`, `trends_related`, and other signals as small badges
- Make multi-signal keywords visually stronger than single-signal keywords

### Noise Cues

- Separate likely noisy terms such as `reddit`, unrelated spillover, or brand-only terms
- Do not hide noisy terms completely; route them into a `Review Manually` view

## Global Filters

- `origin_seed`
- `follow_on_modifier`
- `marketing_priority`
- `keyword_bucket`
- `evidence_signal`

## Local Drill-Down Interactions

- Click a keyword row to show:
  - raw variants
  - all origin seeds
  - evidence signals
  - target reason
- Click a modifier group to filter the main table
- Click a root seed to isolate lineage

## Dashboard Defaults

- Open on Korea marketing targets, not on generic eSIM keywords
- Default the first view to actionable targets instead of all collected keywords
- Default snapshot comparison to the latest available pair

## Action Views

- `Target Now`
  - show high-priority, non-noisy keywords first
  - emphasize landing-page and product-page target candidates
- `Watch`
  - show rising or medium-priority terms that need additional observations
  - keep trend-sensitive modifiers visible without overcommitting
- `Review Manually`
  - show noisy, branded, community-led, or spillover terms
  - preserve evidence and lineage, but lower visual emphasis

## Success Criteria

- A user can identify top Korea eSIM target keywords in under one minute
- A user can distinguish actionable keywords from noisy terms without reading raw CSV files
- A user can compare roots, modifiers, and evidence on one screen
