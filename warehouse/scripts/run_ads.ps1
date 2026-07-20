param(
  [Parameter(Mandatory = $true)]
  [ValidatePattern('^\d{4}-\d{2}-\d{2}$')]
  [string]$BatchDate
)

$ErrorActionPreference = "Stop"

$projectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$dimSql = Join-Path $projectRoot "warehouse\hive\dim\create_dim_tables.sql"
$dwsSql = Join-Path $projectRoot "warehouse\hive\dws\create_dws_tables.sql"
$adsSql = Join-Path $projectRoot "warehouse\hive\ads\create_ads_tables.sql"
$adsJob = Join-Path $projectRoot "warehouse\spark\jobs\ads_job.py"
$adsSqlTemplates = Join-Path $projectRoot "warehouse\spark\jobs\ads_sql.py"
$warehouseDir = Join-Path $projectRoot "warehouse"
$hostExportRoot = Join-Path $projectRoot "warehouse\data\ads"
$hostBatchExportDir = Join-Path $hostExportRoot $BatchDate
$runId = "ads-$BatchDate-$PID"
$containerRunDir = "/tmp/$runId"
$containerProjectDir = "$containerRunDir/project"
$containerDimSqlPath = "$containerRunDir/create_dim_tables.sql"
$containerDwsSqlPath = "$containerRunDir/create_dws_tables.sql"
$containerAdsSqlPath = "$containerRunDir/create_ads_tables.sql"
$containerExportRoot = "$containerRunDir/ads"
$containerBatchExportDir = "$containerExportRoot/$BatchDate"

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

foreach ($path in @($dimSql, $dwsSql, $adsSql, $adsJob, $adsSqlTemplates, $warehouseDir)) {
  if (-not (Test-Path -LiteralPath $path)) {
    throw "Missing ADS runtime path: $path"
  }
}

$hiveTmpCreated = $false
$sparkTmpCreated = $false
$runFailed = $false

try {
  Invoke-Compose -ComposeArgs @("exec", "-T", "hive-server2", "mkdir", "-p", $containerRunDir)
  $hiveTmpCreated = $true
  Invoke-Compose -ComposeArgs @("cp", $dimSql, "hive-server2:$containerDimSqlPath")
  Invoke-Compose -ComposeArgs @("cp", $dwsSql, "hive-server2:$containerDwsSqlPath")
  Invoke-Compose -ComposeArgs @("cp", $adsSql, "hive-server2:$containerAdsSqlPath")
  Invoke-Compose -ComposeArgs @("exec", "-T", "hive-server2", "beeline", "-u", "jdbc:hive2://localhost:10000", "-f", $containerDimSqlPath)
  Invoke-Compose -ComposeArgs @("exec", "-T", "hive-server2", "beeline", "-u", "jdbc:hive2://localhost:10000", "-f", $containerDwsSqlPath)
  Invoke-Compose -ComposeArgs @("exec", "-T", "hive-server2", "beeline", "-u", "jdbc:hive2://localhost:10000", "-f", $containerAdsSqlPath)

  Invoke-Compose -ComposeArgs @("exec", "-T", "--user", "root", "spark-master", "mkdir", "-p", $containerProjectDir)
  $sparkTmpCreated = $true
  Invoke-Compose -ComposeArgs @("cp", $warehouseDir, "spark-master:$containerProjectDir")

  $sparkCommand = "cd $containerProjectDir && PYTHONPATH=$containerProjectDir /opt/spark/bin/spark-submit --master spark://spark-master:7077 warehouse/spark/jobs/ads_job.py --batch-date $BatchDate --export-root $containerExportRoot"
  Invoke-Compose -ComposeArgs @("exec", "-T", "--user", "root", "spark-master", "bash", "-lc", $sparkCommand)

  if (-not (Test-Path -LiteralPath $hostExportRoot)) {
    New-Item -ItemType Directory -Force -Path $hostExportRoot | Out-Null
  }
  if (Test-Path -LiteralPath $hostBatchExportDir) {
    Remove-Item -LiteralPath $hostBatchExportDir -Recurse -Force
  }
  Invoke-Compose -ComposeArgs @("cp", "spark-master:$containerBatchExportDir", $hostBatchExportDir)
}
catch {
  $runFailed = $true
  throw
}
finally {
  if ($hiveTmpCreated) {
    try {
      Invoke-Compose -ComposeArgs @("exec", "-T", "hive-server2", "rm", "-rf", $containerRunDir)
    }
    catch {
      if ($runFailed) {
        Write-Warning "Failed to clean Hive temp directory $containerRunDir after ADS failure: $_"
      }
      else {
        throw
      }
    }
  }

  if ($sparkTmpCreated) {
    try {
      Invoke-Compose -ComposeArgs @("exec", "-T", "--user", "root", "spark-master", "rm", "-rf", $containerRunDir)
    }
    catch {
      if ($runFailed) {
        Write-Warning "Failed to clean Spark temp directory $containerRunDir after ADS failure: $_"
      }
      else {
        throw
      }
    }
  }
}

Write-Host "ADS Spark batch completed for batch date $BatchDate."
