# Validation And Risks

## Validation Framework

### Cross-Signal Validation

- Prefer keywords observed in at least two Google-native signals.
- Treat autocomplete plus Trends agreement as stronger evidence than a single-signal appearance.
- Use related searches to confirm adjacency of query families, not exact demand size.

### Time-Based Validation

- Re-run the same seed set on a fixed cadence.
- Treat repeated appearance across weeks as stronger evidence of stable demand.
- Flag sharp one-run spikes for manual review before promotion.

### Manual Validation

- Spot-check sampled SERPs in a logged-out U.S.-English setup.
- Confirm that top results reflect the same intent implied by the keyword cluster.
- Confirm that destination keywords still point to travel/data-plan contexts rather than unrelated acronym collisions.

## Major Risks

### No Internal Query Logs

- Limitation: public signals are only a proxy for real query frequency.
- Mitigation: keep outputs labeled as estimated search behavior, not ground-truth volume.

### Personalization Leakage

- Limitation: Google results can vary by cookies, prior activity, and device history.
- Mitigation: use logged-out sessions, stable browser settings, and repeat runs.

### DOM Volatility

- Limitation: Google markup can change without notice.
- Mitigation: keep selectors narrow, fail gracefully, and revalidate collectors when extraction counts drop unexpectedly.

### Anti-Bot Friction

- Limitation: aggressive automation can trigger rate limiting or blocks.
- Mitigation: use low-volume collection, request spacing, retries, and bounded seed sets for MVP.

### Regional And Temporal Noise

- Limitation: U.S. behavior may still vary by metro, season, travel events, or telecom news.
- Mitigation: compare repeated weekly snapshots and treat event-driven spikes as provisional.

## Runbook

1. Run autocomplete monitoring daily for a small stable seed subset.
2. Run full autocomplete, related-search, and Trends collection weekly.
3. Rebuild normalized keywords and reports after every collection batch.
4. Compare the latest ranked snapshot against the previous ranked snapshot.
5. Review new keywords, disappeared keywords, and bucket changes before updating any curated keyword set.

