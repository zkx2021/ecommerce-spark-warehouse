import pytest

from backend.app.ads.errors import AdsDatabaseUnavailable
from backend.app.ads.repository import AdsRepository


class FakeCursor:
    def __init__(self, one=None, all_rows=None, fail=False, fetch_fail=False, close_fail=False):
        self.one = one
        self.all_rows = all_rows or []
        self.fail = fail
        self.fetch_fail = fetch_fail
        self.close_fail = close_fail
        self.executed = []
        self.closed = False

    def execute(self, sql, params=None):
        if self.fail:
            raise RuntimeError("database is down")
        self.executed.append((sql, params))

    def fetchone(self):
        if self.fetch_fail:
            raise RuntimeError("fetch failed")
        return self.one

    def fetchall(self):
        if self.fetch_fail:
            raise RuntimeError("fetch failed")
        return self.all_rows

    def close(self):
        self.closed = True
        if self.close_fail:
            raise RuntimeError("close failed")


class FakeConnection:
    def __init__(self, cursor):
        self.cursor_instance = cursor
        self.cursor_kwargs = []

    def cursor(self, **kwargs):
        self.cursor_kwargs.append(kwargs)
        return self.cursor_instance


class FailingCursorConnection:
    def __init__(self):
        self.cursor_kwargs = []

    def cursor(self, **kwargs):
        self.cursor_kwargs.append(kwargs)
        raise RuntimeError("cannot create cursor")


def make_repository(cursor):
    connection = FakeConnection(cursor)
    return AdsRepository(connection), connection


def normalize_sql(sql):
    return " ".join(sql.split())


def assert_date_query(repository_method, expected_table, expected_order_by):
    row = {"date_id": "2026-07-01"}
    cursor = FakeCursor(all_rows=[row])
    repository, connection = make_repository(cursor)

    assert repository_method(repository, "2026-07-01") == [row]

    sql, params = cursor.executed[0]
    normalized_sql = normalize_sql(sql)
    assert f"FROM {expected_table}" in normalized_sql
    assert "WHERE date_id = %s" in normalized_sql
    assert expected_order_by in normalized_sql
    assert params == ("2026-07-01",)
    assert connection.cursor_kwargs == [{"dictionary": True}]
    assert cursor.closed is True


def test_get_latest_date_reads_max_date_over_all_ads_tables():
    cursor = FakeCursor(one={"date_id": "2026-07-01"})
    repository, connection = make_repository(cursor)

    assert repository.get_latest_date() == "2026-07-01"

    sql, params = cursor.executed[0]
    normalized_sql = normalize_sql(sql)
    assert params is None
    assert normalized_sql.count("MAX(date_id)") == 7
    assert "ads_kpi_daily" in normalized_sql
    assert "ads_sales_trend_daily" in normalized_sql
    assert "ads_product_rank_daily" in normalized_sql
    assert "ads_category_share_daily" in normalized_sql
    assert "ads_user_profile_daily" in normalized_sql
    assert "ads_funnel_daily" in normalized_sql
    assert connection.cursor_kwargs == [{"dictionary": True}]
    assert cursor.closed is True


def test_get_latest_date_returns_none_when_no_ads_date_exists():
    cursor = FakeCursor(one={"date_id": None})
    repository, _connection = make_repository(cursor)

    assert repository.get_latest_date() is None


def test_get_kpi_fetches_one_row_by_parameterized_date():
    row = {
        "date_id": "2026-07-01",
        "total_sales_amount": 100,
        "total_order_count": 2,
        "paid_user_count": 1,
        "avg_order_amount": 50,
        "payment_conversion_rate": 0.5,
    }
    cursor = FakeCursor(one=row)
    repository, connection = make_repository(cursor)

    assert repository.get_kpi("2026-07-01") == row

    sql, params = cursor.executed[0]
    normalized_sql = normalize_sql(sql)
    assert "SELECT date_id, total_sales_amount, total_order_count, paid_user_count, avg_order_amount, payment_conversion_rate" in normalized_sql
    assert "FROM ads_kpi_daily" in normalized_sql
    assert "WHERE date_id = %s" in normalized_sql
    assert params == ("2026-07-01",)
    assert connection.cursor_kwargs == [{"dictionary": True}]
    assert cursor.closed is True


def test_get_trend_fetches_rows_by_date_ordered_by_date_id():
    assert_date_query(
        lambda repository, date_id: repository.get_trend(date_id),
        "ads_sales_trend_daily",
        "ORDER BY date_id",
    )


def test_get_product_rank_fetches_rows_by_date_ordered_by_rank_no():
    assert_date_query(
        lambda repository, date_id: repository.get_product_rank(date_id),
        "ads_product_rank_daily",
        "ORDER BY rank_no",
    )


def test_get_category_share_fetches_rows_by_date_ordered_by_share_amount_category():
    assert_date_query(
        lambda repository, date_id: repository.get_category_share(date_id),
        "ads_category_share_daily",
        "ORDER BY sales_share DESC, sales_amount DESC, category",
    )


def test_get_user_profile_fetches_rows_by_date_ordered_by_dimension_and_count():
    assert_date_query(
        lambda repository, date_id: repository.get_user_profile(date_id),
        "ads_user_profile_daily",
        "ORDER BY dimension_type, user_count DESC, dimension_value",
    )


def test_get_funnel_fetches_rows_by_date_ordered_by_stage_order():
    assert_date_query(
        lambda repository, date_id: repository.get_funnel(date_id),
        "ads_funnel_daily",
        "ORDER BY stage_order",
    )


def test_repository_wraps_database_exceptions():
    cursor = FakeCursor(fail=True)
    repository, _connection = make_repository(cursor)

    with pytest.raises(AdsDatabaseUnavailable, match="ADS database query failed") as exc_info:
        repository.get_kpi("2026-07-01")

    assert isinstance(exc_info.value.__cause__, RuntimeError)
    assert cursor.closed is True


@pytest.mark.parametrize(
    "cursor,repository_call",
    [
        (FakeCursor(fetch_fail=True), lambda repository: repository.get_kpi("2026-07-01")),
        (FakeCursor(fetch_fail=True), lambda repository: repository.get_trend("2026-07-01")),
        (FakeCursor(fail=True, close_fail=True), lambda repository: repository.get_kpi("2026-07-01")),
        (FakeCursor(fetch_fail=True, close_fail=True), lambda repository: repository.get_kpi("2026-07-01")),
    ],
)
def test_repository_preserves_query_exception_when_cleanup_fails(cursor, repository_call):
    repository, _connection = make_repository(cursor)

    with pytest.raises(AdsDatabaseUnavailable, match="ADS database query failed") as exc_info:
        repository_call(repository)

    assert isinstance(exc_info.value.__cause__, RuntimeError)
    assert str(exc_info.value.__cause__) != "close failed"
    assert cursor.closed is True


@pytest.mark.parametrize(
    "repository_call",
    [
        lambda repository: repository.get_kpi("2026-07-01"),
        lambda repository: repository.get_trend("2026-07-01"),
    ],
)
def test_repository_wraps_cursor_creation_exceptions(repository_call):
    connection = FailingCursorConnection()
    repository = AdsRepository(connection)

    with pytest.raises(AdsDatabaseUnavailable, match="ADS database query failed") as exc_info:
        repository_call(repository)

    assert isinstance(exc_info.value.__cause__, RuntimeError)
    assert connection.cursor_kwargs == [{"dictionary": True}]
