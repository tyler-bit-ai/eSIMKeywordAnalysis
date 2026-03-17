"""Helpers for expanding autocomplete collection queries."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable


DEFAULT_LETTERS = "abcdefghijklmnopqrstuvwxyz"
DEFAULT_NUMBERS = "0123456789"
DEFAULT_MODIFIERS = (
    "best",
    "buy",
    "review",
    "reddit",
    "unlimited",
    "for travel",
    "with phone number",
)


@dataclass(frozen=True)
class ExpandedQuery:
    query_keyword: str
    source: str


def build_autocomplete_queries(
    seed_keyword: str,
    expansion_config: dict[str, Any] | None,
) -> list[ExpandedQuery]:
    config = expansion_config or {}
    enabled = bool(config.get("enabled", True))
    max_expansions = int(config.get("max_expansions", 16))
    if not enabled or max_expansions <= 1:
        return [ExpandedQuery(query_keyword=seed_keyword, source="seed")]

    queries = [ExpandedQuery(query_keyword=seed_keyword, source="seed")]
    seen = {seed_keyword.lower()}

    _extend_queries(
        queries,
        seen,
        _modifier_queries(seed_keyword, config),
        max_expansions,
    )
    _extend_queries(
        queries,
        seen,
        _suffix_queries(
            seed_keyword,
            values=str(config.get("letters", DEFAULT_LETTERS)),
            include=bool(config.get("include_letters", True)),
            source_prefix="letter",
        ),
        max_expansions,
    )
    _extend_queries(
        queries,
        seen,
        _suffix_queries(
            seed_keyword,
            values=str(config.get("numbers", DEFAULT_NUMBERS)),
            include=bool(config.get("include_numbers", True)),
            source_prefix="number",
        ),
        max_expansions,
    )
    return queries[:max_expansions]


def _modifier_queries(seed_keyword: str, config: dict[str, Any]) -> list[ExpandedQuery]:
    if not bool(config.get("include_modifiers", True)):
        return []

    modifiers = config.get("modifiers", list(DEFAULT_MODIFIERS))
    queries: list[ExpandedQuery] = []
    for modifier in modifiers:
        cleaned = " ".join(str(modifier).split())
        if not cleaned:
            continue
        queries.append(
            ExpandedQuery(
                query_keyword=f"{seed_keyword} {cleaned}",
                source=f"modifier:{cleaned}",
            )
        )
    return queries


def _suffix_queries(
    seed_keyword: str,
    values: str,
    include: bool,
    source_prefix: str,
) -> list[ExpandedQuery]:
    if not include:
        return []

    queries: list[ExpandedQuery] = []
    for suffix in values:
        cleaned = suffix.strip()
        if not cleaned:
            continue
        queries.append(
            ExpandedQuery(
                query_keyword=f"{seed_keyword} {cleaned}",
                source=f"{source_prefix}:{cleaned}",
            )
        )
    return queries


def _extend_queries(
    target: list[ExpandedQuery],
    seen: set[str],
    candidates: Iterable[ExpandedQuery],
    max_expansions: int,
) -> None:
    for candidate in candidates:
        if len(target) >= max_expansions:
            return
        lowered = candidate.query_keyword.lower()
        if lowered in seen:
            continue
        seen.add(lowered)
        target.append(candidate)
