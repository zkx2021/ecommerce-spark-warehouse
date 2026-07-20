import json
from pathlib import Path

import pytest

from warehouse.scripts import quality_check


def write_jsonl(path: Path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")


def write_valid_batch(tmp_path):
    processed = tmp_path / "processed"
    ads = tmp_path / "ads"
    for source in ("products", "carts", "users"):
        write_jsonl(
            processed / "2026-07-01" / f"{source}.jsonl",
            [{"id": 1, "batch_date": "2026-07-01"}],
        )

    write_jsonl(
        ads / "2026-07-01" / "ads_kpi_daily.jsonl",
        [
            {
                "date_id": "2026-07-01",
                "total_sales_amount": 100.0,
                "total_order_count": 2,
                "paid_user_count": 2,
                "avg_order_amount": 50.0,
                "payment_conversion_rate": 1.0,
            }
        ],
    )
    write_jsonl(ads / "2026-07-01" / "ads_sales_trend_daily.jsonl", [{"date_id": "2026-07-01"}])
    write_jsonl(
        ads / "2026-07-01" / "ads_product_rank_daily.jsonl",
        [
            {
                "date_id": "2026-07-01",
                "rank_no": 1,
                "sales_quantity": 2,
                "sales_amount": 100.0,
            }
        ],
    )
    write_jsonl(
        ads / "2026-07-01" / "ads_category_share_daily.jsonl",
        [
            {
                "date_id": "2026-07-01",
                "sales_quantity": 2,
                "sales_amount": 100.0,
                "sales_share": 1.0,
            }
        ],
    )
    write_jsonl(ads / "2026-07-01" / "ads_user_profile_daily.jsonl", [{"date_id": "2026-07-01"}])
    write_jsonl(
        ads / "2026-07-01" / "ads_funnel_daily.jsonl",
        [
            {
                "date_id": "2026-07-01",
                "stage_order": 1,
                "stage_count": 2,
                "conversion_rate": 1.0,
            }
        ],
    )
    return processed, ads


def test_load_jsonl_reads_rows_and_skips_blank_lines(tmp_path):
    path = tmp_path / "rows.jsonl"
    path.write_text('{"id": 1}\n\n{"id": 2}\n', encoding="utf-8")

    assert quality_check.load_jsonl(path) == [{"id": 1}, {"id": 2}]


def test_load_jsonl_raises_for_missing_file(tmp_path):
    with pytest.raises(FileNotFoundError):
        quality_check.load_jsonl(tmp_path / "missing.jsonl")


def test_run_quality_checks_passes_for_valid_batch(tmp_path):
    processed, ads = write_valid_batch(tmp_path)

    report = quality_check.run_quality_checks("2026-07-01", processed, ads)

    assert report["status"] == "passed"
    assert report["summary"]["failed"] == 0
    assert report["summary"]["total_rules"] == len(report["rules"])


def test_run_quality_checks_fails_for_negative_sales_amount(tmp_path):
    processed, ads = write_valid_batch(tmp_path)
    write_jsonl(
        ads / "2026-07-01" / "ads_kpi_daily.jsonl",
        [
            {
                "date_id": "2026-07-01",
                "total_sales_amount": -1.0,
                "total_order_count": 2,
                "paid_user_count": 2,
                "avg_order_amount": 50.0,
                "payment_conversion_rate": 1.0,
            }
        ],
    )

    report = quality_check.run_quality_checks("2026-07-01", processed, ads)

    assert report["status"] == "failed"
    assert any(
        rule["name"] == "ads_kpi_daily_sales_non_negative"
        for rule in report["rules"]
        if rule["status"] == "failed"
    )


def test_main_writes_report_and_returns_zero_for_valid_batch(tmp_path):
    processed, ads = write_valid_batch(tmp_path)
    report_dir = tmp_path / "report"

    exit_code = quality_check.main(
        [
            "--batch-date",
            "2026-07-01",
            "--processed-root",
            str(processed),
            "--ads-root",
            str(ads),
            "--report-dir",
            str(report_dir),
        ]
    )

    assert exit_code == 0
    report = json.loads((report_dir / "quality-report.json").read_text(encoding="utf-8"))
    assert report["status"] == "passed"


def test_warning_failure_does_not_fail_batch(tmp_path):
    processed, ads = write_valid_batch(tmp_path)
    write_jsonl(
        ads / "2026-07-01" / "ads_category_share_daily.jsonl",
        [
            {
                "date_id": "2026-07-01",
                "sales_quantity": 2,
                "sales_amount": 100.0,
                "sales_share": 0.5,
            }
        ],
    )

    report = quality_check.run_quality_checks("2026-07-01", processed, ads)

    assert report["status"] == "passed"
    assert any(rule["severity"] == "warning" and rule["status"] == "failed" for rule in report["rules"])
