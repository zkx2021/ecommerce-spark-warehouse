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
