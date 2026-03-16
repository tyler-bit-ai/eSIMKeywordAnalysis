"""Keyword canonicalization and normalization rules."""

from __future__ import annotations

import re
from dataclasses import asdict
from typing import Iterable

from keyword_analysis.schemas import NormalizedKeyword


DESTINATION_ALIASES: dict[str, tuple[str, ...]] = {
    "south korea": ("south korea",),
    "korea": ("korea", "south korea"),
}

PUNCTUATION_RE = re.compile(r"[^a-z0-9\s]")
WHITESPACE_RE = re.compile(r"\s+")


def normalize_text(keyword: str) -> str:
    lowered = keyword.lower().replace("e-sim", "esim").replace("e sim", "esim")
    no_punctuation = PUNCTUATION_RE.sub(" ", lowered)
    return WHITESPACE_RE.sub(" ", no_punctuation).strip()


def extract_destination(keyword: str) -> str | None:
    normalized = normalize_text(keyword)
    for canonical, aliases in DESTINATION_ALIASES.items():
        if any(alias in normalized for alias in aliases):
            if canonical == "south korea" and "korea" in normalized and "south korea" not in normalized:
                continue
            return canonical
    return None


def canonicalize_keyword(keyword: str) -> NormalizedKeyword:
    normalized = normalize_text(keyword)
    canonical = normalized
    notes: list[str] = []

    if normalized.startswith("esim for "):
        destination = normalized.removeprefix("esim for ").strip()
        canonical = f"{destination} esim"
        notes.append("reordered_destination_preposition")

    if " travel esim" in canonical:
        canonical = canonical.replace(" travel esim", " esim")
        notes.append("collapsed_travel_destination_variant")

    if canonical.startswith("south korea esim"):
        canonical = canonical.replace("south korea esim", "korea esim")
        notes.append("collapsed_south_korea_variant")

    destination = extract_destination(canonical)
    keyword_family = destination if destination else "generic_esim"
    return NormalizedKeyword(
        raw_keyword=keyword,
        canonical_keyword=canonical,
        destination=destination,
        keyword_family=keyword_family,
        clusters=(),
        normalization_notes=",".join(notes) if notes else "normalized_only",
    )


def normalize_keywords(keywords: Iterable[str]) -> list[dict[str, str | tuple[str, ...] | None]]:
    return [asdict(canonicalize_keyword(keyword)) for keyword in keywords]

