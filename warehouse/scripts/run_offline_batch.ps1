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
$AllowedStageStatuses = @('success', 'failed', 'skipped', 'not_run')
$StageLogNames = @{
  crawler = 'crawler.log'
  ods_check = 'ods_check.log'
  ods_ddl = 'ods_ddl.log'
  ods_load = 'ods_load.log'
  dwd = 'dwd.log'
  ads = 'ads.log'
  mysql_export = 'mysql_export.log'
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

$summary.finished_at = (Get-Date).ToString("o")
$summary.status = "success"
Write-RunSummary -Path $summaryPath -Summary $summary
Write-Host "Offline batch plan initialized for batch date $BatchDate."
Write-Host "Summary: $summaryPath"
