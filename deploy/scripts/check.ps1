$ErrorActionPreference = "Stop"

$requiredPaths = @(
  "README.md",
  ".env.example",
  "docker-compose.yml",
  "crawler/config/sources.json",
  "backend/app/main.py",
  "frontend/package.json",
  "warehouse/README.md",
  "warehouse/hive/ods/create_ods_tables.sql",
  "warehouse/hive/dwd/create_dwd_tables.sql",
  "warehouse/scripts/check_ods_inputs.ps1",
  "warehouse/scripts/load_ods.ps1",
  "warehouse/scripts/run_dwd.ps1",
  "warehouse/spark/jobs/dwd_job.py",
  "warehouse/spark/jobs/dwd_transforms.py",
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
