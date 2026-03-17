from __future__ import annotations

from keyword_analysis.query_expansion import build_autocomplete_queries


def test_build_autocomplete_queries_respects_max_expansions() -> None:
    queries = build_autocomplete_queries(
        "korea esim",
        {
            "enabled": True,
            "max_expansions": 4,
            "include_letters": True,
            "include_numbers": True,
            "include_modifiers": True,
            "letters": "ab",
            "numbers": "01",
            "modifiers": ["best", "reddit"],
        },
    )

    assert [query.query_keyword for query in queries] == [
        "korea esim",
        "korea esim best",
        "korea esim reddit",
        "korea esim a",
    ]


def test_build_autocomplete_queries_can_disable_expansion() -> None:
    queries = build_autocomplete_queries(
        "korea esim",
        {
            "enabled": False,
            "max_expansions": 10,
        },
    )

    assert [query.query_keyword for query in queries] == ["korea esim"]
