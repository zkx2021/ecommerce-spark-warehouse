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
