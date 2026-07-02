# Warehouse Module

This module owns HDFS directory planning, Hive warehouse SQL, Spark jobs, and ADS export assets.

## Warehouse Layers

- `hive/ods`: raw source-aligned Hive external tables.
- `hive/dwd`: cleaned detailed tables.
- `hive/dim`: shared dimension tables.
- `hive/dws`: subject summary tables.
- `hive/ads`: dashboard-ready metric tables.
- `spark/jobs`: Spark SQL and PySpark offline jobs.
- `spark/submit`: Spark submit scripts.

## ODS Batch Flow

Run the crawler for the batch date:

```powershell
python crawler/run.py --batch-date 2026-07-01
```

Validate local ODS input files before loading:

```powershell
powershell -ExecutionPolicy Bypass -File warehouse/scripts/check_ods_inputs.ps1 -BatchDate 2026-07-01
```

Create or refresh the ODS Hive tables:

```powershell
Get-Content -Raw warehouse/hive/ods/create_ods_tables.sql | docker compose exec -T hive-server2 beeline -u "jdbc:hive2://localhost:10000"
```

Load the batch files into HDFS and register Hive partitions:

```powershell
powershell -ExecutionPolicy Bypass -File warehouse/scripts/load_ods.ps1 -BatchDate 2026-07-01
```

## HDFS ODS Paths

Expected ODS landing paths use one partition directory per source and batch date:

- `/warehouse/ecommerce/ods/products/dt=2026-07-01/products.jsonl`
- `/warehouse/ecommerce/ods/carts/dt=2026-07-01/carts.jsonl`
- `/warehouse/ecommerce/ods/users/dt=2026-07-01/users.jsonl`
