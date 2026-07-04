# FastAPI ADS API

This backend exposes ADS-layer ecommerce metrics from the MySQL result store as a FastAPI data service.

## Setup

```powershell
python -m pip install -r backend/requirements.txt
python -m uvicorn backend.app.main:app --reload
```

## MySQL Configuration

The API reads ADS tables exported from the warehouse. Configure MySQL with environment variables, or use the local defaults:

| Variable | Default |
| --- | --- |
| `ADS_MYSQL_HOST` | `localhost` |
| `ADS_MYSQL_PORT` | `3306` |
| `ADS_MYSQL_DATABASE` | `ecommerce_ads` |
| `ADS_MYSQL_USER` | `ecommerce` |
| `ADS_MYSQL_PASSWORD` | `ecommerce_password` |

Run `warehouse/scripts/export_ads_mysql.ps1` before calling ADS APIs so MySQL contains the latest ADS results.

## Endpoints

- `/api/health`
- `/api/ads/overview`
- `/api/ads/kpi`
- `/api/ads/trend`
- `/api/ads/products/rank`
- `/api/ads/categories/share`
- `/api/ads/users/profile`
- `/api/ads/funnel`

ADS endpoints accept an optional `?date=YYYY-MM-DD` query parameter. When `date` is omitted, the API uses the latest available ADS date from MySQL.
