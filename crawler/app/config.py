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
