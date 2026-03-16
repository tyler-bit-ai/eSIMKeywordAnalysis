"""Related-search extraction from public Google SERPs."""

from __future__ import annotations

from datetime import UTC, datetime

from playwright.sync_api import Page

from keyword_analysis.collectors.google_base import COLLECTOR_VERSION, GoogleCollectorBase
from keyword_analysis.storage import Observation


class GoogleRelatedSearchesCollector(GoogleCollectorBase):
    collector_name = "google_related_searches"

    def collect(self, seed_keyword: str) -> list[Observation]:
        self.storage.insert_run(self.create_run_record())

        def handler(page: Page) -> list[Observation]:
            page.goto(
                self.build_google_url(seed_keyword),
                wait_until="domcontentloaded",
                timeout=30000,
            )
            page.wait_for_timeout(1000)
            body_text = page.locator("body").inner_text().lower()
            if "our systems have detected unusual traffic" in body_text or "about this page" in body_text:
                raise RuntimeError("google_sorry_page_detected")
            observed_at = datetime.now(UTC).isoformat()
            observations: list[Observation] = []
            seen: set[str] = set()

            candidates = page.locator("a").all_inner_texts()
            for index, text in enumerate(candidates, start=1):
                cleaned = " ".join(text.split())
                if not cleaned:
                    continue
                lowered = cleaned.lower()
                if lowered in seen or "esim" not in lowered and seed_keyword.split()[0] not in lowered:
                    continue
                seen.add(lowered)
                observations.append(
                    Observation(
                        run_id=self.context.run_id,
                        observed_at_utc=observed_at,
                        seed_keyword=seed_keyword,
                        query_keyword=seed_keyword,
                        signal_type="related_search",
                        locale_gl=self.context.locale_gl,
                        language_hl=self.context.language_hl,
                        login_state=self.context.login_state,
                        browser_profile=self.context.browser_profile,
                        device_class=self.context.device_class,
                        rank_position=index,
                        raw_text=cleaned,
                        source_url=page.url,
                        collector_version=COLLECTOR_VERSION,
                        notes="playwright-serp-anchor-filter",
                    )
                )

            return observations

        observations = self.run_with_retries(handler)
        self.storage.insert_observations(observations)
        self.storage.insert_run(self.create_run_record(status="completed"))
        return observations
