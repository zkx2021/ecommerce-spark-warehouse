import json

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
            "data": json.dumps({"id": 1, "title": "Phone"}, ensure_ascii=False),
        },
        {
            "entity": "product",
            "source": "products",
            "batch_date": "2026-07-01",
            "data": json.dumps({"id": 2, "title": "Laptop"}, ensure_ascii=False),
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
