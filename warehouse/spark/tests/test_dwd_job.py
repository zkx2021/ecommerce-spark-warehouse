import json

import pytest

from warehouse.spark.jobs import dwd_job


def _ods_row(source: str, batch_date: str, payload: dict):
    return {
        "entity": source[:-1],
        "source": source,
        "batch_date": batch_date,
        "dt": batch_date,
        "data": json.dumps(payload),
    }


class FakeRow(dict):
    def asDict(self, recursive=False):
        return dict(self)


class FakeReaderDataFrame:
    def __init__(self, rows):
        self.rows = [FakeRow(row) for row in rows]
        self.where_clause = None

    def where(self, clause):
        self.where_clause = clause
        return self

    def collect(self):
        return self.rows


class FakeDataFrameReader:
    def __init__(self, spark):
        self.spark = spark

    def json(self, path):
        frame = FakeReaderDataFrame(self.spark.path_rows[path])
        self.spark.reads.append((path, frame))
        return frame


class FakeWriterDataFrame:
    def __init__(self, rows, spark):
        self.rows = rows
        self.spark = spark

    def createOrReplaceTempView(self, name):
        self.spark.views[name] = self.rows


class FakeSpark:
    def __init__(self, path_rows):
        self.path_rows = path_rows
        self.read = FakeDataFrameReader(self)
        self.reads = []
        self.created_frames = []
        self.views = {}
        self.sql_calls = []

    def createDataFrame(self, rows):
        frame = FakeWriterDataFrame(rows, self)
        self.created_frames.append(frame)
        return frame

    def sql(self, statement):
        self.sql_calls.append(statement)


def test_parse_args_accepts_batch_date():
    args = dwd_job.parse_args(["--batch-date", "2026-07-01"])

    assert args.batch_date == "2026-07-01"


def test_parse_args_rejects_invalid_batch_date():
    with pytest.raises(SystemExit):
        dwd_job.parse_args(["--batch-date", "2026-7-1"])


def test_build_job_config_maps_ods_to_dwd_tables():
    config = dwd_job.build_job_config("2026-07-01")

    assert config.batch_date == "2026-07-01"
    assert config.ods_database == "ecommerce_ods"
    assert config.dwd_database == "ecommerce_dwd"
    assert config.sources["products"].ods_table == "ods_products"
    assert config.sources["products"].ods_path_name == "products"
    assert config.sources["products"].dwd_table == "dwd_product_info"
    assert config.sources["products"].transform_name == "transform_products"
    assert config.sources["users"].ods_table == "ods_users"
    assert config.sources["users"].ods_path_name == "users"
    assert config.sources["users"].dwd_table == "dwd_user_info"
    assert config.sources["users"].transform_name == "transform_users"
    assert config.sources["carts"].ods_table == "ods_carts"
    assert config.sources["carts"].ods_path_name == "carts"
    assert config.sources["carts"].dwd_table == "dwd_order_cart_detail"
    assert config.sources["carts"].transform_name == "transform_carts"


def test_main_passes_config_to_runner():
    captured = []

    def runner(config):
        captured.append(config)
        return {"status": "ok", "batch_date": config.batch_date}

    exit_code = dwd_job.main(["--batch-date", "2026-07-01"], runner=runner)

    assert exit_code == 0
    assert captured[0].batch_date == "2026-07-01"


def test_run_reads_ods_transforms_and_overwrites_dwd_partitions():
    config = dwd_job.build_job_config("2026-07-01")
    spark = FakeSpark(
        {
            "hdfs://namenode:8020/warehouse/ecommerce/ods/products/dt=2026-07-01": [
                _ods_row("products", "2026-07-01", {"id": 1, "title": "Product", "price": 9.99})
            ],
            "hdfs://namenode:8020/warehouse/ecommerce/ods/users/dt=2026-07-01": [
                _ods_row("users", "2026-07-01", {"id": 2, "username": "user2"})
            ],
            "hdfs://namenode:8020/warehouse/ecommerce/ods/carts/dt=2026-07-01": [
                _ods_row(
                    "carts",
                    "2026-07-01",
                    {"id": 3, "userId": 2, "products": [{"id": 1, "title": "Product", "price": 9.99, "quantity": 2}]},
                )
            ],
        }
    )

    summary = dwd_job.run(config, spark=spark)

    assert summary == {
        "status": "ok",
        "batch_date": "2026-07-01",
        "products": {"read": 1, "written": 1, "invalid": 0},
        "users": {"read": 1, "written": 1, "invalid": 0},
        "carts": {"read": 1, "written": 1, "invalid": 0},
    }
    assert [path for path, _frame in spark.reads] == [
        "hdfs://namenode:8020/warehouse/ecommerce/ods/products/dt=2026-07-01",
        "hdfs://namenode:8020/warehouse/ecommerce/ods/users/dt=2026-07-01",
        "hdfs://namenode:8020/warehouse/ecommerce/ods/carts/dt=2026-07-01",
    ]
    assert all("batch_date = '2026-07-01'" in frame.where_clause for _path, frame in spark.reads)
    assert any(
        "INSERT OVERWRITE TABLE ecommerce_dwd.dwd_product_info PARTITION (dt='2026-07-01')" in statement
        for statement in spark.sql_calls
    )
    assert any(
        "INSERT OVERWRITE TABLE ecommerce_dwd.dwd_order_cart_detail PARTITION (dt='2026-07-01')" in statement
        for statement in spark.sql_calls
    )
    assert any(
        "ALTER TABLE ecommerce_dwd.dwd_order_cart_detail ADD COLUMNS (category_hint STRING)" in statement
        for statement in spark.sql_calls
    )


def test_run_fails_empty_ods_partition():
    config = dwd_job.build_job_config("2026-07-01")
    spark = FakeSpark({"hdfs://namenode:8020/warehouse/ecommerce/ods/products/dt=2026-07-01": []})

    with pytest.raises(dwd_job.DwdBatchError, match="Empty ODS partition"):
        dwd_job.run(config, spark=spark)


def test_normalize_dwd_row_converts_float_fields():
    row = {
        "price": 10,
        "rating": 4,
        "stock": 5,
        "product_id": 1,
    }

    normalized = dwd_job._normalize_dwd_row(row)

    assert normalized["price"] == 10.0
    assert normalized["rating"] == 4.0
    assert normalized["stock"] == 5
    assert normalized["product_id"] == 1
