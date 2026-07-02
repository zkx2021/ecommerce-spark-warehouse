# DIM DWS ADS MySQL Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build DIM, DWS, and ADS Hive layers after DWD, then export ADS snapshots into MySQL for the future dashboard.

**Architecture:** Hive DDL defines three new warehouse databases. A Spark batch job executes SQL templates in DIM -> DWS -> ADS order, writes JSONL ADS snapshots for the requested batch date, and a Python exporter loads those snapshots into MySQL idempotently. Tests stay local-first: static SQL/script checks plus fake Spark and fake MySQL unit tests.

**Tech Stack:** Python, PySpark SQL, Hive external tables, HDFS locations, MySQL SQL, PowerShell, pytest.

---

## File Structure

- Create `warehouse/hive/dim/create_dim_tables.sql`: DIM database and tables.
- Create `warehouse/hive/dws/create_dws_tables.sql`: DWS database and tables.
- Create `warehouse/hive/ads/create_ads_tables.sql`: ADS database and dashboard tables.
- Create `deploy/mysql/init/02-create-ads-tables.sql`: MySQL dashboard-facing ADS tables.
- Create `warehouse/spark/jobs/ads_sql.py`: SQL template constants and rendering helpers.
- Create `warehouse/spark/jobs/ads_job.py`: Spark command-line entry point, dependency order runner, JSONL snapshot writer.
- Create `warehouse/scripts/export_ads_mysql.py`: JSONL-to-MySQL exporter with delete-then-insert idempotency.
- Create `warehouse/scripts/run_ads.ps1`: PowerShell wrapper for Hive DDL and Spark ADS batch.
- Create `warehouse/scripts/export_ads_mysql.ps1`: PowerShell wrapper for Python MySQL export.
- Create `warehouse/tests/test_ads_assets.py`: static tests for Hive DDL, MySQL DDL, scripts, and foundation check.
- Create `warehouse/spark/tests/test_ads_sql.py`: SQL template and dependency-order tests.
- Create `warehouse/spark/tests/test_ads_job.py`: fake Spark tests for config, execution order, and snapshot writing.
- Create `warehouse/tests/test_ads_mysql_export.py`: fake connector tests for idempotent MySQL export.
- Modify `deploy/scripts/check.ps1`: include DIM/DWS/ADS/MySQL/export assets.
- Modify `warehouse/README.md`: document ADS batch flow.
- Modify `README.md`: update completed project layers.

---

### Task 1: Hive DIM/DWS/ADS DDL Assets

**Files:**
- Create: `warehouse/hive/dim/create_dim_tables.sql`
- Create: `warehouse/hive/dws/create_dws_tables.sql`
- Create: `warehouse/hive/ads/create_ads_tables.sql`
- Create: `warehouse/tests/test_ads_assets.py`

- [ ] **Step 1: Write failing static tests for Hive DDL**

Add this initial content to `warehouse/tests/test_ads_assets.py`:

```python
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DIM_SQL = PROJECT_ROOT / "warehouse" / "hive" / "dim" / "create_dim_tables.sql"
DWS_SQL = PROJECT_ROOT / "warehouse" / "hive" / "dws" / "create_dws_tables.sql"
ADS_SQL = PROJECT_ROOT / "warehouse" / "hive" / "ads" / "create_ads_tables.sql"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8").lower()


def test_dim_sql_creates_database_tables_and_partitions():
    sql = _read(DIM_SQL)

    assert "create database if not exists ecommerce_dim" in sql
    for table_name in ("dim_date", "dim_product", "dim_category", "dim_user"):
        assert f"create external table if not exists {table_name}" in sql
    for column in (
        "date_id string",
        "product_id bigint",
        "category_id string",
        "user_id bigint",
        "partitioned by (dt string)",
        "stored as parquet",
    ):
        assert column in sql


def test_dws_sql_creates_subject_summary_tables():
    sql = _read(DWS_SQL)

    assert "create database if not exists ecommerce_dws" in sql
    for table_name in (
        "dws_sales_daily",
        "dws_product_daily",
        "dws_category_daily",
        "dws_user_profile_daily",
        "dws_funnel_daily",
    ):
        assert f"create external table if not exists {table_name}" in sql
    for column in (
        "order_count bigint",
        "pay_user_count bigint",
        "total_sales_amount decimal(18,2)",
        "cart_rate decimal(10,4)",
        "partitioned by (dt string)",
        "stored as parquet",
    ):
        assert column in sql


def test_ads_sql_creates_dashboard_tables():
    sql = _read(ADS_SQL)

    assert "create database if not exists ecommerce_ads" in sql
    for table_name in (
        "ads_kpi_daily",
        "ads_sales_trend_daily",
        "ads_product_rank_daily",
        "ads_category_share_daily",
        "ads_user_profile_daily",
        "ads_funnel_daily",
    ):
        assert f"create external table if not exists {table_name}" in sql
    for column in (
        "payment_conversion_rate decimal(10,4)",
        "rank_no int",
        "sales_share decimal(10,4)",
        "stage_order int",
        "partitioned by (dt string)",
        "stored as parquet",
    ):
        assert column in sql
```

- [ ] **Step 2: Run failing Hive DDL tests**

Run:

```powershell
pytest warehouse/tests/test_ads_assets.py -q
```

Expected: failure because the three SQL files do not exist yet.

- [ ] **Step 3: Create Hive DDL files**

Create `warehouse/hive/dim/create_dim_tables.sql` with database `ecommerce_dim`, external Parquet tables `dim_date`, `dim_product`, `dim_category`, and `dim_user`, each with `PARTITIONED BY (dt STRING)` and HDFS locations under `/warehouse/ecommerce/dim/...`.

Create `warehouse/hive/dws/create_dws_tables.sql` with database `ecommerce_dws`, external Parquet tables `dws_sales_daily`, `dws_product_daily`, `dws_category_daily`, `dws_user_profile_daily`, and `dws_funnel_daily`, each with `PARTITIONED BY (dt STRING)` and HDFS locations under `/warehouse/ecommerce/dws/...`.

Create `warehouse/hive/ads/create_ads_tables.sql` with database `ecommerce_ads`, external Parquet tables `ads_kpi_daily`, `ads_sales_trend_daily`, `ads_product_rank_daily`, `ads_category_share_daily`, `ads_user_profile_daily`, and `ads_funnel_daily`, each with `PARTITIONED BY (dt STRING)` and HDFS locations under `/warehouse/ecommerce/ads/...`.

- [ ] **Step 4: Run Hive DDL tests until they pass**

Run:

```powershell
pytest warehouse/tests/test_ads_assets.py -q
```

Expected: 3 passed.

- [ ] **Step 5: Commit Hive DDL assets**

```powershell
git add warehouse/hive/dim/create_dim_tables.sql warehouse/hive/dws/create_dws_tables.sql warehouse/hive/ads/create_ads_tables.sql warehouse/tests/test_ads_assets.py
git commit -m "feat: add dim dws ads hive ddl"
```

---

### Task 2: MySQL ADS DDL

**Files:**
- Create: `deploy/mysql/init/02-create-ads-tables.sql`
- Modify: `warehouse/tests/test_ads_assets.py`

- [ ] **Step 1: Add failing MySQL DDL test**

Append to `warehouse/tests/test_ads_assets.py`:

```python
MYSQL_ADS_SQL = PROJECT_ROOT / "deploy" / "mysql" / "init" / "02-create-ads-tables.sql"


def test_mysql_ads_sql_creates_dashboard_tables_and_keys():
    sql = _read(MYSQL_ADS_SQL)

    assert "use ecommerce_ads" in sql
    for table_name in (
        "ads_kpi_daily",
        "ads_sales_trend_daily",
        "ads_product_rank_daily",
        "ads_category_share_daily",
        "ads_user_profile_daily",
        "ads_funnel_daily",
    ):
        assert f"create table if not exists {table_name}" in sql
    for key_fragment in (
        "primary key (date_id)",
        "primary key (date_id, rank_no)",
        "primary key (date_id, category)",
        "primary key (date_id, dimension_type, dimension_value)",
        "primary key (date_id, stage_order)",
    ):
        assert key_fragment in sql
```

- [ ] **Step 2: Run failing MySQL DDL test**

Run:

```powershell
pytest warehouse/tests/test_ads_assets.py::test_mysql_ads_sql_creates_dashboard_tables_and_keys -q
```

Expected: failure because `deploy/mysql/init/02-create-ads-tables.sql` does not exist.

- [ ] **Step 3: Create MySQL ADS DDL**

Create `deploy/mysql/init/02-create-ads-tables.sql` with:

```sql
USE ecommerce_ads;

CREATE TABLE IF NOT EXISTS ads_kpi_daily (
  date_id VARCHAR(10) NOT NULL,
  total_sales_amount DECIMAL(18,2) NOT NULL DEFAULT 0,
  total_order_count BIGINT NOT NULL DEFAULT 0,
  paid_user_count BIGINT NOT NULL DEFAULT 0,
  avg_order_amount DECIMAL(18,2) NOT NULL DEFAULT 0,
  payment_conversion_rate DECIMAL(10,4) NOT NULL DEFAULT 0,
  updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (date_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

Continue in the same file with these table keys and columns:

```sql
CREATE TABLE IF NOT EXISTS ads_sales_trend_daily (
  date_id VARCHAR(10) NOT NULL,
  sales_amount DECIMAL(18,2) NOT NULL DEFAULT 0,
  order_count BIGINT NOT NULL DEFAULT 0,
  paid_user_count BIGINT NOT NULL DEFAULT 0,
  updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (date_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS ads_product_rank_daily (
  date_id VARCHAR(10) NOT NULL,
  rank_no INT NOT NULL,
  product_id BIGINT NOT NULL,
  product_name VARCHAR(255) NOT NULL,
  category VARCHAR(128),
  sales_quantity BIGINT NOT NULL DEFAULT 0,
  sales_amount DECIMAL(18,2) NOT NULL DEFAULT 0,
  updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (date_id, rank_no)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS ads_category_share_daily (
  date_id VARCHAR(10) NOT NULL,
  category VARCHAR(128) NOT NULL,
  sales_amount DECIMAL(18,2) NOT NULL DEFAULT 0,
  sales_quantity BIGINT NOT NULL DEFAULT 0,
  sales_share DECIMAL(10,4) NOT NULL DEFAULT 0,
  updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (date_id, category)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS ads_user_profile_daily (
  date_id VARCHAR(10) NOT NULL,
  dimension_type VARCHAR(32) NOT NULL,
  dimension_value VARCHAR(128) NOT NULL,
  user_count BIGINT NOT NULL DEFAULT 0,
  buyer_count BIGINT NOT NULL DEFAULT 0,
  sales_amount DECIMAL(18,2) NOT NULL DEFAULT 0,
  updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (date_id, dimension_type, dimension_value)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS ads_funnel_daily (
  date_id VARCHAR(10) NOT NULL,
  stage_name VARCHAR(64) NOT NULL,
  stage_order INT NOT NULL,
  stage_count BIGINT NOT NULL DEFAULT 0,
  conversion_rate DECIMAL(10,4) NOT NULL DEFAULT 0,
  updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (date_id, stage_order)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

- [ ] **Step 4: Run MySQL DDL tests until they pass**

Run:

```powershell
pytest warehouse/tests/test_ads_assets.py -q
```

Expected: 4 passed.

- [ ] **Step 5: Commit MySQL DDL**

```powershell
git add deploy/mysql/init/02-create-ads-tables.sql warehouse/tests/test_ads_assets.py
git commit -m "feat: add mysql ads ddl"
```

---

### Task 3: ADS SQL Template Module

**Files:**
- Create: `warehouse/spark/jobs/ads_sql.py`
- Create: `warehouse/spark/tests/test_ads_sql.py`

- [ ] **Step 1: Write failing SQL template tests**

Create `warehouse/spark/tests/test_ads_sql.py`:

```python
from warehouse.spark.jobs import ads_sql


def test_render_all_sql_uses_batch_date_and_dependency_order():
    statements = ads_sql.render_all_sql("2026-07-01")

    names = [statement.name for statement in statements]
    assert names[0].startswith("dim_")
    assert names.index("dws_sales_daily") < names.index("ads_kpi_daily")
    assert names[-1] == "ads_funnel_daily"
    assert all("2026-07-01" in statement.sql for statement in statements)


def test_dws_sales_sql_deduplicates_cart_totals():
    statement = ads_sql.render_statement("dws_sales_daily", "2026-07-01").lower()

    assert "select distinct cart_id" in statement
    assert "sum(cart_discounted_total)" in statement
    assert "count(distinct user_id)" in statement


def test_ads_product_rank_uses_top_10_window():
    statement = ads_sql.render_statement("ads_product_rank_daily", "2026-07-01").lower()

    assert "row_number() over" in statement
    assert "order by sales_amount desc, sales_quantity desc" in statement
    assert "rank_no <= 10" in statement


def test_share_and_funnel_sql_guard_divide_by_zero():
    category_sql = ads_sql.render_statement("ads_category_share_daily", "2026-07-01").lower()
    funnel_sql = ads_sql.render_statement("ads_funnel_daily", "2026-07-01").lower()

    assert "case when total_sales_amount = 0 then 0" in category_sql
    assert "case when order_count = 0 then 0" in funnel_sql
```

- [ ] **Step 2: Run failing SQL template tests**

Run:

```powershell
pytest warehouse/spark/tests/test_ads_sql.py -q
```

Expected: import failure because `ads_sql.py` does not exist.

- [ ] **Step 3: Create `ads_sql.py`**

Create `warehouse/spark/jobs/ads_sql.py` with:

```python
from dataclasses import dataclass


@dataclass(frozen=True)
class SqlStatement:
    name: str
    sql: str


STATEMENT_ORDER = (
    "dim_date",
    "dim_product",
    "dim_category",
    "dim_user",
    "dws_sales_daily",
    "dws_product_daily",
    "dws_category_daily",
    "dws_user_profile_daily",
    "dws_funnel_daily",
    "ads_kpi_daily",
    "ads_sales_trend_daily",
    "ads_product_rank_daily",
    "ads_category_share_daily",
    "ads_user_profile_daily",
    "ads_funnel_daily",
)


def render_statement(name: str, batch_date: str) -> str:
    return SQL_TEMPLATES[name].format(batch_date=batch_date)


def render_all_sql(batch_date: str) -> list[SqlStatement]:
    return [SqlStatement(name=name, sql=render_statement(name, batch_date)) for name in STATEMENT_ORDER]
```

In the same file, add `SQL_TEMPLATES: dict[str, str]` with exactly the keys from `STATEMENT_ORDER`. Each value is an `INSERT OVERWRITE TABLE ... PARTITION (dt='{batch_date}')` statement. The table references use these databases exactly: `ecommerce_dim`, `ecommerce_dws`, `ecommerce_ads`, and `ecommerce_dwd`. The `dws_sales_daily` template contains `SELECT DISTINCT cart_id` before summing cart totals, the `ads_product_rank_daily` template contains the `ROW_NUMBER()` top-10 rule from the test, and the category/funnel templates contain the zero-denominator `CASE WHEN` guards from the test.

- [ ] **Step 4: Run SQL template tests until they pass**

Run:

```powershell
pytest warehouse/spark/tests/test_ads_sql.py -q
```

Expected: 4 passed.

- [ ] **Step 5: Commit SQL template module**

```powershell
git add warehouse/spark/jobs/ads_sql.py warehouse/spark/tests/test_ads_sql.py
git commit -m "feat: add ads sql templates"
```

---

### Task 4: Spark ADS Job Runner And JSONL Snapshots

**Files:**
- Create: `warehouse/spark/jobs/ads_job.py`
- Create: `warehouse/spark/tests/test_ads_job.py`
- Modify: `warehouse/spark/jobs/ads_sql.py`

- [ ] **Step 1: Write failing job tests**

Create `warehouse/spark/tests/test_ads_job.py`:

```python
import json

import pytest

from warehouse.spark.jobs import ads_job


class FakeRow(dict):
    def asDict(self, recursive=False):
        return dict(self)


class FakeDataFrame:
    def __init__(self, rows):
        self.rows = [FakeRow(row) for row in rows]
        self.where_clause = None

    def where(self, clause):
        self.where_clause = clause
        return self

    def collect(self):
        return self.rows


class FakeSpark:
    def __init__(self):
        self.sql_calls = []
        self.table_reads = []

    def sql(self, statement):
        self.sql_calls.append(statement)

    def table(self, table_name):
        self.table_reads.append(table_name)
        return FakeDataFrame([{"date_id": "2026-07-01", "metric": table_name}])


def test_parse_args_accepts_batch_date_and_export_dir(tmp_path):
    args = ads_job.parse_args(["--batch-date", "2026-07-01", "--export-root", str(tmp_path)])

    assert args.batch_date == "2026-07-01"
    assert args.export_root == str(tmp_path)


def test_parse_args_rejects_invalid_batch_date():
    with pytest.raises(SystemExit):
        ads_job.parse_args(["--batch-date", "2026-7-1"])


def test_run_executes_sql_in_order_and_writes_snapshots(tmp_path):
    config = ads_job.build_job_config("2026-07-01", export_root=tmp_path)
    spark = FakeSpark()

    summary = ads_job.run(config, spark=spark)

    assert summary["status"] == "ok"
    assert summary["batch_date"] == "2026-07-01"
    assert len(spark.sql_calls) == 15
    assert "ecommerce_ads.ads_kpi_daily" in spark.table_reads
    snapshot = tmp_path / "2026-07-01" / "ads_kpi_daily.jsonl"
    assert snapshot.exists()
    assert json.loads(snapshot.read_text(encoding="utf-8").splitlines()[0])["date_id"] == "2026-07-01"
```

- [ ] **Step 2: Run failing job tests**

Run:

```powershell
pytest warehouse/spark/tests/test_ads_job.py -q
```

Expected: import failure because `ads_job.py` does not exist.

- [ ] **Step 3: Create `ads_job.py`**

Create `warehouse/spark/jobs/ads_job.py` with:

```python
import argparse
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

from warehouse.spark.jobs import ads_sql


BATCH_DATE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$")
ADS_DATABASE = "ecommerce_ads"
ADS_EXPORT_TABLES = (
    "ads_kpi_daily",
    "ads_sales_trend_daily",
    "ads_product_rank_daily",
    "ads_category_share_daily",
    "ads_user_profile_daily",
    "ads_funnel_daily",
)


@dataclass(frozen=True)
class AdsJobConfig:
    batch_date: str
    export_root: Path


def _batch_date(value: str) -> str:
    if not BATCH_DATE_PATTERN.fullmatch(value):
        raise argparse.ArgumentTypeError("batch date must use YYYY-MM-DD")
    return value


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run Spark DIM/DWS/ADS batch transformations.")
    parser.add_argument("--batch-date", required=True, type=_batch_date, help="Batch date in YYYY-MM-DD format.")
    parser.add_argument("--export-root", default="warehouse/data/ads", help="Local ADS JSONL export root.")
    return parser.parse_args(argv)


def build_job_config(batch_date: str, export_root: str | Path = "warehouse/data/ads") -> AdsJobConfig:
    return AdsJobConfig(batch_date=_batch_date(batch_date), export_root=Path(export_root))


def _create_spark_session():
    from pyspark.sql import SparkSession

    return SparkSession.builder.appName("ecommerce-ads-batch").enableHiveSupport().getOrCreate()


def _row_to_dict(row: Any) -> dict[str, Any]:
    if hasattr(row, "asDict"):
        return row.asDict(recursive=True)
    return dict(row)


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, default=str) + "\n")


def _export_ads_snapshots(spark: Any, config: AdsJobConfig) -> dict[str, int]:
    counts: dict[str, int] = {}
    output_dir = config.export_root / config.batch_date
    for table_name in ADS_EXPORT_TABLES:
        rows = [
            _row_to_dict(row)
            for row in spark.table(f"{ADS_DATABASE}.{table_name}").where(f"dt = '{config.batch_date}'").collect()
        ]
        _write_jsonl(output_dir / f"{table_name}.jsonl", rows)
        counts[table_name] = len(rows)
    return counts


def run(config: AdsJobConfig, spark: Any | None = None) -> dict[str, object]:
    own_spark = spark is None
    active_spark = spark or _create_spark_session()
    try:
        for statement in ads_sql.render_all_sql(config.batch_date):
            active_spark.sql(statement.sql)
        exported = _export_ads_snapshots(active_spark, config)
        return {"status": "ok", "batch_date": config.batch_date, "exported": exported}
    finally:
        if own_spark and hasattr(active_spark, "stop"):
            active_spark.stop()


def main(argv: list[str] | None = None, runner: Callable[[AdsJobConfig], object] = run) -> int:
    args = parse_args(argv)
    result = runner(build_job_config(args.batch_date, args.export_root))
    if result is not None:
        print(json.dumps(result, ensure_ascii=False, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: Run job tests until they pass**

Run:

```powershell
pytest warehouse/spark/tests/test_ads_job.py warehouse/spark/tests/test_ads_sql.py -q
```

Expected: all ADS Spark tests pass.

- [ ] **Step 5: Commit ADS job runner**

```powershell
git add warehouse/spark/jobs/ads_job.py warehouse/spark/jobs/ads_sql.py warehouse/spark/tests/test_ads_job.py
git commit -m "feat: add ads spark job"
```

---

### Task 5: MySQL JSONL Exporter

**Files:**
- Create: `warehouse/scripts/export_ads_mysql.py`
- Create: `warehouse/tests/test_ads_mysql_export.py`

- [ ] **Step 1: Write failing exporter tests**

Create `warehouse/tests/test_ads_mysql_export.py`:

```python
import json

from warehouse.scripts import export_ads_mysql


class FakeCursor:
    def __init__(self):
        self.statements = []

    def execute(self, statement, params=None):
        self.statements.append((statement, params))

    def executemany(self, statement, rows):
        self.statements.append((statement, rows))

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


class FakeConnection:
    def __init__(self):
        self.cursor_obj = FakeCursor()
        self.committed = False

    def cursor(self):
        return self.cursor_obj

    def commit(self):
        self.committed = True


def test_load_snapshot_reads_jsonl(tmp_path):
    path = tmp_path / "ads_kpi_daily.jsonl"
    path.write_text(json.dumps({"date_id": "2026-07-01", "total_order_count": 2}) + "\n", encoding="utf-8")

    rows = export_ads_mysql.load_snapshot(path)

    assert rows == [{"date_id": "2026-07-01", "total_order_count": 2}]


def test_export_table_deletes_batch_then_inserts_rows():
    connection = FakeConnection()
    rows = [{"date_id": "2026-07-01", "total_order_count": 2}]

    count = export_ads_mysql.export_table(connection, "ads_kpi_daily", rows, batch_date="2026-07-01")

    assert count == 1
    assert "delete from ads_kpi_daily where date_id = %s" in connection.cursor_obj.statements[0][0].lower()
    assert "insert into ads_kpi_daily" in connection.cursor_obj.statements[1][0].lower()
    assert connection.committed is True
```

- [ ] **Step 2: Run failing exporter tests**

Run:

```powershell
pytest warehouse/tests/test_ads_mysql_export.py -q
```

Expected: import failure because `export_ads_mysql.py` does not exist.

- [ ] **Step 3: Create Python exporter**

Create `warehouse/scripts/export_ads_mysql.py` with functions:

```python
import argparse
import json
from pathlib import Path
from typing import Any


ADS_TABLES = (
    "ads_kpi_daily",
    "ads_sales_trend_daily",
    "ads_product_rank_daily",
    "ads_category_share_daily",
    "ads_user_profile_daily",
    "ads_funnel_daily",
)


def load_snapshot(path: Path) -> list[dict[str, Any]]:
    rows = []
    if not path.exists():
        return rows
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def export_table(connection: Any, table_name: str, rows: list[dict[str, Any]], *, batch_date: str) -> int:
    with connection.cursor() as cursor:
        cursor.execute(f"DELETE FROM {table_name} WHERE date_id = %s", (batch_date,))
        if rows:
            columns = list(rows[0].keys())
            placeholders = ", ".join(["%s"] * len(columns))
            column_sql = ", ".join(columns)
            values = [tuple(row.get(column) for column in columns) for row in rows]
            cursor.executemany(f"INSERT INTO {table_name} ({column_sql}) VALUES ({placeholders})", values)
    connection.commit()
    return len(rows)
```

Add `parse_args`, `connect_mysql`, `export_batch`, and `main` in the same file. `parse_args` accepts `--batch-date`, `--snapshot-root`, `--host`, `--port`, `--database`, `--user`, and `--password`. `connect_mysql` imports `mysql.connector` inside the function and returns `mysql.connector.connect(host=args.host, port=args.port, database=args.database, user=args.user, password=args.password)`. `export_batch` loops through `ADS_TABLES`, loads `<snapshot-root>/<batch-date>/<table>.jsonl`, calls `export_table`, and returns a dictionary of table names to exported row counts.

- [ ] **Step 4: Run exporter tests until they pass**

Run:

```powershell
pytest warehouse/tests/test_ads_mysql_export.py -q
```

Expected: 2 passed.

- [ ] **Step 5: Commit exporter**

```powershell
git add warehouse/scripts/export_ads_mysql.py warehouse/tests/test_ads_mysql_export.py
git commit -m "feat: add ads mysql exporter"
```

---

### Task 6: PowerShell Run Scripts

**Files:**
- Create: `warehouse/scripts/run_ads.ps1`
- Create: `warehouse/scripts/export_ads_mysql.ps1`
- Modify: `warehouse/tests/test_ads_assets.py`

- [ ] **Step 1: Add failing script tests**

Append to `warehouse/tests/test_ads_assets.py`:

```python
RUN_ADS_SCRIPT = PROJECT_ROOT / "warehouse" / "scripts" / "run_ads.ps1"
EXPORT_ADS_SCRIPT = PROJECT_ROOT / "warehouse" / "scripts" / "export_ads_mysql.ps1"


def test_run_ads_script_creates_tables_and_submits_spark_job():
    script = _read(RUN_ADS_SCRIPT)

    assert "param(" in script
    assert "$batchdate" in script
    assert "create_dim_tables.sql" in script
    assert "create_dws_tables.sql" in script
    assert "create_ads_tables.sql" in script
    assert "ads_job.py" in script
    assert "spark-submit" in script
    assert "spark://spark-master:7077" in script
    assert "beeline" in script


def test_export_ads_mysql_script_calls_python_exporter():
    script = _read(EXPORT_ADS_SCRIPT)

    assert "param(" in script
    assert "$batchdate" in script
    assert "export_ads_mysql.py" in script
    assert "--batch-date" in script
    assert "--snapshot-root" in script
    assert "--host" in script
    assert "--database" in script
```

- [ ] **Step 2: Run failing script tests**

Run:

```powershell
pytest warehouse/tests/test_ads_assets.py -q
```

Expected: failure because the two PowerShell scripts do not exist.

- [ ] **Step 3: Create `run_ads.ps1`**

Create `warehouse/scripts/run_ads.ps1` by following the existing structure in `warehouse/scripts/run_dwd.ps1`. It must validate `-BatchDate`, run Beeline for `create_dim_tables.sql`, `create_dws_tables.sql`, and `create_ads_tables.sql`, copy `ads_job.py` and `ads_sql.py` into the Spark container context, and submit:

```powershell
spark-submit --master spark://spark-master:7077 /tmp/$runId/ads_job.py --batch-date $BatchDate --export-root /tmp/$runId/ads
```

- [ ] **Step 4: Create `export_ads_mysql.ps1`**

Create `warehouse/scripts/export_ads_mysql.ps1` with parameters:

```powershell
param(
  [Parameter(Mandatory=$true)]
  [ValidatePattern('^\d{4}-\d{2}-\d{2}$')]
  [string]$BatchDate,
  [string]$SnapshotRoot = "warehouse/data/ads",
  [string]$HostName = "localhost",
  [int]$Port = 3306,
  [string]$Database = "ecommerce_ads",
  [string]$User = "ecommerce",
  [string]$Password = "ecommerce"
)
```

The script calls:

```powershell
python warehouse/scripts/export_ads_mysql.py --batch-date $BatchDate --snapshot-root $SnapshotRoot --host $HostName --port $Port --database $Database --user $User --password $Password
```

- [ ] **Step 5: Run script tests until they pass**

Run:

```powershell
pytest warehouse/tests/test_ads_assets.py -q
```

Expected: all ADS asset tests pass.

- [ ] **Step 6: Commit scripts**

```powershell
git add warehouse/scripts/run_ads.ps1 warehouse/scripts/export_ads_mysql.ps1 warehouse/tests/test_ads_assets.py
git commit -m "feat: add ads run scripts"
```

---

### Task 7: Documentation And Foundation Checks

**Files:**
- Modify: `deploy/scripts/check.ps1`
- Modify: `warehouse/README.md`
- Modify: `README.md`
- Modify: `warehouse/tests/test_ads_assets.py`

- [ ] **Step 1: Add failing foundation and documentation tests**

Append to `warehouse/tests/test_ads_assets.py`:

```python
FOUNDATION_CHECK = PROJECT_ROOT / "deploy" / "scripts" / "check.ps1"
WAREHOUSE_README = PROJECT_ROOT / "warehouse" / "README.md"
ROOT_README = PROJECT_ROOT / "README.md"


def test_foundation_check_includes_ads_runtime_assets():
    script = _read(FOUNDATION_CHECK)

    for path in (
        "warehouse/hive/dim/create_dim_tables.sql",
        "warehouse/hive/dws/create_dws_tables.sql",
        "warehouse/hive/ads/create_ads_tables.sql",
        "deploy/mysql/init/02-create-ads-tables.sql",
        "warehouse/spark/jobs/ads_job.py",
        "warehouse/spark/jobs/ads_sql.py",
        "warehouse/scripts/run_ads.ps1",
        "warehouse/scripts/export_ads_mysql.ps1",
        "warehouse/scripts/export_ads_mysql.py",
    ):
        assert path in script


def test_readmes_document_ads_batch_flow():
    warehouse_readme = _read(WAREHOUSE_README)
    root_readme = _read(ROOT_README)

    assert "dim/dws/ads batch flow" in warehouse_readme
    assert "run_ads.ps1" in warehouse_readme
    assert "export_ads_mysql.ps1" in warehouse_readme
    assert "ecommerce_dim" in warehouse_readme
    assert "ecommerce_dws" in warehouse_readme
    assert "ecommerce_ads" in warehouse_readme
    assert "dim, dws, ads" in root_readme
```

- [ ] **Step 2: Run failing documentation tests**

Run:

```powershell
pytest warehouse/tests/test_ads_assets.py -q
```

Expected: failure because docs and foundation check do not reference new assets yet.

- [ ] **Step 3: Update foundation check**

Add the DIM/DWS/ADS DDL, MySQL DDL, Spark ADS job files, run scripts, and exporter file to `$requiredPaths` in `deploy/scripts/check.ps1`.

- [ ] **Step 4: Update warehouse README**

Add a `DIM/DWS/ADS Batch Flow` section to `warehouse/README.md` that shows:

```powershell
powershell -ExecutionPolicy Bypass -File warehouse/scripts/run_ads.ps1 -BatchDate 2026-07-01
powershell -ExecutionPolicy Bypass -File warehouse/scripts/export_ads_mysql.ps1 -BatchDate 2026-07-01
```

Document the layer order `ODS -> DWD -> DIM -> DWS -> ADS -> MySQL` and the JSONL snapshot path `warehouse/data/ads/<batch-date>/`.

- [ ] **Step 5: Update root README**

Update `README.md` to state that the offline warehouse now includes ODS, DWD, DIM, DWS, ADS, and MySQL ADS export.

- [ ] **Step 6: Run documentation tests until they pass**

Run:

```powershell
pytest warehouse/tests/test_ads_assets.py -q
```

Expected: all ADS asset tests pass.

- [ ] **Step 7: Commit docs and checks**

```powershell
git add deploy/scripts/check.ps1 warehouse/README.md README.md warehouse/tests/test_ads_assets.py
git commit -m "docs: document ads warehouse flow"
```

---

### Task 8: Final Verification And PR Preparation

**Files:**
- Review all changed files from Tasks 1-7.

- [ ] **Step 1: Run ADS-focused tests**

Run:

```powershell
pytest warehouse/tests/test_ads_assets.py warehouse/tests/test_ads_mysql_export.py warehouse/spark/tests/test_ads_sql.py warehouse/spark/tests/test_ads_job.py -q
```

Expected: all selected tests pass.

- [ ] **Step 2: Run existing warehouse and Spark tests**

Run:

```powershell
pytest warehouse/tests warehouse/spark/tests -q
```

Expected: all warehouse and Spark tests pass.

- [ ] **Step 3: Run project foundation check**

Run:

```powershell
powershell -ExecutionPolicy Bypass -File deploy/scripts/check.ps1
```

Expected:

```text
Project foundation check passed.
```

- [ ] **Step 4: Inspect final diff**

Run:

```powershell
git status --short --branch
git log --oneline --decorate -8
```

Expected: branch contains only intentional fifth-stage commits, with no unrelated `architecture-options.html` staged or committed.

- [ ] **Step 5: Push and create PR**

Run after local verification passes:

```powershell
git push -u origin codex/phase5-dim-dws-ads-mysql-design
```

Create a PR against `main` with summary:

```markdown
## Summary
- add DIM, DWS, and ADS Hive DDL
- add Spark ADS batch job and JSONL snapshots
- add MySQL ADS DDL and exporter
- document DIM/DWS/ADS/MySQL flow

## Tests
- pytest warehouse/tests warehouse/spark/tests -q
- powershell -ExecutionPolicy Bypass -File deploy/scripts/check.ps1
```
