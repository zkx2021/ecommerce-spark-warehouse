# Offline Batch Orchestration Design

## Goal

Add a local one-command offline batch runner that executes the existing ecommerce data pipeline for one batch date, records per-stage logs, and supports rerunning from a chosen failed stage.

## Scope

This phase includes:

- A PowerShell orchestration entry point for the full offline chain.
- Stage-level execution for crawler, ODS validation, ODS Hive DDL, ODS loading, DWD, ADS, MySQL export, and deployment smoke test.
- Run directories under `logs/offline-batch/<batch-date>/<run-id>/`.
- Per-stage log files and a machine-readable run summary.
- `-StartFrom` support for failure recovery.
- `-SkipStages` support for intentionally reusing already prepared data.
- Documentation and static tests for the orchestration contract.

This phase does not include:

- Airflow, Azkaban, DolphinScheduler, or any external scheduler.
- Windows Task Scheduler or cron registration.
- New warehouse metrics, new Hive tables, or dashboard UI changes.
- Automatic Docker stack startup or teardown.
- Secrets management beyond the existing local `.env` and script defaults.

## User Workflow

The default command runs the whole local chain:

```powershell
powershell -ExecutionPolicy Bypass -File warehouse/scripts/run_offline_batch.ps1 -BatchDate 2026-07-01
```

Rerun from a failed downstream stage:

```powershell
powershell -ExecutionPolicy Bypass -File warehouse/scripts/run_offline_batch.ps1 -BatchDate 2026-07-01 -StartFrom dwd
```

Reuse existing crawler data and skip strict deployment smoke test:

```powershell
powershell -ExecutionPolicy Bypass -File warehouse/scripts/run_offline_batch.ps1 -BatchDate 2026-07-01 -SkipStages crawler,smoke_test
```

## Stage Model

The runner uses a fixed ordered stage list:

```text
crawler
ods_check
ods_ddl
ods_load
dwd
ads
mysql_export
smoke_test
```

Each stage has one clear responsibility:

- `crawler`: runs `python crawler/run.py --batch-date <date>`.
- `ods_check`: runs `warehouse/scripts/check_ods_inputs.ps1`.
- `ods_ddl`: creates or refreshes ODS Hive tables through HiveServer2.
- `ods_load`: runs `warehouse/scripts/load_ods.ps1`.
- `dwd`: runs `warehouse/scripts/run_dwd.ps1`.
- `ads`: runs `warehouse/scripts/run_ads.ps1`.
- `mysql_export`: runs `warehouse/scripts/export_ads_mysql.ps1`.
- `smoke_test`: runs `deploy/scripts/smoke_test.ps1` against `http://127.0.0.1:8000` and `http://127.0.0.1:8088`.

The runner is fail-fast. If a stage fails, subsequent stages do not run and the process exits non-zero.

## Parameters

`run_offline_batch.ps1` accepts:

```powershell
param(
  [Parameter(Mandatory = $true)]
  [ValidatePattern('^\d{4}-\d{2}-\d{2}$')]
  [string]$BatchDate,

  [ValidateSet('crawler', 'ods_check', 'ods_ddl', 'ods_load', 'dwd', 'ads', 'mysql_export', 'smoke_test')]
  [string]$StartFrom = 'crawler',

  [ValidateSet('crawler', 'ods_check', 'ods_ddl', 'ods_load', 'dwd', 'ads', 'mysql_export', 'smoke_test')]
  [string[]]$SkipStages = @(),

  [string]$LogsRoot = 'logs/offline-batch',

  [string]$BackendBaseUrl = 'http://127.0.0.1:8000',

  [string]$FrontendBaseUrl = 'http://127.0.0.1:8088'
)
```

`-StartFrom` excludes all earlier stages from the run. `-SkipStages` excludes named stages after `-StartFrom` filtering. If every stage is excluded, the runner exits non-zero with a clear message.

## Logging And Summary

Each run creates:

```text
logs/offline-batch/<batch-date>/<yyyyMMdd-HHmmss>/
  run-summary.json
  crawler.log
  ods_check.log
  ods_ddl.log
  ods_load.log
  dwd.log
  ads.log
  mysql_export.log
  smoke_test.log
```

`run-summary.json` records:

```json
{
  "batch_date": "2026-07-01",
  "run_id": "20260720-113000",
  "started_at": "2026-07-20T11:30:00+08:00",
  "finished_at": "2026-07-20T11:35:00+08:00",
  "status": "failed",
  "start_from": "crawler",
  "skip_stages": [],
  "stages": [
    {
      "name": "crawler",
      "status": "success",
      "started_at": "2026-07-20T11:30:00+08:00",
      "finished_at": "2026-07-20T11:30:04+08:00",
      "exit_code": 0,
      "log": "crawler.log"
    }
  ]
}
```

Allowed stage statuses are:

```text
success
failed
skipped
not_run
```

The console output stays concise: stage start, stage success/failure, log file path, and final summary path.

## Failure Recovery

Recovery is manual and explicit:

1. Read the failed stage log under the run directory.
2. Fix the local issue, such as Docker service readiness or missing source files.
3. Rerun with `-StartFrom <failed-stage>`.

The stage order is idempotent enough for reruns:

- Crawler rewrites local batch files for the same date.
- ODS loading overwrites HDFS batch files and refreshes Hive partitions.
- DWD and ADS jobs overwrite date partitions.
- MySQL export deletes and reinserts rows for the batch date.

## Docker And Service Assumptions

The runner assumes the local Docker Compose stack is already running. It does not call `docker compose up` or `docker compose down`.

This keeps the batch command focused on data processing and avoids surprising service lifecycle changes during development.

Before the first strict run, the user should start the stack:

```powershell
docker compose up -d --build
```

## Implementation Shape

Add:

```text
warehouse/scripts/run_offline_batch.ps1
warehouse/tests/test_offline_batch_assets.py
```

Modify:

```text
deploy/scripts/check.ps1
warehouse/README.md
docs/deployment-integration.md
.gitignore
```

The orchestration script should use a small internal stage table rather than duplicating complex logic. Each stage calls the existing script or command as a native child process and captures stdout/stderr into that stage's log file.

ODS Hive DDL should use the same Docker copy-and-beeline pattern documented after PR #10:

```powershell
docker compose exec -T hive-server2 mkdir -p /tmp/ods-ddl
docker compose cp warehouse/hive/ods/create_ods_tables.sql hive-server2:/tmp/ods-ddl/create_ods_tables.sql
docker compose exec -T hive-server2 beeline -u jdbc:hive2://localhost:10000 -f /tmp/ods-ddl/create_ods_tables.sql
```

## Testing Strategy

Static tests should verify:

- `run_offline_batch.ps1` exists and validates `BatchDate`.
- The ordered stage list contains exactly `crawler`, `ods_check`, `ods_ddl`, `ods_load`, `dwd`, `ads`, `mysql_export`, and `smoke_test`.
- The script exposes `-StartFrom`, `-SkipStages`, `-LogsRoot`, `-BackendBaseUrl`, and `-FrontendBaseUrl`.
- The script writes `run-summary.json`.
- The script references every existing downstream script.
- `deploy/scripts/check.ps1` includes the new orchestration script.
- Documentation shows default, resume, and skip examples.

Runtime verification should include:

```powershell
powershell -ExecutionPolicy Bypass -File deploy/scripts/check.ps1
python -m pytest warehouse/tests -q
powershell -ExecutionPolicy Bypass -File warehouse/scripts/run_offline_batch.ps1 -BatchDate 2026-07-01 -SkipStages crawler
```

The runtime command assumes the Docker stack is already running and existing crawler input files are present when `crawler` is skipped.

## Documentation

Update:

- `warehouse/README.md`: add a "One-Command Offline Batch" section.
- `docs/deployment-integration.md`: replace the long manual strict chain with the new runner and keep the expanded manual chain as troubleshooting context.

Docs should state that this is local orchestration, not a production scheduler.

## Acceptance Criteria

- A single PowerShell command can run the full offline batch for a date.
- A failed batch can be resumed from any named stage with `-StartFrom`.
- Individual stages can be skipped with `-SkipStages`.
- Every run writes per-stage logs and `run-summary.json`.
- The runner exits non-zero when a stage fails.
- Static tests and foundation checks pass locally.
- The strict deployed smoke test still verifies real ADS data after the runner completes.

## Risks And Mitigations

- Docker services may not be ready. The runner fails clearly at the first Docker-dependent stage and points to the stage log; service startup remains a separate explicit user action.
- Logs may hide important errors if only stdout is captured. Capture both stdout and stderr for each stage.
- Stage skipping can produce misleading success if upstream data is stale. The final summary records skipped stages so demos and debugging can see what was not rerun.
- A PowerShell-only runner is Windows-focused. This matches the current repo scripts and user environment; cross-platform shell orchestration is out of scope for this phase.

## Implementation Boundaries

Task planning should split this phase into independently reviewable tasks:

1. Add static tests and foundation checks for the orchestration contract.
2. Add the batch runner skeleton, stage selection, and summary writing.
3. Implement stage execution and log capture.
4. Add resume and skip behavior tests.
5. Update operational documentation.
6. Run local verification and create the PR.
