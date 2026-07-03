import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

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


def _canonical_row_key(row: dict[str, Any]) -> str:
    return json.dumps(row, ensure_ascii=False, default=str, sort_keys=True)


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in sorted(rows, key=_canonical_row_key):
            handle.write(json.dumps(row, ensure_ascii=False, default=str, sort_keys=True) + "\n")


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
