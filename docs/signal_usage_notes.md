# Signal Usage Notes

## Signal Roles

- `autocomplete`: strongest public signal for likely phrasing and modifier discovery.
- `related_search`: supporting signal for adjacent query families and alternative wording.
- `trends_related`: supporting signal for relative momentum and recurring query families.
- `serp_context`: auxiliary signal for intent interpretation only.

## SERP Context Guardrails

- Use SERP titles and snippets only to interpret likely intent framing.
- Do not treat SERP titles or snippets as direct evidence of true query volume.
- Do not treat SEO-heavy wording as demand truth without support from autocomplete, related searches, or Trends.
- Sample only a limited number of top organic results.
- Disable SERP context collection when DOM instability, bot friction, or noise makes the signal unreliable.

## Interpretation Rules

- Prefer keywords supported by multiple Google-native signals.
- Use SERP context to explain why a keyword looks commercial, informational, destination-specific, or feature-specific.
- Keep raw SERP text separate from normalized keywords.
- Preserve the distinction between observed text and inferred user intent.

