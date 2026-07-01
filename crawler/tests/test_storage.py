import json

from crawler.app.storage import write_processed_jsonl, write_raw_json


def test_write_raw_json_uses_batch_date_directory(tmp_path):
    payload = {"products": [{"id": 1}]}

    path = write_raw_json(tmp_path, "2026-07-01", "products", payload)

    assert path == tmp_path / "raw" / "2026-07-01" / "products.json"
    assert json.loads(path.read_text(encoding="utf-8")) == payload


def test_write_processed_jsonl_writes_one_row_per_line(tmp_path):
    rows = [
        {"entity": "product", "source": "products", "batch_date": "2026-07-01", "data": {"id": 1}},
        {"entity": "product", "source": "products", "batch_date": "2026-07-01", "data": {"id": 2}},
    ]

    path = write_processed_jsonl(tmp_path, "2026-07-01", "products", rows)

    assert path == tmp_path / "processed" / "2026-07-01" / "products.jsonl"
    lines = path.read_text(encoding="utf-8").splitlines()
    assert [json.loads(line) for line in lines] == rows
