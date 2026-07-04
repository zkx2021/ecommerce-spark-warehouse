from decimal import Decimal
from typing import Any

from pydantic import BaseModel, model_serializer


def _json_safe(value: Any) -> Any:
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, BaseModel):
        return value.model_dump(mode="json")
    if isinstance(value, list):
        return [_json_safe(item) for item in value]
    if isinstance(value, tuple):
        return tuple(_json_safe(item) for item in value)
    if isinstance(value, dict):
        return {key: _json_safe(item) for key, item in value.items()}
    return value


class AdsBaseModel(BaseModel):
    @model_serializer(mode="plain", when_used="json")
    def serialize_json(self) -> dict[str, Any]:
        return {
            field_name: _json_safe(getattr(self, field_name))
            for field_name in type(self).model_fields
        }


class KpiResponse(AdsBaseModel):
    date_id: str
    total_sales_amount: Decimal
    total_order_count: int
    paid_user_count: int
    avg_order_amount: Decimal
    payment_conversion_rate: Decimal


class SalesTrendItem(AdsBaseModel):
    date_id: str
    total_sales_amount: Decimal
    total_order_count: int


class ProductRankItem(AdsBaseModel):
    product_id: str
    product_name: str
    total_sales_amount: Decimal
    total_order_count: int


class CategoryShareItem(AdsBaseModel):
    category_name: str
    total_sales_amount: Decimal
    sales_share: Decimal


class UserProfileItem(AdsBaseModel):
    user_type: str
    user_count: int
    total_sales_amount: Decimal


class FunnelItem(AdsBaseModel):
    step_name: str
    user_count: int
    conversion_rate: Decimal


class ListResponse(AdsBaseModel):
    total: int
    items: list[Any]


class OverviewResponse(AdsBaseModel):
    kpi: KpiResponse
    sales_trend: list[SalesTrendItem]
    product_rank: list[ProductRankItem]
    category_share: list[CategoryShareItem]
    user_profile: list[UserProfileItem]
    funnel: list[FunnelItem]
