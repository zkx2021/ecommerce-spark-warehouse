import json
import subprocess
import sys
from pathlib import Path

from crawler.app.config import Source
from crawler.app.runner import run_ingestion


class FakeClient:
    def __init__(self):
        self.calls = []

    def fetch_json(self, url):
        self.calls.append(url)
        return {
            "products": [
                {"id": 1, "title": "Phone"},
            ]
        }


class FailingSecondClient:
    def __init__(self):
        self.calls = []

    def fetch_json(self, url):
        self.calls.append(url)
        if url.endswith("/users"):
            raise RuntimeError("users unavailable")
        return {
            "products": [
                {"id": 1, "title": "Phone"},
            ]
        }


def test_run_ingestion_writes_raw_and_processed_files(tmp_path):
    source = Source(name="products", url="https://dummyjson.com/products", entity="product")
    client = FakeClient()

    results = run_ingestion(
        sources=[source],
        batch_date="2026-07-01",
        data_dir=tmp_path,
        client=client,
    )

    raw_path = tmp_path / "raw" / "2026-07-01" / "products.json"
    processed_path = tmp_path / "processed" / "2026-07-01" / "products.jsonl"
    assert client.calls == ["https://dummyjson.com/products"]
    assert results == {"products": {"raw": raw_path, "processed": processed_path, "rows": 1}}
    assert json.loads(raw_path.read_text(encoding="utf-8")) == {
        "products": [{"id": 1, "title": "Phone"}]
    }
    assert json.loads(processed_path.read_text(encoding="utf-8").strip()) == {
        "entity": "product",
        "source": "products",
        "batch_date": "2026-07-01",
        "data": json.dumps({"id": 1, "title": "Phone"}, ensure_ascii=False),
    }


def test_run_ingestion_does_not_write_partial_batch_when_fetch_fails(tmp_path):
    sources = [
        Source(name="products", url="https://dummyjson.com/products", entity="product"),
        Source(name="users", url="https://dummyjson.com/users", entity="user"),
    ]
    client = FailingSecondClient()

    try:
        run_ingestion(
            sources=sources,
            batch_date="2026-07-01",
            data_dir=tmp_path,
            client=client,
        )
    except RuntimeError as exc:
        assert "users unavailable" in str(exc)
    else:
        raise AssertionError("Expected fetch failure")

    assert client.calls == ["https://dummyjson.com/products", "https://dummyjson.com/users"]
    assert not (tmp_path / "raw").exists()
    assert not (tmp_path / "processed").exists()


def test_cli_help_runs_from_repo_root_without_import_error():
    repo_root = Path(__file__).resolve().parents[2]

    result = subprocess.run(
        [sys.executable, "crawler/run.py", "--help"],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert "Run ecommerce crawler ingestion." in result.stdout
