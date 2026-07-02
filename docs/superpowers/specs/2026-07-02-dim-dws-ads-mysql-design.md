# DIM DWS ADS MySQL Design

## Goal

Build the next offline warehouse stage after DWD: reusable DIM tables, subject-level DWS summary tables, dashboard-ready ADS metric tables, and a MySQL export path for ADS results.

This stage should make the data ready for a later FastAPI and Vue + ECharts dashboard phase. FastAPI endpoints and frontend changes are intentionally excluded from this stage.

## Scope

This phase includes:

- DIM table design for date, product, category, and user dimensions.
- DWS summary table design for sales, product ranking, category, user profile, and funnel-oriented metrics.
- ADS table design for dashboard-facing KPIs, trends, rankings, distributions, and funnel data.
- Spark SQL or PySpark batch jobs that read DWD tables and write DIM, DWS, and ADS Hive tables for one batch date.
- MySQL DDL for ADS result tables.
- Export scripts or jobs that load ADS Hive results into MySQL.
- Documentation and tests for static SQL assets, job configuration, and script contracts.

This phase does not include:

- FastAPI dashboard endpoints.
- Vue or ECharts dashboard implementation.
- Real-time processing.
- Authentication, authorization, or admin management.
- New crawler sources beyond the current products, carts, and users source set.

## Upstream Contract

This phase depends on the DWD layer produced by the previous stage:

- `ecommerce_dwd.dwd_product_info`
- `ecommerce_dwd.dwd_user_info`
- `ecommerce_dwd.dwd_order_cart_detail`

All upstream DWD tables are partitioned by:

```sql
dt STRING
```

All jobs in this phase must accept:

```text
--batch-date YYYY-MM-DD
```

The batch date is used for:

- Reading DWD partitions.
- Writing DIM, DWS, and ADS Hive partitions.
- Exporting the matching ADS batch to MySQL.

## Target Hive Databases

Create three Hive databases:

```sql
ecommerce_dim
ecommerce_dws
ecommerce_ads
```

All Hive tables in this phase are external tables and partitioned by `dt STRING` unless stated otherwise.

## DIM Layer

### `dim_date`

One row per calendar date.

Columns:

```sql
date_id STRING,
date_value DATE,
year INT,
quarter INT,
month INT,
day INT,
week_of_year INT,
day_of_week INT,
is_weekend BOOLEAN
```

Source:

- Generated from the batch date.
- This stage only generates the current batch date; multi-date calendar generation is out of scope.

### `dim_product`

One row per product per batch.

Columns:

```sql
product_id BIGINT,
product_name STRING,
category STRING,
brand STRING,
price DECIMAL(18,2),
stock INT,
availability_status STRING
```

Source:

- `ecommerce_dwd.dwd_product_info`

### `dim_category`

One row per category per batch.

Columns:

```sql
category_id STRING,
category_name STRING,
product_count BIGINT
```

Source:

- Distinct category values from `dwd_product_info`.
- `category_id` can be a deterministic normalized category string for the first version.

### `dim_user`

One row per user per batch.

Columns:

```sql
user_id BIGINT,
username STRING,
gender STRING,
age INT,
age_group STRING,
city STRING,
state STRING,
country STRING,
role STRING
```

Source:

- `ecommerce_dwd.dwd_user_info`

## DWS Layer

### `dws_sales_daily`

Daily sales and order summary.

Columns:

```sql
date_id STRING,
order_count BIGINT,
pay_user_count BIGINT,
total_sales_amount DECIMAL(18,2),
discount_sales_amount DECIMAL(18,2),
avg_order_amount DECIMAL(18,2),
total_quantity BIGINT
```

Source:

- `dwd_order_cart_detail`

Rules:

- One cart is treated as one order-like transaction.
- `total_sales_amount` uses cart-level `cart_total`.
- `discount_sales_amount` uses cart-level `cart_discounted_total`.
- Cart-level totals must be deduplicated by `cart_id` before summing to avoid multiplying cart totals by line count.

### `dws_product_daily`

Daily product performance.

Columns:

```sql
date_id STRING,
product_id BIGINT,
product_name STRING,
category STRING,
brand STRING,
sales_quantity BIGINT,
sales_amount DECIMAL(18,2),
order_count BIGINT
```

Source:

- `dwd_order_cart_detail`
- `dim_product`

### `dws_category_daily`

Daily category performance.

Columns:

```sql
date_id STRING,
category STRING,
product_count BIGINT,
sales_quantity BIGINT,
sales_amount DECIMAL(18,2),
order_count BIGINT
```

Source:

- `dws_product_daily`
- `dim_category`

### `dws_user_profile_daily`

Daily user profile and purchasing summary.

Columns:

```sql
date_id STRING,
age_group STRING,
gender STRING,
country STRING,
user_count BIGINT,
buyer_count BIGINT,
order_count BIGINT,
sales_amount DECIMAL(18,2)
```

Source:

- `dim_user`
- `dwd_order_cart_detail`

### `dws_funnel_daily`

First version behavior funnel using available offline data.

Columns:

```sql
date_id STRING,
view_count BIGINT,
cart_count BIGINT,
order_count BIGINT,
payment_count BIGINT,
cart_rate DECIMAL(10,4),
order_rate DECIMAL(10,4),
payment_rate DECIMAL(10,4)
```

Source:

- `dwd_order_cart_detail`

Rules:

- The current data source does not contain page-view or payment-event logs.
- For the first version, `cart_count`, `order_count`, and `payment_count` all use distinct `cart_id`.
- `view_count` is modeled as `NULL` or `0` until behavior data is introduced.
- Conversion rates should avoid divide-by-zero and return `0` when denominator is missing.

## ADS Layer

ADS tables should be small and shaped for direct MySQL export and API consumption.

### `ads_kpi_daily`

One row per batch date.

Columns:

```sql
date_id STRING,
total_sales_amount DECIMAL(18,2),
total_order_count BIGINT,
paid_user_count BIGINT,
avg_order_amount DECIMAL(18,2),
payment_conversion_rate DECIMAL(10,4)
```

Source:

- `dws_sales_daily`
- `dws_funnel_daily`

### `ads_sales_trend_daily`

One row per date for trend charts.

Columns:

```sql
date_id STRING,
sales_amount DECIMAL(18,2),
order_count BIGINT,
paid_user_count BIGINT
```

Source:

- `dws_sales_daily`

### `ads_product_rank_daily`

Top product ranking.

Columns:

```sql
date_id STRING,
rank_no INT,
product_id BIGINT,
product_name STRING,
category STRING,
sales_quantity BIGINT,
sales_amount DECIMAL(18,2)
```

Source:

- `dws_product_daily`

Rule:

- Keep top 10 products by `sales_amount`, then `sales_quantity`.

### `ads_category_share_daily`

Category sales share.

Columns:

```sql
date_id STRING,
category STRING,
sales_amount DECIMAL(18,2),
sales_quantity BIGINT,
sales_share DECIMAL(10,4)
```

Source:

- `dws_category_daily`

### `ads_user_profile_daily`

User distribution for dashboard charts.

Columns:

```sql
date_id STRING,
dimension_type STRING,
dimension_value STRING,
user_count BIGINT,
buyer_count BIGINT,
sales_amount DECIMAL(18,2)
```

Source:

- `dws_user_profile_daily`

Rules:

- `dimension_type` values for the first version: `age_group`, `gender`, `country`.

### `ads_funnel_daily`

Dashboard funnel data.

Columns:

```sql
date_id STRING,
stage_name STRING,
stage_order INT,
stage_count BIGINT,
conversion_rate DECIMAL(10,4)
```

Source:

- `dws_funnel_daily`

## MySQL ADS Tables

Create MySQL tables that mirror ADS outputs and are friendly to FastAPI.

Database:

```sql
ecommerce_ads
```

Tables:

- `ads_kpi_daily`
- `ads_sales_trend_daily`
- `ads_product_rank_daily`
- `ads_category_share_daily`
- `ads_user_profile_daily`
- `ads_funnel_daily`

The first version should use `REPLACE INTO` or delete-then-insert by `date_id` so rerunning a batch is idempotent.

## Spark Job Design

Add a new job family under:

```text
warehouse/spark/jobs/
  ads_job.py
  ads_sql.py
```

Responsibilities:

- `ads_sql.py`: SQL templates for DIM, DWS, and ADS writes.
- `ads_job.py`: command-line entry point. It parses `--batch-date`, creates a Spark session, executes SQL templates in dependency order, and prints a batch summary.

Dependency order:

1. Create or refresh DIM partitions.
2. Create or refresh DWS partitions.
3. Create or refresh ADS partitions.
4. Write ADS export snapshots under `warehouse/data/ads/<batch-date>/`.

## Hive DDL Assets

Add SQL files:

```text
warehouse/hive/dim/create_dim_tables.sql
warehouse/hive/dws/create_dws_tables.sql
warehouse/hive/ads/create_ads_tables.sql
```

Each SQL file should create the database and tables for its layer.

## MySQL DDL Assets

Add SQL file:

```text
deploy/mysql/init/02-create-ads-tables.sql
```

This file creates dashboard-facing MySQL tables in `ecommerce_ads`.

## Run Scripts

Add PowerShell scripts:

```text
warehouse/scripts/run_ads.ps1
warehouse/scripts/export_ads_mysql.ps1
warehouse/scripts/export_ads_mysql.py
```

Responsibilities:

- `run_ads.ps1`: create DIM/DWS/ADS Hive tables and submit the Spark ADS job. The Spark job writes ADS Hive tables and JSONL export snapshots under `warehouse/data/ads/<batch-date>/`.
- `export_ads_mysql.py`: read the JSONL ADS snapshots and upsert them into MySQL with idempotent reruns.
- `export_ads_mysql.ps1`: wrapper that validates parameters and calls the Python exporter.

The first implementation uses JSONL snapshots plus a Python MySQL exporter instead of Spark JDBC. This avoids depending on a Spark image-level MySQL JDBC driver and keeps the database export isolated from Hive table generation.

## Testing Strategy

Static tests should verify:

- DIM/DWS/ADS SQL files create expected databases and tables.
- MySQL DDL creates all expected ADS result tables.
- Run scripts reference expected SQL files, Spark job files, and Docker Compose services.
- Foundation check includes DIM/DWS/ADS, JSONL snapshot output, and MySQL export assets.

Job tests should verify:

- `ads_job.py` parses and validates `--batch-date`.
- SQL templates are generated with the requested batch date.
- Job execution order is DIM before DWS before ADS before export.
- The job rejects invalid batch dates before touching Spark.

Metric tests should verify:

- Cart-level totals are deduplicated before sales aggregation.
- Product rankings sort by sales amount and quantity.
- Category share avoids divide-by-zero.
- Funnel metrics avoid divide-by-zero and document the lack of page-view/payment events.

## Documentation

Update:

- `warehouse/README.md` with DIM/DWS/ADS batch flow.
- `README.md` with the completed warehouse layers.
- `docs/superpowers/specs/2026-06-30-ecommerce-spark-warehouse-design.md` only if a high-level design correction is needed.

## Acceptance Criteria

- Hive DDL exists for DIM, DWS, and ADS layers.
- MySQL DDL exists for dashboard ADS tables.
- Spark ADS job can run for one batch date after DWD completion.
- ADS metrics are exportable into MySQL with idempotent reruns.
- Static and unit tests pass locally without requiring Docker services.
- Docker-based runtime verification is documented and can be run when services are available.

## Risks And Mitigations

- DummyJSON carts do not include full behavior events. The first funnel version must clearly document this limitation and avoid pretending it has true view-to-pay behavior.
- Spark-to-MySQL JDBC can be image-dependent. This stage avoids that dependency by exporting ADS JSONL snapshots first, then loading MySQL with a small Python exporter.
- Cart detail rows repeat cart-level totals. DWS sales logic must deduplicate by `cart_id` before summing cart totals.
- Dashboard scope can grow quickly. Keep this phase focused on tables and exports; API and frontend work belong to the next phase.

## Implementation Boundaries

Task planning should split this phase into independently reviewable tasks:

1. DIM/DWS/ADS design assets and SQL DDL.
2. MySQL ADS DDL.
3. Spark ADS job skeleton and SQL template tests.
4. DIM and DWS metric SQL templates.
5. ADS metric SQL templates.
6. Run scripts, ADS JSONL snapshots, and Python MySQL exporter.
7. Documentation and foundation checks.
8. Final verification, review, push, and PR.
