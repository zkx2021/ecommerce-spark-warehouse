$ErrorActionPreference = "Stop"

$requiredPaths = @(
  "README.md",
  ".env.example",
  "docker-compose.yml",
  "crawler/config/sources.json",
  "backend/README.md",
  "backend/app/main.py",
  "backend/app/config.py",
  "backend/app/database.py",
  "backend/app/ads/router.py",
  "backend/app/ads/service.py",
  "backend/app/ads/repository.py",
  "backend/app/ads/schemas.py",
  "backend/app/ads/errors.py",
  "frontend/package.json",
  "warehouse/README.md",
  "warehouse/hive/ods/create_ods_tables.sql",
  "warehouse/hive/dwd/create_dwd_tables.sql",
  "warehouse/hive/dim/create_dim_tables.sql",
  "warehouse/hive/dws/create_dws_tables.sql",
  "warehouse/hive/ads/create_ads_tables.sql",
  "deploy/mysql/init/02-create-ads-tables.sql",
  "warehouse/scripts/check_ods_inputs.ps1",
  "warehouse/scripts/load_ods.ps1",
  "warehouse/scripts/run_dwd.ps1",
  "warehouse/scripts/run_ads.ps1",
  "warehouse/scripts/export_ads_mysql.ps1",
  "warehouse/spark/jobs/dwd_job.py",
  "warehouse/spark/jobs/dwd_transforms.py",
  "warehouse/spark/jobs/ads_job.py",
  "warehouse/spark/jobs/ads_sql.py",
  "warehouse/scripts/export_ads_mysql.py",
  "docs/github-workflow.md",
  "deploy/hadoop/core-site.xml",
  "deploy/hadoop/hdfs-site.xml"
)

foreach ($path in $requiredPaths) {
  if (-not (Test-Path -LiteralPath $path)) {
    throw "Missing required path: $path"
  }
}

Write-Host "Project foundation check passed."
