from __future__ import annotations

from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from keyword_analysis.dashboard_help import SECTION_SPECS, build_help_payload
from keyword_analysis.pipeline import refresh_korea_dashboard_dataset
from keyword_analysis.scoring import (
    CORE_STABLE_SCORE_THRESHOLD,
    CORE_STABLE_SIGNAL_COUNT,
    HIGH_PRIORITY_THRESHOLD,
    MEDIUM_PRIORITY_THRESHOLD,
    RISING_SCORE_THRESHOLD,
    RISING_SIGNAL,
    SIGNAL_WEIGHTS,
)


class DashboardHelpTests(unittest.TestCase):
    def test_help_payload_uses_scoring_constants(self) -> None:
        payload = build_help_payload()
        score_rule = payload["score_rule"]

        self.assertEqual(score_rule.signal_weights, SIGNAL_WEIGHTS)
        self.assertIn(f"high: priority_score >= {HIGH_PRIORITY_THRESHOLD}", score_rule.marketing_priority_rules)
        self.assertIn(
            f"medium: priority_score >= {MEDIUM_PRIORITY_THRESHOLD} and < {HIGH_PRIORITY_THRESHOLD}",
            score_rule.marketing_priority_rules,
        )
        self.assertIn(
            f"core_stable: signal_count >= {CORE_STABLE_SIGNAL_COUNT} and priority_score >= {CORE_STABLE_SCORE_THRESHOLD}",
            score_rule.bucket_rules,
        )
        self.assertIn(
            f"rising: evidence_signals includes {RISING_SIGNAL} and priority_score >= {RISING_SCORE_THRESHOLD}",
            score_rule.bucket_rules,
        )

    def test_dashboard_uses_registered_section_ids(self) -> None:
        source = Path("src/keyword_analysis/dashboard.py").read_text(encoding="utf-8")

        for spec in SECTION_SPECS:
            self.assertIn(f'get_section_spec("{spec.id}")', source)


class RefreshPipelineTests(unittest.TestCase):
    @patch("keyword_analysis.pipeline.Storage")
    @patch("keyword_analysis.pipeline.export_reports")
    @patch("keyword_analysis.pipeline.rebuild_keyword_metadata")
    @patch("keyword_analysis.pipeline.collect_korea_focus_seed_set")
    def test_refresh_pipeline_returns_expected_artifacts(
        self,
        collect_mock,
        rebuild_mock,
        export_mock,
        storage_mock,
    ) -> None:
        rebuild_mock.return_value = (11, 19)

        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            database_path = root / "keyword.sqlite3"
            report_dir = root / "reports_korea_focus"
            collection_dir = root / "reports"

            export_mock.return_value = {
                "ranked_keywords": report_dir / "ranked_keywords.csv",
                "cluster_summary": report_dir / "cluster_summary.csv",
                "korea_marketing_targets": report_dir / "korea_marketing_targets.csv",
                "report_summary": report_dir / "report_summary.md",
            }

            artifacts = refresh_korea_dashboard_dataset(
                database_path=database_path,
                report_dir=report_dir,
                collection_export_dir=collection_dir,
                seed_limit=None,
            )

        storage_mock.assert_called_once_with(database_path)
        collect_mock.assert_called_once_with(
            limit=None,
            database_path=database_path,
            export_dir=collection_dir,
        )
        export_mock.assert_called_once_with(output_dir=report_dir, database_path=database_path)
        self.assertEqual(artifacts.normalized_keyword_count, 11)
        self.assertEqual(artifacts.intent_assignment_count, 19)
        self.assertEqual(artifacts.ranked_keywords.name, "ranked_keywords.csv")
        self.assertEqual(artifacts.cluster_summary.name, "cluster_summary.csv")
        self.assertEqual(artifacts.korea_marketing_targets.name, "korea_marketing_targets.csv")
        self.assertEqual(artifacts.report_summary.name, "report_summary.md")


if __name__ == "__main__":
    unittest.main()
