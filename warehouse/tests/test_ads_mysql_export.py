import json

import pytest

from warehouse.scripts import export_ads_mysql


class FakeCursor:
    def __init__(self):
        self.statements = []

    def execute(self, statement, params=None):
        self.statements.append((statement, params))

    def executemany(self, statement, rows):
        self.statements.append((statement, rows))

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


class FakeConnection:
    def __init__(self):
        self.cursor_obj = FakeCursor()
        self.committed = False

    def cursor(self):
        return self.cursor_obj

    def commit(self):
        self.committed = True


def test_load_snapshot_reads_jsonl(tmp_path):
    path = tmp_path / "ads_kpi_daily.jsonl"
    path.write_text(json.dumps({"date_id": "2026-07-01", "total_order_count": 2}) + "\n", encoding="utf-8")

    rows = export_ads_mysql.load_snapshot(path)

    assert rows == [{"date_id": "2026-07-01", "total_order_count": 2}]


def test_load_snapshot_returns_empty_for_missing_file(tmp_path):
    rows = export_ads_mysql.load_snapshot(tmp_path / "missing.jsonl")

    assert rows == []


def test_load_snapshot_skips_blank_lines(tmp_path):
    path = tmp_path / "ads_kpi_daily.jsonl"
    path.write_text(
        "\n"
        + json.dumps({"date_id": "2026-07-01", "total_order_count": 2})
        + "\n\n",
        encoding="utf-8",
    )

    rows = export_ads_mysql.load_snapshot(path)

    assert rows == [{"date_id": "2026-07-01", "total_order_count": 2}]


def test_export_table_deletes_batch_then_inserts_rows():
    connection = FakeConnection()
    rows = [{"date_id": "2026-07-01", "total_order_count": 2}]

    count = export_ads_mysql.export_table(connection, "ads_kpi_daily", rows, batch_date="2026-07-01")

    assert count == 1
    assert "delete from ads_kpi_daily where date_id = %s" in connection.cursor_obj.statements[0][0].lower()
    assert "insert into ads_kpi_daily" in connection.cursor_obj.statements[1][0].lower()
    assert connection.committed is True


def test_export_table_rejects_unknown_table():
    connection = FakeConnection()

    with pytest.raises(ValueError, match="Unknown ADS table"):
        export_ads_mysql.export_table(connection, "not_ads", [], batch_date="2026-07-01")


def test_export_table_deletes_and_commits_when_rows_empty():
    connection = FakeConnection()

    count = export_ads_mysql.export_table(connection, "ads_kpi_daily", [], batch_date="2026-07-01")

    assert count == 0
    assert connection.cursor_obj.statements == [
        ("DELETE FROM ads_kpi_daily WHERE date_id = %s", ("2026-07-01",))
    ]
    assert connection.committed is True


def test_export_table_uses_first_row_column_order():
    connection = FakeConnection()
    rows = [
        {"date_id": "2026-07-01", "rank_no": 1, "product_id": 101},
        {"product_id": 102, "rank_no": 2, "date_id": "2026-07-01"},
    ]

    export_ads_mysql.export_table(connection, "ads_product_rank_daily", rows, batch_date="2026-07-01")

    statement, values = connection.cursor_obj.statements[1]
    assert statement == (
        "INSERT INTO ads_product_rank_daily (date_id, rank_no, product_id) VALUES (%s, %s, %s)"
    )
    assert values == [
        ("2026-07-01", 1, 101),
        ("2026-07-01", 2, 102),
    ]


def test_export_batch_loads_all_ads_snapshots(tmp_path):
    snapshot_dir = tmp_path / "2026-07-01"
    snapshot_dir.mkdir()
    (snapshot_dir / "ads_kpi_daily.jsonl").write_text(
        json.dumps({"date_id": "2026-07-01", "total_order_count": 2}) + "\n",
        encoding="utf-8",
    )
    (snapshot_dir / "ads_funnel_daily.jsonl").write_text(
        json.dumps({"date_id": "2026-07-01", "stage_order": 1}) + "\n",
        encoding="utf-8",
    )
    connection = FakeConnection()

    summary = export_ads_mysql.export_batch(connection, tmp_path, "2026-07-01")

    assert summary == {
        "ads_kpi_daily": 1,
        "ads_sales_trend_daily": 0,
        "ads_product_rank_daily": 0,
        "ads_category_share_daily": 0,
        "ads_user_profile_daily": 0,
        "ads_funnel_daily": 1,
    }


def test_parse_args_accepts_mysql_connection_options(tmp_path):
    args = export_ads_mysql.parse_args(
        [
            "--batch-date",
            "2026-07-01",
            "--snapshot-root",
            str(tmp_path),
            "--host",
            "mysql",
            "--port",
            "3307",
            "--database",
            "ecommerce_ads",
            "--user",
            "warehouse",
            "--password",
            "secret",
        ]
    )

    assert args.batch_date == "2026-07-01"
    assert args.snapshot_root == str(tmp_path)
    assert args.host == "mysql"
    assert args.port == 3307
    assert args.database == "ecommerce_ads"
    assert args.user == "warehouse"
    assert args.password == "secret"


def test_main_prints_json_summary(tmp_path, capsys, monkeypatch):
    connection = FakeConnection()
    monkeypatch.setattr(export_ads_mysql, "connect_mysql", lambda args: connection)

    result = export_ads_mysql.main(["--batch-date", "2026-07-01", "--snapshot-root", str(tmp_path)])

    assert result == 0
    assert json.loads(capsys.readouterr().out) == {
        "ads_kpi_daily": 0,
        "ads_sales_trend_daily": 0,
        "ads_product_rank_daily": 0,
        "ads_category_share_daily": 0,
        "ads_user_profile_daily": 0,
        "ads_funnel_daily": 0,
    }
