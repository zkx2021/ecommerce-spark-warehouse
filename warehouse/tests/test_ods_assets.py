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
