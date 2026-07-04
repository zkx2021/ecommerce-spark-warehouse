from decimal import Decimal

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
