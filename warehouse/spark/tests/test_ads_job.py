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
