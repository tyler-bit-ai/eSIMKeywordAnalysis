"""Rule-based intent and attribute clustering."""

from __future__ import annotations

from dataclasses import replace

from keyword_analysis.normalize import canonicalize_keyword, normalize_text
from keyword_analysis.schemas import IntentAssignment, NormalizedKeyword


CLUSTER_RULES: dict[str, tuple[str, ...]] = {
    "destination": ("korea", "south korea", "for korea"),
    "duration": ("day", "days", "week", "month", "30 day"),
    "price": ("cheap", "price", "cost", "best value"),
    "unlimited": ("unlimited", "unlimited data"),
    "phone_number": ("phone number", "number"),
    "instant_delivery": ("instant", "instant delivery", "activate now"),
    "qr_code": ("qr code", "qr"),
    "network_compatibility": ("carrier", "network", "compatible", "works with"),
}


def classify_keyword(keyword: str) -> tuple[NormalizedKeyword, list[IntentAssignment]]:
    normalized_keyword = canonicalize_keyword(keyword)
    normalized_text = normalize_text(normalized_keyword.canonical_keyword)
    assignments: list[IntentAssignment] = []

    for cluster, markers in CLUSTER_RULES.items():
        matched_markers = [marker for marker in markers if marker in normalized_text]
        if not matched_markers:
            continue
        assignments.append(
            IntentAssignment(
                canonical_keyword=normalized_keyword.canonical_keyword,
                cluster=cluster,
                reason=f"matched:{'|'.join(matched_markers)}",
            )
        )

    if normalized_keyword.destination and not any(item.cluster == "destination" for item in assignments):
        assignments.append(
            IntentAssignment(
                canonical_keyword=normalized_keyword.canonical_keyword,
                cluster="destination",
                reason="extracted_destination",
            )
        )

    enriched = replace(
        normalized_keyword,
        clusters=tuple(sorted({assignment.cluster for assignment in assignments})),
    )
    return enriched, assignments

