import subprocess
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DWD_SQL = PROJECT_ROOT / "warehouse" / "hive" / "dwd" / "create_dwd_tables.sql"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8").lower()


def test_dwd_sql_creates_database_and_expected_tables():
    sql = _read(DWD_SQL)

    assert "create database if not exists ecommerce_dwd" in sql
    for table_name in ("dwd_product_info", "dwd_user_info", "dwd_order_cart_detail"):
        assert f"create external table if not exists {table_name}" in sql


def test_dwd_sql_defines_product_columns_and_partition():
    sql = _read(DWD_SQL)

    for column in (
        "product_id bigint",
        "product_name string",
        "category string",
        "brand string",
        "price decimal(18,2)",
        "discount_percentage decimal(10,2)",
        "rating decimal(10,2)",
        "stock int",
        "availability_status string",
        "thumbnail string",
        "source string",
        "batch_date string",
    ):
        assert column in sql
    assert "partitioned by (dt string)" in sql


def test_dwd_sql_defines_user_columns():
    sql = _read(DWD_SQL)

    for column in (
        "user_id bigint",
        "username string",
        "full_name string",
        "gender string",
        "age int",
        "age_group string",
        "email string",
        "phone string",
        "city string",
        "state string",
        "country string",
        "latitude decimal(18,6)",
        "longitude decimal(18,6)",
        "role string",
    ):
        assert column in sql


def test_dwd_sql_defines_cart_detail_columns():
    sql = _read(DWD_SQL)

    for column in (
        "cart_id bigint",
        "product_id bigint",
        "product_name string",
        "unit_price decimal(18,2)",
        "quantity int",
        "line_total decimal(18,2)",
        "line_discounted_total decimal(18,2)",
        "cart_total decimal(18,2)",
        "cart_discounted_total decimal(18,2)",
        "total_products int",
        "total_quantity int",
    ):
        assert column in sql


def test_dwd_sql_points_to_expected_hdfs_locations():
    sql = _read(DWD_SQL)

    assert "location '/warehouse/ecommerce/dwd/product_info'" in sql
    assert "location '/warehouse/ecommerce/dwd/user_info'" in sql
    assert "location '/warehouse/ecommerce/dwd/order_cart_detail'" in sql
    assert "stored as parquet" in sql


RUN_DWD_SCRIPT = PROJECT_ROOT / "warehouse" / "scripts" / "run_dwd.ps1"
WAREHOUSE_README = PROJECT_ROOT / "warehouse" / "README.md"
FOUNDATION_CHECK = PROJECT_ROOT / "deploy" / "scripts" / "check.ps1"


def test_run_dwd_script_submits_spark_job_and_creates_tables():
    script = _read(RUN_DWD_SCRIPT)

    assert "param(" in script
    assert "$batchdate" in script
    assert "create_dwd_tables.sql" in script
    assert "dwd_job.py" in script
    assert "dwd_transforms.py" in script
    assert "spark-submit" in script
    assert "spark://spark-master:7077" in script
    assert "hive-server2" in script
    assert "beeline" in script
    assert "--project-directory" in script
    assert "$projectroot" in script


def test_run_dwd_script_checks_native_failures_and_cleans_container_paths():
    script = _read(RUN_DWD_SCRIPT)

    assert "function invoke-native" in script
    assert "function invoke-compose" in script
    assert "$lastexitcode" in script
    assert "throw" in script
    assert "$runid" in script
    assert "/tmp/$runid" in script
    assert "finally" in script
    assert "rm" in script
    assert "-rf" in script


def test_run_dwd_script_rejects_invalid_batch_date_before_docker():
    result = subprocess.run(
        [
            "powershell",
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(RUN_DWD_SCRIPT),
            "-BatchDate",
            "2026-7-1",
        ],
        capture_output=True,
        text=True,
    )

    assert result.returncode != 0
    assert "does not match" in result.stderr.lower() or "validatepattern" in result.stderr.lower()


def test_warehouse_readme_documents_dwd_flow():
    readme = _read(WAREHOUSE_README)

    assert "dwd batch flow" in readme
    assert "create_dwd_tables.sql" in readme
    assert "run_dwd.ps1" in readme
    assert "powershell -executionpolicy bypass -file warehouse/scripts/run_dwd.ps1 -batchdate 2026-07-01" in readme
    for table_name in ("dwd_product_info", "dwd_user_info", "dwd_order_cart_detail"):
        assert table_name in readme


def test_foundation_check_includes_dwd_runtime_assets():
    script = _read(FOUNDATION_CHECK)

    assert "warehouse/hive/dwd/create_dwd_tables.sql" in script
    assert "warehouse/spark/jobs/dwd_job.py" in script
    assert "warehouse/spark/jobs/dwd_transforms.py" in script
    assert "warehouse/scripts/run_dwd.ps1" in script
