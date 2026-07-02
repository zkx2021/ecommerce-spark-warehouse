param(
  [Parameter(Mandatory = $true)]
  [ValidatePattern('^\d{4}-\d{2}-\d{2}$')]
  [string]$BatchDate
)

$ErrorActionPreference = "Stop"

$projectRoot = Resolve-Path (Join-Path $PSScriptRoot "..\..")
$processedDir = Join-Path $projectRoot "crawler\data\processed\$BatchDate"
$sources = @(
  @{ Name = "products"; Entity = "product"; File = "products.jsonl" },
  @{ Name = "carts"; Entity = "order"; File = "carts.jsonl" },
  @{ Name = "users"; Entity = "user"; File = "users.jsonl" }
)

function Assert-JsonlContract {
  param(
    [Parameter(Mandatory = $true)]
    [string]$Path,

    [Parameter(Mandatory = $true)]
    [string]$SourceName,

    [Parameter(Mandatory = $true)]
    [string]$EntityName
  )

  $lineNumber = 0
  foreach ($line in Get-Content -LiteralPath $Path -Encoding UTF8) {
    $lineNumber += 1
    if ([string]::IsNullOrWhiteSpace($line)) {
      throw "Blank JSONL line in ${Path} at line $lineNumber"
    }

    try {
      $record = $line | ConvertFrom-Json -ErrorAction Stop
    } catch {
      throw "Invalid JSONL in ${Path} at line ${lineNumber}: $($_.Exception.Message)"
    }

    foreach ($field in @("entity", "source", "batch_date", "data")) {
      if ($record.PSObject.Properties.Name -notcontains $field) {
        throw "Missing required field '$field' in ${Path} at line $lineNumber"
      }
    }

    if ($record.entity -ne $EntityName) {
      throw "entity mismatch in ${Path} at line ${lineNumber}: expected '$EntityName', got '$($record.entity)'"
    }

    if ($record.source -ne $SourceName) {
      throw "source mismatch in ${Path} at line ${lineNumber}: expected '$SourceName', got '$($record.source)'"
    }

    if ($record.batch_date -ne $BatchDate) {
      throw "batch_date mismatch in ${Path} at line ${lineNumber}: expected '$BatchDate', got '$($record.batch_date)'"
    }

    if (-not ($record.data -is [string])) {
      throw "data must be a JSON string in ${Path} at line $lineNumber"
    }

    try {
      $null = $record.data | ConvertFrom-Json -ErrorAction Stop
    } catch {
      throw "data must contain valid JSON in ${Path} at line ${lineNumber}: $($_.Exception.Message)"
    }
  }

  if ($lineNumber -le 0) {
    throw "Processed ODS input is empty for ${SourceName}: $Path"
  }
}

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

  Assert-JsonlContract -Path $path -SourceName $sourceName -EntityName $source.Entity
  Write-Host "Found $sourceName input: $path"
}

Write-Host "ODS input check passed for batch date $BatchDate."
