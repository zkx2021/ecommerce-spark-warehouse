param(
  [string]$BackendBaseUrl = "http://127.0.0.1:8000",
  [string]$FrontendBaseUrl = "http://127.0.0.1:8088",
  [int]$TimeoutSec = 10
)

$ErrorActionPreference = "Stop"

function Join-Url {
  param(
    [string]$BaseUrl,
    [string]$Path
  )

  return $BaseUrl.TrimEnd("/") + "/" + $Path.TrimStart("/")
}

function Write-Pass {
  param([string]$Message)
  Write-Host "[PASS] $Message" -ForegroundColor Green
}

function Write-Fail {
  param([string]$Message)
  Write-Host "[FAIL] $Message" -ForegroundColor Red
}

function Invoke-SmokeRequest {
  param(
    [string]$Url,
    [string]$Description
  )

  try {
    $response = Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec $TimeoutSec
  } catch {
    Write-Fail "$Description unavailable at $Url. $($_.Exception.Message)"
    throw
  }

  if ($response.StatusCode -lt 200 -or $response.StatusCode -ge 300) {
    Write-Fail "$Description returned HTTP $($response.StatusCode) at $Url"
    throw "$Description returned HTTP $($response.StatusCode)"
  }

  Write-Pass "$Description reachable at $Url"
  return $response
}

function Convert-SmokeJson {
  param(
    [string]$Content,
    [string]$Description
  )

  try {
    return $Content | ConvertFrom-Json
  } catch {
    Write-Fail "$Description did not return valid JSON. $($_.Exception.Message)"
    throw
  }
}

function Assert-ObjectProperties {
  param(
    [object]$Object,
    [string[]]$Properties,
    [string]$Description
  )

  $actualProperties = @($Object.PSObject.Properties.Name)
  foreach ($property in $Properties) {
    if ($actualProperties -notcontains $property) {
      Write-Fail "$Description missing property '$property'"
      throw "$Description missing property '$property'"
    }
  }
}

try {
  Write-Host "Running deployment smoke test..."

  $healthUrl = Join-Url $BackendBaseUrl "/api/health"
  $healthResponse = Invoke-SmokeRequest $healthUrl "Backend health endpoint"
  $health = Convert-SmokeJson $healthResponse.Content "Backend health endpoint"
  Assert-ObjectProperties $health @("status", "service") "Backend health payload"
  if ($health.status -ne "ok") {
    Write-Fail "Backend health status expected 'ok' but got '$($health.status)'"
    throw "Backend health status is not ok"
  }
  Write-Pass "Backend health payload shape is valid"

  $overviewUrl = Join-Url $BackendBaseUrl "/api/ads/overview"
  $overviewResponse = Invoke-SmokeRequest $overviewUrl "ADS overview endpoint"
  $overview = Convert-SmokeJson $overviewResponse.Content "ADS overview endpoint"
  Assert-ObjectProperties `
    $overview `
    @("date_id", "kpi", "trend", "product_rank", "category_share", "user_profile", "funnel") `
    "ADS overview payload"
  Assert-ObjectProperties `
    $overview.kpi `
    @("date_id", "total_sales_amount", "total_order_count", "paid_user_count", "avg_order_amount", "payment_conversion_rate") `
    "ADS KPI payload"
  Write-Pass "ADS overview payload shape is valid"

  $frontendResponse = Invoke-SmokeRequest $FrontendBaseUrl "Frontend dashboard"
  if ($frontendResponse.Content -notmatch "<div\s+id=(['""]app['""]|app)") {
    Write-Fail "Frontend dashboard HTML does not contain the Vue app root"
    throw "Frontend dashboard HTML missing Vue app root"
  }
  Write-Pass "Frontend dashboard page shape is valid"

  Write-Host "Deployment smoke test passed."
} catch {
  Write-Host "Deployment smoke test failed." -ForegroundColor Red
  exit 1
}
