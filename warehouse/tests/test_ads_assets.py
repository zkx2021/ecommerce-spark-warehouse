import re
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DIM_SQL = PROJECT_ROOT / "warehouse" / "hive" / "dim" / "create_dim_tables.sql"
DWS_SQL = PROJECT_ROOT / "warehouse" / "hive" / "dws" / "create_dws_tables.sql"
ADS_SQL = PROJECT_ROOT / "warehouse" / "hive" / "ads" / "create_ads_tables.sql"


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
