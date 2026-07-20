# Deployment Integration

This guide starts the local stack that connects the ADS MySQL result tables to the FastAPI API and the Vue/ECharts dashboard.

## Service Path

```text
MySQL ADS tables -> FastAPI ADS API -> Vue/ECharts dashboard
```

The full offline path remains:

```text
Crawler -> HDFS -> Hive ODS/DWD/DIM/DWS/ADS
        -> Spark jobs -> MySQL ADS result tables
        -> FastAPI ADS API -> Vue/ECharts dashboard
```

The local Hadoop containers run as `root` so Namenode and Datanode can initialize Docker-managed HDFS data volumes on Docker Desktop.

## Foundation Check

Run this first after cloning or changing deployment files:

```powershell
powershell -ExecutionPolicy Bypass -File deploy/scripts/check.ps1
```

## Configuration

Copy `.env.example` to `.env` if you need local overrides. Docker Compose uses these defaults when `.env` is absent.

| Variable | Default | Purpose |
| --- | --- | --- |
| `MYSQL_HOST` | `mysql` | MySQL service hostname for warehouse scripts |
| `MYSQL_PORT` | `3306` | MySQL host port |
| `MYSQL_ROOT_PASSWORD` | `root_password` | MySQL root password for the local container |
| `MYSQL_DATABASE` | `ecommerce_ads` | ADS result database |
| `MYSQL_USER` | `ecommerce` | MySQL application user |
| `MYSQL_PASSWORD` | `ecommerce_password` | MySQL application password |
| `HDFS_NAMENODE` | `hdfs://namenode:8020` | HDFS namenode URI |
| `HIVE_SERVER_HOST` | `hive-server2` | HiveServer2 service hostname |
| `HIVE_SERVER_PORT` | `10000` | HiveServer2 port |
| `SPARK_IMAGE` | `apache/spark:3.5.6` | Spark master and worker image |
| `SPARK_MASTER_URL` | `spark://spark-master:7077` | Spark master URL |
| `BACKEND_PORT` | `8000` | Host port for FastAPI |
| `FRONTEND_PORT` | `8088` | Host port for the production dashboard |

Inside the backend container, the ADS API reads `ADS_MYSQL_HOST=mysql`, `ADS_MYSQL_PORT=3306`, `ADS_MYSQL_DATABASE=ecommerce_ads`, `ADS_MYSQL_USER=ecommerce`, and `ADS_MYSQL_PASSWORD=ecommerce_password`.

## Start The Stack

Start all services:

```powershell
docker compose up -d --build
```

Useful narrower starts:

```powershell
docker compose up -d mysql backend frontend
docker compose up -d namenode datanode mysql hive-metastore hive-server2 spark-master spark-worker
```

Check rendered Compose configuration without starting containers:

```powershell
docker compose config
```

## Endpoints

| Service | URL |
| --- | --- |
| Dashboard | `http://127.0.0.1:8088` |
| Backend health | `http://127.0.0.1:8000/api/health` |
| ADS overview | `http://127.0.0.1:8000/api/ads/overview` |
| HDFS namenode UI | `http://127.0.0.1:9870` |
| Spark master UI | `http://127.0.0.1:8081` |
| HiveServer2 | `127.0.0.1:10000` |
| MySQL | `127.0.0.1:3306` |

## Smoke Test

On a fresh stack, verify that the backend, frontend, and API proxy are reachable even before ADS rows exist:

```powershell
powershell -ExecutionPolicy Bypass -File deploy/scripts/smoke_test.ps1 -BackendBaseUrl http://127.0.0.1:8000 -FrontendBaseUrl http://127.0.0.1:8088 -AllowMissingAds
```

For a strict end-to-end ADS data check, run the one-command offline batch after the Docker Compose stack is running:

```powershell
powershell -ExecutionPolicy Bypass -File warehouse/scripts/run_offline_batch.ps1 -BatchDate 2026-07-01
```

If crawler data already exists and you only want to refresh warehouse and dashboard-facing data:

```powershell
powershell -ExecutionPolicy Bypass -File warehouse/scripts/run_offline_batch.ps1 -BatchDate 2026-07-01 -SkipStages crawler
```

If a downstream stage fails, inspect `logs/offline-batch/<batch-date>/<run-id>/<stage>.log`, fix the local issue, then resume:

```powershell
powershell -ExecutionPolicy Bypass -File warehouse/scripts/run_offline_batch.ps1 -BatchDate 2026-07-01 -StartFrom dwd
```

The expanded manual command chain remains useful for troubleshooting individual stages:

```powershell
python crawler/run.py --batch-date 2026-07-01
powershell -ExecutionPolicy Bypass -File warehouse/scripts/check_ods_inputs.ps1 -BatchDate 2026-07-01
docker compose exec -T hive-server2 mkdir -p /tmp/ods-ddl
docker compose cp warehouse/hive/ods/create_ods_tables.sql hive-server2:/tmp/ods-ddl/create_ods_tables.sql
docker compose exec -T hive-server2 beeline -u jdbc:hive2://localhost:10000 -f /tmp/ods-ddl/create_ods_tables.sql
powershell -ExecutionPolicy Bypass -File warehouse/scripts/load_ods.ps1 -BatchDate 2026-07-01
powershell -ExecutionPolicy Bypass -File warehouse/scripts/run_dwd.ps1 -BatchDate 2026-07-01
powershell -ExecutionPolicy Bypass -File warehouse/scripts/run_ads.ps1 -BatchDate 2026-07-01
powershell -ExecutionPolicy Bypass -File warehouse/scripts/export_ads_mysql.ps1 -BatchDate 2026-07-01
```

After services are running and ADS data has been exported to MySQL, verify the deployed API and dashboard:

```powershell
powershell -ExecutionPolicy Bypass -File deploy/scripts/smoke_test.ps1 -BackendBaseUrl http://127.0.0.1:8000 -FrontendBaseUrl http://127.0.0.1:8088
```

The script checks:

- `/api/health` availability and `status=ok`
- `/api/ads/overview` top-level payload shape
- dashboard HTML availability and Vue app root
- frontend `/api/health` proxying through Nginx or Vite

If services are not running, the script exits non-zero with a clear `[FAIL]` message.

## Real API Data vs Mock Fallback

The production dashboard container serves static assets through Nginx and proxies `/api/` to the backend service. In this path, data comes from MySQL ADS tables through FastAPI.

During local Vite development, the dashboard calls same-origin `/api/...` paths and `frontend/vite.config.js` proxies them to `http://127.0.0.1:8000`. If the API is unavailable, the dashboard can show mock fallback data so the UI remains inspectable, but that is not proof of the MySQL/FastAPI integration path. Use the smoke test or direct API requests when verifying real ADS data.

## Stop Services

```powershell
docker compose down
```

To remove persisted local data volumes as well:

```powershell
docker compose down -v
```
