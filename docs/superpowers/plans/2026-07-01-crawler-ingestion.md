# Crawler Ingestion Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a runnable crawler ingestion module that fetches DummyJSON ecommerce data, writes raw JSON by batch date, and writes simple processed JSONL for later HDFS and Hive ingestion.

**Architecture:** The crawler becomes a small Python package under `crawler/app/`, with separate modules for config loading, HTTP fetching, transformation, storage, and orchestration. Tests mock network access and write generated files only under pytest temporary directories. The CLI remains thin and delegates to the runner.

**Tech Stack:** Python 3, requests, pytest, JSON, JSONL, PowerShell-friendly commands.

---

## Scope Check

This plan implements local crawler ingestion only. It does not upload to HDFS, create Hive tables, run Spark jobs, schedule batches, or update the dashboard.

## File Structure

- Create: `crawler/requirements.txt` for crawler runtime dependencies.
- Create: `crawler/app/__init__.py` to mark the app package.
- Create: `crawler/app/config.py` for source config and batch date handling.
- Create: `crawler/app/transform.py` for DummyJSON envelope-to-row conversion.
- Create: `crawler/app/storage.py` for raw JSON and processed JSONL writes.
- Create: `crawler/app/client.py` for HTTP JSON fetches.
- Create: `crawler/app/runner.py` for ingestion orchestration.
- Create: `crawler/run.py` for the command-line entry point.
- Create: `crawler/tests/test_config.py`
- Create: `crawler/tests/test_transform.py`
- Create: `crawler/tests/test_storage.py`
- Create: `crawler/tests/test_client.py`
- Create: `crawler/tests/test_runner.py`
- Modify: `crawler/README.md` with run instructions and output layout.

Generated files under `crawler/data/` remain ignored by Git through the existing `data/raw/` and `data/output/` rules plus the repository-wide generated data policy. This phase should also add `crawler/data/` to `.gitignore` if tests or manual runs reveal it is not ignored.

## Task 1: Crawler Runtime Dependency And Package Skeleton

**Files:**
- Create: `crawler/requirements.txt`
- Create: `crawler/app/__init__.py`

- [ ] **Step 1: Create crawler runtime requirements**

Write `crawler/requirements.txt`:

```text
requests>=2.32,<3
```

- [ ] **Step 2: Create the crawler app package marker**

Write `crawler/app/__init__.py`:

```python
"""Crawler ingestion package."""
```

- [ ] **Step 3: Verify package files exist**

Run:

```powershell
Test-Path crawler/requirements.txt
Test-Path crawler/app/__init__.py
```

Expected: both commands print `True`.

- [ ] **Step 4: Commit package skeleton**

Run:

```powershell
git add crawler/requirements.txt crawler/app/__init__.py
git commit -m "chore: add crawler package skeleton"
```

Expected: commit succeeds.

## Task 2: Source Config Loading And Batch Date Handling

**Files:**
- Create: `crawler/app/config.py`
- Create: `crawler/tests/test_config.py`

- [ ] **Step 1: Write failing config tests**

Write `crawler/tests/test_config.py`:

```python
from datetime import date

import pytest

from crawler.app.config import Source, default_batch_date, load_sources, parse_batch_date


def test_load_sources_reads_config_file(tmp_path):
    config_path = tmp_path / "sources.json"
    config_path.write_text(
        """
        {
          "sources": [
            {
              "name": "products",
              "url": "https://dummyjson.com/products",
              "entity": "product"
            }
          ]
        }
        """,
        encoding="utf-8",
    )

    sources = load_sources(config_path)

    assert sources == [
        Source(
            name="products",
            url="https://dummyjson.com/products",
            entity="product",
        )
    ]


def test_load_sources_rejects_missing_sources_key(tmp_path):
    config_path = tmp_path / "sources.json"
    config_path.write_text("{}", encoding="utf-8")

    with pytest.raises(ValueError, match="sources"):
        load_sources(config_path)


def test_parse_batch_date_accepts_yyyy_mm_dd():
    assert parse_batch_date("2026-07-01") == "2026-07-01"


def test_parse_batch_date_rejects_invalid_format():
    with pytest.raises(ValueError, match="YYYY-MM-DD"):
        parse_batch_date("20260701")


def test_default_batch_date_uses_today():
    assert default_batch_date(today=date(2026, 7, 1)) == "2026-07-01"
```

- [ ] **Step 2: Run tests and verify they fail before implementation**

Run:

```powershell
python -m pytest crawler/tests/test_config.py -v
```

Expected: FAIL because `crawler.app.config` does not exist.

- [ ] **Step 3: Implement config loading**

Write `crawler/app/config.py`:

```python
import json
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Iterable


@dataclass(frozen=True)
class Source:
    name: str
    url: str
    entity: str


def load_sources(config_path: Path | str = Path("crawler/config/sources.json")) -> list[Source]:
    path = Path(config_path)
    data = json.loads(path.read_text(encoding="utf-8"))
    raw_sources = data.get("sources")

    if not isinstance(raw_sources, list) or not raw_sources:
        raise ValueError("Config must contain a non-empty sources list")

    return [_parse_source(source) for source in raw_sources]


def parse_batch_date(value: str) -> str:
    try:
        parsed = datetime.strptime(value, "%Y-%m-%d")
    except ValueError as exc:
        raise ValueError("Batch date must use YYYY-MM-DD format") from exc
    return parsed.date().isoformat()


def default_batch_date(today: date | None = None) -> str:
    return (today or date.today()).isoformat()


def source_names(sources: Iterable[Source]) -> set[str]:
    return {source.name for source in sources}


def _parse_source(source: object) -> Source:
    if not isinstance(source, dict):
        raise ValueError("Each source must be an object")

    required = ("name", "url", "entity")
    missing = [key for key in required if not source.get(key)]
    if missing:
        raise ValueError(f"Source is missing required fields: {', '.join(missing)}")

    return Source(
        name=str(source["name"]),
        url=str(source["url"]),
        entity=str(source["entity"]),
    )
```

- [ ] **Step 4: Run config tests**

Run:

```powershell
python -m pytest crawler/tests/test_config.py -v
```

Expected: 5 tests pass.

- [ ] **Step 5: Commit config module**

Run:

```powershell
git add crawler/app/config.py crawler/tests/test_config.py
git commit -m "feat: add crawler config loading"
```

Expected: commit succeeds.

## Task 3: DummyJSON Transform To Processed Rows

**Files:**
- Create: `crawler/app/transform.py`
- Create: `crawler/tests/test_transform.py`

- [ ] **Step 1: Write failing transform tests**

Write `crawler/tests/test_transform.py`:

```python
import pytest

from crawler.app.config import Source
from crawler.app.transform import transform_payload


def test_transform_payload_creates_jsonl_ready_rows():
    source = Source(name="products", url="https://dummyjson.com/products", entity="product")
    payload = {
        "products": [
            {"id": 1, "title": "Phone"},
            {"id": 2, "title": "Laptop"},
        ]
    }

    rows = transform_payload(source, payload, batch_date="2026-07-01")

    assert rows == [
        {
            "entity": "product",
            "source": "products",
            "batch_date": "2026-07-01",
            "data": {"id": 1, "title": "Phone"},
        },
        {
            "entity": "product",
            "source": "products",
            "batch_date": "2026-07-01",
            "data": {"id": 2, "title": "Laptop"},
        },
    ]


def test_transform_payload_rejects_missing_expected_array():
    source = Source(name="users", url="https://dummyjson.com/users", entity="user")

    with pytest.raises(ValueError, match="users"):
        transform_payload(source, {"items": []}, batch_date="2026-07-01")


def test_transform_payload_rejects_non_list_array_value():
    source = Source(name="carts", url="https://dummyjson.com/carts", entity="order")

    with pytest.raises(ValueError, match="carts"):
        transform_payload(source, {"carts": {"id": 1}}, batch_date="2026-07-01")
```

- [ ] **Step 2: Run tests and verify they fail before implementation**

Run:

```powershell
python -m pytest crawler/tests/test_transform.py -v
```

Expected: FAIL because `crawler.app.transform` does not exist.

- [ ] **Step 3: Implement transform module**

Write `crawler/app/transform.py`:

```python
from typing import Any

from crawler.app.config import Source


def transform_payload(source: Source, payload: dict[str, Any], batch_date: str) -> list[dict[str, Any]]:
    items = payload.get(source.name)
    if not isinstance(items, list):
        raise ValueError(f"Payload for source {source.name} must contain a list at key {source.name}")

    return [
        {
            "entity": source.entity,
            "source": source.name,
            "batch_date": batch_date,
            "data": item,
        }
        for item in items
    ]
```

- [ ] **Step 4: Run transform tests**

Run:

```powershell
python -m pytest crawler/tests/test_transform.py -v
```

Expected: 3 tests pass.

- [ ] **Step 5: Commit transform module**

Run:

```powershell
git add crawler/app/transform.py crawler/tests/test_transform.py
git commit -m "feat: add crawler payload transform"
```

Expected: commit succeeds.

## Task 4: Raw JSON And Processed JSONL Storage

**Files:**
- Create: `crawler/app/storage.py`
- Create: `crawler/tests/test_storage.py`

- [ ] **Step 1: Write failing storage tests**

Write `crawler/tests/test_storage.py`:

```python
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
```

- [ ] **Step 2: Run tests and verify they fail before implementation**

Run:

```powershell
python -m pytest crawler/tests/test_storage.py -v
```

Expected: FAIL because `crawler.app.storage` does not exist.

- [ ] **Step 3: Implement storage module**

Write `crawler/app/storage.py`:

```python
import json
from pathlib import Path
from typing import Any, Iterable


def write_raw_json(base_dir: Path | str, batch_date: str, source_name: str, payload: dict[str, Any]) -> Path:
    path = Path(base_dir) / "raw" / batch_date / f"{source_name}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return path


def write_processed_jsonl(
    base_dir: Path | str,
    batch_date: str,
    source_name: str,
    rows: Iterable[dict[str, Any]],
) -> Path:
    path = Path(base_dir) / "processed" / batch_date / f"{source_name}.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    content = "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows)
    path.write_text(content, encoding="utf-8")
    return path
```

- [ ] **Step 4: Run storage tests**

Run:

```powershell
python -m pytest crawler/tests/test_storage.py -v
```

Expected: 2 tests pass.

- [ ] **Step 5: Commit storage module**

Run:

```powershell
git add crawler/app/storage.py crawler/tests/test_storage.py
git commit -m "feat: add crawler storage writers"
```

Expected: commit succeeds.

## Task 5: HTTP JSON Client

**Files:**
- Create: `crawler/app/client.py`
- Create: `crawler/tests/test_client.py`

- [ ] **Step 1: Write failing client tests**

Write `crawler/tests/test_client.py`:

```python
import pytest

from crawler.app.client import JsonHttpClient


class FakeResponse:
    def __init__(self, payload=None, status_error=None, json_error=None):
        self._payload = payload
        self._status_error = status_error
        self._json_error = json_error

    def raise_for_status(self):
        if self._status_error:
            raise self._status_error

    def json(self):
        if self._json_error:
            raise self._json_error
        return self._payload


class FakeSession:
    def __init__(self, response):
        self.response = response
        self.calls = []

    def get(self, url, timeout):
        self.calls.append((url, timeout))
        return self.response


def test_fetch_json_returns_payload():
    session = FakeSession(FakeResponse(payload={"products": []}))
    client = JsonHttpClient(session=session, timeout_seconds=3)

    payload = client.fetch_json("https://dummyjson.com/products")

    assert payload == {"products": []}
    assert session.calls == [("https://dummyjson.com/products", 3)]


def test_fetch_json_wraps_request_errors():
    session = FakeSession(FakeResponse(status_error=RuntimeError("boom")))
    client = JsonHttpClient(session=session, timeout_seconds=3)

    with pytest.raises(RuntimeError, match="https://dummyjson.com/products"):
        client.fetch_json("https://dummyjson.com/products")


def test_fetch_json_rejects_non_object_payload():
    session = FakeSession(FakeResponse(payload=[{"id": 1}]))
    client = JsonHttpClient(session=session, timeout_seconds=3)

    with pytest.raises(ValueError, match="JSON object"):
        client.fetch_json("https://dummyjson.com/products")
```

- [ ] **Step 2: Run tests and verify they fail before implementation**

Run:

```powershell
python -m pytest crawler/tests/test_client.py -v
```

Expected: FAIL because `crawler.app.client` does not exist.

- [ ] **Step 3: Implement client module**

Write `crawler/app/client.py`:

```python
from typing import Any, Protocol

import requests


class HttpSession(Protocol):
    def get(self, url: str, timeout: float):
        ...


class JsonHttpClient:
    def __init__(self, session: HttpSession | None = None, timeout_seconds: float = 10):
        self._session = session or requests.Session()
        self._timeout_seconds = timeout_seconds

    def fetch_json(self, url: str) -> dict[str, Any]:
        try:
            response = self._session.get(url, timeout=self._timeout_seconds)
            response.raise_for_status()
            payload = response.json()
        except Exception as exc:
            raise RuntimeError(f"Failed to fetch JSON from {url}: {exc}") from exc

        if not isinstance(payload, dict):
            raise ValueError(f"Expected JSON object from {url}")

        return payload
```

- [ ] **Step 4: Run client tests**

Run:

```powershell
python -m pytest crawler/tests/test_client.py -v
```

Expected: 3 tests pass.

- [ ] **Step 5: Commit client module**

Run:

```powershell
git add crawler/app/client.py crawler/tests/test_client.py
git commit -m "feat: add crawler http client"
```

Expected: commit succeeds.

## Task 6: Runner And CLI

**Files:**
- Create: `crawler/app/runner.py`
- Create: `crawler/run.py`
- Create: `crawler/tests/test_runner.py`

- [ ] **Step 1: Write failing runner tests**

Write `crawler/tests/test_runner.py`:

```python
import json

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
        "data": {"id": 1, "title": "Phone"},
    }
```

- [ ] **Step 2: Run tests and verify they fail before implementation**

Run:

```powershell
python -m pytest crawler/tests/test_runner.py -v
```

Expected: FAIL because `crawler.app.runner` does not exist.

- [ ] **Step 3: Implement runner module**

Write `crawler/app/runner.py`:

```python
from pathlib import Path
from typing import Protocol

from crawler.app.client import JsonHttpClient
from crawler.app.config import Source
from crawler.app.storage import write_processed_jsonl, write_raw_json
from crawler.app.transform import transform_payload


class JsonClient(Protocol):
    def fetch_json(self, url: str) -> dict:
        ...


def run_ingestion(
    sources: list[Source],
    batch_date: str,
    data_dir: Path | str = Path("crawler/data"),
    client: JsonClient | None = None,
) -> dict[str, dict]:
    active_client = client or JsonHttpClient()
    results: dict[str, dict] = {}

    for source in sources:
        payload = active_client.fetch_json(source.url)
        rows = transform_payload(source, payload, batch_date)
        raw_path = write_raw_json(data_dir, batch_date, source.name, payload)
        processed_path = write_processed_jsonl(data_dir, batch_date, source.name, rows)
        results[source.name] = {
            "raw": raw_path,
            "processed": processed_path,
            "rows": len(rows),
        }

    return results
```

- [ ] **Step 4: Implement CLI entry point**

Write `crawler/run.py`:

```python
import argparse

from crawler.app.config import default_batch_date, load_sources, parse_batch_date
from crawler.app.runner import run_ingestion


def main() -> int:
    parser = argparse.ArgumentParser(description="Run ecommerce crawler ingestion.")
    parser.add_argument("--batch-date", help="Batch date in YYYY-MM-DD format.")
    args = parser.parse_args()

    batch_date = parse_batch_date(args.batch_date) if args.batch_date else default_batch_date()
    sources = load_sources()
    results = run_ingestion(sources=sources, batch_date=batch_date)

    for source_name, result in results.items():
        print(
            f"{source_name}: rows={result['rows']} "
            f"raw={result['raw']} processed={result['processed']}"
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 5: Run runner tests**

Run:

```powershell
python -m pytest crawler/tests/test_runner.py -v
```

Expected: 1 test passes.

- [ ] **Step 6: Run all crawler tests**

Run:

```powershell
python -m pytest crawler/tests -v
```

Expected: all crawler tests pass.

- [ ] **Step 7: Commit runner and CLI**

Run:

```powershell
git add crawler/app/runner.py crawler/run.py crawler/tests/test_runner.py
git commit -m "feat: add crawler ingestion runner"
```

Expected: commit succeeds.

## Task 7: Documentation, Ignore Rules, And Manual Verification

**Files:**
- Modify: `.gitignore`
- Modify: `crawler/README.md`

- [ ] **Step 1: Ensure crawler generated data is ignored**

Add this line to `.gitignore` if it is not already covered:

```gitignore
crawler/data/
```

- [ ] **Step 2: Update crawler README**

Replace `crawler/README.md` with:

````markdown
# Crawler Module

The crawler module collects stable ecommerce-like data for the offline warehouse.

The default data source is DummyJSON:

- `https://dummyjson.com/products`
- `https://dummyjson.com/carts`
- `https://dummyjson.com/users`

## Install Runtime Dependencies

```powershell
python -m pip install -r crawler/requirements.txt
```

## Run A Batch

```powershell
python crawler/run.py --batch-date 2026-07-01
```

If `--batch-date` is omitted, the current local date is used.

## Output Layout

For batch date `2026-07-01`, raw API responses are written to:

```text
crawler/data/raw/2026-07-01/products.json
crawler/data/raw/2026-07-01/carts.json
crawler/data/raw/2026-07-01/users.json
```

Processed JSONL files are written to:

```text
crawler/data/processed/2026-07-01/products.jsonl
crawler/data/processed/2026-07-01/carts.jsonl
crawler/data/processed/2026-07-01/users.jsonl
```

Generated `crawler/data/` files are ignored by Git.
````

- [ ] **Step 3: Run all crawler tests**

Run:

```powershell
python -m pytest crawler/tests -v
```

Expected: all crawler tests pass.

- [ ] **Step 4: Run manual network verification if dependencies and network are available**

Run:

```powershell
python -m pip install -r crawler/requirements.txt
python crawler/run.py --batch-date 2026-07-01
```

Expected when network access is available: the command prints one summary line per source and writes raw/processed files under `crawler/data/`.

If dependency install or network access is unavailable in the sandbox, record the exact error and keep the code verified through mocked tests.

- [ ] **Step 5: Confirm generated data is ignored**

Run:

```powershell
git status --short
```

Expected: generated `crawler/data/` files are not listed.

- [ ] **Step 6: Commit docs and ignore rule**

Run:

```powershell
git add .gitignore crawler/README.md
git commit -m "docs: document crawler ingestion"
```

Expected: commit succeeds.

## Final Verification

- [ ] **Step 1: Run crawler test suite**

Run:

```powershell
python -m pytest crawler/tests -v
```

Expected: all crawler tests pass.

- [ ] **Step 2: Run existing backend health test**

Run:

```powershell
python -m pytest backend/tests/test_health.py -v
```

Expected: 1 test passes.

- [ ] **Step 3: Run project foundation check**

Run:

```powershell
powershell -ExecutionPolicy Bypass -File deploy/scripts/check.ps1
```

Expected: `Project foundation check passed.`

- [ ] **Step 4: Inspect git status**

Run:

```powershell
git status --short
```

Expected: no tracked changes are left. The pre-existing untracked `architecture-options.html` may still appear in the main checkout and should not be included in this phase.

## Self-Review

Spec coverage:

- Config loading maps to `crawler/config/sources.json`.
- Batch-date partitioning maps to `crawler/data/raw/<batch-date>/` and `crawler/data/processed/<batch-date>/`.
- JSONL rows include `entity`, `source`, `batch_date`, and original item `data`.
- Tests mock HTTP and do not require real network access.
- Manual network verification is explicit but optional when environment access is unavailable.

Completeness scan:

- No incomplete implementation steps are intentionally present.

Type and naming consistency:

- `Source` is defined in `crawler.app.config` and reused by transform and runner.
- `batch_date` is consistently a `YYYY-MM-DD` string.
- `data_dir` defaults to `crawler/data`.
