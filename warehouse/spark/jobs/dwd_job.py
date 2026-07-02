import argparse
import json
import re
from collections import OrderedDict
from dataclasses import dataclass
from typing import Any, Callable, Mapping

from warehouse.spark.jobs import dwd_transforms


BATCH_DATE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$")
ODS_DATABASE = "ecommerce_ods"
DWD_DATABASE = "ecommerce_dwd"


@dataclass(frozen=True)
class SourceConfig:
    ods_table: str
    dwd_table: str
    transform_name: str


@dataclass(frozen=True)
class DwdJobConfig:
    batch_date: str
    ods_database: str
    dwd_database: str
    sources: Mapping[str, SourceConfig]


class DwdBatchError(RuntimeError):
    pass


def _batch_date(value: str) -> str:
    if not BATCH_DATE_PATTERN.fullmatch(value):
        raise argparse.ArgumentTypeError("batch date must use YYYY-MM-DD")
    return value


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run Spark DWD batch transformations.")
    parser.add_argument("--batch-date", required=True, type=_batch_date, help="Batch date in YYYY-MM-DD format.")
    return parser.parse_args(argv)


def build_job_config(batch_date: str) -> DwdJobConfig:
    validated_batch_date = _batch_date(batch_date)
    sources = OrderedDict(
        [
            (
                "products",
                SourceConfig(
                    ods_table="ods_products",
                    dwd_table="dwd_product_info",
                    transform_name="transform_products",
                ),
            ),
            (
                "users",
                SourceConfig(
                    ods_table="ods_users",
                    dwd_table="dwd_user_info",
                    transform_name="transform_users",
                ),
            ),
            (
                "carts",
                SourceConfig(
                    ods_table="ods_carts",
                    dwd_table="dwd_order_cart_detail",
                    transform_name="transform_carts",
                ),
            ),
        ]
    )
    return DwdJobConfig(
        batch_date=validated_batch_date,
        ods_database=ODS_DATABASE,
        dwd_database=DWD_DATABASE,
        sources=sources,
    )


def _create_spark_session():
    from pyspark.sql import SparkSession

    return SparkSession.builder.appName("ecommerce-dwd-batch").enableHiveSupport().getOrCreate()


def _row_to_dict(row: Any) -> dict[str, Any]:
    if hasattr(row, "asDict"):
        return row.asDict(recursive=True)
    return dict(row)


def _load_ods_rows(spark: Any, config: DwdJobConfig, source: SourceConfig) -> list[dict[str, Any]]:
    table_name = f"{config.ods_database}.{source.ods_table}"
    try:
        rows = (
            spark.table(table_name)
            .where(f"dt = '{config.batch_date}' AND batch_date = '{config.batch_date}'")
            .collect()
        )
    except Exception as exc:
        raise DwdBatchError(f"Failed to read ODS table {table_name}: {exc}") from exc

    records = [_row_to_dict(row) for row in rows]
    if not records:
        raise DwdBatchError(f"Empty ODS partition for {table_name} dt={config.batch_date}")
    return records


def _write_dwd_rows(spark: Any, config: DwdJobConfig, source_name: str, source: SourceConfig, rows: list[dict[str, Any]]) -> None:
    if not rows:
        raise DwdBatchError(f"No valid DWD rows for source {source_name} dt={config.batch_date}")

    view_name = f"tmp_{source_name}_dwd_{config.batch_date.replace('-', '')}"
    spark.createDataFrame(rows).createOrReplaceTempView(view_name)
    target_table = f"{config.dwd_database}.{source.dwd_table}"
    selected_columns = ", ".join(f"`{column}`" for column in rows[0] if column != "dt")
    spark.sql(
        f"INSERT OVERWRITE TABLE {target_table} PARTITION (dt='{config.batch_date}') "
        f"SELECT {selected_columns} FROM {view_name}"
    )


def run(config: DwdJobConfig, spark: Any | None = None) -> dict[str, object]:
    own_spark = spark is None
    active_spark = spark or _create_spark_session()
    summary: dict[str, object] = {"status": "ok", "batch_date": config.batch_date}

    try:
        for source_name, source in config.sources.items():
            transform = getattr(dwd_transforms, source.transform_name)
            ods_rows = _load_ods_rows(active_spark, config, source)
            result = transform(ods_rows, batch_date=config.batch_date)
            _write_dwd_rows(active_spark, config, source_name, source, result.rows)
            summary[source_name] = {
                "read": len(ods_rows),
                "written": len(result.rows),
                "invalid": result.invalid_count,
            }
    finally:
        if own_spark and hasattr(active_spark, "stop"):
            active_spark.stop()

    return summary


def main(argv: list[str] | None = None, runner: Callable[[DwdJobConfig], object] = run) -> int:
    args = parse_args(argv)
    result = runner(build_job_config(args.batch_date))
    if result is not None:
        print(json.dumps(result, ensure_ascii=False, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
