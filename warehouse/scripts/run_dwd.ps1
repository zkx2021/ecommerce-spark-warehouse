param(
  [Parameter(Mandatory = $true)]
  [ValidatePattern('^\d{4}-\d{2}-\d{2}$')]
  [string]$BatchDate
)

$ErrorActionPreference = "Stop"

$projectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$dwdSql = Join-Path $projectRoot "warehouse\hive\dwd\create_dwd_tables.sql"
$dwdJob = Join-Path $projectRoot "warehouse\spark\jobs\dwd_job.py"
$dwdTransforms = Join-Path $projectRoot "warehouse\spark\jobs\dwd_transforms.py"
$warehouseDir = Join-Path $projectRoot "warehouse"
$runId = "dwd-$BatchDate-$PID"
$containerRunDir = "/tmp/$runId"
$containerProjectDir = "$containerRunDir/project"
$containerSqlPath = "$containerRunDir/create_dwd_tables.sql"

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

foreach ($path in @($dwdSql, $dwdJob, $dwdTransforms)) {
  if (-not (Test-Path -LiteralPath $path)) {
    throw "Missing DWD runtime path: $path"
  }
}

$hiveTmpCreated = $false
$sparkTmpCreated = $false
$runFailed = $false

try {
  Invoke-Compose -ComposeArgs @("exec", "-T", "hive-server2", "mkdir", "-p", $containerRunDir)
  $hiveTmpCreated = $true
  Invoke-Compose -ComposeArgs @("cp", $dwdSql, "hive-server2:$containerSqlPath")
  Invoke-Compose -ComposeArgs @("exec", "-T", "hive-server2", "beeline", "-u", "jdbc:hive2://localhost:10000", "-f", $containerSqlPath)

  Invoke-Compose -ComposeArgs @("exec", "-T", "spark-master", "mkdir", "-p", $containerProjectDir)
  $sparkTmpCreated = $true
  Invoke-Compose -ComposeArgs @("cp", $warehouseDir, "spark-master:$containerProjectDir")

  $sparkCommand = "cd $containerProjectDir && spark-submit --master spark://spark-master:7077 warehouse/spark/jobs/dwd_job.py --batch-date $BatchDate"
  Invoke-Compose -ComposeArgs @("exec", "-T", "spark-master", "bash", "-lc", $sparkCommand)
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
        Write-Warning "Failed to clean Hive temp directory $containerRunDir after DWD failure: $_"
      }
      else {
        throw
      }
    }
  }

  if ($sparkTmpCreated) {
    try {
      Invoke-Compose -ComposeArgs @("exec", "-T", "spark-master", "rm", "-rf", $containerRunDir)
    }
    catch {
      if ($runFailed) {
        Write-Warning "Failed to clean Spark temp directory $containerRunDir after DWD failure: $_"
      }
      else {
        throw
      }
    }
  }
}

Write-Host "DWD Spark batch completed for batch date $BatchDate."
