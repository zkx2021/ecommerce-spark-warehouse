from typing import Any

from backend.app.ads.errors import AdsDatabaseUnavailable


class AdsRepository:
    def __init__(self, connection: Any):
        self.connection = connection

    def _fetch_one(self, sql: str, params: tuple[Any, ...] | None = None) -> dict[str, Any] | None:
        cursor = None
        try:
            cursor = self.connection.cursor(dictionary=True)
            cursor.execute(sql, params)
            return cursor.fetchone()
        except Exception as exc:
            raise AdsDatabaseUnavailable("ADS database query failed") from exc
        finally:
            if cursor is not None:
                cursor.close()

    def _fetch_all(self, sql: str, params: tuple[Any, ...] | None = None) -> list[dict[str, Any]]:
        cursor = None
        try:
            cursor = self.connection.cursor(dictionary=True)
            cursor.execute(sql, params)
            return cursor.fetchall()
        except Exception as exc:
            raise AdsDatabaseUnavailable("ADS database query failed") from exc
        finally:
            if cursor is not None:
                cursor.close()

    def get_latest_date(self) -> str | None:
        row = self._fetch_one(
            """
            SELECT MAX(date_id) AS date_id
            FROM (
                SELECT MAX(date_id) AS date_id FROM ads_kpi_daily
                UNION ALL
                SELECT MAX(date_id) AS date_id FROM ads_sales_trend_daily
                UNION ALL
                SELECT MAX(date_id) AS date_id FROM ads_product_rank_daily
                UNION ALL
                SELECT MAX(date_id) AS date_id FROM ads_category_share_daily
                UNION ALL
                SELECT MAX(date_id) AS date_id FROM ads_user_profile_daily
                UNION ALL
                SELECT MAX(date_id) AS date_id FROM ads_funnel_daily
            ) AS latest_dates
            """
        )
        if row is None:
            return None
        return row["date_id"]

    def get_kpi(self, date_id: str) -> dict[str, Any] | None:
        return self._fetch_one(
            """
            SELECT
                date_id,
                total_sales_amount,
                total_order_count,
                paid_user_count,
                avg_order_amount,
                payment_conversion_rate
            FROM ads_kpi_daily
            WHERE date_id = %s
            """,
            (date_id,),
        )

    def get_trend(self, date_id: str) -> list[dict[str, Any]]:
        return self._fetch_all(
            """
            SELECT
                date_id,
                sales_amount,
                order_count,
                paid_user_count
            FROM ads_sales_trend_daily
            WHERE date_id = %s
            ORDER BY date_id
            """,
            (date_id,),
        )

    def get_product_rank(self, date_id: str) -> list[dict[str, Any]]:
        return self._fetch_all(
            """
            SELECT
                date_id,
                rank_no,
                product_id,
                product_name,
                category,
                sales_quantity,
                sales_amount
            FROM ads_product_rank_daily
            WHERE date_id = %s
            ORDER BY rank_no
            """,
            (date_id,),
        )

    def get_category_share(self, date_id: str) -> list[dict[str, Any]]:
        return self._fetch_all(
            """
            SELECT
                date_id,
                category,
                sales_amount,
                sales_quantity,
                sales_share
            FROM ads_category_share_daily
            WHERE date_id = %s
            ORDER BY sales_share DESC, sales_amount DESC, category
            """,
            (date_id,),
        )

    def get_user_profile(self, date_id: str) -> list[dict[str, Any]]:
        return self._fetch_all(
            """
            SELECT
                date_id,
                dimension_type,
                dimension_value,
                user_count,
                buyer_count,
                sales_amount
            FROM ads_user_profile_daily
            WHERE date_id = %s
            ORDER BY dimension_type, user_count DESC, dimension_value
            """,
            (date_id,),
        )

    def get_funnel(self, date_id: str) -> list[dict[str, Any]]:
        return self._fetch_all(
            """
            SELECT
                date_id,
                stage_name,
                stage_order,
                stage_count,
                conversion_rate
            FROM ads_funnel_daily
            WHERE date_id = %s
            ORDER BY stage_order
            """,
            (date_id,),
        )
