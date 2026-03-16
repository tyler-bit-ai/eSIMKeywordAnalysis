"""Autocomplete collection from public Google search UI."""

from __future__ import annotations

import requests
from datetime import UTC, datetime

from playwright.sync_api import Page

from keyword_analysis.collectors.google_base import COLLECTOR_VERSION, GoogleCollectorBase
from keyword_analysis.storage import Observation


class GoogleAutocompleteCollector(GoogleCollectorBase):
    collector_name = "google_autocomplete"

    def collect(self, seed_keyword: str) -> list[Observation]:
        self.storage.insert_run(self.create_run_record())

        def handler(page: Page) -> list[Observation]:
            page.goto(
                self.build_google_url(seed_keyword),
                wait_until="domcontentloaded",
                timeout=30000,
            )
            body_text = page.locator("body").inner_text().lower()
            if "our systems have detected unusual traffic" in body_text or "about this page" in body_text:
                raise RuntimeError("google_sorry_page_detected")
            search_box = page.locator("textarea[name='q']").first
            search_box.click()
            search_box.fill(seed_keyword)
            page.wait_for_timeout(1500)

            suggestions = page.locator("li span").all_inner_texts()
            observed_at = datetime.now(UTC).isoformat()
            seen: set[str] = set()
            observations: list[Observation] = []

            for index, text in enumerate(suggestions, start=1):
                cleaned = " ".join(text.split())
                if not cleaned or cleaned.lower() in seen:
                    continue
                seen.add(cleaned.lower())
                observations.append(
                    Observation(
                        run_id=self.context.run_id,
                        observed_at_utc=observed_at,
                        seed_keyword=seed_keyword,
                        query_keyword=seed_keyword,
                        signal_type="autocomplete",
                        locale_gl=self.context.locale_gl,
                        language_hl=self.context.language_hl,
                        login_state=self.context.login_state,
                        browser_profile=self.context.browser_profile,
                        device_class=self.context.device_class,
                        rank_position=index,
                        raw_text=cleaned,
                        source_url=page.url,
                        collector_version=COLLECTOR_VERSION,
                        notes="playwright-ui",
                    )
                )

            return observations

        try:
            observations = self.run_with_retries(handler)
        except RuntimeError:
            observations = self._collect_from_suggest_endpoint(seed_keyword)
        self.storage.insert_observations(observations)
        self.storage.insert_run(self.create_run_record(status="completed"))
        return observations

    def _collect_from_suggest_endpoint(self, seed_keyword: str) -> list[Observation]:
        response = requests.get(
            "https://suggestqueries.google.com/complete/search",
            params={
                "client": "firefox",
                "q": seed_keyword,
                "hl": self.context.language_hl,
                "gl": self.context.locale_gl,
            },
            headers={"User-Agent": "Mozilla/5.0"},
            timeout=30,
        )
        response.raise_for_status()
        payload = response.json()
        suggestions = payload[1] if len(payload) > 1 else []
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
                    query_keyword=seed_keyword,
                    signal_type="autocomplete",
                    locale_gl=self.context.locale_gl,
                    language_hl=self.context.language_hl,
                    login_state=self.context.login_state,
                    browser_profile=self.context.browser_profile,
                    device_class=self.context.device_class,
                    rank_position=index,
                    raw_text=cleaned,
                    source_url=response.url,
                    collector_version=COLLECTOR_VERSION,
                    notes="requests-suggest-endpoint-fallback",
                )
            )

        return observations
