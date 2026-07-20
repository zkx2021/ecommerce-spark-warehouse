# Offline Batch Orchestration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a local one-command offline batch runner for the ecommerce warehouse pipeline with stage logs, summary output, stage skipping, and failure recovery.

**Architecture:** A new PowerShell orchestrator coordinates existing crawler, ODS, DWD, ADS, MySQL export, and smoke-test scripts without duplicating their internals. It owns stage ordering, run directory creation, child-process execution, log capture, and `run-summary.json`.

**Tech Stack:** PowerShell, Python pytest static tests, Docker Compose command wrappers, existing Spark/HDFS/Hive/MySQL/FastAPI/Vue pipeline.

## Global Constraints

- Every implementation task starts only after the user explicitly sends the matching `Task N` command.
- The runner is local orchestration, not Airflow/Azkaban/DolphinScheduler.
- The runner must not start or stop Docker Compose services.
- The fixed stage order is `crawler`, `ods_check`, `ods_ddl`, `ods_load`, `dwd`, `ads`, `mysql_export`, `smoke_test`.
- Run logs are written under `logs/offline-batch/<batch-date>/<run-id>/`.
- `BatchDate` must match `YYYY-MM-DD`.
- Generated logs and batch outputs must not be committed.
- Keep `architecture-options.html` unrelated and unstaged.

---

## File Structure

- Create `warehouse/scripts/run_offline_batch.ps1`: one-command batch runner, stage selection, log capture, summary JSON, and child command execution.
- Create `warehouse/tests/test_offline_batch_assets.py`: static contract tests for runner parameters, stage order, summary/log behavior, docs references, and foundation checks.
- Modify `deploy/scripts/check.ps1`: require the new runner and assert important contract strings.
- Modify `.gitignore`: ignore `logs/offline-batch/`.
- Modify `warehouse/README.md`: document the one-command batch entry point, resume, skip examples, and log location.
- Modify `docs/deployment-integration.md`: replace the long strict chain with the runner and keep manual commands as troubleshooting context.

---

### Task 1: Orchestration Contract Tests And Foundation Checks

**Files:**
- Create: `warehouse/tests/test_offline_batch_assets.py`
- Modify: `deploy/scripts/check.ps1`
- Modify: `.gitignore`

**Interfaces:**
- Consumes: Existing repository paths and script names.
- Produces: Test expectations that later tasks must satisfy:
  - `warehouse/scripts/run_offline_batch.ps1`
  - ordered stage names
  - `run-summary.json`
  - `logs/offline-batch`

- [ ] **Step 1: Write failing static tests**

Create `warehouse/tests/test_offline_batch_assets.py`:

```python
import re
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
RUNNER = PROJECT_ROOT / "warehouse" / "scripts" / "run_offline_batch.ps1"
CHECK = PROJECT_ROOT / "deploy" / "scripts" / "check.ps1"
WAREHOUSE_README = PROJECT_ROOT / "warehouse" / "README.md"
DEPLOYMENT_DOC = PROJECT_ROOT / "docs" / "deployment-integration.md"
GITIGNORE = PROJECT_ROOT / ".gitignore"

EXPECTED_STAGES = [
    "crawler",
    "ods_check",
    "ods_ddl",
    "ods_load",
    "dwd",
    "ads",
    "mysql_export",
    "smoke_test",
]


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8").lower()


def test_offline_batch_runner_exists_and_exposes_parameters():
    script = _read(RUNNER)

    assert "param(" in script
    assert "$batchdate" in script
    assert "validatepattern('^\\d{4}-\\d{2}-\\d{2}$')" in script
    for parameter in ("$startfrom", "$skipstages", "$logsroot", "$backendbaseurl", "$frontendbaseurl"):
        assert parameter in script


def test_offline_batch_runner_declares_expected_stage_order():
    script = _read(RUNNER)
    stage_match = re.search(r"\\$stageorder\\s*=\\s*@\\((.*?)\\)", script, flags=re.DOTALL)
    assert stage_match is not None

    stages = re.findall(r"'([^']+)'", stage_match.group(1))
    assert stages == EXPECTED_STAGES


def test_offline_batch_runner_references_existing_pipeline_scripts():
    script = _read(RUNNER).replace("\\\\", "/")

    for expected in (
        "crawler/run.py",
        "warehouse/scripts/check_ods_inputs.ps1",
        "warehouse/hive/ods/create_ods_tables.sql",
        "warehouse/scripts/load_ods.ps1",
        "warehouse/scripts/run_dwd.ps1",
        "warehouse/scripts/run_ads.ps1",
        "warehouse/scripts/export_ads_mysql.ps1",
        "deploy/scripts/smoke_test.ps1",
    ):
        assert expected in script


def test_offline_batch_runner_writes_logs_and_summary():
    script = _read(RUNNER)

    assert "logs/offline-batch" in script
    assert "run-summary.json" in script
    for stage in EXPECTED_STAGES:
        assert f"{stage}.log" in script
    for status in ("success", "failed", "skipped", "not_run"):
        assert status in script


def test_foundation_check_and_gitignore_include_offline_batch_assets():
    check = _read(CHECK)
    gitignore = _read(GITIGNORE)

    assert "warehouse/scripts/run_offline_batch.ps1" in check
    assert "run-summary.json" in check
    assert "logs/offline-batch/" in gitignore


def test_docs_show_default_resume_and_skip_examples():
    docs = _read(WAREHOUSE_README) + "\n" + _read(DEPLOYMENT_DOC)

    assert "run_offline_batch.ps1" in docs
    assert "-startfrom dwd" in docs
    assert "-skipstages crawler,smoke_test" in docs
    assert "logs/offline-batch" in docs
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```powershell
python -m pytest warehouse/tests/test_offline_batch_assets.py -q
```

Expected: FAIL because the runner, checks, ignore rule, and docs are not implemented yet.

- [ ] **Step 3: Add foundation path and contract checks**

Modify `deploy/scripts/check.ps1`:

```powershell
$requiredPaths = @(
  ...
  "warehouse/scripts/run_offline_batch.ps1",
  ...
)
```

Add assertions near the existing script assertions:

```powershell
Assert-FileContains "warehouse/scripts/run_offline_batch.ps1" "run-summary.json" "offline batch runner writes summary"
Assert-FileContains "warehouse/scripts/run_offline_batch.ps1" "logs/offline-batch" "offline batch runner writes stage logs"
Assert-FileContains "warehouse/scripts/run_offline_batch.ps1" "crawler', 'ods_check', 'ods_ddl', 'ods_load', 'dwd', 'ads', 'mysql_export', 'smoke_test" "offline batch runner preserves stage order"
```

- [ ] **Step 4: Ignore generated batch logs**

Modify `.gitignore`:

```gitignore
logs/offline-batch/
```

- [ ] **Step 5: Run targeted checks**

Run:

```powershell
python -m pytest warehouse/tests/test_offline_batch_assets.py -q
powershell -ExecutionPolicy Bypass -File deploy/scripts/check.ps1
```

Expected: still FAIL until Task 2 creates the runner and Task 5 updates docs. Commit only after the planned Task 1 files are correct; this task may intentionally leave red tests that define the contract for the next tasks.

- [ ] **Step 6: Commit**

Run:

```powershell
git add warehouse/tests/test_offline_batch_assets.py deploy/scripts/check.ps1 .gitignore
git commit -m "test: define offline batch orchestration contract"
```

---

### Task 2: Runner Skeleton, Stage Selection, And Summary Initialization

**Files:**
- Create: `warehouse/scripts/run_offline_batch.ps1`
- Modify: `warehouse/tests/test_offline_batch_assets.py` if static assertions need path normalization only.

**Interfaces:**
- Consumes: Stage order from Task 1.
- Produces:
  - `$StageOrder`
  - `Get-SelectedStages`
  - `New-StageRecord`
  - `Write-RunSummary`
  - initial `run-summary.json`

- [ ] **Step 1: Write the runner parameter block and stage order**

Create `warehouse/scripts/run_offline_batch.ps1`:

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

$ErrorActionPreference = "Stop"

$StageOrder = @('crawler', 'ods_check', 'ods_ddl', 'ods_load', 'dwd', 'ads', 'mysql_export', 'smoke_test')
```

- [ ] **Step 2: Add stage selection helper**

Add:

```powershell
function Get-SelectedStages {
  param(
    [string[]]$StageOrder,
    [string]$StartFrom,
    [string[]]$SkipStages
  )

  $startIndex = [array]::IndexOf($StageOrder, $StartFrom)
  if ($startIndex -lt 0) {
    throw "Unknown StartFrom stage: $StartFrom"
  }

  $skipLookup = @{}
  foreach ($stage in $SkipStages) {
    $skipLookup[$stage] = $true
  }

  $selected = @()
  for ($index = $startIndex; $index -lt $StageOrder.Count; $index++) {
    $stage = $StageOrder[$index]
    if (-not $skipLookup.ContainsKey($stage)) {
      $selected += $stage
    }
  }

  if ($selected.Count -eq 0) {
    throw "No stages selected. Adjust -StartFrom or -SkipStages."
  }

  return $selected
}
```

- [ ] **Step 3: Add run directory and summary helpers**

Add:

```powershell
function New-StageRecord {
  param(
    [string]$Name,
    [string]$Status,
    [string]$LogName
  )

  [ordered]@{
    name = $Name
    status = $Status
    started_at = $null
    finished_at = $null
    exit_code = $null
    log = $LogName
  }
}

function Write-RunSummary {
  param(
    [string]$Path,
    [ordered]$Summary
  )

  $Summary | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $Path -Encoding UTF8
}
```

- [ ] **Step 4: Add initial main flow without executing stages**

Add:

```powershell
$projectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$runId = Get-Date -Format "yyyyMMdd-HHmmss"
$runDir = Join-Path (Join-Path (Join-Path $projectRoot $LogsRoot) $BatchDate) $runId
New-Item -ItemType Directory -Force -Path $runDir | Out-Null

$selectedStages = Get-SelectedStages -StageOrder $StageOrder -StartFrom $StartFrom -SkipStages $SkipStages
$summaryPath = Join-Path $runDir "run-summary.json"
$summary = [ordered]@{
  batch_date = $BatchDate
  run_id = $runId
  started_at = (Get-Date).ToString("o")
  finished_at = $null
  status = "not_run"
  start_from = $StartFrom
  skip_stages = @($SkipStages)
  stages = @()
}

foreach ($stage in $StageOrder) {
  $status = if ($selectedStages -contains $stage) { "not_run" } else { "skipped" }
  $summary.stages += New-StageRecord -Name $stage -Status $status -LogName "$stage.log"
}

$summary.finished_at = (Get-Date).ToString("o")
$summary.status = "success"
Write-RunSummary -Path $summaryPath -Summary $summary
Write-Host "Offline batch plan initialized for batch date $BatchDate."
Write-Host "Summary: $summaryPath"
```

- [ ] **Step 5: Run static checks**

Run:

```powershell
python -m pytest warehouse/tests/test_offline_batch_assets.py -q
powershell -ExecutionPolicy Bypass -File deploy/scripts/check.ps1
```

Expected: docs-related assertions may still fail until Task 5; runner and foundation assertions should pass.

- [ ] **Step 6: Commit**

Run:

```powershell
git add warehouse/scripts/run_offline_batch.ps1 warehouse/tests/test_offline_batch_assets.py
git commit -m "feat: add offline batch runner skeleton"
```

---

### Task 3: Stage Command Execution And Log Capture

**Files:**
- Modify: `warehouse/scripts/run_offline_batch.ps1`
- Modify: `warehouse/tests/test_offline_batch_assets.py`

**Interfaces:**
- Consumes: `Get-SelectedStages`, `Write-RunSummary`.
- Produces:
  - `Get-StageCommand`
  - `Invoke-LoggedStage`
  - fail-fast non-zero exit behavior.

- [ ] **Step 1: Add static test for child execution contracts**

Append to `warehouse/tests/test_offline_batch_assets.py`:

```python
def test_offline_batch_runner_captures_output_and_fails_fast():
    script = _read(RUNNER)

    assert "Invoke-LoggedStage" in script
    assert "Start-Process" in script
    assert "RedirectStandardOutput" in script
    assert "RedirectStandardError" in script
    assert "throw \"Offline batch failed at stage" in script
```

- [ ] **Step 2: Implement stage command mapping**

Add to `warehouse/scripts/run_offline_batch.ps1`:

```powershell
function Get-StageCommand {
  param(
    [string]$Stage,
    [string]$ProjectRoot,
    [string]$BatchDate,
    [string]$BackendBaseUrl,
    [string]$FrontendBaseUrl
  )

  switch ($Stage) {
    "crawler" {
      return @{
        FilePath = "python"
        Arguments = @("crawler/run.py", "--batch-date", $BatchDate)
      }
    }
    "ods_check" {
      return @{
        FilePath = "powershell"
        Arguments = @("-ExecutionPolicy", "Bypass", "-File", "warehouse/scripts/check_ods_inputs.ps1", "-BatchDate", $BatchDate)
      }
    }
    "ods_ddl" {
      return @{
        FilePath = "powershell"
        Arguments = @("-ExecutionPolicy", "Bypass", "-Command", "docker compose exec -T hive-server2 mkdir -p /tmp/ods-ddl; docker compose cp warehouse/hive/ods/create_ods_tables.sql hive-server2:/tmp/ods-ddl/create_ods_tables.sql; docker compose exec -T hive-server2 beeline -u jdbc:hive2://localhost:10000 -f /tmp/ods-ddl/create_ods_tables.sql")
      }
    }
    "ods_load" {
      return @{
        FilePath = "powershell"
        Arguments = @("-ExecutionPolicy", "Bypass", "-File", "warehouse/scripts/load_ods.ps1", "-BatchDate", $BatchDate)
      }
    }
    "dwd" {
      return @{
        FilePath = "powershell"
        Arguments = @("-ExecutionPolicy", "Bypass", "-File", "warehouse/scripts/run_dwd.ps1", "-BatchDate", $BatchDate)
      }
    }
    "ads" {
      return @{
        FilePath = "powershell"
        Arguments = @("-ExecutionPolicy", "Bypass", "-File", "warehouse/scripts/run_ads.ps1", "-BatchDate", $BatchDate)
      }
    }
    "mysql_export" {
      return @{
        FilePath = "powershell"
        Arguments = @("-ExecutionPolicy", "Bypass", "-File", "warehouse/scripts/export_ads_mysql.ps1", "-BatchDate", $BatchDate)
      }
    }
    "smoke_test" {
      return @{
        FilePath = "powershell"
        Arguments = @("-ExecutionPolicy", "Bypass", "-File", "deploy/scripts/smoke_test.ps1", "-BackendBaseUrl", $BackendBaseUrl, "-FrontendBaseUrl", $FrontendBaseUrl)
      }
    }
  }

  throw "Unknown stage: $Stage"
}
```

- [ ] **Step 3: Implement log capture**

Add:

```powershell
function Invoke-LoggedStage {
  param(
    [string]$Stage,
    [hashtable]$Command,
    [string]$ProjectRoot,
    [string]$RunDir
  )

  $stdoutPath = Join-Path $RunDir "$Stage.stdout.tmp"
  $stderrPath = Join-Path $RunDir "$Stage.stderr.tmp"
  $logPath = Join-Path $RunDir "$Stage.log"
  $displayCommand = ((@($Command.FilePath) + $Command.Arguments) -join " ")

  "Command: $displayCommand" | Set-Content -LiteralPath $logPath -Encoding UTF8
  "" | Add-Content -LiteralPath $logPath -Encoding UTF8

  $process = Start-Process -FilePath $Command.FilePath `
    -ArgumentList $Command.Arguments `
    -WorkingDirectory $ProjectRoot `
    -NoNewWindow `
    -Wait `
    -PassThru `
    -RedirectStandardOutput $stdoutPath `
    -RedirectStandardError $stderrPath

  if (Test-Path -LiteralPath $stdoutPath) {
    Get-Content -LiteralPath $stdoutPath -Raw -ErrorAction SilentlyContinue | Add-Content -LiteralPath $logPath -Encoding UTF8
    Remove-Item -LiteralPath $stdoutPath -Force
  }
  if (Test-Path -LiteralPath $stderrPath) {
    Get-Content -LiteralPath $stderrPath -Raw -ErrorAction SilentlyContinue | Add-Content -LiteralPath $logPath -Encoding UTF8
    Remove-Item -LiteralPath $stderrPath -Force
  }

  return $process.ExitCode
}
```

- [ ] **Step 4: Replace the no-op main loop with execution**

Change the loop so selected stages run:

```powershell
$failedStage = $null

foreach ($record in $summary.stages) {
  if ($record.status -eq "skipped") {
    continue
  }

  $stage = $record.name
  Write-Host "[$stage] starting..."
  $record.started_at = (Get-Date).ToString("o")
  $command = Get-StageCommand -Stage $stage -ProjectRoot $projectRoot -BatchDate $BatchDate -BackendBaseUrl $BackendBaseUrl -FrontendBaseUrl $FrontendBaseUrl
  $exitCode = Invoke-LoggedStage -Stage $stage -Command $command -ProjectRoot $projectRoot -RunDir $runDir
  $record.exit_code = $exitCode
  $record.finished_at = (Get-Date).ToString("o")

  if ($exitCode -eq 0) {
    $record.status = "success"
    Write-Host "[$stage] success. Log: $(Join-Path $runDir "$stage.log")"
  }
  else {
    $record.status = "failed"
    $failedStage = $stage
    Write-Host "[$stage] failed. Log: $(Join-Path $runDir "$stage.log")"
    break
  }

  Write-RunSummary -Path $summaryPath -Summary $summary
}

$summary.finished_at = (Get-Date).ToString("o")
$summary.status = if ($failedStage) { "failed" } else { "success" }
Write-RunSummary -Path $summaryPath -Summary $summary

if ($failedStage) {
  throw "Offline batch failed at stage $failedStage. Summary: $summaryPath"
}

Write-Host "Offline batch completed for batch date $BatchDate."
Write-Host "Summary: $summaryPath"
```

- [ ] **Step 5: Run tests**

Run:

```powershell
python -m pytest warehouse/tests/test_offline_batch_assets.py -q
powershell -ExecutionPolicy Bypass -File deploy/scripts/check.ps1
```

Expected: docs tests may still fail until Task 5; runner execution assertions should pass.

- [ ] **Step 6: Commit**

Run:

```powershell
git add warehouse/scripts/run_offline_batch.ps1 warehouse/tests/test_offline_batch_assets.py
git commit -m "feat: execute offline batch stages with logs"
```

---

### Task 4: Resume And Skip Behavior Hardening

**Files:**
- Modify: `warehouse/scripts/run_offline_batch.ps1`
- Modify: `warehouse/tests/test_offline_batch_assets.py`

**Interfaces:**
- Consumes: `Get-SelectedStages`.
- Produces: Clear static contracts for resume, skip, and no-stage failure.

- [ ] **Step 1: Add tests for resume and skip behavior**

Append:

```python
def test_offline_batch_runner_documents_resume_and_skip_logic_in_code():
    script = _read(RUNNER)

    assert "Get-SelectedStages" in script
    assert "[array]::IndexOf($StageOrder, $StartFrom)" in script
    assert "$skipLookup.ContainsKey($stage)" in script
    assert "No stages selected" in script
    assert "start_from = $StartFrom" in script
    assert "skip_stages = @($SkipStages)" in script
```

- [ ] **Step 2: Mark not-run downstream stages after failure**

In `run_offline_batch.ps1`, after a failed stage breaks the loop, keep unexecuted selected records as `not_run`. Do not mark them `skipped`, because they were selected but blocked by failure.

Use this explicit logic after the loop:

```powershell
if ($failedStage) {
  $failureSeen = $false
  foreach ($record in $summary.stages) {
    if ($record.name -eq $failedStage) {
      $failureSeen = $true
      continue
    }
    if ($failureSeen -and $record.status -ne "skipped") {
      $record.status = "not_run"
    }
  }
}
```

- [ ] **Step 3: Improve console guidance on failure**

Add this before throwing:

```powershell
Write-Host "To resume after fixing the issue, rerun with: -StartFrom $failedStage"
```

- [ ] **Step 4: Run runner parameter validation checks**

Run:

```powershell
powershell -ExecutionPolicy Bypass -File warehouse/scripts/run_offline_batch.ps1 -BatchDate 2026-7-1
```

Expected: FAIL before any stage starts because `BatchDate` does not match `YYYY-MM-DD`.

Run:

```powershell
powershell -ExecutionPolicy Bypass -File warehouse/scripts/run_offline_batch.ps1 -BatchDate 2026-07-01 -StartFrom smoke_test -SkipStages smoke_test
```

Expected: FAIL with `No stages selected. Adjust -StartFrom or -SkipStages.`

- [ ] **Step 5: Run static checks**

Run:

```powershell
python -m pytest warehouse/tests/test_offline_batch_assets.py -q
powershell -ExecutionPolicy Bypass -File deploy/scripts/check.ps1
```

Expected: docs tests may still fail until Task 5; resume/skip assertions should pass.

- [ ] **Step 6: Commit**

Run:

```powershell
git add warehouse/scripts/run_offline_batch.ps1 warehouse/tests/test_offline_batch_assets.py
git commit -m "feat: harden offline batch resume controls"
```

---

### Task 5: Operational Documentation

**Files:**
- Modify: `warehouse/README.md`
- Modify: `docs/deployment-integration.md`
- Modify: `warehouse/tests/test_offline_batch_assets.py` only if exact wording changes.

**Interfaces:**
- Consumes: Runner command-line contract.
- Produces: User-facing operating instructions for default runs, resume runs, skipped stages, and logs.

- [ ] **Step 1: Update warehouse README**

Add this section before the existing manual ODS batch flow:

~~~markdown
## One-Command Offline Batch

After the Docker Compose stack is running, run the local offline chain for one batch date:

```powershell
powershell -ExecutionPolicy Bypass -File warehouse/scripts/run_offline_batch.ps1 -BatchDate 2026-07-01
```

The runner executes:

```text
crawler -> ods_check -> ods_ddl -> ods_load -> dwd -> ads -> mysql_export -> smoke_test
```

Resume from a failed stage after fixing the local issue:

```powershell
powershell -ExecutionPolicy Bypass -File warehouse/scripts/run_offline_batch.ps1 -BatchDate 2026-07-01 -StartFrom dwd
```

Reuse existing crawler output and skip the final strict smoke test:

```powershell
powershell -ExecutionPolicy Bypass -File warehouse/scripts/run_offline_batch.ps1 -BatchDate 2026-07-01 -SkipStages crawler,smoke_test
```

Each run writes logs and `run-summary.json` under `logs/offline-batch/<batch-date>/<run-id>/`.
This is local orchestration for development and demos, not a production scheduler.
~~~

- [ ] **Step 2: Update deployment integration doc**

In `docs/deployment-integration.md`, replace the strict manual chain with:

~~~markdown
For a strict end-to-end ADS data check, run the one-command offline batch after the Docker Compose stack is running:

```powershell
powershell -ExecutionPolicy Bypass -File warehouse/scripts/run_offline_batch.ps1 -BatchDate 2026-07-01
```

If crawler data already exists and you only want to refresh warehouse and dashboard-facing data:

```powershell
powershell -ExecutionPolicy Bypass -File warehouse/scripts/run_offline_batch.ps1 -BatchDate 2026-07-01 -SkipStages crawler
```

If a downstream stage fails, inspect `logs/offline-batch/<batch-date>/<run-id>/<stage>.log`, fix the local issue, then resume:

```powershell
powershell -ExecutionPolicy Bypass -File warehouse/scripts/run_offline_batch.ps1 -BatchDate 2026-07-01 -StartFrom dwd
```

The expanded manual command chain remains useful for troubleshooting individual stages:
~~~

Then keep the existing manual commands below that line.

- [ ] **Step 3: Run docs/static tests**

Run:

```powershell
python -m pytest warehouse/tests/test_offline_batch_assets.py -q
powershell -ExecutionPolicy Bypass -File deploy/scripts/check.ps1
```

Expected: PASS.

- [ ] **Step 4: Commit**

Run:

```powershell
git add warehouse/README.md docs/deployment-integration.md warehouse/tests/test_offline_batch_assets.py
git commit -m "docs: document offline batch runner"
```

---

### Task 6: Full Verification, Push, And PR

**Files:**
- No planned implementation files unless verification exposes a blocker.

**Interfaces:**
- Consumes: Completed runner, tests, docs.
- Produces: Ready PR for this phase.

- [ ] **Step 1: Run static and unit verification**

Run:

```powershell
python -m pytest warehouse/tests -q
python -m pytest warehouse/spark/tests -q
powershell -ExecutionPolicy Bypass -File deploy/scripts/check.ps1
```

Expected: PASS.

- [ ] **Step 2: Run compose config validation**

Run:

```powershell
docker compose config
```

Expected: PASS. If Docker access is denied by sandbox, rerun with approved Docker access.

- [ ] **Step 3: Run local offline batch verification when services are running**

Run:

```powershell
powershell -ExecutionPolicy Bypass -File warehouse/scripts/run_offline_batch.ps1 -BatchDate 2026-07-01 -SkipStages crawler
```

Expected: PASS, with `run-summary.json` showing `status = success`, `crawler = skipped`, and all downstream selected stages `success`.

- [ ] **Step 4: Confirm generated files stay untracked**

Run:

```powershell
git status --short --branch
```

Expected: only intentional source changes are present. `logs/offline-batch/`, `warehouse/data/`, and `crawler/data/` must not appear as tracked changes. Existing unrelated `architecture-options.html` must remain unstaged.

- [ ] **Step 5: Push branch**

Run:

```powershell
git -c http.proxy=http://127.0.0.1:7897 -c https.proxy=http://127.0.0.1:7897 push -u origin codex/offline-batch-orchestration
```

Expected: branch is pushed to `zkx2021/ecommerce-spark-warehouse`.

- [ ] **Step 6: Create PR**

Create a ready PR against `main` with:

```markdown
## Summary

- Add a one-command local offline batch runner.
- Capture per-stage logs and write run-summary.json.
- Support -StartFrom failure recovery and -SkipStages selective reruns.
- Document local orchestration workflow.

## Validation

- `python -m pytest warehouse/tests -q`
- `python -m pytest warehouse/spark/tests -q`
- `powershell -ExecutionPolicy Bypass -File deploy/scripts/check.ps1`
- `docker compose config`
- `powershell -ExecutionPolicy Bypass -File warehouse/scripts/run_offline_batch.ps1 -BatchDate 2026-07-01 -SkipStages crawler`
```

Expected: PR is open and ready for review.

---

## Self-Review

- Spec coverage: The plan covers one-command runner, fixed stage order, logs, summary JSON, start-from recovery, skip stages, documentation, and verification.
- Completion scan: No incomplete sections remain.
- Type consistency: Stage names match the design exactly across tests, script contract, docs, and PR body.
