# Quality Check Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a `quality_check` stage that validates local ecommerce batch outputs without cleaning or modifying data.

**Architecture:** A Python checker reads processed crawler files and ADS JSONL snapshots, evaluates deterministic critical and warning rules, and writes `quality-report.json`. A PowerShell wrapper runs the checker, and the offline batch runner executes `quality_check` after `mysql_export` and before `smoke_test`.

**Tech Stack:** Python standard library, pytest, PowerShell, existing local JSONL artifacts, existing offline batch runner.

## Global Constraints

- Every implementation task starts only after the user explicitly sends the matching `Task N` command.
- Use the name `quality_check` for stage names, scripts, logs, and docs.
- `quality_check` validates data only; it must not clean, modify, rewrite, or auto-fix data.
- The offline batch order becomes `crawler`, `ods_check`, `ods_ddl`, `ods_load`, `dwd`, `ads`, `mysql_export`, `quality_check`, `smoke_test`.
- `quality_check` runs after `mysql_export` and before `smoke_test`.
- `quality-report.json` is written under the offline batch run directory when the runner invokes the stage.
- Critical rule failures exit non-zero; warning rule failures appear in the report but do not fail the batch.
- Generated logs, reports, crawler data, and ADS data must not be committed.
- Keep `architecture-options.html` unrelated and unstaged.

---

## File Structure

- Create `warehouse/scripts/quality_check.py`: JSONL loader, rule engine, report writer, CLI, and exit code behavior.
- Create `warehouse/scripts/run_quality_check.ps1`: PowerShell wrapper around the Python checker.
- Create `warehouse/tests/test_quality_check.py`: unit tests for checker behavior.
- Create or extend `warehouse/tests/test_quality_check_assets.py`: static tests for wrapper, runner integration, docs, and foundation checks.
- Modify `warehouse/scripts/run_offline_batch.ps1`: add `quality_check` stage, log name, stage reference, and command.
- Modify `deploy/scripts/check.ps1`: require checker and wrapper assets and assert runner integration.
- Modify `warehouse/README.md`: document standalone and runner usage.
- Modify `docs/deployment-integration.md`: document report inspection and failed quality handling.

---

### Task 1: Quality Checker Core And Unit Tests

**Files:**
- Create: `warehouse/scripts/quality_check.py`
- Create: `warehouse/tests/test_quality_check.py`

**Interfaces:**
- Produces:
  - `load_jsonl(path: Path) -> list[dict[str, Any]]`
  - `RuleResult(name: str, severity: str, status: str, message: str)`
  - `run_quality_checks(batch_date: str, processed_root: Path, ads_root: Path) -> dict[str, Any]`
  - `write_report(report: dict[str, Any], report_path: Path) -> None`
  - `main(argv: list[str] | None = None) -> int`

- [ ] **Step 1: Write failing tests for JSONL loading and missing files**

Create `warehouse/tests/test_quality_check.py`:

```python
import json
from pathlib import Path

import pytest

from warehouse.scripts import quality_check


def write_jsonl(path: Path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")


def test_load_jsonl_reads_rows_and_skips_blank_lines(tmp_path):
    path = tmp_path / "rows.jsonl"
    path.write_text('{"id": 1}\n\n{"id": 2}\n', encoding="utf-8")

    assert quality_check.load_jsonl(path) == [{"id": 1}, {"id": 2}]


def test_load_jsonl_raises_for_missing_file(tmp_path):
    with pytest.raises(FileNotFoundError):
        quality_check.load_jsonl(tmp_path / "missing.jsonl")
```

Run:

```powershell
python -m pytest warehouse/tests/test_quality_check.py -q
```

Expected: FAIL because `warehouse/scripts/quality_check.py` does not exist.

- [ ] **Step 2: Add minimal module and JSONL loader**

Create `warehouse/scripts/quality_check.py`:

```python
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
```

Run:

```powershell
python -m pytest warehouse/tests/test_quality_check.py -q
```

Expected: PASS for the initial loader tests.

- [ ] **Step 3: Add tests for passing report and critical failures**

Append:

```python
def write_valid_batch(tmp_path):
    processed = tmp_path / "processed"
    ads = tmp_path / "ads"
    for source in ("products", "carts", "users"):
        write_jsonl(processed / "2026-07-01" / f"{source}.jsonl", [{"id": 1, "batch_date": "2026-07-01"}])

    write_jsonl(ads / "2026-07-01" / "ads_kpi_daily.jsonl", [{
        "date_id": "2026-07-01",
        "total_sales_amount": 100.0,
        "total_order_count": 2,
        "paid_user_count": 2,
        "avg_order_amount": 50.0,
        "payment_conversion_rate": 1.0,
    }])
    write_jsonl(ads / "2026-07-01" / "ads_sales_trend_daily.jsonl", [{"date_id": "2026-07-01"}])
    write_jsonl(ads / "2026-07-01" / "ads_product_rank_daily.jsonl", [{
        "date_id": "2026-07-01",
        "rank_no": 1,
        "sales_quantity": 2,
        "sales_amount": 100.0,
    }])
    write_jsonl(ads / "2026-07-01" / "ads_category_share_daily.jsonl", [{
        "date_id": "2026-07-01",
        "sales_quantity": 2,
        "sales_amount": 100.0,
        "sales_share": 1.0,
    }])
    write_jsonl(ads / "2026-07-01" / "ads_user_profile_daily.jsonl", [{"date_id": "2026-07-01"}])
    write_jsonl(ads / "2026-07-01" / "ads_funnel_daily.jsonl", [{
        "date_id": "2026-07-01",
        "stage_order": 1,
        "stage_count": 2,
        "conversion_rate": 1.0,
    }])
    return processed, ads


def test_run_quality_checks_passes_for_valid_batch(tmp_path):
    processed, ads = write_valid_batch(tmp_path)

    report = quality_check.run_quality_checks("2026-07-01", processed, ads)

    assert report["status"] == "passed"
    assert report["summary"]["failed"] == 0
    assert report["summary"]["total_rules"] == len(report["rules"])


def test_run_quality_checks_fails_for_negative_sales_amount(tmp_path):
    processed, ads = write_valid_batch(tmp_path)
    write_jsonl(ads / "2026-07-01" / "ads_kpi_daily.jsonl", [{
        "date_id": "2026-07-01",
        "total_sales_amount": -1.0,
        "total_order_count": 2,
        "paid_user_count": 2,
        "avg_order_amount": 50.0,
        "payment_conversion_rate": 1.0,
    }])

    report = quality_check.run_quality_checks("2026-07-01", processed, ads)

    assert report["status"] == "failed"
    assert any(rule["name"] == "ads_kpi_daily_sales_non_negative" for rule in report["rules"] if rule["status"] == "failed")
```

Run:

```powershell
python -m pytest warehouse/tests/test_quality_check.py -q
```

Expected: FAIL because `run_quality_checks` is not implemented.

- [ ] **Step 4: Implement rule engine**

Add helper functions and `run_quality_checks`:

```python
def _passed(name: str, severity: str, message: str) -> RuleResult:
    return RuleResult(name=name, severity=severity, status="passed", message=message)


def _failed(name: str, severity: str, message: str) -> RuleResult:
    return RuleResult(name=name, severity=severity, status="failed", message=message)


def _to_float(value: Any) -> float:
    return float(value or 0)


def _to_int(value: Any) -> int:
    return int(value or 0)


def _check_file_has_rows(name: str, path: Path, severity: str = "critical") -> tuple[list[RuleResult], list[dict[str, Any]]]:
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

    kpi_rows = ads_rows.get("ads_kpi_daily", [])
    if len(kpi_rows) == 1:
        rules.append(_passed("ads_kpi_daily_single_row", "critical", "ads_kpi_daily has exactly one row"))
        kpi = kpi_rows[0]
        rules.extend([
            _range_rule("ads_kpi_daily_sales_non_negative", kpi.get("total_sales_amount"), 0),
            _range_rule("ads_kpi_daily_order_count_positive", kpi.get("total_order_count"), 1),
            _range_rule("ads_kpi_daily_paid_user_count_non_negative", kpi.get("paid_user_count"), 0),
            _range_rule("ads_kpi_daily_avg_order_amount_non_negative", kpi.get("avg_order_amount"), 0),
            _range_rule("ads_kpi_daily_payment_conversion_rate_range", kpi.get("payment_conversion_rate"), 0, 1),
        ])
    else:
        rules.append(_failed("ads_kpi_daily_single_row", "critical", f"ads_kpi_daily has {len(kpi_rows)} rows"))

    rank_rows = ads_rows.get("ads_product_rank_daily", [])
    if rank_rows:
        rules.append(_range_rule("ads_product_rank_daily_row_count", len(rank_rows), 1, 10))
        rules.append(_unique_positive_int_rule("ads_product_rank_daily_rank_no_unique", rank_rows, "rank_no"))
        for field in ("sales_quantity", "sales_amount"):
            rules.append(_passed(f"ads_product_rank_daily_{field}_non_negative", "critical", f"{field} values are non-negative") if all(_to_float(row.get(field)) >= 0 for row in rank_rows) else _failed(f"ads_product_rank_daily_{field}_non_negative", "critical", f"{field} contains negative values"))

    category_rows = ads_rows.get("ads_category_share_daily", [])
    if category_rows:
        for field in ("sales_quantity", "sales_amount"):
            rules.append(_passed(f"ads_category_share_daily_{field}_non_negative", "critical", f"{field} values are non-negative") if all(_to_float(row.get(field)) >= 0 for row in category_rows) else _failed(f"ads_category_share_daily_{field}_non_negative", "critical", f"{field} contains negative values"))
        rules.append(_passed("ads_category_share_daily_share_range", "critical", "sales_share values are within range") if all(0 <= _to_float(row.get("sales_share")) <= 1 for row in category_rows) else _failed("ads_category_share_daily_share_range", "critical", "sales_share contains out-of-range values"))
        share_sum = sum(_to_float(row.get("sales_share")) for row in category_rows)
        rules.append(_passed("ads_category_share_daily_share_sum_near_one", "warning", f"sales_share sum is {share_sum}") if 0.95 <= share_sum <= 1.05 else _failed("ads_category_share_daily_share_sum_near_one", "warning", f"sales_share sum is {share_sum}"))

    funnel_rows = ads_rows.get("ads_funnel_daily", [])
    if funnel_rows:
        rules.append(_unique_positive_int_rule("ads_funnel_daily_stage_order_unique", funnel_rows, "stage_order"))
        rules.append(_passed("ads_funnel_daily_stage_count_non_negative", "critical", "stage_count values are non-negative") if all(_to_float(row.get("stage_count")) >= 0 for row in funnel_rows) else _failed("ads_funnel_daily_stage_count_non_negative", "critical", "stage_count contains negative values"))
        rules.append(_passed("ads_funnel_daily_conversion_rate_range", "critical", "conversion_rate values are within range") if all(0 <= _to_float(row.get("conversion_rate")) <= 1 for row in funnel_rows) else _failed("ads_funnel_daily_conversion_rate_range", "critical", "conversion_rate contains out-of-range values"))

    failed_critical = [rule for rule in rules if rule.status == "failed" and rule.severity == "critical"]
    report_rules = [asdict(rule) for rule in rules]
    failed_count = sum(1 for rule in rules if rule.status == "failed")
    return {
        "batch_date": batch_date,
        "status": "failed" if failed_critical else "passed",
        "checked_at": datetime.now(timezone.utc).astimezone().isoformat(),
        "summary": {
            "total_rules": len(rules),
            "passed": len(rules) - failed_count,
            "failed": failed_count,
        },
        "rules": report_rules,
    }
```

Run:

```powershell
python -m pytest warehouse/tests/test_quality_check.py -q
```

Expected: PASS.

- [ ] **Step 5: Add CLI and report tests**

Append:

```python
def test_main_writes_report_and_returns_zero_for_valid_batch(tmp_path):
    processed, ads = write_valid_batch(tmp_path)
    report_dir = tmp_path / "report"

    exit_code = quality_check.main([
        "--batch-date", "2026-07-01",
        "--processed-root", str(processed),
        "--ads-root", str(ads),
        "--report-dir", str(report_dir),
    ])

    assert exit_code == 0
    report = json.loads((report_dir / "quality-report.json").read_text(encoding="utf-8"))
    assert report["status"] == "passed"


def test_warning_failure_does_not_fail_batch(tmp_path):
    processed, ads = write_valid_batch(tmp_path)
    write_jsonl(ads / "2026-07-01" / "ads_category_share_daily.jsonl", [{
        "date_id": "2026-07-01",
        "sales_quantity": 2,
        "sales_amount": 100.0,
        "sales_share": 0.5,
    }])

    report = quality_check.run_quality_checks("2026-07-01", processed, ads)

    assert report["status"] == "passed"
    assert any(rule["severity"] == "warning" and rule["status"] == "failed" for rule in report["rules"])
```

Run:

```powershell
python -m pytest warehouse/tests/test_quality_check.py -q
```

Expected: FAIL until CLI is implemented.

- [ ] **Step 6: Implement CLI and report writer**

Add:

```python
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
    report_path = Path(args.report_dir) / "quality-report.json"
    write_report(report, report_path)
    print(f"Quality check {report['status']}. Report: {report_path}")
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
```

Run:

```powershell
python -m pytest warehouse/tests/test_quality_check.py -q
```

Expected: PASS.

- [ ] **Step 7: Commit**

Run:

```powershell
git add warehouse/scripts/quality_check.py warehouse/tests/test_quality_check.py
git commit -m "feat: add local quality check rules"
```

---

### Task 2: PowerShell Wrapper And Foundation Checks

**Files:**
- Create: `warehouse/scripts/run_quality_check.ps1`
- Create: `warehouse/tests/test_quality_check_assets.py`
- Modify: `deploy/scripts/check.ps1`

**Interfaces:**
- Consumes: `warehouse/scripts/quality_check.py` CLI from Task 1.
- Produces: `run_quality_check.ps1` with parameters `-BatchDate`, `-ReportDir`, `-ProcessedRoot`, and `-AdsRoot`.

- [ ] **Step 1: Write failing static tests**

Create `warehouse/tests/test_quality_check_assets.py`:

```python
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
WRAPPER = PROJECT_ROOT / "warehouse" / "scripts" / "run_quality_check.ps1"
CHECKER = PROJECT_ROOT / "warehouse" / "scripts" / "quality_check.py"
FOUNDATION_CHECK = PROJECT_ROOT / "deploy" / "scripts" / "check.ps1"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8").lower()


def test_quality_check_wrapper_exists_and_calls_python_checker():
    script = _read(WRAPPER)

    assert "param(" in script
    assert "$batchdate" in script
    assert "$reportdir" in script
    assert "$processedroot" in script
    assert "$adsroot" in script
    assert "quality_check.py" in script
    assert "--batch-date" in script
    assert "--report-dir" in script


def test_foundation_check_includes_quality_check_assets():
    check = _read(FOUNDATION_CHECK)

    assert "warehouse/scripts/quality_check.py" in check
    assert "warehouse/scripts/run_quality_check.ps1" in check
    assert "quality-report.json" in check


def test_quality_checker_mentions_validation_not_cleaning():
    checker = _read(CHECKER)

    assert "quality" in checker
    assert "clean" not in checker
```

Run:

```powershell
python -m pytest warehouse/tests/test_quality_check_assets.py -q
```

Expected: FAIL because wrapper and foundation checks do not exist yet.

- [ ] **Step 2: Create wrapper**

Create `warehouse/scripts/run_quality_check.ps1`:

```powershell
param(
  [Parameter(Mandatory = $true)]
  [ValidatePattern('^\d{4}-\d{2}-\d{2}$')]
  [string]$BatchDate,

  [string]$ReportDir = "",

  [string]$ProcessedRoot = "crawler/data/processed",

  [string]$AdsRoot = "warehouse/data/ads"
)

$ErrorActionPreference = "Stop"

$projectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$checker = Join-Path $projectRoot "warehouse\scripts\quality_check.py"

if (-not (Test-Path -LiteralPath $checker)) {
  throw "Missing quality checker path: $checker"
}

if ([string]::IsNullOrWhiteSpace($ReportDir)) {
  $ReportDir = Join-Path $projectRoot (Join-Path "logs\quality-check" $BatchDate)
}

Push-Location $projectRoot
try {
  python $checker `
    --batch-date $BatchDate `
    --processed-root $ProcessedRoot `
    --ads-root $AdsRoot `
    --report-dir $ReportDir

  if ($LASTEXITCODE -ne 0) {
    throw "Quality check failed for batch date $BatchDate. Report directory: $ReportDir"
  }
}
finally {
  Pop-Location
}

Write-Host "Quality check completed for batch date $BatchDate. Report directory: $ReportDir"
```

- [ ] **Step 3: Update foundation check**

Modify `deploy/scripts/check.ps1`:

```powershell
$requiredPaths = @(
  ...
  "warehouse/scripts/quality_check.py",
  "warehouse/scripts/run_quality_check.ps1",
  ...
)
```

Add:

```powershell
Assert-FileContains "warehouse/scripts/run_quality_check.ps1" "quality_check.py" "quality check wrapper calls Python checker"
Assert-FileContains "warehouse/scripts/quality_check.py" "quality-report.json" "quality checker writes report"
```

- [ ] **Step 4: Run tests**

Run:

```powershell
python -m pytest warehouse/tests/test_quality_check_assets.py -q
powershell -ExecutionPolicy Bypass -File deploy/scripts/check.ps1
```

Expected: PASS.

- [ ] **Step 5: Commit**

Run:

```powershell
git add warehouse/scripts/run_quality_check.ps1 warehouse/tests/test_quality_check_assets.py deploy/scripts/check.ps1
git commit -m "feat: add quality check wrapper"
```

---

### Task 3: Offline Batch Runner Integration

**Files:**
- Modify: `warehouse/scripts/run_offline_batch.ps1`
- Modify: `warehouse/tests/test_offline_batch_assets.py`
- Modify: `warehouse/tests/test_quality_check_assets.py`
- Modify: `deploy/scripts/check.ps1` if needed.

**Interfaces:**
- Consumes: `run_quality_check.ps1`.
- Produces: `quality_check` stage between `mysql_export` and `smoke_test`.

- [ ] **Step 1: Write failing integration tests**

Modify `EXPECTED_STAGES` in `warehouse/tests/test_offline_batch_assets.py`:

```python
EXPECTED_STAGES = [
    "crawler",
    "ods_check",
    "ods_ddl",
    "ods_load",
    "dwd",
    "ads",
    "mysql_export",
    "quality_check",
    "smoke_test",
]
```

Add to `warehouse/tests/test_quality_check_assets.py`:

```python
RUNNER = PROJECT_ROOT / "warehouse" / "scripts" / "run_offline_batch.ps1"


def test_offline_batch_runner_places_quality_check_before_smoke_test():
    runner = _read(RUNNER)

    assert "'mysql_export', 'quality_check', 'smoke_test'" in runner
    assert "quality_check.log" in runner
    assert "warehouse/scripts/run_quality_check.ps1" in runner.replace("\\", "/")
```

Run:

```powershell
python -m pytest warehouse/tests/test_offline_batch_assets.py warehouse/tests/test_quality_check_assets.py -q
```

Expected: FAIL until runner integration is implemented.

- [ ] **Step 2: Update runner parameters and stage metadata**

Modify `warehouse/scripts/run_offline_batch.ps1`:

```powershell
[ValidateSet('crawler', 'ods_check', 'ods_ddl', 'ods_load', 'dwd', 'ads', 'mysql_export', 'quality_check', 'smoke_test')]
```

Apply to both `StartFrom` and `SkipStages`.

Update:

```powershell
$StageOrder = @('crawler', 'ods_check', 'ods_ddl', 'ods_load', 'dwd', 'ads', 'mysql_export', 'quality_check', 'smoke_test')
```

Add:

```powershell
quality_check = 'quality_check.log'
```

and:

```powershell
quality_check = 'warehouse/scripts/run_quality_check.ps1'
```

- [ ] **Step 3: Add quality command mapping**

In `Get-StageCommand`, add:

```powershell
"quality_check" {
  return @{
    FilePath = "powershell"
    Arguments = @(
      "-ExecutionPolicy", "Bypass",
      "-File", "warehouse/scripts/run_quality_check.ps1",
      "-BatchDate", $BatchDate,
      "-ReportDir", $RunDir
    )
  }
}
```

To support this, add `[string]$RunDir` to `Get-StageCommand` parameters and pass it from the main loop:

```powershell
$command = Get-StageCommand -Stage $stage -ProjectRoot $projectRoot -BatchDate $BatchDate -BackendBaseUrl $BackendBaseUrl -FrontendBaseUrl $FrontendBaseUrl -RunDir $runDir
```

- [ ] **Step 4: Run tests and checks**

Run:

```powershell
python -m pytest warehouse/tests/test_offline_batch_assets.py warehouse/tests/test_quality_check_assets.py -q
powershell -ExecutionPolicy Bypass -File deploy/scripts/check.ps1
```

Expected: PASS except documentation assertions that Task 4 owns.

- [ ] **Step 5: Commit**

Run:

```powershell
git add warehouse/scripts/run_offline_batch.ps1 warehouse/tests/test_offline_batch_assets.py warehouse/tests/test_quality_check_assets.py deploy/scripts/check.ps1
git commit -m "feat: add quality check to offline batch"
```

---

### Task 4: Documentation Updates

**Files:**
- Modify: `warehouse/README.md`
- Modify: `docs/deployment-integration.md`
- Modify: `warehouse/tests/test_quality_check_assets.py`

**Interfaces:**
- Consumes: quality checker and runner integration.
- Produces: user-facing docs that distinguish quality checking from cleaning.

- [ ] **Step 1: Add failing docs test**

Add to `warehouse/tests/test_quality_check_assets.py`:

```python
WAREHOUSE_README = PROJECT_ROOT / "warehouse" / "README.md"
DEPLOYMENT_DOC = PROJECT_ROOT / "docs" / "deployment-integration.md"


def test_docs_explain_quality_check_is_not_cleaning():
    docs = _read(WAREHOUSE_README) + "\n" + _read(DEPLOYMENT_DOC)

    assert "quality_check" in docs
    assert "quality-report.json" in docs
    assert "not data cleaning" in docs
    assert "does not modify data" in docs
```

Run:

```powershell
python -m pytest warehouse/tests/test_quality_check_assets.py::test_docs_explain_quality_check_is_not_cleaning -q
```

Expected: FAIL until docs are updated.

- [ ] **Step 2: Update warehouse README**

Add a section after "One-Command Offline Batch":

~~~markdown
## Quality Check

`quality_check` is not data cleaning. It validates local batch outputs and does not modify data.

The standalone command is:

```powershell
powershell -ExecutionPolicy Bypass -File warehouse/scripts/run_quality_check.ps1 -BatchDate 2026-07-01
```

The offline runner executes `quality_check` after `mysql_export` and before `smoke_test`.
If a critical rule fails, the runner stops before the dashboard smoke test.

Inspect `quality-report.json` in the run log directory first when a quality check fails.
Warning rules appear in the report but do not fail the batch.
~~~

- [ ] **Step 3: Update deployment integration doc**

Add under the strict batch section:

~~~markdown
The `quality_check` stage validates data and is not data cleaning. It does not modify data.
It writes `quality-report.json` beside the offline batch logs. If the stage fails, inspect the report before presenting the dashboard.
~~~

- [ ] **Step 4: Run docs tests**

Run:

```powershell
python -m pytest warehouse/tests/test_quality_check_assets.py -q
powershell -ExecutionPolicy Bypass -File deploy/scripts/check.ps1
```

Expected: PASS.

- [ ] **Step 5: Commit**

Run:

```powershell
git add warehouse/README.md docs/deployment-integration.md warehouse/tests/test_quality_check_assets.py
git commit -m "docs: document quality check stage"
```

---

### Task 5: Full Verification, Push, And PR

**Files:**
- No planned implementation files unless verification exposes a blocker.

**Interfaces:**
- Consumes: completed `quality_check` stage.
- Produces: ready PR against `main`.

- [ ] **Step 1: Run local test suites**

Run:

```powershell
python -m pytest warehouse/tests warehouse/spark/tests -q
powershell -ExecutionPolicy Bypass -File deploy/scripts/check.ps1
```

Expected: PASS.

- [ ] **Step 2: Run standalone quality check**

Run:

```powershell
powershell -ExecutionPolicy Bypass -File warehouse/scripts/run_quality_check.ps1 -BatchDate 2026-07-01
```

Expected: PASS and writes `logs/quality-check/2026-07-01/quality-report.json`.

- [ ] **Step 3: Run offline batch with quality stage**

Run:

```powershell
powershell -ExecutionPolicy Bypass -File warehouse/scripts/run_offline_batch.ps1 -BatchDate 2026-07-01 -SkipStages crawler
```

Expected: PASS, with `quality_check` stage `success` and `quality-report.json` in the offline batch run directory.

- [ ] **Step 4: Confirm generated outputs remain untracked**

Run:

```powershell
git status --short --branch
```

Expected: only intentional source changes are present. Generated logs, reports, `crawler/data/`, `warehouse/data/`, and unrelated `architecture-options.html` must remain untracked or ignored.

- [ ] **Step 5: Push branch**

Run:

```powershell
git -c http.proxy=http://127.0.0.1:7897 -c https.proxy=http://127.0.0.1:7897 push -u origin codex/quality-check
```

Expected: branch is pushed.

- [ ] **Step 6: Create PR**

Create a ready PR against `main`:

```markdown
## Summary

- Add standalone `quality_check` validation for local processed and ADS JSONL outputs.
- Write `quality-report.json` with critical and warning rule results.
- Integrate `quality_check` into the offline batch before `smoke_test`.
- Document that quality checking does not clean or modify data.

## Validation

- `python -m pytest warehouse/tests warehouse/spark/tests -q`
- `powershell -ExecutionPolicy Bypass -File deploy/scripts/check.ps1`
- `powershell -ExecutionPolicy Bypass -File warehouse/scripts/run_quality_check.ps1 -BatchDate 2026-07-01`
- `powershell -ExecutionPolicy Bypass -File warehouse/scripts/run_offline_batch.ps1 -BatchDate 2026-07-01 -SkipStages crawler`
```

Expected: PR is open and ready for review.

---

## Self-Review

- Spec coverage: The plan covers standalone quality checking, report writing, runner integration, docs, and final runtime verification.
- Completion scan: No incomplete sections remain.
- Type consistency: Stage name is `quality_check` throughout.
