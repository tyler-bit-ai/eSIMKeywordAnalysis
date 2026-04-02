from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pytest

from keyword_analysis.dashboard_data import publish_dashboard_snapshot_bundle


def test_publish_dashboard_snapshot_bundle_fails_when_manifest_references_missing_snapshot_payload(tmp_path: Path) -> None:
    report_dir = tmp_path / "reports_korea_focus"
    output_dir = tmp_path / "site_data"
    report_dir.mkdir(parents=True)
    output_dir.mkdir(parents=True)

    (output_dir / "dashboard_manifest.json").write_text(
        """
{
  "generated_at": "2026-03-18T04:35:05Z",
  "default_dataset_id": "snapshot-20260318T043505Z",
  "datasets": [
    {
      "dataset_id": "snapshot-20260318T043505Z",
      "label": "Snapshot 2026-03-18 04:35:05 UTC",
      "path": "snapshots/snapshot-20260318T043505Z.json",
      "generated_at": "2026-03-18T04:35:05Z",
      "source_report_dir": "outputs\\\\reports_korea_focus",
      "dataset_version": "v1",
      "has_previous_snapshot": false,
      "has_current_snapshot": false
    }
  ]
}
""".strip(),
        encoding="utf-8",
    )

    (report_dir / "ranked_keywords.csv").write_text(
        "\n".join(
            [
                "canonical_keyword,priority_score,keyword_bucket",
                "current keyword,15,core_stable",
            ]
        ),
        encoding="utf-8",
    )
    (report_dir / "cluster_summary.csv").write_text(
        "\n".join(
            [
                "keyword_family,keyword_bucket,keyword_count,avg_priority_score",
                "korea,core_stable,1,15",
            ]
        ),
        encoding="utf-8",
    )
    (report_dir / "korea_marketing_targets.csv").write_text(
        "\n".join(
            [
                "canonical_keyword,follow_on_modifier,marketing_priority,priority_score,keyword_bucket,observed_signals,origin_seeds,raw_variants,target_reason",
                "current keyword,root,high,15,core_stable,autocomplete,korea esim,current keyword,Observed from tests",
            ]
        ),
        encoding="utf-8",
    )

    with pytest.raises(FileNotFoundError, match="snapshot-20260318T043505Z.json"):
        publish_dashboard_snapshot_bundle(
            report_dir=report_dir,
            output_dir=output_dir,
            generated_at=datetime(2026, 4, 2, 4, 5, 6, tzinfo=UTC),
        )
