$ErrorActionPreference = "Stop"

$requiredPaths = @(
  "README.md",
  ".env.example",
  "docker-compose.yml"
)

foreach ($path in $requiredPaths) {
  if (-not (Test-Path -LiteralPath $path)) {
    throw "Missing required path: $path"
  }
}

Write-Host "Project foundation root check passed."
