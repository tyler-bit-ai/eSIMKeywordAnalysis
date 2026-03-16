# Seed Keyword Design

## Seed Taxonomy

### Korea-Focused Priority Seeds

- `korea esim`
- `esim for korea`
- `south korea esim`
- `korea travel esim`
- `best esim for korea`
- `unlimited data esim korea`
- `korea esim with phone number`

### Broad Product Seeds

- `esim`
- `travel esim`
- `prepaid esim`
- `data only esim`
- `best esim`

### Destination-Specific Seeds

- `korea esim`
- `south korea esim`
- `esim for korea`
- `korea travel esim`
- `best esim for korea`

### Feature And Offer Seeds

- `unlimited esim`
- `unlimited data esim`
- `esim with phone number`
- `prepaid travel esim`
- `instant esim`
- `qr code esim`

### Comparison And Purchase-Intent Seeds

- `best travel esim`
- `cheap esim`
- `best esim for travel`
- `esim plans`
- `esim for tourists`

## Expansion Rules

### Suffix Expansion

- Append intent modifiers discovered in autocomplete or related searches.
- Example:
  - base: `korea esim`
  - expansions: `korea esim unlimited data`, `korea esim phone number`, `korea esim price`

### Prefix Expansion

- Add commercial or evaluative prefixes to candidate keywords.
- Allowed prefixes:
  - `best`
  - `cheap`
  - `prepaid`
  - `unlimited`
  - `instant`
- Example:
  - base: `esim for korea`
  - expansions: `best esim for korea`, `prepaid esim for korea`

### Destination Substitution

- Replace a destination token with another verified destination from the discovered backlog.
- Preserve the original query pattern.
- Example:
  - `esim for korea` -> `esim for japan`
  - `best esim for korea` -> `best esim for thailand`

### Attribute Substitution

- Swap one feature modifier for another within the same pattern family.
- Allowed attribute families:
  - `unlimited`, `unlimited data`
  - `prepaid`
  - `with phone number`
  - `data only`
  - `qr code`, `instant`
  - `cheap`, `price`

### Question And Comparison Variants

- Add research-style modifiers when they appear in Google suggestions or related searches.
- Examples:
  - `best esim for korea`
  - `is esim good for korea`
  - `korea esim vs sim card`
  - `how to get esim for korea`

## Canonical Expansion Logic

1. Start from curated seed keywords.
2. Prioritize Korea-focused seeds before broader generic seeds.
3. Collect public Google suggestions and related queries.
4. Normalize casing and whitespace before deduplication.
5. Match each discovered candidate against pattern families.
6. Expand only when the pattern stays within project scope and remains relevant to eSIM product search behavior.
7. Store the discovered phrase and the canonical query family separately.
8. Mark whether the candidate came from a Korea-focused seed so it can feed a marketing-target report.

## Korea Follow-On Keyword Goal

- Treat `korea esim` and its close variants as primary discovery roots.
- Capture what users append to that root query, such as:
  - price modifiers
  - best/comparison modifiers
  - unlimited-data modifiers
  - phone-number modifiers
  - travel/tourist modifiers
- Promote discovered follow-on keywords into a Korea marketing target list when they are observed in Google autocomplete or another Google-native signal.

## Exclusion Rules

- Exclude queries unrelated to mobile connectivity products.
- Exclude developer, hardware-spec, or carrier-activation troubleshooting unless they clearly express purchase or plan-search intent.
- Exclude navigational queries targeting a single brand unless they still reveal reusable modifier patterns.
- Exclude irrelevant acronym collisions where `esim` does not mean embedded SIM.
- Exclude duplicates after canonical normalization of case, whitespace, and destination-preposition patterns.

## Duplicate Handling

- Normalize `eSIM` and `esim` to the same canonical token.
- Normalize equivalent destination forms into a shared family record while preserving raw text.
- Examples:
  - `korea esim` and `esim for korea` share the same destination family
  - `south korea esim` and `korea travel esim` remain separate raw variants but map to the same destination cluster

## Decision Rules

- Keep a candidate if it appears in at least one public Google signal and matches an allowed intent family.
- Promote a candidate to the curated backlog if it is observed repeatedly across runs or across more than one signal.
- Flag a candidate for manual review if it is ambiguous, heavily branded, or looks driven by temporary news noise.
