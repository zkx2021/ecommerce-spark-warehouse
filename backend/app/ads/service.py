from collections.abc import Callable
from typing import Any, TypeVar

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

SchemaItem = TypeVar(
    "SchemaItem",
    SalesTrendItem,
    ProductRankItem,
    CategoryShareItem,
    UserProfileItem,
    FunnelItem,
)


class AdsService:
    def __init__(self, repository: Any):
        self.repository = repository

    def get_kpi(self, date_id: str | None = None) -> KpiResponse:
        resolved_date = self._resolve_date(date_id)
        return self._get_kpi_for_date(resolved_date)

    def get_trend(self, date_id: str | None = None) -> tuple[str, list[SalesTrendItem]]:
        resolved_date = self._resolve_date(date_id)
        return resolved_date, self._get_items_for_date(
            resolved_date,
            self.repository.get_trend,
            SalesTrendItem,
            "No ADS trend data",
        )

    def get_product_rank(self, date_id: str | None = None) -> tuple[str, list[ProductRankItem]]:
        resolved_date = self._resolve_date(date_id)
        return resolved_date, self._get_items_for_date(
            resolved_date,
            self.repository.get_product_rank,
            ProductRankItem,
            "No ADS product rank data",
        )

    def get_category_share(self, date_id: str | None = None) -> tuple[str, list[CategoryShareItem]]:
        resolved_date = self._resolve_date(date_id)
        return resolved_date, self._get_items_for_date(
            resolved_date,
            self.repository.get_category_share,
            CategoryShareItem,
            "No ADS category share data",
        )

    def get_user_profile(self, date_id: str | None = None) -> tuple[str, list[UserProfileItem]]:
        resolved_date = self._resolve_date(date_id)
        return resolved_date, self._get_items_for_date(
            resolved_date,
            self.repository.get_user_profile,
            UserProfileItem,
            "No ADS user profile data",
        )

    def get_funnel(self, date_id: str | None = None) -> tuple[str, list[FunnelItem]]:
        resolved_date = self._resolve_date(date_id)
        return resolved_date, self._get_items_for_date(
            resolved_date,
            self.repository.get_funnel,
            FunnelItem,
            "No ADS funnel data",
        )

    def get_overview(self, date_id: str | None = None) -> OverviewResponse:
        resolved_date = self._resolve_date(date_id)
        return OverviewResponse(
            date_id=resolved_date,
            kpi=self._get_kpi_for_date(resolved_date),
            trend=self._get_items_for_date(
                resolved_date,
                self.repository.get_trend,
                SalesTrendItem,
                "No ADS trend data",
            ),
            product_rank=self._get_items_for_date(
                resolved_date,
                self.repository.get_product_rank,
                ProductRankItem,
                "No ADS product rank data",
            ),
            category_share=self._get_items_for_date(
                resolved_date,
                self.repository.get_category_share,
                CategoryShareItem,
                "No ADS category share data",
            ),
            user_profile=self._get_items_for_date(
                resolved_date,
                self.repository.get_user_profile,
                UserProfileItem,
                "No ADS user profile data",
            ),
            funnel=self._get_items_for_date(
                resolved_date,
                self.repository.get_funnel,
                FunnelItem,
                "No ADS funnel data",
            ),
        )

    def _resolve_date(self, date_id: str | None) -> str:
        if isinstance(date_id, str) and date_id:
            return date_id

        latest_date = self.repository.get_latest_date()
        if not latest_date:
            raise AdsDataNotFound("No ADS data is available")
        return latest_date

    def _get_kpi_for_date(self, date_id: str) -> KpiResponse:
        row = self.repository.get_kpi(date_id)
        if not row:
            raise AdsDataNotFound(f"No ADS KPI data found for date {date_id}")
        return self._build_model(KpiResponse, row)

    def _get_items_for_date(
        self,
        date_id: str,
        fetch_rows: Callable[[str], list[dict[str, Any]]],
        schema_class: type[SchemaItem],
        not_found_message: str,
    ) -> list[SchemaItem]:
        rows = fetch_rows(date_id)
        if not rows:
            raise AdsDataNotFound(f"{not_found_message} found for date {date_id}")
        return [self._build_model(schema_class, row) for row in rows]

    def _build_model(self, schema_class: type[SchemaItem], row: dict[str, Any]) -> SchemaItem:
        fields = schema_class.model_fields
        return schema_class(**{key: value for key, value in row.items() if key in fields})
