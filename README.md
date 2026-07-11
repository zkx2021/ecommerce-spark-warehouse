# ecommerce-spark-warehouse

电商 Spark 离线数仓分析与可视化系统。

## Project Goal

This project builds an offline ecommerce data warehouse using Spark, HDFS, and Hive. It collects ecommerce-like data through a configurable crawler, stores raw data in HDFS, builds layered Hive tables, computes offline metrics with Spark SQL, and exports ADS results to MySQL for the FastAPI ADS API and an active Vue/ECharts dashboard UI.

The offline warehouse now includes ODS, DWD, DIM, DWS, ADS, and MySQL ADS export assets. The dim, dws, ads layers prepare dashboard-ready metrics after the detailed DWD layer.

## Tech Stack

- Data collection: Python crawler
- Storage: HDFS
- Warehouse: Hive
- Compute: Spark SQL
- Result store: MySQL
- API: FastAPI ADS data service
- Dashboard: Vue 3 + ECharts dashboard
- Deployment: Docker Compose

## Current Data Flow

```text
Crawler -> Local raw files -> HDFS -> Hive ODS/DWD/DIM/DWS/ADS
        -> Spark offline jobs -> MySQL ADS result tables
        -> FastAPI ADS API -> Vue/ECharts dashboard
```

## Repository Structure

```text
crawler/      Data collection module
warehouse/    HDFS, Hive, and Spark warehouse assets
backend/      FastAPI ADS API backend
frontend/     Vue/ECharts dashboard UI
deploy/       Local and server deployment scripts
docs/         Architecture, data model, deployment, and GitHub workflow docs
```

## First Verification

```powershell
powershell -ExecutionPolicy Bypass -File deploy/scripts/check.ps1
```

## Local Deployment

The integrated local deployment connects MySQL ADS tables to the FastAPI API and the Vue/ECharts dashboard:

```text
MySQL ADS tables -> FastAPI ADS API -> Vue/ECharts dashboard
```

Start the stack with Docker Compose:

```powershell
docker compose up -d --build
```

Default local endpoints:

- Dashboard: `http://127.0.0.1:8088`
- FastAPI health: `http://127.0.0.1:8000/api/health`
- ADS overview: `http://127.0.0.1:8000/api/ads/overview`

Run the deployment smoke test after services are running:

```powershell
powershell -ExecutionPolicy Bypass -File deploy/scripts/smoke_test.ps1 -BackendBaseUrl http://127.0.0.1:8000 -FrontendBaseUrl http://127.0.0.1:8088
```

The smoke test expects ADS rows to exist in MySQL. See [docs/deployment-integration.md](docs/deployment-integration.md) for ports, environment variables, startup paths, ADS export steps, and the difference between real API data and dashboard mock fallback.
