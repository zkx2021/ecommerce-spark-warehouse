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
