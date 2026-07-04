from decimal import Decimal

import pytest

from backend.app.ads.errors import AdsDataNotFound
from backend.app.ads.schemas import (
    CategoryShareItem,
    FunnelItem,
    KpiResponse,
    OverviewResponse,
    ProductRankItem,
    SalesTrendItem,
    UserProfileItem,
)
from backend.app.ads.service import AdsService


class FakeAdsRepository:
    def __init__(self, latest_date="2026-07-03", overrides=None):
        self.latest_date = latest_date
        self.calls = []
        self.rows = {
            "kpi": {
                "date_id": "2026-07-03",
                "total_sales_amount": Decimal("123.45"),
                "total_order_count": 3,
                "paid_user_count": 2,
                "avg_order_amount": Decimal("41.15"),
                "payment_conversion_rate": Decimal("0.6667"),
            },
            "trend": [
                {
                    "date_id": "2026-07-03",
                    "sales_amount": Decimal("123.45"),
                    "order_count": 3,
                    "paid_user_count": 2,
                }
            ],
            "product_rank": [
                {
                    "date_id": "2026-07-03",
                    "rank_no": 1,
                    "product_id": 101,
                    "product_name": "Demo Product",
                    "category": "Demo Category",
                    "sales_quantity": 4,
                    "sales_amount": Decimal("98.76"),
                }
            ],
            "category_share": [
                {
                    "date_id": "2026-07-03",
                    "category": "Demo Category",
                    "sales_amount": Decimal("98.76"),
                    "sales_quantity": 4,
                    "sales_share": Decimal("0.8000"),
                }
            ],
            "user_profile": [
                {
                    "date_id": "2026-07-03",
                    "dimension_type": "lifecycle",
                    "dimension_value": "new",
                    "user_count": 7,
                    "buyer_count": 2,
                    "sales_amount": Decimal("88.80"),
                }
            ],
            "funnel": [
                {
                    "date_id": "2026-07-03",
                    "stage_name": "paid",
                    "stage_order": 3,
                    "stage_count": 2,
                    "conversion_rate": Decimal("0.5000"),
                }
            ],
        }
        if overrides:
            self.rows.update(overrides)

    def get_latest_date(self):
        self.calls.append(("get_latest_date",))
        return self.latest_date

    def get_kpi(self, date_id):
        self.calls.append(("get_kpi", date_id))
        return self.rows["kpi"]

    def get_trend(self, date_id):
        self.calls.append(("get_trend", date_id))
        return self.rows["trend"]

    def get_product_rank(self, date_id):
        self.calls.append(("get_product_rank", date_id))
        return self.rows["product_rank"]

    def get_category_share(self, date_id):
        self.calls.append(("get_category_share", date_id))
        return self.rows["category_share"]

    def get_user_profile(self, date_id):
        self.calls.append(("get_user_profile", date_id))
        return self.rows["user_profile"]

    def get_funnel(self, date_id):
        self.calls.append(("get_funnel", date_id))
        return self.rows["funnel"]


def test_get_kpi_uses_explicit_date_without_latest_lookup():
    repository = FakeAdsRepository()
    repository.rows["kpi"] = {**repository.rows["kpi"], "date_id": "2026-07-01"}
    service = AdsService(repository)

    payload = service.get_kpi("2026-07-01")

    assert isinstance(payload, KpiResponse)
    assert payload.date_id == "2026-07-01"
    assert payload.total_sales_amount == Decimal("123.45")
    assert repository.calls == [("get_kpi", "2026-07-01")]


def test_get_kpi_resolves_latest_date_when_date_is_omitted():
    repository = FakeAdsRepository(latest_date="2026-07-03")
    service = AdsService(repository)

    payload = service.get_kpi()

    assert payload.date_id == "2026-07-03"
    assert repository.calls == [
        ("get_latest_date",),
        ("get_kpi", "2026-07-03"),
    ]


def test_missing_latest_date_raises_data_not_found():
    service = AdsService(FakeAdsRepository(latest_date=None))

    with pytest.raises(AdsDataNotFound, match="No ADS data is available"):
        service.get_kpi(None)


def test_missing_kpi_row_raises_message_with_resolved_date():
    service = AdsService(FakeAdsRepository(overrides={"kpi": None}))

    with pytest.raises(AdsDataNotFound, match="No ADS KPI data.*2026-07-03"):
        service.get_kpi(None)


@pytest.mark.parametrize(
    "method_name,row_key,item_type,message",
    [
        ("get_trend", "trend", SalesTrendItem, "No ADS trend data"),
        ("get_product_rank", "product_rank", ProductRankItem, "No ADS product rank data"),
        ("get_category_share", "category_share", CategoryShareItem, "No ADS category share data"),
        ("get_user_profile", "user_profile", UserProfileItem, "No ADS user profile data"),
        ("get_funnel", "funnel", FunnelItem, "No ADS funnel data"),
    ],
)
def test_list_methods_return_resolved_date_and_schema_items(method_name, row_key, item_type, message):
    repository = FakeAdsRepository()
    service = AdsService(repository)

    resolved_date, items = getattr(service, method_name)(None)

    assert resolved_date == "2026-07-03"
    assert len(items) == 1
    assert isinstance(items[0], item_type)
    assert "date_id" not in items[0].model_dump()
    assert repository.calls == [
        ("get_latest_date",),
        (method_name, "2026-07-03"),
    ]

    empty_service = AdsService(FakeAdsRepository(overrides={row_key: []}))
    with pytest.raises(AdsDataNotFound, match=message):
        getattr(empty_service, method_name)("2026-07-03")


def test_overview_composes_all_sections_and_resolves_latest_date_once():
    repository = FakeAdsRepository(latest_date="2026-07-03")
    service = AdsService(repository)

    payload = service.get_overview(None)

    assert isinstance(payload, OverviewResponse)
    assert payload.date_id == "2026-07-03"
    assert isinstance(payload.kpi, KpiResponse)
    assert isinstance(payload.trend[0], SalesTrendItem)
    assert isinstance(payload.product_rank[0], ProductRankItem)
    assert isinstance(payload.category_share[0], CategoryShareItem)
    assert isinstance(payload.user_profile[0], UserProfileItem)
    assert isinstance(payload.funnel[0], FunnelItem)
    assert payload.model_dump()["kpi"]["total_sales_amount"] == Decimal("123.45")
    assert repository.calls == [
        ("get_latest_date",),
        ("get_kpi", "2026-07-03"),
        ("get_trend", "2026-07-03"),
        ("get_product_rank", "2026-07-03"),
        ("get_category_share", "2026-07-03"),
        ("get_user_profile", "2026-07-03"),
        ("get_funnel", "2026-07-03"),
    ]
