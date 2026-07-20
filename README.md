# ecommerce-spark-warehouse

电商 Spark 离线数仓分析与可视化系统。

This project is a complete offline ecommerce data warehouse demo built with Spark, HDFS, Hive, MySQL, FastAPI, Vue 3, and ECharts. It collects ecommerce data through a crawler, stores raw data in HDFS, builds layered Hive warehouse tables, computes offline ADS metrics with Spark SQL, exports results to MySQL, and presents the final metrics through an API-backed operations dashboard.

## Project Highlights

- End-to-end offline warehouse: `Crawler -> HDFS -> Hive -> Spark -> MySQL -> FastAPI -> Vue/ECharts`.
- Required big data stack included: Spark, HDFS, and Hive.
- Crawler-based data ingestion from public ecommerce-like APIs.
- Warehouse layers: ODS, DWD, DIM, DWS, ADS, and MySQL ADS export.
- One-command local batch runner with stage logs, resume support, quality checks, and smoke tests.
- API-backed dashboard for sales KPI, trend, product rank, category share, user profile, and conversion funnel.
- Docker Compose local deployment for Hadoop, Hive, Spark, MySQL, backend, and frontend services.

## Tech Stack

| Area | Stack |
| --- | --- |
| Data collection | Python crawler |
| Storage | HDFS |
| Warehouse | Hive |
| Compute | Spark SQL / PySpark |
| Result database | MySQL |
| API | FastAPI |
| Dashboard | Vue 3 + ECharts dashboard |
| Deployment | Docker Compose |
| Validation | PowerShell scripts, pytest, Node asset checks |

Dashboard: Vue 3 + ECharts dashboard.

## Current Data Flow

```text
Crawler -> Local raw/processed files -> HDFS -> Hive ODS
        -> Spark DWD -> Spark DIM/DWS/ADS -> MySQL ADS result tables
        -> FastAPI ADS API -> Vue/ECharts dashboard
```

## Warehouse Layers

| Layer | Purpose | Main assets |
| --- | --- | --- |
| ODS | Source-aligned raw tables | `warehouse/hive/ods` |
| DWD | Clean detailed product, user, and cart/order detail data | `warehouse/hive/dwd`, `warehouse/spark/jobs/dwd_*` |
| DIM | Shared product, category, user, and date dimensions | `warehouse/hive/dim` |
| DWS | Subject-level daily summaries | `warehouse/hive/dws` |
| ADS | Dashboard-ready metrics | `warehouse/hive/ads`, `warehouse/spark/jobs/ads_*` |
| MySQL ADS | API-facing result tables | `deploy/mysql/init/02-create-ads-tables.sql` |

## Repository Structure

```text
crawler/      Data collection module and source configuration
warehouse/    HDFS, Hive, Spark jobs, ADS exports, and batch scripts
backend/      FastAPI ADS API backend
frontend/     Vue/ECharts dashboard UI
deploy/       Docker, Hadoop, MySQL, smoke test, and deployment scripts
docs/         Acceptance guide, demo runbook, deployment, and workflow docs
```

## Data Sources

The crawler source configuration is stored in `crawler/config/sources.json`.

| Source | URL | Output |
| --- | --- | --- |
| products | `https://dummyjson.com/products?limit=200` | Product catalog data |
| carts | `https://dummyjson.com/carts` | Cart/order detail data |
| users | `https://dummyjson.com/users` | User profile data |

Crawler output is written by batch date under:

```text
crawler/data/raw/<batch-date>/
crawler/data/processed/<batch-date>/
```

## Quick Start

Run the foundation check first:

```powershell
powershell -ExecutionPolicy Bypass -File deploy/scripts/check.ps1
```

Start the local stack:

```powershell
docker compose up -d --build
```

Run the complete offline chain for the demo batch date:

```powershell
powershell -ExecutionPolicy Bypass -File warehouse/scripts/run_offline_batch.ps1 -BatchDate 2026-07-01
```

The batch runner executes:

```text
crawler -> ods_check -> ods_ddl -> ods_load -> dwd -> ads -> mysql_export -> quality_check -> smoke_test
```

Every run writes logs and a summary under:

```text
logs/offline-batch/<batch-date>/<run-id>/
```

## Local Endpoints

| Service | URL |
| --- | --- |
| Dashboard | `http://127.0.0.1:8088` |
| FastAPI health | `http://127.0.0.1:8000/api/health` |
| ADS overview | `http://127.0.0.1:8000/api/ads/overview?date=2026-07-01` |
| HDFS Namenode UI | `http://127.0.0.1:9870` |
| Spark Master UI | `http://127.0.0.1:8081` |

## Dashboard Metrics

The Vue/ECharts dashboard reads FastAPI ADS data and displays:

- KPI cards: sales amount, order count, paid users, payment conversion rate.
- Sales trend: sales amount, order count, paid users.
- Product sales rank: top products by sales amount.
- Category share: Top 6 categories plus `其他` to keep labels readable.
- User profile: age group, country, and gender dimensions.
- Conversion funnel: cart, order, and payment stages.

## Final Validation Snapshot

Latest full-chain validation:

| Item | Result |
| --- | --- |
| Batch date | `2026-07-01` |
| Run ID | `20260720-190621` |
| Run status | `success` |
| Crawler rows | products `194`, carts `30`, users `30` |
| ADS sales amount | `725,678.95` |
| ADS order count | `30` |
| ADS paid users | `30` |
| ADS payment conversion rate | `100.0%` |
| Quality rules | `26/26` passed |

Validation evidence:

- `logs/offline-batch/2026-07-01/20260720-190621/run-summary.json`
- `logs/offline-batch/2026-07-01/20260720-190621/quality-report.json`
- `http://127.0.0.1:8000/api/ads/overview?date=2026-07-01`
- `http://127.0.0.1:8088`

## Documentation

| Document | Purpose |
| --- | --- |
| [Project acceptance](docs/project-acceptance.md) | Final acceptance scope, evidence, metrics, and pass criteria |
| [Demo runbook](docs/demo-runbook.md) | Step-by-step local demo and troubleshooting guide |
| [Deployment integration](docs/deployment-integration.md) | Docker Compose services, endpoints, environment, and smoke tests |
| [GitHub workflow](docs/github-workflow.md) | Branch, commit, and PR workflow |
| [Warehouse module](warehouse/README.md) | Warehouse layers, batch scripts, and HDFS/Hive paths |

## Common Commands

Run quality checks only:

```powershell
powershell -ExecutionPolicy Bypass -File warehouse/scripts/run_quality_check.ps1 -BatchDate 2026-07-01
```

Resume from a failed DWD stage:

```powershell
powershell -ExecutionPolicy Bypass -File warehouse/scripts/run_offline_batch.ps1 -BatchDate 2026-07-01 -StartFrom dwd
```

Run deployment smoke test after ADS data exists:

```powershell
powershell -ExecutionPolicy Bypass -File deploy/scripts/smoke_test.ps1 -BackendBaseUrl http://127.0.0.1:8000 -FrontendBaseUrl http://127.0.0.1:8088
```

Stop local services:

```powershell
docker compose down
```
