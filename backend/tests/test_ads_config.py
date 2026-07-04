from decimal import Decimal

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
    for model_name in (
        "AdsBaseModel",
        "SalesTrendItem",
        "ProductRankItem",
        "CategoryShareItem",
        "UserProfileItem",
        "FunnelItem",
        "ListResponse",
        "OverviewResponse",
    ):
        assert hasattr(schemas, model_name)


def test_overview_schema_serializes_nested_decimals_as_json_numbers():
    payload = schemas.OverviewResponse(
        kpi=KpiResponse(
            date_id="2026-07-01",
            total_sales_amount=Decimal("123.45"),
            total_order_count=2,
            paid_user_count=1,
            avg_order_amount=Decimal("61.72"),
            payment_conversion_rate=Decimal("0.5000"),
        ),
        sales_trend=[
            schemas.SalesTrendItem(
                date_id="2026-07-01",
                total_sales_amount=Decimal("123.45"),
                total_order_count=2,
            )
        ],
        product_rank=[
            schemas.ProductRankItem(
                product_id="sku-1",
                product_name="Demo Product",
                total_sales_amount=Decimal("99.90"),
                total_order_count=3,
            )
        ],
        category_share=[
            schemas.CategoryShareItem(
                category_name="Demo Category",
                total_sales_amount=Decimal("99.90"),
                sales_share=Decimal("0.2500"),
            )
        ],
        user_profile=[
            schemas.UserProfileItem(
                user_type="new",
                user_count=4,
                total_sales_amount=Decimal("88.80"),
            )
        ],
        funnel=[
            schemas.FunnelItem(
                step_name="paid",
                user_count=2,
                conversion_rate=Decimal("0.5000"),
            )
        ],
    )

    assert payload.model_dump(mode="json") == {
        "kpi": {
            "date_id": "2026-07-01",
            "total_sales_amount": 123.45,
            "total_order_count": 2,
            "paid_user_count": 1,
            "avg_order_amount": 61.72,
            "payment_conversion_rate": 0.5,
        },
        "sales_trend": [
            {
                "date_id": "2026-07-01",
                "total_sales_amount": 123.45,
                "total_order_count": 2,
            }
        ],
        "product_rank": [
            {
                "product_id": "sku-1",
                "product_name": "Demo Product",
                "total_sales_amount": 99.9,
                "total_order_count": 3,
            }
        ],
        "category_share": [
            {
                "category_name": "Demo Category",
                "total_sales_amount": 99.9,
                "sales_share": 0.25,
            }
        ],
        "user_profile": [
            {
                "user_type": "new",
                "user_count": 4,
                "total_sales_amount": 88.8,
            }
        ],
        "funnel": [
            {
                "step_name": "paid",
                "user_count": 2,
                "conversion_rate": 0.5,
            }
        ],
    }
