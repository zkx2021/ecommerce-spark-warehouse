# HDFS Hive ODS Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add the ODS landing layer that validates crawler JSONL output, loads it into HDFS partition paths, and exposes it through Hive external tables.

**Architecture:** Keep ODS source-preserving and narrow. Hive external tables point at `/warehouse/ecommerce/ods/<source>/` and partition by `dt`; scripts validate local crawler outputs before writing to HDFS and register partitions after upload. Static tests verify SQL and script conventions without requiring Docker, HDFS, or Hive.

**Tech Stack:** PowerShell, Hive SQL, HDFS CLI through Docker Compose, pytest.

---

## Scope Check

This plan implements ODS only. It does not parse JSON into DWD typed columns, run Spark jobs, export ADS data to MySQL, or update the dashboard.

## File Structure

- Create: `warehouse/hive/ods/create_ods_tables.sql` for Hive ODS external table DDL.
- Create: `warehouse/scripts/check_ods_inputs.ps1` for local processed JSONL validation.
- Create: `warehouse/scripts/load_ods.ps1` for HDFS upload and Hive partition registration.
- Create: `warehouse/tests/test_ods_assets.py` for static checks.
- Modify: `warehouse/README.md` with ODS run instructions and layer plan.
- Modify: `deploy/scripts/check.ps1` so foundation checks include ODS assets.

## Task 1: ODS Hive DDL

**Files:**
- Create: `warehouse/hive/ods/create_ods_tables.sql`
- Create: `warehouse/tests/test_ods_assets.py`

- [ ] **Step 1: Write failing SQL asset tests**

Create `warehouse/tests/test_ods_assets.py`:

```python
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
ODS_SQL = PROJECT_ROOT / "warehouse" / "hive" / "ods" / "create_ods_tables.sql"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8").lower()


def test_ods_sql_defines_expected_external_tables():
    sql = _read(ODS_SQL)

    for table_name in ("ods_products", "ods_carts", "ods_users"):
        assert f"create external table if not exists {table_name}" in sql


def test_ods_sql_uses_expected_columns_and_dt_partition():
    sql = _read(ODS_SQL)

    for column in ("entity string", "source string", "batch_date string", "data string"):
        assert column in sql
    assert "partitioned by (dt string)" in sql


def test_ods_sql_points_to_expected_hdfs_locations():
    sql = _read(ODS_SQL)

    assert "location '/warehouse/ecommerce/ods/products'" in sql
    assert "location '/warehouse/ecommerce/ods/carts'" in sql
    assert "location '/warehouse/ecommerce/ods/users'" in sql
```

- [ ] **Step 2: Run SQL tests and verify they fail**

Run:

```powershell
python -m pytest warehouse/tests/test_ods_assets.py -v
```

Expected: FAIL because `warehouse/hive/ods/create_ods_tables.sql` does not exist.

- [ ] **Step 3: Implement Hive ODS DDL**

Create `warehouse/hive/ods/create_ods_tables.sql`:

```sql
CREATE DATABASE IF NOT EXISTS ecommerce_ods;

USE ecommerce_ods;

CREATE EXTERNAL TABLE IF NOT EXISTS ods_products (
  entity STRING,
  source STRING,
  batch_date STRING,
  data STRING
)
PARTITIONED BY (dt STRING)
ROW FORMAT SERDE 'org.apache.hive.hcatalog.data.JsonSerDe'
STORED AS TEXTFILE
LOCATION '/warehouse/ecommerce/ods/products';

CREATE EXTERNAL TABLE IF NOT EXISTS ods_carts (
  entity STRING,
  source STRING,
  batch_date STRING,
  data STRING
)
PARTITIONED BY (dt STRING)
ROW FORMAT SERDE 'org.apache.hive.hcatalog.data.JsonSerDe'
STORED AS TEXTFILE
LOCATION '/warehouse/ecommerce/ods/carts';

CREATE EXTERNAL TABLE IF NOT EXISTS ods_users (
  entity STRING,
  source STRING,
  batch_date STRING,
  data STRING
)
PARTITIONED BY (dt STRING)
ROW FORMAT SERDE 'org.apache.hive.hcatalog.data.JsonSerDe'
STORED AS TEXTFILE
LOCATION '/warehouse/ecommerce/ods/users';
```

- [ ] **Step 4: Run SQL tests**

Run:

```powershell
python -m pytest warehouse/tests/test_ods_assets.py -v
```

Expected: 3 tests pass.

- [ ] **Step 5: Commit ODS DDL**

Run:

```powershell
git add warehouse/hive/ods/create_ods_tables.sql warehouse/tests/test_ods_assets.py
git commit -m "feat: add hive ods ddl"
```

Expected: commit succeeds.

## Task 2: ODS Input Validation Script

**Files:**
- Modify: `warehouse/tests/test_ods_assets.py`
- Create: `warehouse/scripts/check_ods_inputs.ps1`

- [ ] **Step 1: Add failing tests for the input check script**

Append to `warehouse/tests/test_ods_assets.py`:

```python
CHECK_SCRIPT = PROJECT_ROOT / "warehouse" / "scripts" / "check_ods_inputs.ps1"


def test_check_ods_inputs_script_validates_all_sources():
    script = _read(CHECK_SCRIPT)

    assert "param(" in script
    assert "$batchdate" in script
    for source in ("products", "carts", "users"):
        assert f'"{source}"' in script
        assert f'{source}.jsonl' in script
    assert "crawler" in script
    assert "data" in script
    assert "processed" in script
```

- [ ] **Step 2: Run the new test and verify it fails**

Run:

```powershell
python -m pytest warehouse/tests/test_ods_assets.py::test_check_ods_inputs_script_validates_all_sources -v
```

Expected: FAIL because `warehouse/scripts/check_ods_inputs.ps1` does not exist.

- [ ] **Step 3: Implement input validation script**

Create `warehouse/scripts/check_ods_inputs.ps1`:

```powershell
param(
  [Parameter(Mandatory = $true)]
  [ValidatePattern('^\d{4}-\d{2}-\d{2}$')]
  [string]$BatchDate
)

$ErrorActionPreference = "Stop"

$projectRoot = Resolve-Path (Join-Path $PSScriptRoot "..\..")
$processedDir = Join-Path $projectRoot "crawler\data\processed\$BatchDate"
$sources = @("products", "carts", "users")

foreach ($source in $sources) {
  $path = Join-Path $processedDir "$source.jsonl"
  if (-not (Test-Path -LiteralPath $path)) {
    throw "Missing processed ODS input for $source: $path"
  }

  $item = Get-Item -LiteralPath $path
  if ($item.Length -le 0) {
    throw "Processed ODS input is empty for $source: $path"
  }

  Write-Host "Found $source input: $path"
}

Write-Host "ODS input check passed for batch date $BatchDate."
```

- [ ] **Step 4: Run script tests**

Run:

```powershell
python -m pytest warehouse/tests/test_ods_assets.py -v
```

Expected: all current warehouse tests pass.

- [ ] **Step 5: Run the script against a missing batch**

Run:

```powershell
powershell -ExecutionPolicy Bypass -File warehouse/scripts/check_ods_inputs.ps1 -BatchDate 1999-01-01
```

Expected: FAIL with `Missing processed ODS input`.

- [ ] **Step 6: Commit input validation script**

Run:

```powershell
git add warehouse/scripts/check_ods_inputs.ps1 warehouse/tests/test_ods_assets.py
git commit -m "feat: add ods input checks"
```

Expected: commit succeeds.

## Task 3: ODS HDFS And Hive Load Script

**Files:**
- Modify: `warehouse/tests/test_ods_assets.py`
- Create: `warehouse/scripts/load_ods.ps1`

- [ ] **Step 1: Add failing tests for load script conventions**

Append to `warehouse/tests/test_ods_assets.py`:

```python
LOAD_SCRIPT = PROJECT_ROOT / "warehouse" / "scripts" / "load_ods.ps1"


def test_load_ods_script_uses_expected_hdfs_partition_paths():
    script = _read(LOAD_SCRIPT)

    assert "/warehouse/ecommerce/ods" in script
    assert "dt=$batchdate" in script
    for source in ("products", "carts", "users"):
        assert f'"{source}"' in script
        assert f"{source}.jsonl" in script


def test_load_ods_script_registers_hive_partitions():
    script = _read(LOAD_SCRIPT)

    assert "alter table ods_products add if not exists partition" in script
    assert "alter table ods_carts add if not exists partition" in script
    assert "alter table ods_users add if not exists partition" in script
    assert "docker compose exec" in script
    assert "hdfs dfs -put -f" in script
```

- [ ] **Step 2: Run load script tests and verify they fail**

Run:

```powershell
python -m pytest warehouse/tests/test_ods_assets.py::test_load_ods_script_uses_expected_hdfs_partition_paths warehouse/tests/test_ods_assets.py::test_load_ods_script_registers_hive_partitions -v
```

Expected: FAIL because `warehouse/scripts/load_ods.ps1` does not exist.

- [ ] **Step 3: Implement load script**

Create `warehouse/scripts/load_ods.ps1`:

```powershell
param(
  [Parameter(Mandatory = $true)]
  [ValidatePattern('^\d{4}-\d{2}-\d{2}$')]
  [string]$BatchDate
)

$ErrorActionPreference = "Stop"

$projectRoot = Resolve-Path (Join-Path $PSScriptRoot "..\..")
$checkScript = Join-Path $projectRoot "warehouse\scripts\check_ods_inputs.ps1"
$processedDir = Join-Path $projectRoot "crawler\data\processed\$BatchDate"
$hdfsBase = "/warehouse/ecommerce/ods"

& powershell -ExecutionPolicy Bypass -File $checkScript -BatchDate $BatchDate

$sources = @(
  @{ Name = "products"; Table = "ods_products" },
  @{ Name = "carts"; Table = "ods_carts" },
  @{ Name = "users"; Table = "ods_users" }
)

foreach ($source in $sources) {
  $name = $source.Name
  $table = $source.Table
  $localPath = Join-Path $processedDir "$name.jsonl"
  $hdfsDir = "$hdfsBase/$name/dt=$BatchDate"
  $hdfsPath = "$hdfsDir/$name.jsonl"

  Write-Host "Loading $name from $localPath to $hdfsPath"

  docker compose exec namenode hdfs dfs -mkdir -p $hdfsDir
  docker compose cp $localPath "namenode:/tmp/$name.jsonl"
  docker compose exec namenode hdfs dfs -put -f "/tmp/$name.jsonl" $hdfsPath
  docker compose exec namenode rm -f "/tmp/$name.jsonl"

  $partitionSql = "USE ecommerce_ods; ALTER TABLE $table ADD IF NOT EXISTS PARTITION (dt='$BatchDate') LOCATION '$hdfsDir';"
  docker compose exec hive-server2 beeline -u "jdbc:hive2://localhost:10000" -e $partitionSql
}

Write-Host "ODS load completed for batch date $BatchDate."
```

- [ ] **Step 4: Run load script tests**

Run:

```powershell
python -m pytest warehouse/tests/test_ods_assets.py -v
```

Expected: all current warehouse tests pass.

- [ ] **Step 5: Run load script missing-input check**

Run:

```powershell
powershell -ExecutionPolicy Bypass -File warehouse/scripts/load_ods.ps1 -BatchDate 1999-01-01
```

Expected: FAIL before Docker/HDFS commands with `Missing processed ODS input`.

- [ ] **Step 6: Commit load script**

Run:

```powershell
git add warehouse/scripts/load_ods.ps1 warehouse/tests/test_ods_assets.py
git commit -m "feat: add ods hdfs load script"
```

Expected: commit succeeds.

## Task 4: Warehouse Documentation And Foundation Check

**Files:**
- Modify: `warehouse/README.md`
- Modify: `deploy/scripts/check.ps1`
- Modify: `warehouse/tests/test_ods_assets.py`

- [ ] **Step 1: Add failing tests for docs and foundation assets**

Append to `warehouse/tests/test_ods_assets.py`:

```python
WAREHOUSE_README = PROJECT_ROOT / "warehouse" / "README.md"
FOUNDATION_CHECK = PROJECT_ROOT / "deploy" / "scripts" / "check.ps1"


def test_warehouse_readme_documents_ods_flow():
    readme = _read(WAREHOUSE_README)

    assert "ods" in readme
    assert "check_ods_inputs.ps1" in readme
    assert "load_ods.ps1" in readme
    assert "/warehouse/ecommerce/ods" in readme


def test_foundation_check_includes_ods_assets():
    script = _read(FOUNDATION_CHECK)

    assert "warehouse/hive/ods/create_ods_tables.sql" in script
    assert "warehouse/scripts/check_ods_inputs.ps1" in script
    assert "warehouse/scripts/load_ods.ps1" in script
```

- [ ] **Step 2: Run new docs tests and verify they fail**

Run:

```powershell
python -m pytest warehouse/tests/test_ods_assets.py::test_warehouse_readme_documents_ods_flow warehouse/tests/test_ods_assets.py::test_foundation_check_includes_ods_assets -v
```

Expected: FAIL because README and foundation check do not yet mention all ODS assets.

- [ ] **Step 3: Update warehouse README**

Replace `warehouse/README.md` with:

```markdown
# Warehouse Module

This module owns HDFS directory planning, Hive warehouse SQL, Spark jobs, and ADS export assets.

## Warehouse Layers

- `hive/ods`: source-preserving landing tables loaded from crawler JSONL.
- `hive/dwd`: cleaned detailed tables.
- `hive/dim`: shared dimension tables.
- `hive/dws`: subject summary tables.
- `hive/ads`: dashboard-ready metric tables.
- `spark/jobs`: Spark SQL and PySpark offline jobs.
- `spark/submit`: submit scripts.

## ODS Batch Flow

Generate crawler data from the project root:

```powershell
python crawler/run.py --batch-date 2026-07-01
```

Validate local processed JSONL inputs:

```powershell
powershell -ExecutionPolicy Bypass -File warehouse/scripts/check_ods_inputs.ps1 -BatchDate 2026-07-01
```

Create Hive ODS tables:

```powershell
docker compose exec hive-server2 beeline -u "jdbc:hive2://localhost:10000" -f /workspace/warehouse/hive/ods/create_ods_tables.sql
```

Load processed JSONL files to HDFS and register Hive partitions:

```powershell
powershell -ExecutionPolicy Bypass -File warehouse/scripts/load_ods.ps1 -BatchDate 2026-07-01
```

ODS files are stored in HDFS under:

```text
/warehouse/ecommerce/ods/products/dt=2026-07-01/products.jsonl
/warehouse/ecommerce/ods/carts/dt=2026-07-01/carts.jsonl
/warehouse/ecommerce/ods/users/dt=2026-07-01/users.jsonl
```
```

- [ ] **Step 4: Update foundation check paths**

Modify the `$requiredPaths` array in `deploy/scripts/check.ps1` to include:

```powershell
  "warehouse/hive/ods/create_ods_tables.sql",
  "warehouse/scripts/check_ods_inputs.ps1",
  "warehouse/scripts/load_ods.ps1",
```

- [ ] **Step 5: Run warehouse tests**

Run:

```powershell
python -m pytest warehouse/tests -v
```

Expected: all warehouse tests pass.

- [ ] **Step 6: Run foundation check**

Run:

```powershell
powershell -ExecutionPolicy Bypass -File deploy/scripts/check.ps1
```

Expected: `Project foundation check passed.`

- [ ] **Step 7: Commit documentation and foundation check**

Run:

```powershell
git add warehouse/README.md deploy/scripts/check.ps1 warehouse/tests/test_ods_assets.py
git commit -m "docs: document ods load flow"
```

Expected: commit succeeds.

## Task 5: Manual ODS Runtime Verification

**Files:**
- No required code changes unless verification exposes a bug.

- [ ] **Step 1: Run crawler tests**

Run:

```powershell
python -m pytest crawler/tests -v
```

Expected: all crawler tests pass.

- [ ] **Step 2: Run warehouse tests**

Run:

```powershell
python -m pytest warehouse/tests -v
```

Expected: all warehouse tests pass.

- [ ] **Step 3: Run backend health test**

Run:

```powershell
python -m pytest backend/tests/test_health.py -v
```

Expected: 1 test passes.

- [ ] **Step 4: Run project foundation check**

Run:

```powershell
powershell -ExecutionPolicy Bypass -File deploy/scripts/check.ps1
```

Expected: `Project foundation check passed.`

- [ ] **Step 5: Generate crawler data if network is available**

Run:

```powershell
python crawler/run.py --batch-date 2026-07-01
```

Expected when network is available: products, carts, and users each print a row count and write files under `crawler/data/processed/2026-07-01/`.

If network is unavailable, record the exact error and use existing generated files if present.

- [ ] **Step 6: Validate ODS inputs**

Run:

```powershell
powershell -ExecutionPolicy Bypass -File warehouse/scripts/check_ods_inputs.ps1 -BatchDate 2026-07-01
```

Expected when crawler files exist: `ODS input check passed for batch date 2026-07-01.`

- [ ] **Step 7: Run Docker ODS load only if services are available**

Run:

```powershell
docker compose ps
powershell -ExecutionPolicy Bypass -File warehouse/scripts/load_ods.ps1 -BatchDate 2026-07-01
```

Expected when Docker, HDFS, and Hive services are running: the script uploads each source file and registers Hive partitions.

If Docker services are unavailable, record the exact error and keep static tests as the verified baseline.

- [ ] **Step 8: Inspect git status**

Run:

```powershell
git status --short
```

Expected: no tracked changes are left. Ignored crawler data may exist but must not appear.

## Final Verification

- [ ] **Step 1: Run warehouse tests**

Run:

```powershell
python -m pytest warehouse/tests -v
```

Expected: all warehouse tests pass.

- [ ] **Step 2: Run crawler tests**

Run:

```powershell
python -m pytest crawler/tests -v
```

Expected: all crawler tests pass.

- [ ] **Step 3: Run backend health test**

Run:

```powershell
python -m pytest backend/tests/test_health.py -v
```

Expected: 1 test passes.

- [ ] **Step 4: Run project foundation check**

Run:

```powershell
powershell -ExecutionPolicy Bypass -File deploy/scripts/check.ps1
```

Expected: `Project foundation check passed.`

- [ ] **Step 5: Inspect git status**

Run:

```powershell
git status --short --branch
```

Expected: clean feature branch.

## Self-Review

Spec coverage:

- HDFS path convention is implemented by SQL locations and `load_ods.ps1`.
- Hive ODS tables are created for products, carts, and users.
- Input validation is handled by `check_ods_inputs.ps1`.
- Static tests cover SQL, scripts, README, and foundation check paths.
- Manual Docker/HDFS/Hive verification is explicit and optional when services are unavailable.

Completeness scan:

- No DWD, DIM, DWS, ADS, Spark, MySQL export, FastAPI, or dashboard work is included.

Type and naming consistency:

- Batch date is consistently named `BatchDate` in PowerShell and `dt` in Hive/HDFS partitions.
- Source names remain `products`, `carts`, and `users`.
- HDFS base path remains `/warehouse/ecommerce/ods`.
