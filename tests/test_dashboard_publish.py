from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

from keyword_analysis.dashboard_data import (
    PublishedDashboardSpec,
    export_public_dashboard_bundle,
    export_public_dashboard_manifest,
    publish_dashboard_snapshot_bundle,
)


def test_export_public_dashboard_bundle_writes_expected_json(tmp_path: Path) -> None:
    report_dir = tmp_path / "reports_korea_focus"
    output_dir = tmp_path / "published_dashboard"
    report_dir.mkdir()

    (report_dir / "ranked_keywords.csv").write_text(
        "\n".join([
            "canonical_keyword,priority_score,keyword_bucket",
            "korea esim,15,core_stable",
            "best esim for korea,11,rising",
        ]),
        encoding="utf-8",
    )
    (report_dir / "cluster_summary.csv").write_text(
        "\n".join([
            "keyword_family,keyword_bucket,keyword_count,avg_priority_score",
            "korea esim,core_stable,1,15",
        ]),
        encoding="utf-8",
    )
    (report_dir / "korea_marketing_targets.csv").write_text(
        "\n".join([
            "canonical_keyword,follow_on_modifier,marketing_priority,priority_score,keyword_bucket,observed_signals,origin_seeds,raw_variants,target_reason",
            "korea esim,root,high,15,core_stable,\"autocomplete,trends_related\",\"korea esim,south korea esim\",\"korea esim | korea e sim\",Observed from tests",
            "best esim for korea,best,medium,11,rising,autocomplete,esim for korea,best esim for korea,Observed from tests",
        ]),
        encoding="utf-8",
    )

    output_path = export_public_dashboard_bundle(
        report_dir=report_dir,
        output_dir=output_dir,
        generated_at=datetime(2026, 3, 18, 1, 2, 3, tzinfo=UTC),
    )

    payload = json.loads(output_path.read_text(encoding="utf-8"))

    assert output_path.name == "dashboard_data.json"
    assert payload["generated_at"] == "2026-03-18T01:02:03Z"
    assert payload["source_report_dir"] == str(report_dir)
    assert payload["dataset_version"] == "v1"
    assert payload["help"]["score_rule"]["title"] == "How scoring works"
    assert payload["help"]["sections"][0]["id"] == "kpi"
    assert payload["kpis"]["high_priority_targets"] == 1
    assert payload["kpis"]["new_keywords"] == 0
    assert payload["target_table"][0]["observed_signals"] == ["autocomplete", "trends_related"]
    assert payload["target_table"][0]["origin_seeds"] == ["korea esim", "south korea esim"]
    assert payload["target_table"][0]["raw_variants"] == ["korea esim", "korea e sim"]
    assert payload["metadata"]["has_previous_snapshot"] is False
    assert payload["metadata"]["has_current_snapshot"] is False


def test_export_public_dashboard_bundle_handles_missing_reports(tmp_path: Path) -> None:
    report_dir = tmp_path / "missing_reports"

    output_path = export_public_dashboard_bundle(
        report_dir=report_dir,
        output_dir=tmp_path / "published_dashboard",
        generated_at=datetime(2026, 3, 18, 1, 2, 3, tzinfo=UTC),
    )

    payload = json.loads(output_path.read_text(encoding="utf-8"))

    assert payload["kpis"] == {
        "high_priority_targets": 0,
        "rising_keywords": 0,
        "new_keywords": 0,
        "manual_review_terms": 0,
        "tracked_targets": 0,
    }
    assert payload["target_table"] == []
    assert payload["modifier_summary"] == []
    assert payload["seed_lineage"] == []
    assert payload["signal_summary"] == []
    assert payload["snapshot_changes"] == {
        "new_keywords": [],
        "disappeared_keywords": [],
        "rank_changes": [],
        "bucket_changes": [],
    }


def test_export_public_dashboard_manifest_writes_manifest_and_default_bundle(tmp_path: Path) -> None:
    current_report_dir = tmp_path / "reports_current"
    baseline_report_dir = tmp_path / "reports_baseline"
    output_dir = tmp_path / "published_dashboard"
    current_report_dir.mkdir()
    baseline_report_dir.mkdir()

    for report_dir, keyword in (
        (current_report_dir, "korea esim"),
        (baseline_report_dir, "best esim for korea"),
    ):
        (report_dir / "ranked_keywords.csv").write_text(
            "\n".join([
                "canonical_keyword,priority_score,keyword_bucket",
                f"{keyword},15,core_stable",
            ]),
            encoding="utf-8",
        )
        (report_dir / "cluster_summary.csv").write_text(
            "\n".join([
                "keyword_family,keyword_bucket,keyword_count,avg_priority_score",
                "korea esim,core_stable,1,15",
            ]),
            encoding="utf-8",
        )
        (report_dir / "korea_marketing_targets.csv").write_text(
            "\n".join([
                "canonical_keyword,follow_on_modifier,marketing_priority,priority_score,keyword_bucket,observed_signals,origin_seeds,raw_variants,target_reason",
                f"{keyword},root,high,15,core_stable,autocomplete,korea esim,{keyword},Observed from tests",
            ]),
            encoding="utf-8",
        )

    manifest_path = export_public_dashboard_manifest(
        dataset_specs=[
            PublishedDashboardSpec(
                dataset_id="current",
                label="Current Crawl",
                report_dir=current_report_dir,
            ),
            PublishedDashboardSpec(
                dataset_id="baseline",
                label="Baseline Crawl",
                report_dir=baseline_report_dir,
                output_filename="baseline-snapshot.json",
            ),
        ],
        output_dir=output_dir,
        generated_at=datetime(2026, 3, 24, 0, 0, 0, tzinfo=UTC),
        default_dataset_id="baseline",
    )

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    default_payload = json.loads((output_dir / "dashboard_data.json").read_text(encoding="utf-8"))
    baseline_payload = json.loads((output_dir / "baseline-snapshot.json").read_text(encoding="utf-8"))

    assert manifest_path.name == "dashboard_manifest.json"
    assert manifest["default_dataset_id"] == "baseline"
    assert [entry["dataset_id"] for entry in manifest["datasets"]] == ["current", "baseline"]
    assert manifest["datasets"][0]["path"] == "current.json"
    assert manifest["datasets"][1]["path"] == "baseline-snapshot.json"
    assert manifest["datasets"][1]["source_report_dir"] == str(baseline_report_dir)
    assert default_payload["target_table"][0]["canonical_keyword"] == "best esim for korea"
    assert baseline_payload["target_table"][0]["canonical_keyword"] == "best esim for korea"


def test_publish_dashboard_snapshot_bundle_appends_snapshot_and_manifest(tmp_path: Path) -> None:
    report_dir = tmp_path / "reports_korea_focus"
    output_dir = tmp_path / "site_data"
    report_dir.mkdir()

    (report_dir / "ranked_keywords.csv").write_text(
        "\n".join([
            "canonical_keyword,priority_score,keyword_bucket",
            "korea esim,15,core_stable",
        ]),
        encoding="utf-8",
    )
    (report_dir / "cluster_summary.csv").write_text(
        "\n".join([
            "keyword_family,keyword_bucket,keyword_count,avg_priority_score",
            "korea esim,core_stable,1,15",
        ]),
        encoding="utf-8",
    )
    (report_dir / "korea_marketing_targets.csv").write_text(
        "\n".join([
            "canonical_keyword,follow_on_modifier,marketing_priority,priority_score,keyword_bucket,observed_signals,origin_seeds,raw_variants,target_reason",
            "korea esim,root,high,15,core_stable,autocomplete,korea esim,korea esim,Observed from tests",
        ]),
        encoding="utf-8",
    )

    first = publish_dashboard_snapshot_bundle(
        report_dir=report_dir,
        output_dir=output_dir,
        generated_at=datetime(2026, 4, 1, 1, 2, 3, tzinfo=UTC),
    )
    second = publish_dashboard_snapshot_bundle(
        report_dir=report_dir,
        output_dir=output_dir,
        generated_at=datetime(2026, 4, 2, 4, 5, 6, tzinfo=UTC),
    )

    manifest = json.loads(first.manifest_path.read_text(encoding="utf-8"))
    latest_payload = json.loads(first.dashboard_data_path.read_text(encoding="utf-8"))

    assert first.snapshot_path.name == "snapshot-20260401T010203Z.json"
    assert second.snapshot_path.name == "snapshot-20260402T040506Z.json"
    assert manifest["default_dataset_id"] == "snapshot-20260402T040506Z"
    assert len(manifest["datasets"]) == 2
    assert manifest["datasets"][0]["path"] == "snapshots/snapshot-20260402T040506Z.json"
    assert manifest["datasets"][1]["path"] == "snapshots/snapshot-20260401T010203Z.json"
    assert latest_payload["generated_at"] == "2026-04-02T04:05:06Z"


def test_publish_dashboard_snapshot_bundle_preserves_existing_snapshot_payloads(tmp_path: Path) -> None:
    report_dir = tmp_path / "reports_korea_focus"
    output_dir = tmp_path / "site_data"
    snapshot_dir = output_dir / "snapshots"
    report_dir.mkdir(parents=True)
    snapshot_dir.mkdir(parents=True)

    legacy_payload = {
        "generated_at": "2026-03-18T04:35:05Z",
        "source_report_dir": "outputs\\reports_korea_focus",
        "dataset_version": "v1",
        "help": {"score_rule": {}, "sections": []},
        "kpis": {"high_priority_targets": 1, "rising_keywords": 0, "new_keywords": 0, "manual_review_terms": 0, "tracked_targets": 1},
        "target_table": [{"canonical_keyword": "legacy keyword"}],
        "modifier_summary": [],
        "seed_lineage": [],
        "signal_summary": [],
        "snapshot_changes": {
            "new_keywords": [],
            "disappeared_keywords": [],
            "rank_changes": [],
            "bucket_changes": [],
        },
        "metadata": {"has_previous_snapshot": False, "has_current_snapshot": False, "notes": []},
    }
    (snapshot_dir / "snapshot-20260318T043505Z.json").write_text(json.dumps(legacy_payload), encoding="utf-8")
    (output_dir / "dashboard_manifest.json").write_text(
        json.dumps(
            {
                "generated_at": "2026-03-18T04:35:05Z",
                "default_dataset_id": "snapshot-20260318T043505Z",
                "datasets": [
                    {
                        "dataset_id": "snapshot-20260318T043505Z",
                        "label": "Snapshot 2026-03-18 04:35:05 UTC",
                        "path": "snapshots/snapshot-20260318T043505Z.json",
                        "generated_at": "2026-03-18T04:35:05Z",
                        "source_report_dir": "outputs\\reports_korea_focus",
                        "dataset_version": "v1",
                        "has_previous_snapshot": False,
                        "has_current_snapshot": False,
                    }
                ],
            }
        ),
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

    publish_dashboard_snapshot_bundle(
        report_dir=report_dir,
        output_dir=output_dir,
        generated_at=datetime(2026, 4, 2, 4, 5, 6, tzinfo=UTC),
    )

    preserved_payload = json.loads((snapshot_dir / "snapshot-20260318T043505Z.json").read_text(encoding="utf-8"))

    assert preserved_payload["target_table"][0]["canonical_keyword"] == "legacy keyword"
