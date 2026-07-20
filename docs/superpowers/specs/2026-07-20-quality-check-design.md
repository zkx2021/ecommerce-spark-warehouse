# Quality Check Design

## Goal

Add a local `quality_check` stage that validates the ecommerce offline batch results after ADS export and before the final dashboard smoke test. The stage checks whether data is trustworthy; it does not clean, modify, or rewrite data.

## Naming

Use `quality_check` for scripts, stage names, logs, and documentation.

This phase intentionally does not use `data_quality` as the stage name because that can sound like data cleaning. `quality_check` means validation only.

## Scope

This phase includes:

- A Python quality checker for local batch artifacts.
- A PowerShell wrapper script for running the checker.
- A `quality_check` stage in the one-command offline batch runner.
- A JSON quality report under the offline batch run directory.
- Static and unit tests for rule behavior, script contracts, and runner integration.
- Documentation for how to read quality reports and resume after failed checks.

This phase does not include:

- Modifying source, DWD, ADS, or MySQL data.
- Auto-fixing nulls, duplicates, negative amounts, or schema drift.
- Introducing Great Expectations, Deequ, dbt, Airflow, or another quality platform.
- Adding new warehouse metrics or changing dashboard visuals.
- Replacing existing ODS/DWD/ADS transformation logic.

## Runner Integration

Update the one-command offline batch stage order to:

```text
crawler
ods_check
ods_ddl
ods_load
dwd
ads
mysql_export
quality_check
smoke_test
```

`quality_check` runs after MySQL export and before `smoke_test`.

This placement verifies the dashboard-facing ADS JSONL snapshots and MySQL-ready output before the API and frontend smoke test. If `quality_check` fails, `smoke_test` does not run and the batch exits non-zero.

The runner must support the new stage in:

- `-StartFrom`
- `-SkipStages`
- stage log names
- run summary records
- resume guidance after failure

Example:

```powershell
powershell -ExecutionPolicy Bypass -File warehouse/scripts/run_offline_batch.ps1 -BatchDate 2026-07-01 -StartFrom quality_check
```

## Quality Report Location

The wrapper receives the offline batch run directory and writes:

```text
logs/offline-batch/<batch-date>/<run-id>/
  quality_check.log
  quality-report.json
```

`quality-report.json` records:

```json
{
  "batch_date": "2026-07-01",
  "status": "failed",
  "checked_at": "2026-07-20T13:30:00+08:00",
  "summary": {
    "total_rules": 8,
    "passed": 7,
    "failed": 1
  },
  "rules": [
    {
      "name": "ads_kpi_daily_sales_non_negative",
      "severity": "critical",
      "status": "passed",
      "message": "total_sales_amount is non-negative"
    }
  ]
}
```

Allowed report statuses:

```text
passed
failed
```

Allowed rule statuses:

```text
passed
failed
```

Allowed severities:

```text
critical
warning
```

Only `critical` failures make the script exit non-zero in the first version. `warning` rules are reported but do not fail the batch.

## Inputs

The first version validates local artifacts already produced by the existing pipeline:

```text
crawler/data/processed/<batch-date>/products.jsonl
crawler/data/processed/<batch-date>/carts.jsonl
crawler/data/processed/<batch-date>/users.jsonl
warehouse/data/ads/<batch-date>/ads_kpi_daily.jsonl
warehouse/data/ads/<batch-date>/ads_sales_trend_daily.jsonl
warehouse/data/ads/<batch-date>/ads_product_rank_daily.jsonl
warehouse/data/ads/<batch-date>/ads_category_share_daily.jsonl
warehouse/data/ads/<batch-date>/ads_user_profile_daily.jsonl
warehouse/data/ads/<batch-date>/ads_funnel_daily.jsonl
```

It does not query Hive or MySQL directly in the first version. This keeps the checker fast, testable without Docker, and aligned with the ADS export path used by MySQL.

## Scripts

Add:

```text
warehouse/scripts/run_quality_check.ps1
warehouse/scripts/quality_check.py
```

`run_quality_check.ps1` responsibilities:

- Validate `-BatchDate`.
- Accept `-ReportDir`, defaulting to `logs/quality-check/<batch-date>`.
- Call `quality_check.py`.
- Pass repository-relative input roots to Python.
- Exit non-zero when Python reports critical failures.

`quality_check.py` responsibilities:

- Parse command-line arguments.
- Load JSONL files.
- Run deterministic rules.
- Print concise PASS/FAIL output.
- Write `quality-report.json`.
- Return exit code `0` when all critical rules pass, otherwise `1`.

## Rules

### Source File Rules

Critical:

- Processed `products.jsonl` exists and has at least one row.
- Processed `carts.jsonl` exists and has at least one row.
- Processed `users.jsonl` exists and has at least one row.

### ADS Presence Rules

Critical:

- Every required ADS JSONL snapshot exists.
- `ads_kpi_daily.jsonl` has exactly one row for the batch date.
- `ads_sales_trend_daily.jsonl` has at least one row.
- `ads_product_rank_daily.jsonl` has between one and ten rows.
- `ads_category_share_daily.jsonl` has at least one row.
- `ads_user_profile_daily.jsonl` has at least one row.
- `ads_funnel_daily.jsonl` has at least one row.

### KPI Rules

Critical:

- `total_sales_amount >= 0`.
- `total_order_count > 0`.
- `paid_user_count >= 0`.
- `avg_order_amount >= 0`.
- `0 <= payment_conversion_rate <= 1`.

### Rank Rules

Critical:

- `rank_no` is unique within `ads_product_rank_daily`.
- `rank_no` values are positive integers.
- `sales_quantity >= 0`.
- `sales_amount >= 0`.

### Category Share Rules

Critical:

- `sales_quantity >= 0`.
- `sales_amount >= 0`.
- `0 <= sales_share <= 1`.

Warning:

- Sum of `sales_share` is between `0.95` and `1.05` when category rows exist.

### Funnel Rules

Critical:

- `stage_order` is unique within `ads_funnel_daily`.
- `stage_count >= 0`.
- `0 <= conversion_rate <= 1`.

## Error Handling

Missing files, invalid JSON, and unreadable files are critical failures.

The checker should keep evaluating independent rules after a failure when possible, so the report lists all visible issues instead of stopping at the first one. The wrapper should still exit non-zero if any critical rule fails.

## Offline Batch Summary Behavior

When `quality_check` passes:

- `quality_check` stage status is `success`.
- `quality_check.log` points to the wrapper output.
- `quality-report.json` has `status = passed`.

When `quality_check` fails:

- `quality_check` stage status is `failed`.
- Subsequent selected stages remain `not_run`.
- Console output includes resume guidance through the existing offline runner behavior.
- `quality-report.json` has `status = failed`.

## Testing Strategy

Unit tests should cover:

- JSONL loading.
- Missing file failure.
- Empty source failure.
- KPI valid and invalid ranges.
- Rank uniqueness.
- Category share ranges.
- Funnel conversion ranges.
- Exit code behavior for critical versus warning failures.

Static tests should verify:

- `run_quality_check.ps1` exists and calls `quality_check.py`.
- `run_offline_batch.ps1` includes `quality_check` in the expected stage order.
- The runner calls the quality wrapper after `mysql_export` and before `smoke_test`.
- `deploy/scripts/check.ps1` includes the new scripts.
- Documentation explains that `quality_check` validates data and does not clean it.

Runtime verification should include:

```powershell
python -m pytest warehouse/tests warehouse/spark/tests -q
powershell -ExecutionPolicy Bypass -File deploy/scripts/check.ps1
powershell -ExecutionPolicy Bypass -File warehouse/scripts/run_quality_check.ps1 -BatchDate 2026-07-01
powershell -ExecutionPolicy Bypass -File warehouse/scripts/run_offline_batch.ps1 -BatchDate 2026-07-01 -SkipStages crawler
```

The last two commands assume the local batch artifacts already exist.

## Documentation

Update:

- `warehouse/README.md`
- `docs/deployment-integration.md`

Docs should state:

- `quality_check` is not data cleaning.
- Failed quality checks should be investigated before presenting the dashboard.
- Use `quality-report.json` as the first place to inspect rule failures.
- The checker validates local batch outputs in the first version.

## Acceptance Criteria

- `quality_check` is part of the offline batch stage order between `mysql_export` and `smoke_test`.
- A standalone quality check command can run for one batch date.
- The checker writes `quality-report.json`.
- Critical quality failures make the quality script and offline runner exit non-zero.
- Warning quality failures appear in the report but do not fail the batch.
- Static and unit tests pass locally.
- Existing one-command offline batch verification still passes for `2026-07-01`.

## Risks And Mitigations

- Rule scope can grow quickly. Keep the first version focused on local source and ADS output checks.
- Local JSONL validation may miss Hive or MySQL-only problems. The existing MySQL export and smoke test still cover the API-facing path; direct database quality checks can be a later phase.
- Warning thresholds may need adjustment as data sources change. Keep threshold values explicit in tests and docs.
- Users may confuse quality checking with cleaning. Use `quality_check` naming consistently and document that it does not modify data.

## Implementation Boundaries

Task planning should split this phase into independently reviewable tasks:

1. Quality checker unit tests and core rule engine.
2. PowerShell wrapper and foundation checks.
3. Offline batch runner integration.
4. Documentation updates.
5. Full verification, push, and PR.
