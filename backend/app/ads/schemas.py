from decimal import Decimal

from pydantic import BaseModel, field_serializer


class KpiResponse(BaseModel):
    date_id: str
    total_sales_amount: Decimal
    total_order_count: int
    paid_user_count: int
    avg_order_amount: Decimal
    payment_conversion_rate: Decimal

    @field_serializer(
        "total_sales_amount",
        "avg_order_amount",
        "payment_conversion_rate",
        when_used="json",
    )
    def serialize_decimal(self, value: Decimal) -> float:
        return float(value)
