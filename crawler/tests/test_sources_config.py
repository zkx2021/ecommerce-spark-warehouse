import json
from pathlib import Path


def test_sources_config_contains_required_dummyjson_sources():
    config_path = Path(__file__).resolve().parents[1] / "config" / "sources.json"
    data = json.loads(config_path.read_text(encoding="utf-8"))

    names = {source["name"] for source in data["sources"]}

    assert names == {"products", "carts", "users"}


def test_each_source_has_url_and_entity():
    config_path = Path(__file__).resolve().parents[1] / "config" / "sources.json"
    data = json.loads(config_path.read_text(encoding="utf-8"))

    for source in data["sources"]:
        assert source["url"].startswith("https://dummyjson.com/")
        assert source["entity"] in {"product", "order", "user"}
