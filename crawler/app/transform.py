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
