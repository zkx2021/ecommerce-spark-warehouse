# HDFS Hive ODS Design

## Goal

Build the first warehouse landing layer for crawler output. This phase takes local processed JSONL files from `crawler/data/processed/<batch-date>/` and defines how they are validated, uploaded to HDFS, and exposed through Hive ODS external tables.

## Scope

This phase includes:

- HDFS directory conventions for ecommerce ODS data.
- Hive ODS external table DDL for products, carts, and users.
- PowerShell scripts that validate local crawler outputs and load a batch into HDFS/Hive.
- Static tests that verify paths, table names, partition conventions, and script assets.
- Documentation that explains how to run the ODS loading flow.

This phase does not include:

- DWD JSON parsing or data cleaning.
- DIM, DWS, or ADS tables.
- Spark jobs.
- MySQL ADS exports.
- Dashboard or FastAPI changes.

## Warehouse Layer Plan

The full offline warehouse will use these layers:

- `ODS`: raw mapped source records from crawler output.
- `DWD`: cleaned and typed detailed facts.
- `DIM`: shared dimensions such as date, product, category, and user.
- `DWS`: subject-level summaries for sales, product, and user behavior.
- `ADS`: dashboard-ready application metrics.

This phase implements only ODS so later DWD/Spark work can depend on stable HDFS and Hive input locations.

## Input Data

The crawler writes processed JSONL files under:

```text
crawler/data/processed/<batch-date>/products.jsonl
crawler/data/processed/<batch-date>/carts.jsonl
crawler/data/processed/<batch-date>/users.jsonl
```

Each JSONL line has this logical shape:

```json
{
  "entity": "product",
  "source": "products",
  "batch_date": "2026-07-01",
  "data": "{\"id\":1}"
}
```

## HDFS Layout

The ODS HDFS base path is:

```text
/warehouse/ecommerce/ods
```

For batch date `2026-07-01`, files are loaded to:

```text
/warehouse/ecommerce/ods/products/dt=2026-07-01/products.jsonl
/warehouse/ecommerce/ods/carts/dt=2026-07-01/carts.jsonl
/warehouse/ecommerce/ods/users/dt=2026-07-01/users.jsonl
```

The `dt=<batch-date>` partition directory mirrors the Hive partition value and keeps reruns idempotent at the batch/source level.

## Hive ODS Tables

Create one external table per source:

- `ods_products`
- `ods_carts`
- `ods_users`

Each table reads JSONL records as text columns for the ODS phase:

```sql
entity string,
source string,
batch_date string,
data string
```

Each table is partitioned by:

```sql
dt string
```

The `data` field remains a JSON string in ODS. DWD will parse it into typed columns in a later phase. This keeps ODS stable and source-preserving.

## Load Flow

From the project root:

1. Generate or confirm crawler data:

```powershell
python crawler/run.py --batch-date 2026-07-01
```

2. Validate required local JSONL files:

```powershell
.\warehouse\scripts\check_ods_inputs.ps1 -BatchDate 2026-07-01
```

3. Create Hive ODS tables:

```powershell
Get-Content -Raw warehouse/hive/ods/create_ods_tables.sql | docker compose exec -T hive-server2 beeline -u "jdbc:hive2://localhost:10000"
```

4. Load the batch:

```powershell
.\warehouse\scripts\load_ods.ps1 -BatchDate 2026-07-01
```

The load script should:

- Validate the batch date format as `YYYY-MM-DD`.
- Verify the local JSONL files exist before touching HDFS.
- Create the HDFS partition directories.
- Upload each JSONL file to its matching HDFS partition path.
- Run Hive partition registration statements for each table and source.

## Error Handling

- Missing local JSONL files must fail before any HDFS write.
- Invalid batch dates must fail before any filesystem or Docker command.
- HDFS upload failures must stop the script with a non-zero exit.
- Hive partition registration failures must stop the script with a non-zero exit.
- Scripts should print the exact source and path being processed so failed runs are easy to diagnose.

## Testing

Static tests should verify:

- ODS SQL defines `ods_products`, `ods_carts`, and `ods_users`.
- Each table is external and partitioned by `dt`.
- The HDFS path convention uses `/warehouse/ecommerce/ods/<source>/dt=<batch-date>/`.
- `load_ods.ps1` references the expected local processed JSONL files.
- `check_ods_inputs.ps1` exists and validates products, carts, and users.

Runtime verification should include:

```powershell
python -m pytest warehouse/tests -v
python -m pytest crawler/tests -v
powershell -ExecutionPolicy Bypass -File deploy/scripts/check.ps1
```

If Docker services are available, manual verification should also run:

```powershell
python crawler/run.py --batch-date 2026-07-01
.\warehouse\scripts\check_ods_inputs.ps1 -BatchDate 2026-07-01
.\warehouse\scripts\load_ods.ps1 -BatchDate 2026-07-01
```

## Open Follow-Up

Later phases should validate source names as Hive-safe identifiers before allowing arbitrary external source configuration. Current built-in source names are safe.
