"""Shared schemas for normalized keywords and cluster assignments."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class NormalizedKeyword:
    raw_keyword: str
    canonical_keyword: str
    destination: str | None
    keyword_family: str
    clusters: tuple[str, ...]
    normalization_notes: str


@dataclass(frozen=True)
class IntentAssignment:
    canonical_keyword: str
    cluster: str
    reason: str

