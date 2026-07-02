# Spark DWD Design

## Goal

Build the first Spark transformation layer for the ecommerce offline warehouse. This phase reads source-preserving Hive ODS rows, parses the `data` JSON string from each row, and writes cleaned, typed DWD detail tables for products, users, and cart line items.

The DWD layer should become the stable input for later DIM, DWS, ADS, MySQL export, FastAPI, and dashboard work.

## Scope

This phase includes:

- DWD table design for product, user, and cart detail entities.
- Spark job structure for batch-date-driven ODS to DWD transformation.
- Local transformation functions that can be tested without Docker, HDFS, Hive, or a running Spark cluster.
- PySpark job entry points that can run inside the Docker Compose Spark environment when available.
- Hive DWD DDL and documentation for running the batch.

This phase does not include:

- DIM, DWS, or ADS tables.
- MySQL exports.
- Dashboard API or frontend changes.
- Real-time processing.
- Arbitrary source onboarding beyond the built-in `products`, `carts`, and `users` sources.

## Upstream Contract

ODS data exists in Hive database `ecommerce_ods`:

- `ods_products`
- `ods_carts`
- `ods_users`

Each ODS table has:

```sql
entity STRING,
source STRING,
batch_date STRING,
data STRING,
dt STRING
```

The `data` column is a JSON string. Spark must parse it with explicit schemas instead of treating it as untyped text.

For a batch date `2026-07-01`, DWD jobs read only rows where:

```sql
dt = '2026-07-01'
batch_date = '2026-07-01'
```

Rows that fail required-field parsing should be rejected from DWD output and counted as invalid records in the job summary.

## Target DWD Tables

Create Hive database:

```sql
ecommerce_dwd
```

All DWD tables are partitioned by:

```sql
dt STRING
```

### `dwd_product_info`

One row per product per batch.

Columns:

```sql
product_id BIGINT,
product_name STRING,
category STRING,
brand STRING,
price DECIMAL(18,2),
discount_percentage DECIMAL(10,2),
rating DECIMAL(10,2),
stock INT,
availability_status STRING,
thumbnail STRING,
source STRING,
batch_date STRING
```

Required fields:

- `product_id`
- `product_name`
- `price`
- `source`
- `batch_date`

Quality rules:

- `product_id` must be positive.
- `price` must be greater than or equal to 0.
- `stock` must be greater than or equal to 0 when present.
- `source` must equal `products`.
- `dt` must equal `batch_date`.

### `dwd_user_info`

One row per user per batch.

Columns:

```sql
user_id BIGINT,
username STRING,
full_name STRING,
gender STRING,
age INT,
age_group STRING,
email STRING,
phone STRING,
city STRING,
state STRING,
country STRING,
latitude DECIMAL(18,6),
longitude DECIMAL(18,6),
role STRING,
source STRING,
batch_date STRING
```

Age groups:

```text
unknown, <18, 18-24, 25-34, 35-44, 45-54, 55+
```

Required fields:

- `user_id`
- `username`
- `source`
- `batch_date`

Quality rules:

- `user_id` must be positive.
- `age_group` must be derived deterministically from `age`.
- Missing nested address fields should produce null city/state/country/latitude/longitude, not fail the row.
- `source` must equal `users`.
- `dt` must equal `batch_date`.

### `dwd_order_cart_detail`

One row per cart product line per batch. This table acts as the first order-detail fact table for later sales and product ranking metrics.

Columns:

```sql
cart_id BIGINT,
user_id BIGINT,
product_id BIGINT,
product_name STRING,
unit_price DECIMAL(18,2),
quantity INT,
line_total DECIMAL(18,2),
discount_percentage DECIMAL(10,2),
line_discounted_total DECIMAL(18,2),
cart_total DECIMAL(18,2),
cart_discounted_total DECIMAL(18,2),
total_products INT,
total_quantity INT,
source STRING,
batch_date STRING
```

Required fields:

- `cart_id`
- `user_id`
- `product_id`
- `quantity`
- `source`
- `batch_date`

Quality rules:

- `cart_id`, `user_id`, and `product_id` must be positive.
- `quantity` must be greater than 0.
- Monetary fields must be greater than or equal to 0 when present.
- The nested `products` array in ODS cart payloads must be exploded into one DWD row per line item.
- `source` must equal `carts`.
- `dt` must equal `batch_date`.

## Spark Job Design

Use PySpark for the first DWD implementation because the rest of the repository already uses Python tests and scripts.

Proposed module structure:

```text
warehouse/
  hive/
    dwd/
      create_dwd_tables.sql
  spark/
    jobs/
      dwd_job.py
      dwd_transforms.py
    tests/
      test_dwd_transforms.py
  scripts/
    run_dwd.ps1
```

Responsibilities:

- `dwd_transforms.py`: pure transformation functions for products, users, and cart details. Tests should exercise these functions with small local Spark DataFrames or pure row fixtures when Spark is unavailable.
- `dwd_job.py`: command-line entry point. It parses `--batch-date`, starts or receives a Spark session, reads ODS Hive tables, calls transformation functions, writes DWD Hive tables, and prints a batch summary.
- `create_dwd_tables.sql`: Hive DDL for `ecommerce_dwd` tables.
- `run_dwd.ps1`: Docker Compose wrapper that validates required scripts and calls `spark-submit`.

## Data Flow

```text
Hive ecommerce_ods.ods_products
  -> parse product data JSON
  -> validate and type fields
  -> Hive ecommerce_dwd.dwd_product_info

Hive ecommerce_ods.ods_users
  -> parse user data JSON and nested address
  -> derive full_name and age_group
  -> Hive ecommerce_dwd.dwd_user_info

Hive ecommerce_ods.ods_carts
  -> parse cart data JSON
  -> explode products array
  -> Hive ecommerce_dwd.dwd_order_cart_detail
```

Writes should overwrite only the requested `dt=<batch-date>` partition, not entire tables.

## Batch Parameters

All DWD commands require:

```text
--batch-date YYYY-MM-DD
```

The same value is used for:

- ODS partition filter `dt`.
- DWD partition value `dt`.
- Row-level `batch_date` validation.

Invalid date format must fail before Spark reads or writes data.

## Error Handling

- Missing ODS tables should fail the job with a clear message naming the table.
- Empty ODS partitions should fail by default for the first version.
- Invalid records should be counted and excluded from DWD output.
- If any source has zero valid rows after parsing, the job should fail the batch.
- Spark and Hive write failures should return non-zero exit codes through `run_dwd.ps1`.

## Testing Strategy

Static tests should verify:

- DWD SQL creates the expected database and three DWD tables.
- All DWD tables are partitioned by `dt`.
- DWD SQL uses the expected table names and key columns.
- `run_dwd.ps1` references `spark-submit`, `dwd_job.py`, and `create_dwd_tables.sql`.

Transformation tests should verify:

- Product JSON is parsed into typed product rows.
- User JSON derives `full_name`, nested address fields, and `age_group`.
- Cart JSON explodes nested product lines into multiple rows.
- Invalid source or mismatched batch date rows are rejected.
- Non-string or invalid `data` JSON is rejected before field extraction.

Runtime verification should include:

```powershell
python -m pytest warehouse/tests -v
python -m pytest warehouse/spark/tests -v
powershell -ExecutionPolicy Bypass -File deploy/scripts/check.ps1
```

When Docker services are available, manual verification should also run:

```powershell
Get-Content -Raw warehouse/hive/dwd/create_dwd_tables.sql | docker compose exec -T hive-server2 beeline -u "jdbc:hive2://localhost:10000"
powershell -ExecutionPolicy Bypass -File warehouse/scripts/run_dwd.ps1 -BatchDate 2026-07-01
```

Then validate Hive row counts:

```sql
SELECT count(*) FROM ecommerce_dwd.dwd_product_info WHERE dt='2026-07-01';
SELECT count(*) FROM ecommerce_dwd.dwd_user_info WHERE dt='2026-07-01';
SELECT count(*) FROM ecommerce_dwd.dwd_order_cart_detail WHERE dt='2026-07-01';
```

## Implementation Boundaries

Task 2 should create the Spark job skeleton and tests only.
Task 3 should add DWD Hive DDL.
Task 4 should implement product and user transformations.
Task 5 should implement cart detail transformation.
Task 6 should add the DWD run script and documentation.
Task 7 should perform final verification, review, push, and PR creation.

No task should implement DIM, DWS, ADS, MySQL export, API, or dashboard work.

## Open Follow-Up

Later phases should:

- Add DIM tables for product, category, user, and date dimensions.
- Add DWS aggregations for sales, product rankings, user profiles, and behavior funnels.
- Add ADS exports to MySQL for dashboard queries.
- Revisit invalid-record persistence. The first DWD version rejects and counts invalid rows, but a later phase may add an error table for auditability.
