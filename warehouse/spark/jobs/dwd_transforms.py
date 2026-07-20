from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any, Iterable


@dataclass(frozen=True)
class TransformResult:
    rows: list[dict[str, Any]]
    invalid_count: int


def _is_positive_number(value: Any) -> bool:
    return not isinstance(value, bool) and isinstance(value, (int, float)) and value > 0


def _is_non_negative_number(value: Any) -> bool:
    return not isinstance(value, bool) and isinstance(value, (int, float)) and value >= 0


def _is_positive_integer(value: Any) -> bool:
    return not isinstance(value, bool) and isinstance(value, int) and value > 0


def _is_non_negative_integer(value: Any) -> bool:
    return not isinstance(value, bool) and isinstance(value, int) and value >= 0


def _is_non_empty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _parse_payload(row: dict[str, Any], *, source: str, batch_date: str) -> dict[str, Any] | None:
    if row.get("source") != source:
        return None
    if row.get("batch_date") != batch_date or row.get("dt") != batch_date:
        return None

    data = row.get("data")
    if not isinstance(data, str):
        return None

    try:
        payload = json.loads(data)
    except json.JSONDecodeError:
        return None

    if not isinstance(payload, dict):
        return None
    return payload


def transform_products(rows: Iterable[dict[str, Any]], *, batch_date: str) -> TransformResult:
    dwd_rows: list[dict[str, Any]] = []
    invalid_count = 0

    for row in rows:
        payload = _parse_payload(row, source="products", batch_date=batch_date)
        if payload is None:
            invalid_count += 1
            continue

        product_id = payload.get("id")
        product_name = payload.get("title")
        price = payload.get("price")
        stock = payload.get("stock")

        if not _is_positive_integer(product_id) or not _is_non_empty_string(product_name) or not _is_non_negative_number(price):
            invalid_count += 1
            continue
        if stock is not None and not _is_non_negative_integer(stock):
            invalid_count += 1
            continue

        dwd_rows.append(
            {
                "product_id": product_id,
                "product_name": product_name,
                "category": payload.get("category"),
                "brand": payload.get("brand"),
                "price": price,
                "discount_percentage": payload.get("discountPercentage"),
                "rating": payload.get("rating"),
                "stock": stock,
                "availability_status": payload.get("availabilityStatus"),
                "thumbnail": payload.get("thumbnail"),
                "source": row["source"],
                "batch_date": row["batch_date"],
                "dt": row["dt"],
            }
        )

    return TransformResult(rows=dwd_rows, invalid_count=invalid_count)


def _age_group(age: Any) -> str:
    if not isinstance(age, int):
        return "unknown"
    if age < 18:
        return "<18"
    if age <= 24:
        return "18-24"
    if age <= 34:
        return "25-34"
    if age <= 44:
        return "35-44"
    if age <= 54:
        return "45-54"
    return "55+"


def _full_name(payload: dict[str, Any]) -> str | None:
    parts = [payload.get("firstName"), payload.get("lastName")]
    name = " ".join(part for part in parts if part)
    return name or None


def transform_users(rows: Iterable[dict[str, Any]], *, batch_date: str) -> TransformResult:
    dwd_rows: list[dict[str, Any]] = []
    invalid_count = 0

    for row in rows:
        payload = _parse_payload(row, source="users", batch_date=batch_date)
        if payload is None:
            invalid_count += 1
            continue

        user_id = payload.get("id")
        username = payload.get("username")
        if not _is_positive_integer(user_id) or not _is_non_empty_string(username):
            invalid_count += 1
            continue

        address = payload.get("address") if isinstance(payload.get("address"), dict) else {}
        coordinates = address.get("coordinates") if isinstance(address.get("coordinates"), dict) else {}

        dwd_rows.append(
            {
                "user_id": user_id,
                "username": username,
                "full_name": _full_name(payload),
                "gender": payload.get("gender"),
                "age": payload.get("age"),
                "age_group": _age_group(payload.get("age")),
                "email": payload.get("email"),
                "phone": payload.get("phone"),
                "city": address.get("city"),
                "state": address.get("state"),
                "country": address.get("country"),
                "latitude": coordinates.get("lat"),
                "longitude": coordinates.get("lng"),
                "role": payload.get("role"),
                "source": row["source"],
                "batch_date": row["batch_date"],
                "dt": row["dt"],
            }
        )

    return TransformResult(rows=dwd_rows, invalid_count=invalid_count)


def _valid_cart_line(product: Any) -> bool:
    if not isinstance(product, dict):
        return False
    return (
        _is_positive_integer(product.get("id"))
        and _is_positive_integer(product.get("quantity"))
        and _is_non_negative_number(product.get("price"))
        and _is_optional_non_negative_number(product.get("total"))
        and _is_optional_non_negative_number(product.get("discountPercentage"))
        and _is_optional_non_negative_number(product.get("discountedTotal"))
    )


def _category_hint_from_thumbnail(thumbnail: Any) -> str | None:
    if not isinstance(thumbnail, str):
        return None
    match = re.search(r"/product-images/([^/]+)/", thumbnail)
    if match is None:
        return None
    category = match.group(1).strip()
    return category or None


def _is_optional_non_negative_number(value: Any) -> bool:
    return value is None or _is_non_negative_number(value)


def _valid_cart_amounts(payload: dict[str, Any]) -> bool:
    return (
        _is_optional_non_negative_number(payload.get("total"))
        and _is_optional_non_negative_number(payload.get("discountedTotal"))
        and _is_optional_non_negative_integer(payload.get("totalProducts"))
        and _is_optional_non_negative_integer(payload.get("totalQuantity"))
    )


def _is_optional_non_negative_integer(value: Any) -> bool:
    return value is None or _is_non_negative_integer(value)


def transform_carts(rows: Iterable[dict[str, Any]], *, batch_date: str) -> TransformResult:
    dwd_rows: list[dict[str, Any]] = []
    invalid_count = 0

    for row in rows:
        payload = _parse_payload(row, source="carts", batch_date=batch_date)
        if payload is None:
            invalid_count += 1
            continue

        cart_id = payload.get("id")
        user_id = payload.get("userId")
        products = payload.get("products")
        if (
            not _is_positive_integer(cart_id)
            or not _is_positive_integer(user_id)
            or not isinstance(products, list)
            or not _valid_cart_amounts(payload)
        ):
            invalid_count += 1
            continue
        if not products:
            invalid_count += 1
            continue

        valid_lines = []
        for product in products:
            if not _valid_cart_line(product):
                continue
            valid_lines.append(product)

        if len(valid_lines) != len(products):
            invalid_count += 1
            continue

        for product in valid_lines:
            dwd_rows.append(
                {
                    "cart_id": cart_id,
                    "user_id": user_id,
                    "product_id": product.get("id"),
                    "product_name": product.get("title"),
                    "unit_price": product.get("price"),
                    "quantity": product.get("quantity"),
                    "line_total": product.get("total"),
                    "discount_percentage": product.get("discountPercentage"),
                    "line_discounted_total": product.get("discountedTotal"),
                    "category_hint": _category_hint_from_thumbnail(product.get("thumbnail")),
                    "cart_total": payload.get("total"),
                    "cart_discounted_total": payload.get("discountedTotal"),
                    "total_products": payload.get("totalProducts"),
                    "total_quantity": payload.get("totalQuantity"),
                    "source": row["source"],
                    "batch_date": row["batch_date"],
                    "dt": row["dt"],
                }
            )

    return TransformResult(rows=dwd_rows, invalid_count=invalid_count)
