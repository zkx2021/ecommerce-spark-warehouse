param(
  [Parameter(Mandatory = $true)]
  [ValidatePattern('^\d{4}-\d{2}-\d{2}$')]
  [string]$BatchDate,

  [string]$SnapshotRoot = "warehouse/data/ads",

  [string]$HostName = "localhost",

  [int]$Port = 3306,

  [string]$Database = "ecommerce_ads",

  [string]$User = "ecommerce",

  [string]$Password = "ecommerce"
)

$ErrorActionPreference = "Stop"

$projectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$exporter = Join-Path $projectRoot "warehouse\scripts\export_ads_mysql.py"

function Invoke-Native {
  param(
    [Parameter(Mandatory = $true)]
    [string]$FilePath,

    [Parameter(Mandatory = $true)]
    [string[]]$Arguments
  )

  & $FilePath @Arguments
  if ($LASTEXITCODE -ne 0) {
    $displayCommand = ((@($FilePath) + $Arguments) -join " ")
    throw "Native command failed with exit code ${LASTEXITCODE}: $displayCommand"
  }
}

if (-not (Test-Path -LiteralPath $exporter)) {
  throw "Missing ADS MySQL exporter path: $exporter"
}

Push-Location $projectRoot
try {
  Invoke-Native -FilePath "python" -Arguments @(
    $exporter,
    "--batch-date", $BatchDate,
    "--snapshot-root", $SnapshotRoot,
    "--host", $HostName,
    "--port", "$Port",
    "--database", $Database,
    "--user", $User,
    "--password", $Password
  )
}
finally {
  Pop-Location
}

Write-Host "ADS MySQL export completed for batch date $BatchDate."
