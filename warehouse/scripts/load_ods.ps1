param(
  [Parameter(Mandatory = $true)]
  [ValidatePattern('^\d{4}-\d{2}-\d{2}$')]
  [string]$BatchDate
)

$ErrorActionPreference = "Stop"

$projectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$checkScript = Join-Path $projectRoot "warehouse\scripts\check_ods_inputs.ps1"
$processedDir = Join-Path $projectRoot "crawler\data\processed\$BatchDate"
$hdfsBase = "/warehouse/ecommerce/ods"
$runId = "ods-$BatchDate-$PID"
$containerTmpDir = "/tmp/$runId"

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

function Invoke-Compose {
  param(
    [Parameter(Mandatory = $true)]
    [string[]]$ComposeArgs
  )

  Invoke-Native -FilePath "docker" -Arguments (@("compose", "--project-directory", $projectRoot) + $ComposeArgs)
}

& $checkScript -BatchDate $BatchDate

$sources = @(
  @{ Name = "products"; File = "products.jsonl"; Table = "ods_products" },
  @{ Name = "carts"; File = "carts.jsonl"; Table = "ods_carts" },
  @{ Name = "users"; File = "users.jsonl"; Table = "ods_users" }
)

$partitionSqlContractByTable = @{
  "ods_products" = "ALTER TABLE ods_products ADD IF NOT EXISTS PARTITION"
  "ods_carts" = "ALTER TABLE ods_carts ADD IF NOT EXISTS PARTITION"
  "ods_users" = "ALTER TABLE ods_users ADD IF NOT EXISTS PARTITION"
}

$tmpDirCreated = $false
$loadFailed = $false
try {
  Invoke-Compose -ComposeArgs @("exec", "-T", "namenode", "mkdir", "-p", $containerTmpDir)
  $tmpDirCreated = $true

  foreach ($source in $sources) {
    $name = $source.Name
    $table = $source.Table
    $file = $source.File
    $localPath = Join-Path $processedDir $file
    $hdfsDir = "$hdfsBase/$name/dt=$BatchDate"
    $hdfsPath = "$hdfsDir/$file"
    $containerTmpPath = "$containerTmpDir/$file"

    Write-Host "Loading $name from $localPath to $hdfsPath"

    Invoke-Compose -ComposeArgs @("exec", "-T", "namenode", "hdfs", "dfs", "-mkdir", "-p", $hdfsDir)
    Invoke-Compose -ComposeArgs @("cp", $localPath, "namenode:$containerTmpPath")
    Invoke-Compose -ComposeArgs @("exec", "-T", "namenode", "hdfs", "dfs", "-put", "-f", $containerTmpPath, $hdfsPath)

    $alterPartitionSql = "ALTER TABLE $table ADD IF NOT EXISTS PARTITION"
    if ($partitionSqlContractByTable[$table] -ne $alterPartitionSql) {
      throw "Unexpected partition SQL table mapping for $table."
    }

    $partitionSql = "USE ecommerce_ods; $alterPartitionSql (dt='$BatchDate') LOCATION '$hdfsDir';"
    Invoke-Compose -ComposeArgs @("exec", "-T", "hive-server2", "beeline", "-u", "jdbc:hive2://localhost:10000", "-e", $partitionSql)
  }
}
catch {
  $loadFailed = $true
  throw
}
finally {
  if ($tmpDirCreated) {
    try {
      Invoke-Compose -ComposeArgs @("exec", "-T", "namenode", "rm", "-rf", $containerTmpDir)
    }
    catch {
      if ($loadFailed) {
        Write-Warning "Failed to clean container temp directory $containerTmpDir after load failure: $_"
      }
      else {
        throw
      }
    }
  }
}

Write-Host "ODS load completed for batch date $BatchDate."
