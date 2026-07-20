import json

import pytest

from warehouse.spark.jobs.dwd_transforms import transform_carts, transform_products, transform_users


def _ods_row(source: str, batch_date: str, payload, dt: str | None = None):
    return {
        "entity": source[:-1] if source.endswith("s") else source,
        "source": source,
        "batch_date": batch_date,
        "dt": dt or batch_date,
        "data": json.dumps(payload, ensure_ascii=False),
    }


def test_transform_products_parses_valid_product_rows():
    result = transform_products(
        [
            _ods_row(
                "products",
                "2026-07-01",
                {
                    "id": 1,
                    "title": "Essence Mascara Lash Princess",
                    "category": "beauty",
                    "brand": "Essence",
                    "price": 9.99,
                    "discountPercentage": 7.17,
                    "rating": 4.94,
                    "stock": 5,
                    "availabilityStatus": "Low Stock",
                    "thumbnail": "https://example.test/product.png",
                },
            )
        ],
        batch_date="2026-07-01",
    )

    assert result.invalid_count == 0
    assert result.rows == [
        {
            "product_id": 1,
            "product_name": "Essence Mascara Lash Princess",
            "category": "beauty",
            "brand": "Essence",
            "price": 9.99,
            "discount_percentage": 7.17,
            "rating": 4.94,
            "stock": 5,
            "availability_status": "Low Stock",
            "thumbnail": "https://example.test/product.png",
            "source": "products",
            "batch_date": "2026-07-01",
            "dt": "2026-07-01",
        }
    ]


def test_transform_products_rejects_invalid_contract_rows():
    rows = [
        _ods_row("users", "2026-07-01", {"id": 1, "title": "Wrong source", "price": 1}),
        _ods_row("products", "2026-07-02", {"id": 2, "title": "Wrong date", "price": 1}),
        _ods_row("products", "2026-07-01", {"id": -1, "title": "Bad id", "price": 1}),
        _ods_row("products", "2026-07-01", {"id": 1.5, "title": "Fractional id", "price": 1}),
        _ods_row("products", "2026-07-01", {"id": True, "title": "Boolean id", "price": 1}),
        _ods_row("products", "2026-07-01", {"id": 4, "title": 123, "price": 1}),
        _ods_row("products", "2026-07-01", {"id": 5, "title": "Bad stock", "price": 1, "stock": 3.7}),
        _ods_row("products", "2026-07-01", {"id": 3, "title": "Missing price"}),
        {"source": "products", "batch_date": "2026-07-01", "dt": "2026-07-01", "data": {"id": 1}},
    ]

    result = transform_products(rows, batch_date="2026-07-01")

    assert result.rows == []
    assert result.invalid_count == 9


def test_transform_users_parses_valid_user_rows_and_derives_fields():
    result = transform_users(
        [
            _ods_row(
                "users",
                "2026-07-01",
                {
                    "id": 42,
                    "username": "emilys",
                    "firstName": "Emily",
                    "lastName": "Johnson",
                    "gender": "female",
                    "age": 28,
                    "email": "emily@example.test",
                    "phone": "+1 555 1111",
                    "role": "user",
                    "address": {
                        "city": "Phoenix",
                        "state": "Arizona",
                        "country": "United States",
                        "coordinates": {"lat": 33.44, "lng": -112.07},
                    },
                },
            )
        ],
        batch_date="2026-07-01",
    )

    assert result.invalid_count == 0
    assert result.rows == [
        {
            "user_id": 42,
            "username": "emilys",
            "full_name": "Emily Johnson",
            "gender": "female",
            "age": 28,
            "age_group": "25-34",
            "email": "emily@example.test",
            "phone": "+1 555 1111",
            "city": "Phoenix",
            "state": "Arizona",
            "country": "United States",
            "latitude": 33.44,
            "longitude": -112.07,
            "role": "user",
            "source": "users",
            "batch_date": "2026-07-01",
            "dt": "2026-07-01",
        }
    ]


@pytest.mark.parametrize(
    ("age", "expected"),
    [
        (None, "unknown"),
        (17, "<18"),
        (18, "18-24"),
        (25, "25-34"),
        (35, "35-44"),
        (45, "45-54"),
        (55, "55+"),
    ],
)
def test_transform_users_derives_age_groups(age, expected):
    payload = {"id": 1, "username": "agecase", "age": age}

    result = transform_users([_ods_row("users", "2026-07-01", payload)], batch_date="2026-07-01")

    assert result.invalid_count == 0
    assert result.rows[0]["age_group"] == expected


def test_transform_users_rejects_invalid_contract_rows():
    rows = [
        _ods_row("products", "2026-07-01", {"id": 1, "username": "wrongsource"}),
        _ods_row("users", "2026-07-02", {"id": 2, "username": "wrongdate"}),
        _ods_row("users", "2026-07-01", {"id": 0, "username": "badid"}),
        _ods_row("users", "2026-07-01", {"id": 1.5, "username": "fractional"}),
        _ods_row("users", "2026-07-01", {"id": True, "username": "boolean"}),
        _ods_row("users", "2026-07-01", {"id": 4, "username": 123}),
        _ods_row("users", "2026-07-01", {"id": 3}),
        {"source": "users", "batch_date": "2026-07-01", "dt": "2026-07-01", "data": "{bad json"},
    ]

    result = transform_users(rows, batch_date="2026-07-01")

    assert result.rows == []
    assert result.invalid_count == 8


def test_transform_carts_explodes_product_lines():
    result = transform_carts(
        [
            _ods_row(
                "carts",
                "2026-07-01",
                {
                    "id": 100,
                    "userId": 7,
                    "total": 250.5,
                    "discountedTotal": 225.4,
                    "totalProducts": 2,
                    "totalQuantity": 5,
                    "products": [
                        {
                            "id": 1,
                            "title": "Phone Case",
                            "price": 20.0,
                            "quantity": 2,
                            "total": 40.0,
                            "discountPercentage": 5.0,
                            "discountedTotal": 38.0,
                            "thumbnail": "https://cdn.dummyjson.com/product-images/mobile-accessories/phone-case/thumbnail.webp",
                        },
                        {
                            "id": 2,
                            "title": "USB Cable",
                            "price": 10.0,
                            "quantity": 3,
                            "total": 30.0,
                            "discountPercentage": 10.0,
                            "discountedTotal": 27.0,
                        },
                    ],
                },
            )
        ],
        batch_date="2026-07-01",
    )

    assert result.invalid_count == 0
    assert result.rows == [
        {
            "cart_id": 100,
            "user_id": 7,
            "product_id": 1,
            "product_name": "Phone Case",
            "unit_price": 20.0,
            "quantity": 2,
            "line_total": 40.0,
            "discount_percentage": 5.0,
            "line_discounted_total": 38.0,
            "category_hint": "mobile-accessories",
            "cart_total": 250.5,
            "cart_discounted_total": 225.4,
            "total_products": 2,
            "total_quantity": 5,
            "source": "carts",
            "batch_date": "2026-07-01",
            "dt": "2026-07-01",
        },
        {
            "cart_id": 100,
            "user_id": 7,
            "product_id": 2,
            "product_name": "USB Cable",
            "unit_price": 10.0,
            "quantity": 3,
            "line_total": 30.0,
            "discount_percentage": 10.0,
            "line_discounted_total": 27.0,
            "category_hint": None,
            "cart_total": 250.5,
            "cart_discounted_total": 225.4,
            "total_products": 2,
            "total_quantity": 5,
            "source": "carts",
            "batch_date": "2026-07-01",
            "dt": "2026-07-01",
        },
    ]


@pytest.mark.parametrize(
    ("thumbnail", "expected"),
    [
        ("https://cdn.dummyjson.com/product-images/smartphones/iphone-13-pro/thumbnail.webp", "smartphones"),
        ("https://cdn.dummyjson.com/product-images/mens-watches/rolex-datejust/thumbnail.webp", "mens-watches"),
        ("https://example.test/no-category.png", None),
        (None, None),
    ],
)
def test_transform_carts_derives_category_hint_from_dummyjson_thumbnail(thumbnail, expected):
    product = {
        "id": 9,
        "title": "Catalog item",
        "price": 10.0,
        "quantity": 1,
        "total": 10.0,
        "discountedTotal": 9.0,
    }
    if thumbnail is not None:
        product["thumbnail"] = thumbnail

    result = transform_carts(
        [
            _ods_row(
                "carts",
                "2026-07-01",
                {
                    "id": 101,
                    "userId": 7,
                    "products": [product],
                },
            )
        ],
        batch_date="2026-07-01",
    )

    assert result.invalid_count == 0
    assert result.rows[0]["category_hint"] == expected


def test_transform_carts_rejects_invalid_contract_and_line_rows():
    rows = [
        _ods_row("users", "2026-07-01", {"id": 1, "userId": 7, "products": []}),
        _ods_row("carts", "2026-07-02", {"id": 2, "userId": 7, "products": []}),
        _ods_row("carts", "2026-07-01", {"id": 0, "userId": 7, "products": []}),
        _ods_row("carts", "2026-07-01", {"id": 3, "userId": 0, "products": []}),
        _ods_row("carts", "2026-07-01", {"id": 1.5, "userId": 7, "products": []}),
        _ods_row("carts", "2026-07-01", {"id": True, "userId": 7, "products": []}),
        _ods_row("carts", "2026-07-01", {"id": 9, "userId": 7.5, "products": []}),
        _ods_row("carts", "2026-07-01", {"id": 4, "userId": 7, "products": "bad"}),
        _ods_row("carts", "2026-07-01", {"id": 5, "userId": 7, "products": [{"id": 9, "quantity": 0}]}),
        _ods_row("carts", "2026-07-01", {"id": 10, "userId": 7, "products": [{"id": 9.5, "price": 1, "quantity": 1}]}),
        _ods_row("carts", "2026-07-01", {"id": 11, "userId": 7, "products": [{"id": 9, "price": 1, "quantity": 1.5}]}),
        _ods_row("carts", "2026-07-01", {"id": 12, "userId": 7, "totalProducts": 1.5, "products": [{"id": 9, "price": 1, "quantity": 1}]}),
        _ods_row(
            "carts",
            "2026-07-01",
            {"id": 6, "userId": 7, "products": [{"id": 9, "price": -1, "quantity": 1}]},
        ),
        _ods_row(
            "carts",
            "2026-07-01",
            {"id": 7, "userId": 7, "total": -1, "products": [{"id": 9, "price": 1, "quantity": 1}]},
        ),
        _ods_row(
            "carts",
            "2026-07-01",
            {"id": 8, "userId": 7, "products": [{"id": 9, "price": 1, "quantity": 1, "total": -1}]},
        ),
        {"source": "carts", "batch_date": "2026-07-01", "dt": "2026-07-01", "data": "{bad json"},
    ]

    result = transform_carts(rows, batch_date="2026-07-01")

    assert result.rows == []
    assert result.invalid_count == 16
