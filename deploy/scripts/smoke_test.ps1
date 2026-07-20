param(
  [string]$BackendBaseUrl = "http://127.0.0.1:8000",
  [string]$FrontendBaseUrl = "http://127.0.0.1:8088",
  [int]$TimeoutSec = 10,
  [switch]$AllowMissingAds
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

function Test-MissingAdsResponse {
  param([string]$Url)

  try {
    Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec $TimeoutSec | Out-Null
    return $false
  } catch {
    $response = $_.Exception.Response
    if (-not $response) {
      throw
    }

    $statusCode = [int]$response.StatusCode
    if ($statusCode -ne 404) {
      throw
    }

    $openApiUrl = Join-Url $BackendBaseUrl "/openapi.json"
    $openApiResponse = Invoke-SmokeRequest $openApiUrl "Backend OpenAPI document"
    $openApi = Convert-SmokeJson $openApiResponse.Content "Backend OpenAPI document"
    $routeNames = @($openApi.paths.PSObject.Properties.Name)
    if ($routeNames -notcontains "/api/ads/overview") {
      Write-Fail "ADS overview route is missing from the backend OpenAPI document"
      throw "ADS overview route is not registered"
    }

    Write-Pass "ADS overview endpoint is reachable but no ADS data has been exported yet"
    return $true
  }
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

function Assert-HealthPayload {
  param(
    [object]$Health,
    [string]$Description
  )

  Assert-ObjectProperties $Health @("status", "service") $Description
  if ($Health.status -ne "ok") {
    Write-Fail "$Description status expected 'ok' but got '$($Health.status)'"
    throw "$Description status is not ok"
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
  Assert-HealthPayload $health "Backend health payload"
  Write-Pass "Backend health payload shape is valid"

  $overviewUrl = Join-Url $BackendBaseUrl "/api/ads/overview"
  if ($AllowMissingAds -and (Test-MissingAdsResponse $overviewUrl)) {
    Write-Host "Skipping ADS payload shape check until ADS rows are exported to MySQL."
  } else {
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
  }

  $frontendResponse = Invoke-SmokeRequest $FrontendBaseUrl "Frontend dashboard"
  if ($frontendResponse.Content -notmatch "<div\s+id=(['""]app['""]|app)") {
    Write-Fail "Frontend dashboard HTML does not contain the Vue app root"
    throw "Frontend dashboard HTML missing Vue app root"
  }
  Write-Pass "Frontend dashboard page shape is valid"

  $frontendHealthUrl = Join-Url $FrontendBaseUrl "/api/health"
  $frontendHealthResponse = Invoke-SmokeRequest $frontendHealthUrl "Frontend API proxy health endpoint"
  $frontendHealth = Convert-SmokeJson $frontendHealthResponse.Content "Frontend API proxy health endpoint"
  Assert-HealthPayload $frontendHealth "Frontend API proxy health payload"
  Write-Pass "Frontend API proxy path is valid"

  Write-Host "Deployment smoke test passed."
} catch {
  Write-Host "Deployment smoke test failed." -ForegroundColor Red
  exit 1
}
