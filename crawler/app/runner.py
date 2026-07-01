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
