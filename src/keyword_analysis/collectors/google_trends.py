"""Google Trends collection using public endpoints via pytrends."""

from __future__ import annotations

from datetime import UTC, datetime

from pytrends.request import TrendReq
from pytrends import exceptions as pytrends_exceptions

from keyword_analysis.collectors.google_base import COLLECTOR_VERSION, GoogleCollectorBase
from keyword_analysis.storage import Observation


class GoogleTrendsCollector(GoogleCollectorBase):
    collector_name = "google_trends"

    def collect_related_queries(self, seed_keyword: str) -> list[Observation]:
        self.storage.insert_run(self.create_run_record())
        try:
            trends = TrendReq(hl="en-US", tz=0, geo="US")
            trends.build_payload([seed_keyword], timeframe="today 12-m")
            related = trends.related_queries().get(seed_keyword, {})
        except pytrends_exceptions.ResponseError as error:
            self.storage.insert_run(self.create_run_record(status="failed", notes=str(error)))
            return []
        except Exception as error:
            self.storage.insert_run(self.create_run_record(status="failed", notes=str(error)))
            return []
        observed_at = datetime.now(UTC).isoformat()
        observations: list[Observation] = []

        for bucket_name in ("top", "rising"):
            frame = related.get(bucket_name)
            if frame is None:
                continue
            for index, record in enumerate(frame.to_dict("records"), start=1):
                text = str(record.get("query", "")).strip()
                if not text:
                    continue
                observations.append(
                    Observation(
                        run_id=self.context.run_id,
                        observed_at_utc=observed_at,
                        seed_keyword=seed_keyword,
                        query_keyword=seed_keyword,
                        signal_type="trends_related",
                        locale_gl=self.context.locale_gl,
                        language_hl=self.context.language_hl,
                        login_state=self.context.login_state,
                        browser_profile="pytrends",
                        device_class=self.context.device_class,
                        rank_position=index,
                        raw_text=text,
                        source_url="https://trends.google.com/trends/",
                        collector_version=COLLECTOR_VERSION,
                        notes=bucket_name,
                    )
                )

        self.storage.insert_observations(observations)
        self.storage.insert_run(self.create_run_record(status="completed"))
        return observations
