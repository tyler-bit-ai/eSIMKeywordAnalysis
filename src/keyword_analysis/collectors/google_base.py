"""Shared helpers for Playwright-based Google collection."""

from __future__ import annotations

import time
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Callable, TypeVar
from uuid import uuid4

from playwright.sync_api import Browser, BrowserContext, Error, Page, TimeoutError, sync_playwright

from keyword_analysis.config import load_collection_profile
from keyword_analysis.storage import CollectionRun, Storage


COLLECTOR_VERSION = "0.1.0"
T = TypeVar("T")


@dataclass(frozen=True)
class CollectorContext:
    run_id: str
    started_at_utc: str
    profile_name: str
    locale_gl: str
    language_hl: str
    login_state: str
    browser_profile: str
    device_class: str
    request_spacing_seconds: int
    retry_limit: int
    google_domain: str
    user_agent_mode: str
    viewport_width: int
    viewport_height: int


class GoogleCollectorBase:
    collector_name = "google_base"

    def __init__(self, storage: Storage, profile_name: str = "default_profile") -> None:
        profile = load_collection_profile(profile_name)
        self.storage = storage
        self.context = CollectorContext(
            run_id=str(uuid4()),
            started_at_utc=datetime.now(UTC).isoformat(),
            profile_name=profile_name,
            locale_gl=profile["locale_gl"],
            language_hl=profile["language_hl"],
            login_state=profile["login_state"],
            browser_profile=profile["user_agent_mode"],
            device_class=profile["device_class"],
            request_spacing_seconds=int(profile["request_spacing_seconds"]),
            retry_limit=int(profile["retry_limit"]),
            google_domain=profile["google_domain"],
            user_agent_mode=profile["user_agent_mode"],
            viewport_width=int(profile["viewport"]["width"]),
            viewport_height=int(profile["viewport"]["height"]),
        )

    def create_run_record(self, status: str = "started", notes: str = "") -> CollectionRun:
        return CollectionRun(
            run_id=self.context.run_id,
            started_at_utc=self.context.started_at_utc,
            collector_name=self.collector_name,
            profile_name=self.context.profile_name,
            locale_gl=self.context.locale_gl,
            language_hl=self.context.language_hl,
            login_state=self.context.login_state,
            browser_profile=self.context.browser_profile,
            device_class=self.context.device_class,
            status=status,
            notes=notes,
        )

    def build_google_url(self, query: str) -> str:
        encoded_query = query.replace(" ", "+")
        return (
            f"https://{self.context.google_domain}/search"
            f"?q={encoded_query}&hl={self.context.language_hl}&gl={self.context.locale_gl}&pws=0"
        )

    def _new_browser_context(self, browser: Browser) -> BrowserContext:
        return browser.new_context(
            locale="en-US",
            viewport={"width": self.context.viewport_width, "height": self.context.viewport_height},
        )

    def _with_page(self, handler: Callable[[Page], T]) -> T:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            context = self._new_browser_context(browser)
            page = context.new_page()
            try:
                return handler(page)
            finally:
                context.close()
                browser.close()

    def run_with_retries(self, handler: Callable[[Page], T]) -> T:
        attempts = 0
        last_error: Exception | None = None
        while attempts <= self.context.retry_limit:
            try:
                time.sleep(self.context.request_spacing_seconds)
                return self._with_page(handler)
            except (TimeoutError, Error) as error:
                attempts += 1
                last_error = error
        raise RuntimeError(f"{self.collector_name} failed after retries") from last_error

