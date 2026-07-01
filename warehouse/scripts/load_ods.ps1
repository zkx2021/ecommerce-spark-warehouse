param(
  [Parameter(Mandatory = $true)]
  [ValidatePattern('^\d{4}-\d{2}-\d{2}$')]
  [string]$BatchDate
)

$ErrorActionPreference = "Stop"

$projectRoot = Resolve-Path (Join-Path $PSScriptRoot "..\..")
$checkScript = Join-Path $projectRoot "warehouse\scripts\check_ods_inputs.ps1"
$processedDir = Join-Path $projectRoot "crawler\data\processed\$BatchDate"
$hdfsBase = "/warehouse/ecommerce/ods"

& $checkScript -BatchDate $BatchDate

$sources = @(
  @{ Name = "products"; File = "products.jsonl"; Table = "ods_products"; PartitionSqlPrefix = "ALTER TABLE ods_products ADD IF NOT EXISTS PARTITION" },
  @{ Name = "carts"; File = "carts.jsonl"; Table = "ods_carts"; PartitionSqlPrefix = "ALTER TABLE ods_carts ADD IF NOT EXISTS PARTITION" },
  @{ Name = "users"; File = "users.jsonl"; Table = "ods_users"; PartitionSqlPrefix = "ALTER TABLE ods_users ADD IF NOT EXISTS PARTITION" }
)

foreach ($source in $sources) {
  $name = $source.Name
  $table = $source.Table
  $file = $source.File
  $localPath = Join-Path $processedDir $file
  $hdfsDir = "$hdfsBase/$name/dt=$BatchDate"
  $hdfsPath = "$hdfsDir/$file"

  Write-Host "Loading $name from $localPath to $hdfsPath"

  docker compose exec namenode hdfs dfs -mkdir -p $hdfsDir
  docker compose cp $localPath "namenode:/tmp/$file"
  docker compose exec namenode hdfs dfs -put -f "/tmp/$file" $hdfsPath
  docker compose exec namenode rm -f "/tmp/$file"

  $partitionSql = "USE ecommerce_ods; $($source.PartitionSqlPrefix) (dt='$BatchDate') LOCATION '$hdfsDir';"
  docker compose exec hive-server2 beeline -u "jdbc:hive2://localhost:10000" -e $partitionSql
}

Write-Host "ODS load completed for batch date $BatchDate."
