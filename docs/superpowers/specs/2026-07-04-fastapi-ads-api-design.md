# FastAPI ADS API Design

## Goal

Build a FastAPI backend data service that reads MySQL ADS result tables and exposes stable JSON APIs for the future Vue and ECharts dashboard.

## Scope

This phase implements backend read APIs only. It does not build the Vue dashboard, trigger Spark jobs, mutate warehouse data, or manage MySQL schema migrations.

The API reads the six ADS tables created in `deploy/mysql/init/02-create-ads-tables.sql`:

- `ads_kpi_daily`
- `ads_sales_trend_daily`
- `ads_product_rank_daily`
- `ads_category_share_daily`
- `ads_user_profile_daily`
- `ads_funnel_daily`

## API Endpoints

All endpoints live under `/api/ads`.

| Endpoint | Purpose |
| --- | --- |
| `GET /api/ads/overview` | Return one dashboard-ready payload containing all ADS sections for a batch date. |
| `GET /api/ads/kpi` | Return KPI metrics for a batch date. |
| `GET /api/ads/trend` | Return sales trend rows for a batch date. |
| `GET /api/ads/products/rank` | Return product ranking rows for a batch date. |
| `GET /api/ads/categories/share` | Return category sales share rows for a batch date. |
| `GET /api/ads/users/profile` | Return user profile rows grouped by dimension type and value. |
| `GET /api/ads/funnel` | Return funnel rows ordered by stage. |

Each endpoint accepts an optional `date` query parameter in `YYYY-MM-DD` format.

- If `date` is supplied, the API reads that exact `date_id`.
- If `date` is omitted, the API resolves the latest available `date_id` from ADS tables.
- If the requested or inferred date has no data for the requested section, the API returns `404`.
- If MySQL cannot be reached, the API returns `503`.
- If `date` does not match `YYYY-MM-DD`, FastAPI returns `422`.

## Architecture

Use a small layered backend:

```text
FastAPI app
  -> ADS router
  -> ADS service
  -> ADS repository
  -> MySQL connection provider
```

### Router

The router owns URL paths, query parameter validation, dependency wiring, and HTTP exception mapping. It should not contain SQL.

### Service

The service owns dashboard use cases:

- resolve `date` to the requested date or latest date
- call repository methods for each ADS section
- compose `/api/ads/overview`
- normalize "no rows" into a domain-level not-found result

### Repository

The repository owns SQL and maps database rows to dictionaries. It uses parameterized queries for every request. Queries are read-only and scoped to known table and column names.

### Schemas

Pydantic schemas define stable response shapes for frontend consumers. Numeric values from MySQL decimals should be converted to JSON-safe numbers or strings consistently. The preferred shape is JSON numbers where precision is acceptable for dashboard display.

### Configuration

MySQL settings come from environment variables with Docker Compose-compatible defaults:

- `ADS_MYSQL_HOST`, default `localhost`
- `ADS_MYSQL_PORT`, default `3306`
- `ADS_MYSQL_DATABASE`, default `ecommerce_ads`
- `ADS_MYSQL_USER`, default `ecommerce`
- `ADS_MYSQL_PASSWORD`, default `ecommerce_password`

The backend dependency list should include `mysql-connector-python` so the API can connect to MySQL without relying on the warehouse exporter dependency.

## Response Shape

Every section response includes the resolved `date_id`.

KPI response:

```json
{
  "date_id": "2026-07-01",
  "total_sales_amount": 12345.67,
  "total_order_count": 120,
  "paid_user_count": 86,
  "avg_order_amount": 102.88,
  "payment_conversion_rate": 0.7500
}
```

List endpoints return:

```json
{
  "date_id": "2026-07-01",
  "items": []
}
```

Overview response:

```json
{
  "date_id": "2026-07-01",
  "kpi": {},
  "trend": [],
  "product_rank": [],
  "category_share": [],
  "user_profile": [],
  "funnel": []
}
```

## Error Handling

- Invalid date format: `422` from FastAPI query validation.
- No ADS dates available: `404` with a clear message.
- No rows for a requested section and date: `404`.
- MySQL connection or query failure: `503`.
- Unexpected errors should remain visible in tests and be handled by FastAPI's default behavior during development.

## Testing Strategy

Tests should not require a real MySQL server. Use fake repository or fake connection objects to test:

- health endpoint remains unchanged
- each ADS endpoint returns expected JSON for explicit `date`
- omitted `date` resolves to latest date
- `/api/ads/overview` composes all sections
- empty ADS data returns `404`
- repository/database failure maps to `503`
- invalid date format returns `422`

Repository tests can use fake cursor objects to verify SQL parameters and result mapping without connecting to MySQL.

## Documentation

Update backend or root documentation with:

- API startup command
- required environment variables
- endpoint list
- note that MySQL ADS data must be loaded by the warehouse exporter before API calls return data

## Verification

Expected local checks:

```powershell
python -m pytest backend/tests -q
powershell -ExecutionPolicy Bypass -File deploy/scripts/check.ps1
```

If the implementation touches shared requirements or root docs, run any affected existing tests as well.
