$ErrorActionPreference = "Stop"

$requiredPaths = @(
  "README.md",
  ".env.example",
  "docker-compose.yml",
  "crawler/config/sources.json",
  "backend/README.md",
  ".dockerignore",
  "backend/Dockerfile",
  "backend/app/main.py",
  "backend/app/config.py",
  "backend/app/database.py",
  "backend/app/ads/router.py",
  "backend/app/ads/service.py",
  "backend/app/ads/repository.py",
  "backend/app/ads/schemas.py",
  "backend/app/ads/errors.py",
  "frontend/package.json",
  "frontend/Dockerfile",
  "frontend/nginx.conf",
  "frontend\src\App.vue",
  "frontend\src\main.js",
  "frontend\src\components\BaseChart.vue",
  "frontend\src\components\KpiCard.vue",
  "frontend\src\components\StatusBadge.vue",
  "frontend\src\components\DashboardPanel.vue",
  "frontend\src\data\mockAds.js",
  "frontend\src\services\adsApi.js",
  "frontend\src\utils\categoryShare.js",
  "frontend\src\utils\formatters.js",
  "frontend\src\styles\dashboard.css",
  "frontend\tests\dashboard-assets.test.mjs",
  "warehouse/README.md",
  "warehouse/hive/ods/create_ods_tables.sql",
  "warehouse/hive/dwd/create_dwd_tables.sql",
  "warehouse/hive/dim/create_dim_tables.sql",
  "warehouse/hive/dws/create_dws_tables.sql",
  "warehouse/hive/ads/create_ads_tables.sql",
  "deploy/mysql/init/02-create-ads-tables.sql",
  "deploy/scripts/smoke_test.ps1",
  "warehouse/scripts/check_ods_inputs.ps1",
  "warehouse/scripts/load_ods.ps1",
  "warehouse/scripts/run_dwd.ps1",
  "warehouse/scripts/run_ads.ps1",
  "warehouse/scripts/run_offline_batch.ps1",
  "warehouse/scripts/export_ads_mysql.ps1",
  "warehouse/scripts/quality_check.py",
  "warehouse/scripts/run_quality_check.ps1",
  "warehouse/spark/jobs/dwd_job.py",
  "warehouse/spark/jobs/dwd_transforms.py",
  "warehouse/spark/jobs/ads_job.py",
  "warehouse/spark/jobs/ads_sql.py",
  "warehouse/scripts/export_ads_mysql.py",
  "docs/project-acceptance.md",
  "docs/demo-runbook.md",
  "docs/deployment-integration.md",
  "docs/github-workflow.md",
  "deploy/hadoop/core-site.xml",
  "deploy/hadoop/hdfs-site.xml"
)

foreach ($path in $requiredPaths) {
  if (-not (Test-Path -LiteralPath $path)) {
    throw "Missing required path: $path"
  }
}

function Assert-FileContains {
  param(
    [string]$Path,
    [string]$Pattern,
    [string]$Description
  )

  if (-not (Select-String -LiteralPath $Path -Pattern $Pattern -Quiet)) {
    throw "Missing required configuration: $Description"
  }
}

function Assert-FileContainsCount {
  param(
    [string]$Path,
    [string]$Pattern,
    [int]$ExpectedCount,
    [string]$Description
  )

  $actualCount = @(
    Select-String -LiteralPath $Path -Pattern $Pattern
  ).Count
  if ($actualCount -ne $ExpectedCount) {
    throw "Missing required configuration: $Description"
  }
}

Assert-FileContains "docker-compose.yml" "^\s{2}backend:\s*$" "docker compose backend service"
Assert-FileContains "docker-compose.yml" "^\s{2}frontend:\s*$" "docker compose frontend service"
Assert-FileContainsCount "docker-compose.yml" "^\s{4}user: root\s*$" 2 "hadoop services run as root for Docker volume permissions"
Assert-FileContains ".env.example" "^BACKEND_PORT=8000$" "backend host port"
Assert-FileContains ".env.example" "^FRONTEND_PORT=8088$" "frontend host port"
Assert-FileContains ".env.example" "^SPARK_IMAGE=apache/spark:3\.5\.6$" "spark image override"
Assert-FileContains "warehouse/scripts/run_dwd.ps1" "/opt/spark/bin/spark-submit" "DWD script uses Apache Spark image submit path"
Assert-FileContains "warehouse/scripts/run_ads.ps1" "/opt/spark/bin/spark-submit" "ADS script uses Apache Spark image submit path"
Assert-FileContains "warehouse/scripts/run_dwd.ps1" 'PYTHONPATH=\$containerProjectDir' "DWD script sets Spark Python path"
Assert-FileContains "warehouse/scripts/run_ads.ps1" 'PYTHONPATH=\$containerProjectDir' "ADS script sets Spark Python path"
Assert-FileContains "warehouse/scripts/run_ads.ps1" "containerBatchExportDir" "ADS script copies only one batch snapshot directory"
Assert-FileContains "warehouse/scripts/run_offline_batch.ps1" "run-summary.json" "offline batch runner writes summary"
Assert-FileContains "warehouse/scripts/run_offline_batch.ps1" "logs/offline-batch" "offline batch runner writes stage logs"
Assert-FileContains "warehouse/scripts/run_offline_batch.ps1" "crawler', 'ods_check', 'ods_ddl', 'ods_load', 'dwd', 'ads', 'mysql_export', 'quality_check', 'smoke_test" "offline batch runner preserves stage order"
Assert-FileContains "warehouse/scripts/run_offline_batch.ps1" "quality_check.log" "offline batch runner writes quality check log"
Assert-FileContains "warehouse/scripts/run_offline_batch.ps1" "warehouse/scripts/run_quality_check.ps1" "offline batch runner invokes quality check wrapper"
Assert-FileContains "warehouse/scripts/run_quality_check.ps1" "quality_check.py" "quality check wrapper calls Python checker"
Assert-FileContains "warehouse/scripts/quality_check.py" "quality-report.json" "quality checker writes report"
Assert-FileContains "warehouse/spark/jobs/dwd_job.py" "thrift://hive-metastore:9083" "DWD Spark job uses external Hive metastore"
Assert-FileContains "warehouse/spark/jobs/ads_job.py" "thrift://hive-metastore:9083" "ADS Spark job uses external Hive metastore"
Assert-FileContains "deploy/scripts/smoke_test.ps1" "BackendBaseUrl" "smoke test backend URL parameter"
Assert-FileContains "deploy/scripts/smoke_test.ps1" "FrontendBaseUrl" "smoke test frontend URL parameter"
Assert-FileContains "docs/project-acceptance.md" "Crawler -> Local raw/processed files -> HDFS -> Hive ODS" "project acceptance documents end-to-end data flow"
Assert-FileContains "docs/project-acceptance.md" "quality-report.json" "project acceptance documents quality report evidence"
Assert-FileContains "docs/demo-runbook.md" "run_offline_batch.ps1" "demo runbook documents one-command offline batch"
Assert-FileContains "docs/demo-runbook.md" "http://127.0.0.1:8088" "demo runbook documents dashboard URL"

Write-Host "Project foundation check passed."
