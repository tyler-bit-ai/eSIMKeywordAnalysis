"""Autocomplete collection from public Google search UI."""

from __future__ import annotations

import requests
from datetime import UTC, datetime
from typing import Iterable

from playwright.sync_api import Page

from keyword_analysis.collectors.google_base import COLLECTOR_VERSION, GoogleCollectorBase
from keyword_analysis.query_expansion import ExpandedQuery
from keyword_analysis.storage import Observation


class GoogleAutocompleteCollector(GoogleCollectorBase):
    collector_name = "google_autocomplete"

    def collect(
        self,
        seed_keyword: str,
        expanded_queries: Iterable[ExpandedQuery] | None = None,
    ) -> list[Observation]:
        self.storage.insert_run(self.create_run_record())
        queries = list(expanded_queries or [ExpandedQuery(query_keyword=seed_keyword, source="seed")])
        observations: list[Observation] = []

        for expanded_query in queries:
            observations.extend(
                self._collect_query(
                    seed_keyword=seed_keyword,
                    query_keyword=expanded_query.query_keyword,
                    expansion_source=expanded_query.source,
                )
            )

        deduped_observations = self._dedupe_observations(observations)
        self.storage.insert_observations(deduped_observations)
        self.storage.insert_run(self.create_run_record(status="completed"))
        return deduped_observations

    def _collect_query(
        self,
        seed_keyword: str,
        query_keyword: str,
        expansion_source: str,
    ) -> list[Observation]:
        def handler(page: Page) -> list[Observation]:
            page.goto(
                self.build_google_url(query_keyword),
                wait_until="domcontentloaded",
                timeout=30000,
            )
            body_text = page.locator("body").inner_text().lower()
            if "our systems have detected unusual traffic" in body_text or "about this page" in body_text:
                raise RuntimeError("google_sorry_page_detected")
            search_box = page.locator("textarea[name='q']").first
            search_box.click()
            search_box.fill(query_keyword)
            page.wait_for_timeout(1500)

            suggestions = page.locator("li span").all_inner_texts()
            return self._build_observations(
                suggestions=suggestions,
                seed_keyword=seed_keyword,
                query_keyword=query_keyword,
                source_url=page.url,
                collection_note=f"{expansion_source}|playwright-ui",
            )

        try:
            return self.run_with_retries(handler)
        except RuntimeError:
            return self._collect_from_suggest_endpoint(
                seed_keyword=seed_keyword,
                query_keyword=query_keyword,
                expansion_source=expansion_source,
            )

    def _collect_from_suggest_endpoint(
        self,
        seed_keyword: str,
        query_keyword: str,
        expansion_source: str,
    ) -> list[Observation]:
        response = requests.get(
            "https://suggestqueries.google.com/complete/search",
            params={
                "client": "firefox",
                "q": query_keyword,
                "hl": self.context.language_hl,
                "gl": self.context.locale_gl,
            },
            headers={"User-Agent": "Mozilla/5.0"},
            timeout=30,
        )
        response.raise_for_status()
        payload = response.json()
        suggestions = payload[1] if len(payload) > 1 else []
        return self._build_observations(
            suggestions=suggestions,
            seed_keyword=seed_keyword,
            query_keyword=query_keyword,
            source_url=response.url,
            collection_note=f"{expansion_source}|requests-suggest-endpoint-fallback",
        )

    def _build_observations(
        self,
        suggestions: Iterable[str],
        seed_keyword: str,
        query_keyword: str,
        source_url: str,
        collection_note: str,
    ) -> list[Observation]:
        observed_at = datetime.now(UTC).isoformat()
        observations: list[Observation] = []

        for index, text in enumerate(suggestions, start=1):
            cleaned = " ".join(str(text).split())
            if not cleaned:
                continue
            observations.append(
                Observation(
                    run_id=self.context.run_id,
                    observed_at_utc=observed_at,
                    seed_keyword=seed_keyword,
                    query_keyword=query_keyword,
                    signal_type="autocomplete",
                    locale_gl=self.context.locale_gl,
                    language_hl=self.context.language_hl,
                    login_state=self.context.login_state,
                    browser_profile=self.context.browser_profile,
                    device_class=self.context.device_class,
                    rank_position=index,
                    raw_text=cleaned,
                    source_url=source_url,
                    collector_version=COLLECTOR_VERSION,
                    notes=collection_note,
                )
            )

        return observations

    def _dedupe_observations(self, observations: Iterable[Observation]) -> list[Observation]:
        deduped: list[Observation] = []
        seen: set[str] = set()

        for observation in observations:
            lowered = observation.raw_text.lower()
            if lowered in seen:
                continue
            seen.add(lowered)
            deduped.append(observation)

        return deduped
