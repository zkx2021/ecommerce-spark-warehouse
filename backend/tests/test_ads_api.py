from decimal import Decimal

import pytest
from fastapi.testclient import TestClient

from backend.app.ads.errors import AdsDataNotFound, AdsDatabaseUnavailable
from backend.app.ads.router import get_ads_service
from backend.app.ads.schemas import (
    CategoryShareItem,
    FunnelItem,
    KpiResponse,
    OverviewResponse,
    ProductRankItem,
    SalesTrendItem,
    UserProfileItem,
)
from backend.app.main import app


class FakeAdsService:
    def __init__(self):
        self.calls = []
        self.kpi = KpiResponse(
            date_id="2026-07-01",
            total_sales_amount=Decimal("123.45"),
            total_order_count=3,
            paid_user_count=2,
            avg_order_amount=Decimal("41.15"),
            payment_conversion_rate=Decimal("0.6667"),
        )
        self.trend = [
            SalesTrendItem(
                sales_amount=Decimal("123.45"),
                order_count=3,
                paid_user_count=2,
            )
        ]
        self.product_rank = [
            ProductRankItem(
                rank_no=1,
                product_id=101,
                product_name="Demo Product",
                category="Demo Category",
                sales_quantity=4,
                sales_amount=Decimal("98.76"),
            )
        ]
        self.category_share = [
            CategoryShareItem(
                category="Demo Category",
                sales_amount=Decimal("98.76"),
                sales_quantity=4,
                sales_share=Decimal("0.8000"),
            )
        ]
        self.user_profile = [
            UserProfileItem(
                dimension_type="lifecycle",
                dimension_value="new",
                user_count=7,
                buyer_count=2,
                sales_amount=Decimal("88.80"),
            )
        ]
        self.funnel = [
            FunnelItem(
                stage_name="paid",
                stage_order=3,
                stage_count=2,
                conversion_rate=Decimal("0.5000"),
            )
        ]

    def get_kpi(self, date_id=None):
        self.calls.append(("get_kpi", date_id))
        return self.kpi

    def get_trend(self, date_id=None):
        self.calls.append(("get_trend", date_id))
        return "2026-07-01", self.trend

    def get_product_rank(self, date_id=None):
        self.calls.append(("get_product_rank", date_id))
        return "2026-07-01", self.product_rank

    def get_category_share(self, date_id=None):
        self.calls.append(("get_category_share", date_id))
        return "2026-07-01", self.category_share

    def get_user_profile(self, date_id=None):
        self.calls.append(("get_user_profile", date_id))
        return "2026-07-01", self.user_profile

    def get_funnel(self, date_id=None):
        self.calls.append(("get_funnel", date_id))
        return "2026-07-01", self.funnel

    def get_overview(self, date_id=None):
        self.calls.append(("get_overview", date_id))
        return OverviewResponse(
            date_id="2026-07-01",
            kpi=self.kpi,
            trend=self.trend,
            product_rank=self.product_rank,
            category_share=self.category_share,
            user_profile=self.user_profile,
            funnel=self.funnel,
        )


@pytest.fixture
def fake_service():
    service = FakeAdsService()
    app.dependency_overrides[get_ads_service] = lambda: service
    try:
        yield service
    finally:
        app.dependency_overrides.pop(get_ads_service, None)


@pytest.fixture
def client(fake_service):
    return TestClient(app)


def test_kpi_endpoint_returns_explicit_date_and_json_numbers(client, fake_service):
    response = client.get("/api/ads/kpi?date=2026-07-01")

    assert response.status_code == 200
    assert response.json() == {
        "date_id": "2026-07-01",
        "total_sales_amount": 123.45,
        "total_order_count": 3,
        "paid_user_count": 2,
        "avg_order_amount": 41.15,
        "payment_conversion_rate": 0.6667,
    }
    assert fake_service.calls == [("get_kpi", "2026-07-01")]


def test_kpi_endpoint_accepts_omitted_date(client, fake_service):
    response = client.get("/api/ads/kpi")

    assert response.status_code == 200
    assert fake_service.calls == [("get_kpi", None)]


def test_trend_endpoint_returns_date_items_wrapper(client, fake_service):
    response = client.get("/api/ads/trend?date=2026-07-01")

    assert response.status_code == 200
    assert response.json() == {
        "date_id": "2026-07-01",
        "items": [
            {
                "sales_amount": 123.45,
                "order_count": 3,
                "paid_user_count": 2,
            }
        ],
    }
    assert fake_service.calls == [("get_trend", "2026-07-01")]


@pytest.mark.parametrize(
    "path,method_name,expected_item",
    [
        (
            "/api/ads/products/rank",
            "get_product_rank",
            {
                "rank_no": 1,
                "product_id": 101,
                "product_name": "Demo Product",
                "category": "Demo Category",
                "sales_quantity": 4,
                "sales_amount": 98.76,
            },
        ),
        (
            "/api/ads/categories/share",
            "get_category_share",
            {
                "category": "Demo Category",
                "sales_amount": 98.76,
                "sales_quantity": 4,
                "sales_share": 0.8,
            },
        ),
        (
            "/api/ads/users/profile",
            "get_user_profile",
            {
                "dimension_type": "lifecycle",
                "dimension_value": "new",
                "user_count": 7,
                "buyer_count": 2,
                "sales_amount": 88.8,
            },
        ),
        (
            "/api/ads/funnel",
            "get_funnel",
            {
                "stage_name": "paid",
                "stage_order": 3,
                "stage_count": 2,
                "conversion_rate": 0.5,
            },
        ),
    ],
)
def test_remaining_list_endpoints_return_wrappers(client, fake_service, path, method_name, expected_item):
    response = client.get(f"{path}?date=2026-07-01")

    assert response.status_code == 200
    assert response.json() == {"date_id": "2026-07-01", "items": [expected_item]}
    assert fake_service.calls == [(method_name, "2026-07-01")]


def test_overview_endpoint_returns_composed_payload(client, fake_service):
    response = client.get("/api/ads/overview?date=2026-07-01")

    assert response.status_code == 200
    payload = response.json()
    assert payload["date_id"] == "2026-07-01"
    assert payload["kpi"]["total_sales_amount"] == 123.45
    assert payload["trend"] == [
        {
            "sales_amount": 123.45,
            "order_count": 3,
            "paid_user_count": 2,
        }
    ]
    assert payload["product_rank"][0]["product_id"] == 101
    assert payload["category_share"][0]["sales_share"] == 0.8
    assert payload["user_profile"][0]["dimension_value"] == "new"
    assert payload["funnel"][0]["conversion_rate"] == 0.5
    assert fake_service.calls == [("get_overview", "2026-07-01")]


def test_invalid_date_returns_validation_error(client):
    response = client.get("/api/ads/kpi?date=2026-7-1")

    assert response.status_code == 422


def test_data_not_found_maps_to_404(fake_service):
    fake_service.get_kpi = lambda date_id=None: (_ for _ in ()).throw(
        AdsDataNotFound("No ADS KPI data found")
    )
    client = TestClient(app)

    response = client.get("/api/ads/kpi?date=2026-07-01")

    assert response.status_code == 404
    assert response.json() == {"detail": "No ADS KPI data found"}


def test_database_unavailable_maps_to_503(fake_service):
    fake_service.get_kpi = lambda date_id=None: (_ for _ in ()).throw(
        AdsDatabaseUnavailable("ADS database query failed")
    )
    client = TestClient(app)

    response = client.get("/api/ads/kpi?date=2026-07-01")

    assert response.status_code == 503
    assert response.json() == {"detail": "ADS database query failed"}
