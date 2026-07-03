import json

import pytest

from warehouse.spark.jobs import ads_job, ads_sql


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
    def __init__(self, rows_by_table=None):
        self.sql_calls = []
        self.table_reads = []
        self.table_records = []
        self.rows_by_table = rows_by_table or {}
        self.stopped = False

    def sql(self, statement):
        self.sql_calls.append(statement)

    def table(self, table_name):
        self.table_reads.append(table_name)
        short_name = table_name.rsplit(".", 1)[-1]
        rows = self.rows_by_table.get(short_name, [{"date_id": "2026-07-01", "metric": table_name}])
        frame = FakeDataFrame(rows)
        self.table_records.append((table_name, frame))
        return frame

    def stop(self):
        self.stopped = True


def test_parse_args_accepts_batch_date_and_export_dir(tmp_path):
    args = ads_job.parse_args(["--batch-date", "2026-07-01", "--export-root", str(tmp_path)])

    assert args.batch_date == "2026-07-01"
    assert args.export_root == str(tmp_path)


def test_parse_args_rejects_invalid_batch_date():
    with pytest.raises(SystemExit):
        ads_job.parse_args(["--batch-date", "2026-7-1"])


def test_run_executes_sql_in_order_and_writes_snapshots(tmp_path):
    config = ads_job.build_job_config("2026-07-01", export_root=tmp_path)
    rows_by_table = {
        table_name: [
            {"date_id": "2026-07-01", "metric": table_name, "rank": 2},
            {"date_id": "2026-07-01", "metric": table_name, "rank": 1},
        ][: (index % 3) + 1]
        for index, table_name in enumerate(ads_job.ADS_EXPORT_TABLES)
    }
    spark = FakeSpark(rows_by_table=rows_by_table)

    summary = ads_job.run(config, spark=spark)

    assert summary["status"] == "ok"
    assert summary["batch_date"] == "2026-07-01"
    assert spark.sql_calls == [statement.sql for statement in ads_sql.render_all_sql("2026-07-01")]
    assert spark.table_reads == [f"{ads_job.ADS_DATABASE}.{table_name}" for table_name in ads_job.ADS_EXPORT_TABLES]
    assert [record[0] for record in spark.table_records] == [
        f"{ads_job.ADS_DATABASE}.{table_name}" for table_name in ads_job.ADS_EXPORT_TABLES
    ]
    assert [record[1].where_clause for record in spark.table_records] == ["dt = '2026-07-01'"] * len(
        ads_job.ADS_EXPORT_TABLES
    )
    assert summary["exported"] == {table_name: len(rows_by_table[table_name]) for table_name in ads_job.ADS_EXPORT_TABLES}

    for table_name in ads_job.ADS_EXPORT_TABLES:
        snapshot = tmp_path / "2026-07-01" / f"{table_name}.jsonl"
        assert snapshot.exists()
        lines = snapshot.read_text(encoding="utf-8").splitlines()
        expected_rows = sorted(
            rows_by_table[table_name],
            key=lambda row: json.dumps(row, ensure_ascii=False, default=str, sort_keys=True),
        )
        assert [json.loads(line) for line in lines] == expected_rows


def test_run_does_not_stop_injected_spark_session(tmp_path):
    config = ads_job.build_job_config("2026-07-01", export_root=tmp_path)
    spark = FakeSpark()

    ads_job.run(config, spark=spark)

    assert spark.stopped is False


def test_run_stops_owned_spark_session(tmp_path, monkeypatch):
    config = ads_job.build_job_config("2026-07-01", export_root=tmp_path)
    spark = FakeSpark()
    monkeypatch.setattr(ads_job, "_create_spark_session", lambda: spark)

    ads_job.run(config)

    assert spark.stopped is True


def test_main_prints_runner_result(tmp_path, capsys):
    def runner(config):
        assert config == ads_job.AdsJobConfig(batch_date="2026-07-01", export_root=tmp_path)
        return {"status": "ok", "exported": {"ads_kpi_daily": 1}}

    exit_code = ads_job.main(["--batch-date", "2026-07-01", "--export-root", str(tmp_path)], runner=runner)

    assert exit_code == 0
    assert json.loads(capsys.readouterr().out) == {"status": "ok", "exported": {"ads_kpi_daily": 1}}
