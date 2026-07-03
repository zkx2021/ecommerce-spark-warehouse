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

## DWD Batch Flow

Create or refresh the DWD Hive tables:

```powershell
Get-Content -Raw warehouse/hive/dwd/create_dwd_tables.sql | docker compose exec -T hive-server2 beeline -u "jdbc:hive2://localhost:10000"
```

Run the Spark DWD batch for the same date after ODS files are loaded:

```powershell
powershell -ExecutionPolicy Bypass -File warehouse/scripts/run_dwd.ps1 -BatchDate 2026-07-01
```

The DWD batch reads `ecommerce_ods` partitions for the requested date and writes:

- `ecommerce_dwd.dwd_product_info`
- `ecommerce_dwd.dwd_user_info`
- `ecommerce_dwd.dwd_order_cart_detail`

## DIM/DWS/ADS Batch Flow

Run the downstream warehouse batch after ODS and DWD are complete for the same date:

```powershell
powershell -ExecutionPolicy Bypass -File warehouse/scripts/run_ads.ps1 -BatchDate 2026-07-01
```

Export the ADS JSONL snapshots into MySQL:

```powershell
powershell -ExecutionPolicy Bypass -File warehouse/scripts/export_ads_mysql.ps1 -BatchDate 2026-07-01
```

Layer order: `ODS -> DWD -> DIM -> DWS -> ADS -> MySQL`.

The Spark ADS batch creates or refreshes Hive tables in `ecommerce_dim`, `ecommerce_dws`, and `ecommerce_ads`, then writes dashboard snapshots under `warehouse/data/ads/<batch-date>/` for the MySQL exporter.

## HDFS ODS Paths

Expected ODS landing paths use one partition directory per source and batch date:

- `/warehouse/ecommerce/ods/products/dt=2026-07-01/products.jsonl`
- `/warehouse/ecommerce/ods/carts/dt=2026-07-01/carts.jsonl`
- `/warehouse/ecommerce/ods/users/dt=2026-07-01/users.jsonl`

## HDFS DWD Paths

Expected DWD table locations are:

- `/warehouse/ecommerce/dwd/product_info`
- `/warehouse/ecommerce/dwd/user_info`
- `/warehouse/ecommerce/dwd/order_cart_detail`
