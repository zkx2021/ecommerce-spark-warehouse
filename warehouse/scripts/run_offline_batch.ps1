param(
  [Parameter(Mandatory = $true)]
  [ValidatePattern('^\d{4}-\d{2}-\d{2}$')]
  [string]$BatchDate,

  [ValidateSet('crawler', 'ods_check', 'ods_ddl', 'ods_load', 'dwd', 'ads', 'mysql_export', 'quality_check', 'smoke_test')]
  [string]$StartFrom = 'crawler',

  [ValidateSet('crawler', 'ods_check', 'ods_ddl', 'ods_load', 'dwd', 'ads', 'mysql_export', 'quality_check', 'smoke_test')]
  [string[]]$SkipStages = @(),

  [string]$LogsRoot = 'logs/offline-batch',

  [string]$BackendBaseUrl = 'http://127.0.0.1:8000',

  [string]$FrontendBaseUrl = 'http://127.0.0.1:8088'
)

$ErrorActionPreference = "Stop"

$StageOrder = @('crawler', 'ods_check', 'ods_ddl', 'ods_load', 'dwd', 'ads', 'mysql_export', 'quality_check', 'smoke_test')
$AllowedStageStatuses = @('success', 'failed', 'skipped', 'not_run')
$StageLogNames = @{
  crawler = 'crawler.log'
  ods_check = 'ods_check.log'
  ods_ddl = 'ods_ddl.log'
  ods_load = 'ods_load.log'
  dwd = 'dwd.log'
  ads = 'ads.log'
  mysql_export = 'mysql_export.log'
  quality_check = 'quality_check.log'
  smoke_test = 'smoke_test.log'
}
$StageScriptReferences = @{
  crawler = 'crawler/run.py'
  ods_check = 'warehouse/scripts/check_ods_inputs.ps1'
  ods_ddl = 'warehouse/hive/ods/create_ods_tables.sql'
  ods_load = 'warehouse/scripts/load_ods.ps1'
  dwd = 'warehouse/scripts/run_dwd.ps1'
  ads = 'warehouse/scripts/run_ads.ps1'
  mysql_export = 'warehouse/scripts/export_ads_mysql.ps1'
  quality_check = 'warehouse/scripts/run_quality_check.ps1'
  smoke_test = 'deploy/scripts/smoke_test.ps1'
}

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
    [object]$Summary
  )

  $Summary | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $Path -Encoding UTF8
}

function Get-StageCommand {
  param(
    [string]$Stage,
    [string]$ProjectRoot,
    [string]$BatchDate,
    [string]$BackendBaseUrl,
    [string]$FrontendBaseUrl,
    [string]$RunDir
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
    "quality_check" {
      return @{
        FilePath = "powershell"
        Arguments = @("-ExecutionPolicy", "Bypass", "-File", "warehouse/scripts/run_quality_check.ps1", "-BatchDate", $BatchDate, "-ReportDir", $RunDir)
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
  $summary.stages += New-StageRecord -Name $stage -Status $status -LogName $StageLogNames[$stage]
}

$failedStage = $null

foreach ($record in $summary.stages) {
  if ($record.status -eq "skipped") {
    continue
  }

  $stage = $record.name
  Write-Host "[$stage] starting..."
  $record.started_at = (Get-Date).ToString("o")
  $command = Get-StageCommand -Stage $stage -ProjectRoot $projectRoot -BatchDate $BatchDate -BackendBaseUrl $BackendBaseUrl -FrontendBaseUrl $FrontendBaseUrl -RunDir $runDir
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

Write-RunSummary -Path $summaryPath -Summary $summary

if ($failedStage) {
  Write-Host "To resume after fixing the issue, rerun with: -StartFrom $failedStage"
  throw "Offline batch failed at stage $failedStage. Summary: $summaryPath"
}

Write-Host "Offline batch completed for batch date $BatchDate."
Write-Host "Summary: $summaryPath"
