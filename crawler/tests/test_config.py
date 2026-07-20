from datetime import date
from pathlib import Path

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


def test_load_sources_default_path_is_not_cwd_dependent(monkeypatch):
    monkeypatch.chdir(Path("crawler"))

    sources = load_sources()

    assert sources == [
        Source(
            name="products",
            url="https://dummyjson.com/products?limit=200",
            entity="product",
        ),
        Source(
            name="carts",
            url="https://dummyjson.com/carts",
            entity="order",
        ),
        Source(
            name="users",
            url="https://dummyjson.com/users",
            entity="user",
        ),
    ]


def test_parse_batch_date_accepts_yyyy_mm_dd():
    assert parse_batch_date("2026-07-01") == "2026-07-01"


def test_parse_batch_date_rejects_invalid_format():
    with pytest.raises(ValueError, match="YYYY-MM-DD"):
        parse_batch_date("20260701")


def test_parse_batch_date_rejects_non_zero_padded_values():
    with pytest.raises(ValueError, match="YYYY-MM-DD"):
        parse_batch_date("2026-7-1")


def test_default_batch_date_uses_today():
    assert default_batch_date(today=date(2026, 7, 1)) == "2026-07-01"
