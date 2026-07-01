$ErrorActionPreference = "Stop"

$requiredPaths = @(
  "README.md",
  ".env.example",
  "docker-compose.yml",
  "deploy/hadoop/core-site.xml",
  "deploy/hadoop/hdfs-site.xml"
)

foreach ($path in $requiredPaths) {
  if (-not (Test-Path -LiteralPath $path)) {
    throw "Missing required path: $path"
  }
}

Write-Host "Project foundation root check passed."
