from decimal import Decimal

import pytest
from pydantic import ValidationError

from backend.app.ads import schemas
from backend.app.ads.schemas import KpiResponse
from backend.app.config import MySqlSettings


def test_mysql_settings_use_compose_defaults(monkeypatch):
    for key in (
        "ADS_MYSQL_HOST",
        "ADS_MYSQL_PORT",
        "ADS_MYSQL_DATABASE",
        "ADS_MYSQL_USER",
        "ADS_MYSQL_PASSWORD",
    ):
        monkeypatch.delenv(key, raising=False)

    settings = MySqlSettings.from_env()

    assert settings.host == "localhost"
    assert settings.port == 3306
    assert settings.database == "ecommerce_ads"
    assert settings.user == "ecommerce"
    assert settings.password == "ecommerce_password"


def test_mysql_settings_read_environment(monkeypatch):
    monkeypatch.setenv("ADS_MYSQL_HOST", "mysql")
    monkeypatch.setenv("ADS_MYSQL_PORT", "3307")
    monkeypatch.setenv("ADS_MYSQL_DATABASE", "ads_test")
    monkeypatch.setenv("ADS_MYSQL_USER", "api")
    monkeypatch.setenv("ADS_MYSQL_PASSWORD", "secret")

    settings = MySqlSettings.from_env()

    assert settings.host == "mysql"
    assert settings.port == 3307
    assert settings.database == "ads_test"
    assert settings.user == "api"
    assert settings.password == "secret"


def test_kpi_schema_serializes_decimal_as_json_number():
    payload = KpiResponse(
        date_id="2026-07-01",
        total_sales_amount=Decimal("123.45"),
        total_order_count=2,
        paid_user_count=1,
        avg_order_amount=Decimal("61.72"),
        payment_conversion_rate=Decimal("0.5000"),
    )

    assert payload.model_dump(mode="json") == {
        "date_id": "2026-07-01",
        "total_sales_amount": 123.45,
        "total_order_count": 2,
        "paid_user_count": 1,
        "avg_order_amount": 61.72,
        "payment_conversion_rate": 0.5,
    }


def test_ads_schema_module_exposes_required_models():
    expected_fields = {
        "AdsBaseModel": set(),
        "SalesTrendItem": {"sales_amount", "order_count", "paid_user_count"},
        "ProductRankItem": {
            "rank_no",
            "product_id",
            "product_name",
            "category",
            "sales_quantity",
            "sales_amount",
        },
        "CategoryShareItem": {
            "category",
            "sales_amount",
            "sales_quantity",
            "sales_share",
        },
        "UserProfileItem": {
            "dimension_type",
            "dimension_value",
            "user_count",
            "buyer_count",
            "sales_amount",
        },
        "FunnelItem": {
            "stage_name",
            "stage_order",
            "stage_count",
            "conversion_rate",
        },
        "ListResponse": {"date_id", "items"},
        "OverviewResponse": {
            "date_id",
            "kpi",
            "trend",
            "product_rank",
            "category_share",
            "user_profile",
            "funnel",
        },
    }

    for model_name, fields in expected_fields.items():
        model = getattr(schemas, model_name)
        assert set(model.model_fields) == fields


def test_overview_schema_serializes_nested_decimals_as_json_numbers():
    payload = schemas.OverviewResponse(
        date_id="2026-07-01",
        kpi=KpiResponse(
            date_id="2026-07-01",
            total_sales_amount=Decimal("123.45"),
            total_order_count=2,
            paid_user_count=1,
            avg_order_amount=Decimal("61.72"),
            payment_conversion_rate=Decimal("0.5000"),
        ),
        trend=[
            schemas.SalesTrendItem(
                sales_amount=Decimal("123.45"),
                order_count=2,
                paid_user_count=1,
            )
        ],
        product_rank=[
            schemas.ProductRankItem(
                rank_no=1,
                product_id=101,
                product_name="Demo Product",
                category=None,
                sales_quantity=5,
                sales_amount=Decimal("99.90"),
            )
        ],
        category_share=[
            schemas.CategoryShareItem(
                category="Demo Category",
                sales_amount=Decimal("99.90"),
                sales_quantity=5,
                sales_share=Decimal("0.2500"),
            )
        ],
        user_profile=[
            schemas.UserProfileItem(
                dimension_type="lifecycle",
                dimension_value="new",
                user_count=4,
                buyer_count=2,
                sales_amount=Decimal("88.80"),
            )
        ],
        funnel=[
            schemas.FunnelItem(
                stage_name="paid",
                stage_order=3,
                stage_count=2,
                conversion_rate=Decimal("0.5000"),
            )
        ],
    )

    assert payload.model_dump(mode="json") == {
        "date_id": "2026-07-01",
        "kpi": {
            "date_id": "2026-07-01",
            "total_sales_amount": 123.45,
            "total_order_count": 2,
            "paid_user_count": 1,
            "avg_order_amount": 61.72,
            "payment_conversion_rate": 0.5,
        },
        "trend": [
            {
                "sales_amount": 123.45,
                "order_count": 2,
                "paid_user_count": 1,
            }
        ],
        "product_rank": [
            {
                "rank_no": 1,
                "product_id": 101,
                "product_name": "Demo Product",
                "category": None,
                "sales_quantity": 5,
                "sales_amount": 99.9,
            }
        ],
        "category_share": [
            {
                "category": "Demo Category",
                "sales_amount": 99.9,
                "sales_quantity": 5,
                "sales_share": 0.25,
            }
        ],
        "user_profile": [
            {
                "dimension_type": "lifecycle",
                "dimension_value": "new",
                "user_count": 4,
                "buyer_count": 2,
                "sales_amount": 88.8,
            }
        ],
        "funnel": [
            {
                "stage_name": "paid",
                "stage_order": 3,
                "stage_count": 2,
                "conversion_rate": 0.5,
            }
        ],
    }


def test_product_rank_schema_preserves_numeric_product_id():
    payload = schemas.ProductRankItem(
        rank_no=1,
        product_id=101,
        product_name="Demo Product",
        category="Demo Category",
        sales_quantity=5,
        sales_amount=Decimal("99.90"),
    )

    assert payload.model_dump(mode="json") == {
        "rank_no": 1,
        "product_id": 101,
        "product_name": "Demo Product",
        "category": "Demo Category",
        "sales_quantity": 5,
        "sales_amount": 99.9,
    }


def test_list_response_uses_date_id_and_items():
    payload = schemas.ListResponse(
        date_id="2026-07-01",
        items=[{"metric": 1}],
    )

    assert payload.model_dump(mode="json") == {
        "date_id": "2026-07-01",
        "items": [{"metric": 1}],
    }

    with pytest.raises(ValidationError):
        schemas.ListResponse(date_id="2026-07-01", items=["bad"])
