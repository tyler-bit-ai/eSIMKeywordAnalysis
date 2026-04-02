from __future__ import annotations

import pandas as pd

from keyword_analysis.dashboard_data import is_noisy_keyword
from keyword_analysis.scoring import score_keywords


def test_reddit_and_platform_terms_are_not_marked_noisy() -> None:
    assert is_noisy_keyword("korea esim reddit") is False
    assert is_noisy_keyword("korea esim klook") is False


def test_faq_and_carrier_queries_are_marked_noisy() -> None:
    assert is_noisy_keyword("does ee provide esim") is True
    assert is_noisy_keyword("does china mobile support esim") is True
    assert is_noisy_keyword("does esim work in nepal") is True


def test_generic_faq_queries_receive_score_demotion() -> None:
    frame = pd.DataFrame(
        [
            {
                "id": 1,
                "canonical_keyword": "korea esim reddit",
                "keyword_family": "korea",
                "destination": "korea",
                "signal_type": "autocomplete",
                "rank_position": 1,
                "notes": "seed",
            },
            {
                "id": 2,
                "canonical_keyword": "does ee provide esim",
                "keyword_family": "generic_esim",
                "destination": None,
                "signal_type": "autocomplete",
                "rank_position": 1,
                "notes": "seed",
            },
        ]
    )

    scored = score_keywords(frame).set_index("canonical_keyword")

    assert scored.loc["korea esim reddit", "priority_score"] > scored.loc["does ee provide esim", "priority_score"]
    assert scored.loc["does ee provide esim", "keyword_bucket"] == "niche_long_tail"
