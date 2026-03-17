"""Related-search extraction from public Google SERPs."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Iterable

from playwright.sync_api import Page

from keyword_analysis.collectors.google_base import COLLECTOR_VERSION, GoogleCollectorBase
from keyword_analysis.storage import Observation


RELATED_SEARCH_PATTERNS = ("related searches", "people also search for")


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

            related_texts = self._extract_related_search_texts(page, seed_keyword)
            if not related_texts:
                raise RuntimeError("related_search_section_not_found")

            observed_at = datetime.now(UTC).isoformat()
            return [
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
                    raw_text=text,
                    source_url=page.url,
                    collector_version=COLLECTOR_VERSION,
                    notes="playwright-related-search-section",
                )
                for index, text in enumerate(related_texts, start=1)
            ]

        try:
            observations = self.run_with_retries(handler)
        except RuntimeError as error:
            self.storage.insert_run(self.create_run_record(status="failed", notes=str(error)))
            return []

        self.storage.insert_observations(observations)
        completion_note = "" if observations else "no_related_searches_found"
        self.storage.insert_run(self.create_run_record(status="completed", notes=completion_note))
        return observations

    def _extract_related_search_texts(self, page: Page, seed_keyword: str) -> list[str]:
        texts = page.evaluate(
            """
            () => {
              const headings = Array.from(document.querySelectorAll('h2, h3, div[role="heading"]'));
              const matchedHeading = headings.find((node) => {
                const text = (node.textContent || '').trim().toLowerCase();
                return ['related searches', 'people also search for'].some((pattern) => text.includes(pattern));
              });
              if (!matchedHeading) {
                return [];
              }
              let current = matchedHeading;
              for (let depth = 0; depth < 4 && current; depth += 1) {
                const links = Array.from(current.querySelectorAll('a'));
                const values = links
                  .map((link) => (link.innerText || link.textContent || '').trim())
                  .filter(Boolean);
                if (values.length > 0) {
                  return values;
                }
                current = current.parentElement;
              }
              return [];
            }
            """
        )
        return self._clean_candidate_texts(texts, seed_keyword=seed_keyword)

    def _clean_candidate_texts(self, texts: Iterable[str], seed_keyword: str) -> list[str]:
        seed_tokens = {token.lower() for token in seed_keyword.split() if len(token) > 2}
        cleaned_results: list[str] = []
        seen: set[str] = set()

        for text in texts:
            cleaned = " ".join(str(text).split())
            lowered = cleaned.lower()
            if not cleaned or lowered in seen:
                continue
            if len(cleaned) > 80:
                continue
            if seed_tokens and "esim" not in lowered and not any(token in lowered for token in seed_tokens):
                continue
            seen.add(lowered)
            cleaned_results.append(cleaned)

        return cleaned_results
