import re
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DIM_SQL = PROJECT_ROOT / "warehouse" / "hive" / "dim" / "create_dim_tables.sql"
DWS_SQL = PROJECT_ROOT / "warehouse" / "hive" / "dws" / "create_dws_tables.sql"
ADS_SQL = PROJECT_ROOT / "warehouse" / "hive" / "ads" / "create_ads_tables.sql"
MYSQL_ADS_SQL = PROJECT_ROOT / "deploy" / "mysql" / "init" / "02-create-ads-tables.sql"
DOCKER_COMPOSE = PROJECT_ROOT / "docker-compose.yml"
RUN_ADS_SCRIPT = PROJECT_ROOT / "warehouse" / "scripts" / "run_ads.ps1"
EXPORT_ADS_SCRIPT = PROJECT_ROOT / "warehouse" / "scripts" / "export_ads_mysql.ps1"
FOUNDATION_CHECK = PROJECT_ROOT / "deploy" / "scripts" / "check.ps1"
WAREHOUSE_README = PROJECT_ROOT / "warehouse" / "README.md"
ROOT_README = PROJECT_ROOT / "README.md"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8").lower()


def _table_locations(sql: str) -> dict[str, str]:
    return dict(
        re.findall(
            r"create external table if not exists\s+(\w+).*?location\s+'([^']+)';",
            sql,
            flags=re.DOTALL,
        )
    )


def _mysql_table_block(sql: str, table_name: str) -> str:
    match = re.search(rf"create table if not exists\s+{table_name}\s*\(", sql)
    assert match is not None, f"missing CREATE TABLE for {table_name}"

    start = match.end() - 1
    depth = 0
    for index in range(start, len(sql)):
        if sql[index] == "(":
            depth += 1
        elif sql[index] == ")":
            depth -= 1
            if depth == 0:
                return sql[start : index + 1]

    raise AssertionError(f"unterminated CREATE TABLE block for {table_name}")


def _compose_env_value(name: str) -> str:
    compose = _read(DOCKER_COMPOSE)
    match = re.search(rf"^\s*{re.escape(name.lower())}:\s*([^\s#]+)", compose, flags=re.MULTILINE)
    assert match is not None, f"missing Compose environment value for {name}"
    return match.group(1)


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


def test_dim_sql_points_to_expected_hdfs_locations():
    sql = _read(DIM_SQL)

    assert _table_locations(sql) == {
        "dim_date": "/warehouse/ecommerce/dim/date",
        "dim_product": "/warehouse/ecommerce/dim/product",
        "dim_category": "/warehouse/ecommerce/dim/category",
        "dim_user": "/warehouse/ecommerce/dim/user",
    }


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


def test_dws_sql_points_to_expected_hdfs_locations():
    sql = _read(DWS_SQL)

    assert _table_locations(sql) == {
        "dws_sales_daily": "/warehouse/ecommerce/dws/sales_daily",
        "dws_product_daily": "/warehouse/ecommerce/dws/product_daily",
        "dws_category_daily": "/warehouse/ecommerce/dws/category_daily",
        "dws_user_profile_daily": "/warehouse/ecommerce/dws/user_profile_daily",
        "dws_funnel_daily": "/warehouse/ecommerce/dws/funnel_daily",
    }


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


def test_ads_sql_points_to_expected_hdfs_locations():
    sql = _read(ADS_SQL)

    assert _table_locations(sql) == {
        "ads_kpi_daily": "/warehouse/ecommerce/ads/kpi_daily",
        "ads_sales_trend_daily": "/warehouse/ecommerce/ads/sales_trend_daily",
        "ads_product_rank_daily": "/warehouse/ecommerce/ads/product_rank_daily",
        "ads_category_share_daily": "/warehouse/ecommerce/ads/category_share_daily",
        "ads_user_profile_daily": "/warehouse/ecommerce/ads/user_profile_daily",
        "ads_funnel_daily": "/warehouse/ecommerce/ads/funnel_daily",
    }


def test_mysql_ads_sql_creates_dashboard_tables_and_keys():
    sql = _read(MYSQL_ADS_SQL)

    assert "use ecommerce_ads" in sql
    expected_primary_keys = {
        "ads_kpi_daily": "primary key (date_id)",
        "ads_sales_trend_daily": "primary key (date_id)",
        "ads_product_rank_daily": "primary key (date_id, rank_no)",
        "ads_category_share_daily": "primary key (date_id, category)",
        "ads_user_profile_daily": "primary key (date_id, dimension_type, dimension_value)",
        "ads_funnel_daily": "primary key (date_id, stage_order)",
    }
    for table_name, primary_key in expected_primary_keys.items():
        table_block = _mysql_table_block(sql, table_name)
        assert primary_key in table_block


def test_mysql_init_directory_is_mounted_for_entrypoint_scripts():
    compose = _read(DOCKER_COMPOSE).replace("\\", "/")

    assert re.search(
        r"^\s*-\s+\.?/deploy/mysql/init:/docker-entrypoint-initdb\.d(?::ro)?\s*$",
        compose,
        flags=re.MULTILINE,
    )


def test_run_ads_script_creates_tables_and_submits_spark_job():
    script = _read(RUN_ADS_SCRIPT)
    normalized_script = script.replace("\\", "/")

    assert "param(" in script
    assert "$batchdate" in script
    assert "create_dim_tables.sql" in script
    assert "create_dws_tables.sql" in script
    assert "create_ads_tables.sql" in script
    assert "ads_job.py" in script
    assert "ads_sql.py" in script
    assert "spark-submit" in script
    assert "spark://spark-master:7077" in script
    assert "beeline" in script
    assert "--export-root" in script
    assert "--project-directory" in script
    assert "warehouse/data/ads" in normalized_script


def test_run_ads_script_runs_hive_layers_in_dependency_order():
    script = _read(RUN_ADS_SCRIPT)

    beeline_lines = [
        line for line in script.splitlines() if '"beeline"' in line and '"-f"' in line
    ]
    beeline_targets = [
        re.search(r'"-f",\s*(\$container(?:dim|dws|ads)sqlpath)', line).group(1)
        for line in beeline_lines
    ]

    assert beeline_targets == [
        "$containerdimsqlpath",
        "$containerdwssqlpath",
        "$containeradssqlpath",
    ]


def test_run_ads_script_copies_container_exports_to_host_before_cleanup():
    script = _read(RUN_ADS_SCRIPT)

    assert "$hostbatchexportdir" in script
    assert "$containerexportroot" in script
    copy_match = re.search(
        r'invoke-compose\s+-composeargs\s+@\([^)]*"cp"[^)]*'
        r'"spark-master:\$containerexportroot"[^)]*\$hostbatchexportdir[^)]*\)',
        script,
        flags=re.DOTALL,
    )
    assert copy_match is not None

    spark_cleanup_index = script.index('"spark-master", "rm", "-rf", $containerrundir')
    assert copy_match.start() < spark_cleanup_index


def test_export_ads_mysql_script_calls_python_exporter():
    script = _read(EXPORT_ADS_SCRIPT)

    assert "param(" in script
    assert "$batchdate" in script
    assert "export_ads_mysql.py" in script
    assert "--batch-date" in script
    assert "--snapshot-root" in script
    assert "--host" in script
    assert "--port" in script
    assert "--database" in script
    assert "--user" in script
    assert "--password" in script
    assert "$lastexitcode" in script


def test_export_ads_mysql_script_defaults_to_compose_mysql_password():
    compose_password = _compose_env_value("MYSQL_PASSWORD")
    script = _read(EXPORT_ADS_SCRIPT)

    assert f'$password = "{compose_password}"' in script
    assert "--password" in script
    assert "$password" in script


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
    assert "ods -> dwd -> dim -> dws -> ads -> mysql" in warehouse_readme
    assert "warehouse/data/ads/<batch-date>/" in warehouse_readme
    assert "dim, dws, ads" in root_readme
