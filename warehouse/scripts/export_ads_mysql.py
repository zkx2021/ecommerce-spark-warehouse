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

ADS_TABLE_COLUMNS = {
    "ads_kpi_daily": (
        "date_id",
        "total_sales_amount",
        "total_order_count",
        "paid_user_count",
        "avg_order_amount",
        "payment_conversion_rate",
    ),
    "ads_sales_trend_daily": (
        "date_id",
        "sales_amount",
        "order_count",
        "paid_user_count",
    ),
    "ads_product_rank_daily": (
        "date_id",
        "rank_no",
        "product_id",
        "product_name",
        "category",
        "sales_quantity",
        "sales_amount",
    ),
    "ads_category_share_daily": (
        "date_id",
        "category",
        "sales_amount",
        "sales_quantity",
        "sales_share",
    ),
    "ads_user_profile_daily": (
        "date_id",
        "dimension_type",
        "dimension_value",
        "user_count",
        "buyer_count",
        "sales_amount",
    ),
    "ads_funnel_daily": (
        "date_id",
        "stage_name",
        "stage_order",
        "stage_count",
        "conversion_rate",
    ),
}


def load_snapshot(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []

    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def export_table(connection: Any, table_name: str, rows: list[dict[str, Any]], *, batch_date: str) -> int:
    if table_name not in ADS_TABLES:
        raise ValueError(f"Unknown ADS table: {table_name}")

    with connection.cursor() as cursor:
        cursor.execute(f"DELETE FROM {table_name} WHERE date_id = %s", (batch_date,))
        if rows:
            columns = ADS_TABLE_COLUMNS[table_name]
            placeholders = ", ".join(["%s"] * len(columns))
            column_sql = ", ".join(columns)
            values = [tuple(row.get(column) for column in columns) for row in rows]
            cursor.executemany(
                f"INSERT INTO {table_name} ({column_sql}) VALUES ({placeholders})",
                values,
            )

    return len(rows)


def _snapshot_path(snapshot_root: str | Path, batch_date: str, table_name: str) -> Path:
    return Path(snapshot_root) / batch_date / f"{table_name}.jsonl"


def _preflight_snapshots(snapshot_root: str | Path, batch_date: str) -> None:
    missing_paths = [
        _snapshot_path(snapshot_root, batch_date, table_name)
        for table_name in ADS_TABLES
        if not _snapshot_path(snapshot_root, batch_date, table_name).exists()
    ]
    if missing_paths:
        raise FileNotFoundError(missing_paths[0])


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Export ADS JSONL snapshots into MySQL.")
    parser.add_argument("--batch-date", required=True, help="Batch date matching the snapshot directory.")
    parser.add_argument("--snapshot-root", default="warehouse/data/ads", help="ADS JSONL snapshot root.")
    parser.add_argument("--host", default="localhost", help="MySQL host.")
    parser.add_argument("--port", type=int, default=3306, help="MySQL port.")
    parser.add_argument("--database", default="ecommerce_ads", help="MySQL database.")
    parser.add_argument("--user", default="ecommerce", help="MySQL user.")
    parser.add_argument("--password", default="ecommerce_password", help="MySQL password.")
    return parser.parse_args(argv)


def connect_mysql(args: argparse.Namespace) -> Any:
    import mysql.connector

    return mysql.connector.connect(
        host=args.host,
        port=args.port,
        database=args.database,
        user=args.user,
        password=args.password,
    )


def export_batch(connection: Any, snapshot_root: str | Path, batch_date: str) -> dict[str, int]:
    _preflight_snapshots(snapshot_root, batch_date)
    snapshots = {
        table_name: load_snapshot(_snapshot_path(snapshot_root, batch_date, table_name))
        for table_name in ADS_TABLES
    }

    try:
        exported: dict[str, int] = {}
        for table_name, rows in snapshots.items():
            exported[table_name] = export_table(connection, table_name, rows, batch_date=batch_date)
        connection.commit()
        return exported
    except Exception:
        rollback = getattr(connection, "rollback", None)
        if callable(rollback):
            rollback()
        raise


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    connection = None
    try:
        connection = connect_mysql(args)
        summary = export_batch(connection, args.snapshot_root, args.batch_date)
        print(json.dumps(summary, ensure_ascii=False))
        return 0
    finally:
        close = getattr(connection, "close", None)
        if callable(close):
            close()


if __name__ == "__main__":
    raise SystemExit(main())
