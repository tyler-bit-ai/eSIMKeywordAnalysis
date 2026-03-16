"""Optional SERP title and snippet collector for intent interpretation."""

from __future__ import annotations

from datetime import UTC, datetime

from playwright.sync_api import Page

from keyword_analysis.collectors.google_base import COLLECTOR_VERSION, GoogleCollectorBase
from keyword_analysis.storage import Observation


class SerpContextCollector(GoogleCollectorBase):
    collector_name = "serp_context"

    def collect(self, seed_keyword: str, max_results: int = 5) -> list[Observation]:
        self.storage.insert_run(self.create_run_record())

        def handler(page: Page) -> list[Observation]:
            page.goto(
                self.build_google_url(seed_keyword),
                wait_until="domcontentloaded",
                timeout=30000,
            )
            page.wait_for_timeout(1200)

            cards = page.locator("div.g")
            count = min(cards.count(), max_results)
            observed_at = datetime.now(UTC).isoformat()
            observations: list[Observation] = []

            for index in range(count):
                card = cards.nth(index)
                title = " ".join(card.locator("h3").all_inner_texts()).strip()
                snippet = " ".join(card.locator("div[data-sncf='1'], div.VwiC3b").all_inner_texts()).strip()
                combined = " | ".join(part for part in (title, snippet) if part)
                if not combined:
                    continue

                observations.append(
                    Observation(
                        run_id=self.context.run_id,
                        observed_at_utc=observed_at,
                        seed_keyword=seed_keyword,
                        query_keyword=seed_keyword,
                        signal_type="serp_context",
                        locale_gl=self.context.locale_gl,
                        language_hl=self.context.language_hl,
                        login_state=self.context.login_state,
                        browser_profile=self.context.browser_profile,
                        device_class=self.context.device_class,
                        rank_position=index + 1,
                        raw_text=combined,
                        source_url=page.url,
                        collector_version=COLLECTOR_VERSION,
                        notes="title_and_snippet_for_intent_only",
                    )
                )

            return observations

        observations = self.run_with_retries(handler)
        self.storage.insert_observations(observations)
        self.storage.insert_run(self.create_run_record(status="completed"))
        return observations

