param(
  [Parameter(Mandatory = $true)]
  [ValidatePattern('^\d{4}-\d{2}-\d{2}$')]
  [string]$BatchDate
)

$ErrorActionPreference = "Stop"

$projectRoot = Resolve-Path (Join-Path $PSScriptRoot "..\..")
$processedDir = Join-Path $projectRoot "crawler\data\processed\$BatchDate"
$sources = @(
  @{ Name = "products"; File = "products.jsonl" },
  @{ Name = "carts"; File = "carts.jsonl" },
  @{ Name = "users"; File = "users.jsonl" }
)

foreach ($source in $sources) {
  $sourceName = $source.Name
  $path = Join-Path $processedDir $source.File
  if (-not (Test-Path -LiteralPath $path)) {
    throw "Missing processed ODS input for ${sourceName}: $path"
  }

  $item = Get-Item -LiteralPath $path
  if ($item.Length -le 0) {
    throw "Processed ODS input is empty for ${sourceName}: $path"
  }

  Write-Host "Found $sourceName input: $path"
}

Write-Host "ODS input check passed for batch date $BatchDate."
