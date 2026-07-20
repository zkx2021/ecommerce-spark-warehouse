from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ADS_TABLES = (
    "ads_kpi_daily",
    "ads_sales_trend_daily",
    "ads_product_rank_daily",
    "ads_category_share_daily",
    "ads_user_profile_daily",
    "ads_funnel_daily",
)
REPORT_NAME = "quality-report.json"


@dataclass(frozen=True)
class RuleResult:
    name: str
    severity: str
    status: str
    message: str


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def _passed(name: str, severity: str, message: str) -> RuleResult:
    return RuleResult(name=name, severity=severity, status="passed", message=message)


def _failed(name: str, severity: str, message: str) -> RuleResult:
    return RuleResult(name=name, severity=severity, status="failed", message=message)


def _to_float(value: Any) -> float:
    return float(value or 0)


def _to_int(value: Any) -> int:
    return int(value or 0)


def _all_non_negative_rule(
    name: str,
    rows: list[dict[str, Any]],
    field: str,
    severity: str = "critical",
) -> RuleResult:
    if all(_to_float(row.get(field)) >= 0 for row in rows):
        return _passed(name, severity, f"{field} values are non-negative")
    return _failed(name, severity, f"{field} contains negative values")


def _all_rate_range_rule(
    name: str,
    rows: list[dict[str, Any]],
    field: str,
    severity: str = "critical",
) -> RuleResult:
    if all(0 <= _to_float(row.get(field)) <= 1 for row in rows):
        return _passed(name, severity, f"{field} values are within range")
    return _failed(name, severity, f"{field} contains out-of-range values")


def _check_file_has_rows(
    name: str,
    path: Path,
    severity: str = "critical",
) -> tuple[list[RuleResult], list[dict[str, Any]]]:
    try:
        rows = load_jsonl(path)
    except Exception as exc:
        return [_failed(name, severity, f"{path} is missing or unreadable: {exc}")], []
    if not rows:
        return [_failed(name, severity, f"{path} has no rows")], rows
    return [_passed(name, severity, f"{path} has {len(rows)} rows")], rows


def _range_rule(name: str, value: Any, minimum: float, maximum: float | None = None) -> RuleResult:
    numeric = _to_float(value)
    if numeric < minimum:
        return _failed(name, "critical", f"{numeric} is below {minimum}")
    if maximum is not None and numeric > maximum:
        return _failed(name, "critical", f"{numeric} is above {maximum}")
    return _passed(name, "critical", f"{numeric} is within range")


def _unique_positive_int_rule(name: str, rows: list[dict[str, Any]], field: str) -> RuleResult:
    values = [_to_int(row.get(field)) for row in rows]
    if any(value <= 0 for value in values):
        return _failed(name, "critical", f"{field} contains non-positive values")
    if len(values) != len(set(values)):
        return _failed(name, "critical", f"{field} contains duplicates")
    return _passed(name, "critical", f"{field} values are unique positive integers")


def _append_kpi_rules(rules: list[RuleResult], kpi_rows: list[dict[str, Any]]) -> None:
    if len(kpi_rows) != 1:
        rules.append(_failed("ads_kpi_daily_single_row", "critical", f"ads_kpi_daily has {len(kpi_rows)} rows"))
        return

    rules.append(_passed("ads_kpi_daily_single_row", "critical", "ads_kpi_daily has exactly one row"))
    kpi = kpi_rows[0]
    rules.extend(
        [
            _range_rule("ads_kpi_daily_sales_non_negative", kpi.get("total_sales_amount"), 0),
            _range_rule("ads_kpi_daily_order_count_positive", kpi.get("total_order_count"), 1),
            _range_rule("ads_kpi_daily_paid_user_count_non_negative", kpi.get("paid_user_count"), 0),
            _range_rule("ads_kpi_daily_avg_order_amount_non_negative", kpi.get("avg_order_amount"), 0),
            _range_rule("ads_kpi_daily_payment_conversion_rate_range", kpi.get("payment_conversion_rate"), 0, 1),
        ]
    )


def _append_product_rank_rules(rules: list[RuleResult], rank_rows: list[dict[str, Any]]) -> None:
    if not rank_rows:
        return

    rules.append(_range_rule("ads_product_rank_daily_row_count", len(rank_rows), 1, 10))
    rules.append(_unique_positive_int_rule("ads_product_rank_daily_rank_no_unique", rank_rows, "rank_no"))
    rules.append(
        _all_non_negative_rule("ads_product_rank_daily_sales_quantity_non_negative", rank_rows, "sales_quantity")
    )
    rules.append(_all_non_negative_rule("ads_product_rank_daily_sales_amount_non_negative", rank_rows, "sales_amount"))


def _append_category_rules(rules: list[RuleResult], category_rows: list[dict[str, Any]]) -> None:
    if not category_rows:
        return

    rules.append(
        _all_non_negative_rule("ads_category_share_daily_sales_quantity_non_negative", category_rows, "sales_quantity")
    )
    rules.append(
        _all_non_negative_rule("ads_category_share_daily_sales_amount_non_negative", category_rows, "sales_amount")
    )
    rules.append(_all_rate_range_rule("ads_category_share_daily_share_range", category_rows, "sales_share"))
    share_sum = sum(_to_float(row.get("sales_share")) for row in category_rows)
    if 0.95 <= share_sum <= 1.05:
        rules.append(_passed("ads_category_share_daily_share_sum_near_one", "warning", f"sales_share sum is {share_sum}"))
    else:
        rules.append(_failed("ads_category_share_daily_share_sum_near_one", "warning", f"sales_share sum is {share_sum}"))


def _append_funnel_rules(rules: list[RuleResult], funnel_rows: list[dict[str, Any]]) -> None:
    if not funnel_rows:
        return

    rules.append(_unique_positive_int_rule("ads_funnel_daily_stage_order_unique", funnel_rows, "stage_order"))
    rules.append(_all_non_negative_rule("ads_funnel_daily_stage_count_non_negative", funnel_rows, "stage_count"))
    rules.append(_all_rate_range_rule("ads_funnel_daily_conversion_rate_range", funnel_rows, "conversion_rate"))


def run_quality_checks(batch_date: str, processed_root: Path, ads_root: Path) -> dict[str, Any]:
    rules: list[RuleResult] = []
    processed_dir = processed_root / batch_date
    ads_dir = ads_root / batch_date

    for source in ("products", "carts", "users"):
        source_rules, _ = _check_file_has_rows(f"processed_{source}_non_empty", processed_dir / f"{source}.jsonl")
        rules.extend(source_rules)

    ads_rows: dict[str, list[dict[str, Any]]] = {}
    for table in ADS_TABLES:
        table_rules, rows = _check_file_has_rows(f"{table}_snapshot_non_empty", ads_dir / f"{table}.jsonl")
        rules.extend(table_rules)
        ads_rows[table] = rows

    _append_kpi_rules(rules, ads_rows.get("ads_kpi_daily", []))
    _append_product_rank_rules(rules, ads_rows.get("ads_product_rank_daily", []))
    _append_category_rules(rules, ads_rows.get("ads_category_share_daily", []))
    _append_funnel_rules(rules, ads_rows.get("ads_funnel_daily", []))

    failed_count = sum(1 for rule in rules if rule.status == "failed")
    failed_critical_count = sum(1 for rule in rules if rule.status == "failed" and rule.severity == "critical")
    return {
        "batch_date": batch_date,
        "status": "failed" if failed_critical_count else "passed",
        "checked_at": datetime.now(timezone.utc).astimezone().isoformat(),
        "summary": {
            "total_rules": len(rules),
            "passed": len(rules) - failed_count,
            "failed": failed_count,
            "failed_critical": failed_critical_count,
        },
        "rules": [asdict(rule) for rule in rules],
    }


def write_report(report: dict[str, Any], report_path: Path) -> None:
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run local ecommerce batch quality checks.")
    parser.add_argument("--batch-date", required=True)
    parser.add_argument("--processed-root", default="crawler/data/processed")
    parser.add_argument("--ads-root", default="warehouse/data/ads")
    parser.add_argument("--report-dir", required=True)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    report = run_quality_checks(args.batch_date, Path(args.processed_root), Path(args.ads_root))
    report_path = Path(args.report_dir) / REPORT_NAME
    write_report(report, report_path)
    print(f"Quality check {report['status']}. Report: {report_path}")
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
