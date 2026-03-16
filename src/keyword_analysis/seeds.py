"""Seed keywords and expansion helpers for Google-only eSIM research."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True)
class SeedDefinition:
    keyword: str
    category: str
    notes: str = ""


SEED_KEYWORDS: tuple[SeedDefinition, ...] = (
    SeedDefinition("esim", "broad_product"),
    SeedDefinition("travel esim", "broad_product"),
    SeedDefinition("prepaid esim", "broad_product"),
    SeedDefinition("data only esim", "feature_intent"),
    SeedDefinition("best esim", "comparison_commercial"),
    SeedDefinition("korea esim", "destination_specific"),
    SeedDefinition("south korea esim", "destination_specific"),
    SeedDefinition("esim for korea", "destination_specific"),
    SeedDefinition("korea travel esim", "destination_specific"),
    SeedDefinition("best esim for korea", "comparison_commercial"),
    SeedDefinition("unlimited esim", "feature_intent"),
    SeedDefinition("unlimited data esim", "feature_intent"),
    SeedDefinition("esim with phone number", "feature_intent"),
    SeedDefinition("instant esim", "feature_intent"),
    SeedDefinition("qr code esim", "feature_intent"),
    SeedDefinition("best travel esim", "comparison_commercial"),
    SeedDefinition("cheap esim", "comparison_commercial"),
    SeedDefinition("esim plans", "comparison_commercial"),
    SeedDefinition("esim for tourists", "comparison_commercial"),
)

KOREA_FOCUS_SEEDS: tuple[SeedDefinition, ...] = (
    SeedDefinition("korea esim", "destination_specific", "primary_korea_root"),
    SeedDefinition("esim for korea", "destination_specific", "primary_korea_root"),
    SeedDefinition("south korea esim", "destination_specific", "primary_korea_root"),
    SeedDefinition("korea travel esim", "destination_specific", "primary_korea_root"),
    SeedDefinition("best esim for korea", "comparison_commercial", "korea_marketing_target"),
    SeedDefinition("unlimited data esim korea", "feature_intent", "korea_marketing_target"),
    SeedDefinition("korea esim with phone number", "feature_intent", "korea_marketing_target"),
)

ALLOWED_PREFIXES: tuple[str, ...] = (
    "best",
    "cheap",
    "prepaid",
    "unlimited",
    "instant",
)

ATTRIBUTE_FAMILIES: dict[str, tuple[str, ...]] = {
    "unlimited": ("unlimited", "unlimited data"),
    "prepaid": ("prepaid",),
    "phone_number": ("with phone number",),
    "data_only": ("data only",),
    "delivery": ("qr code", "instant"),
    "price": ("cheap", "price"),
}


def list_seed_keywords() -> list[str]:
    return [seed.keyword for seed in SEED_KEYWORDS]


def iter_category(category: str) -> Iterable[SeedDefinition]:
    return (seed for seed in SEED_KEYWORDS if seed.category == category)


def list_korea_focus_seed_keywords() -> list[str]:
    return [seed.keyword for seed in KOREA_FOCUS_SEEDS]
