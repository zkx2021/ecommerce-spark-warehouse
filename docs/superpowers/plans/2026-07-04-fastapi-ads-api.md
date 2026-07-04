# FastAPI ADS API Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build FastAPI read APIs that expose MySQL ADS result tables for the future ecommerce dashboard.

**Architecture:** Add a small layered backend: router -> service -> repository -> MySQL connection provider. The router owns HTTP shape, the service owns default-date and overview composition, and the repository owns read-only SQL for the known ADS tables.

**Tech Stack:** FastAPI, Pydantic, mysql-connector-python, pytest, FastAPI TestClient.

---

## File Structure

- Create `backend/app/config.py`: environment-backed MySQL settings.
- Create `backend/app/database.py`: MySQL connection factory and dependency boundary.
- Create `backend/app/ads/errors.py`: domain exceptions used by service/router.
- Create `backend/app/ads/schemas.py`: Pydantic response models.
- Create `backend/app/ads/repository.py`: parameterized SQL for ADS tables.
- Create `backend/app/ads/service.py`: default date resolution and overview composition.
- Create `backend/app/ads/router.py`: `/api/ads` endpoints and HTTP exception mapping.
- Modify `backend/app/main.py`: include ADS router.
- Modify `backend/requirements.txt`: add `mysql-connector-python`.
- Create `backend/README.md`: API startup, environment variables, endpoint list.
- Modify `deploy/scripts/check.ps1`: require new backend files.
- Create `backend/tests/test_ads_config.py`: config tests.
- Create `backend/tests/test_ads_repository.py`: repository SQL and row mapping tests.
- Create `backend/tests/test_ads_service.py`: service behavior tests.
- Create `backend/tests/test_ads_api.py`: endpoint tests.
- Keep `backend/tests/test_health.py`: existing health endpoint regression.

## Task 1: Backend Config, Database Boundary, Errors, and Schemas

**Files:**
- Create: `backend/app/config.py`
- Create: `backend/app/database.py`
- Create: `backend/app/ads/errors.py`
- Create: `backend/app/ads/schemas.py`
- Create: `backend/app/ads/__init__.py`
- Test: `backend/tests/test_ads_config.py`

- [ ] **Step 1: Write failing config and schema tests**

Create `backend/tests/test_ads_config.py`:

```python
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```powershell
python -m pytest backend/tests/test_ads_config.py -q
```

Expected: FAIL because `backend.app.config` and `backend.app.ads.schemas` do not exist.

- [ ] **Step 3: Implement config, database boundary, errors, and schemas**

Create `backend/app/config.py`:

```python
import os
from dataclasses import dataclass


@dataclass(frozen=True)
class MySqlSettings:
    host: str
    port: int
    database: str
    user: str
    password: str

    @classmethod
    def from_env(cls) -> "MySqlSettings":
        return cls(
            host=os.getenv("ADS_MYSQL_HOST", "localhost"),
            port=int(os.getenv("ADS_MYSQL_PORT", "3306")),
            database=os.getenv("ADS_MYSQL_DATABASE", "ecommerce_ads"),
            user=os.getenv("ADS_MYSQL_USER", "ecommerce"),
            password=os.getenv("ADS_MYSQL_PASSWORD", "ecommerce_password"),
        )
```

Create `backend/app/database.py`:

```python
from typing import Any

from backend.app.config import MySqlSettings


def connect_mysql(settings: MySqlSettings | None = None) -> Any:
    import mysql.connector

    resolved = settings or MySqlSettings.from_env()
    return mysql.connector.connect(
        host=resolved.host,
        port=resolved.port,
        database=resolved.database,
        user=resolved.user,
        password=resolved.password,
    )
```

Create `backend/app/ads/__init__.py`:

```python
"""ADS API package."""
```

Create `backend/app/ads/errors.py`:

```python
class AdsError(Exception):
    """Base ADS service error."""


class AdsDataNotFound(AdsError):
    """Raised when requested ADS data does not exist."""


class AdsDatabaseUnavailable(AdsError):
    """Raised when the ADS MySQL database cannot be reached or queried."""
```

Create `backend/app/ads/schemas.py`:

```python
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, ConfigDict, field_serializer


class AdsBaseModel(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    @field_serializer("*", when_used="json")
    def serialize_decimal(self, value: Any) -> Any:
        if isinstance(value, Decimal):
            return float(value)
        return value


class KpiResponse(AdsBaseModel):
    date_id: str
    total_sales_amount: Decimal | float | int
    total_order_count: int
    paid_user_count: int
    avg_order_amount: Decimal | float | int
    payment_conversion_rate: Decimal | float | int


class SalesTrendItem(AdsBaseModel):
    sales_amount: Decimal | float | int
    order_count: int
    paid_user_count: int


class ProductRankItem(AdsBaseModel):
    rank_no: int
    product_id: int
    product_name: str
    category: str | None = None
    sales_quantity: int
    sales_amount: Decimal | float | int


class CategoryShareItem(AdsBaseModel):
    category: str
    sales_amount: Decimal | float | int
    sales_quantity: int
    sales_share: Decimal | float | int


class UserProfileItem(AdsBaseModel):
    dimension_type: str
    dimension_value: str
    user_count: int
    buyer_count: int
    sales_amount: Decimal | float | int


class FunnelItem(AdsBaseModel):
    stage_name: str
    stage_order: int
    stage_count: int
    conversion_rate: Decimal | float | int


class ListResponse(AdsBaseModel):
    date_id: str
    items: list[dict[str, Any]]


class OverviewResponse(AdsBaseModel):
    date_id: str
    kpi: KpiResponse
    trend: list[SalesTrendItem]
    product_rank: list[ProductRankItem]
    category_share: list[CategoryShareItem]
    user_profile: list[UserProfileItem]
    funnel: list[FunnelItem]
```

- [ ] **Step 4: Run tests to verify they pass**

Run:

```powershell
python -m pytest backend/tests/test_ads_config.py -q
```

Expected: PASS.

- [ ] **Step 5: Commit**

```powershell
git add backend/app/config.py backend/app/database.py backend/app/ads/__init__.py backend/app/ads/errors.py backend/app/ads/schemas.py backend/tests/test_ads_config.py
git commit -m "feat: add ads api config and schemas"
```

## Task 2: ADS Repository

**Files:**
- Create: `backend/app/ads/repository.py`
- Test: `backend/tests/test_ads_repository.py`

- [ ] **Step 1: Write failing repository tests**

Create `backend/tests/test_ads_repository.py` with fake cursor and connection objects that verify parameterized SQL:

```python
from decimal import Decimal

import pytest

from backend.app.ads.errors import AdsDatabaseUnavailable
from backend.app.ads.repository import AdsRepository


class FakeCursor:
    def __init__(self, rows=None, fail=False):
        self.rows = rows or []
        self.fail = fail
        self.executed = []

    def execute(self, statement, params=None):
        if self.fail:
            raise RuntimeError("database failed")
        self.executed.append((statement, params))

    def fetchone(self):
        return self.rows[0] if self.rows else None

    def fetchall(self):
        return self.rows

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


class FakeConnection:
    def __init__(self, rows=None, fail=False):
        self.cursor_obj = FakeCursor(rows=rows, fail=fail)

    def cursor(self, dictionary=True):
        assert dictionary is True
        return self.cursor_obj


def test_get_latest_date_reads_max_date_id():
    connection = FakeConnection(rows=[{"date_id": "2026-07-01"}])
    repository = AdsRepository(connection)

    assert repository.get_latest_date() == "2026-07-01"
    statement, params = connection.cursor_obj.executed[0]
    assert "MAX(date_id)" in statement
    assert params is None


def test_get_kpi_fetches_one_row_by_date():
    connection = FakeConnection(
        rows=[
            {
                "date_id": "2026-07-01",
                "total_sales_amount": Decimal("100.00"),
                "total_order_count": 2,
                "paid_user_count": 1,
                "avg_order_amount": Decimal("50.00"),
                "payment_conversion_rate": Decimal("0.5000"),
            }
        ]
    )
    repository = AdsRepository(connection)

    row = repository.get_kpi("2026-07-01")

    assert row["total_order_count"] == 2
    statement, params = connection.cursor_obj.executed[0]
    assert "FROM ads_kpi_daily" in statement
    assert params == ("2026-07-01",)


def test_get_product_rank_orders_by_rank_number():
    connection = FakeConnection(rows=[{"date_id": "2026-07-01", "rank_no": 1, "product_id": 1}])
    repository = AdsRepository(connection)

    rows = repository.get_product_rank("2026-07-01")

    assert rows == [{"date_id": "2026-07-01", "rank_no": 1, "product_id": 1}]
    statement, params = connection.cursor_obj.executed[0]
    assert "FROM ads_product_rank_daily" in statement
    assert "ORDER BY rank_no" in statement
    assert params == ("2026-07-01",)


def test_repository_wraps_database_failures():
    repository = AdsRepository(FakeConnection(fail=True))

    with pytest.raises(AdsDatabaseUnavailable, match="ADS database query failed"):
        repository.get_funnel("2026-07-01")
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```powershell
python -m pytest backend/tests/test_ads_repository.py -q
```

Expected: FAIL because `backend.app.ads.repository` does not exist.

- [ ] **Step 3: Implement repository**

Create `backend/app/ads/repository.py`:

```python
from typing import Any

from backend.app.ads.errors import AdsDatabaseUnavailable


class AdsRepository:
    def __init__(self, connection: Any):
        self.connection = connection

    def _fetch_one(self, statement: str, params: tuple[Any, ...] | None = None) -> dict[str, Any] | None:
        try:
            with self.connection.cursor(dictionary=True) as cursor:
                cursor.execute(statement, params)
                return cursor.fetchone()
        except Exception as exc:
            raise AdsDatabaseUnavailable("ADS database query failed") from exc

    def _fetch_all(self, statement: str, params: tuple[Any, ...] | None = None) -> list[dict[str, Any]]:
        try:
            with self.connection.cursor(dictionary=True) as cursor:
                cursor.execute(statement, params)
                return list(cursor.fetchall())
        except Exception as exc:
            raise AdsDatabaseUnavailable("ADS database query failed") from exc

    def get_latest_date(self) -> str | None:
        row = self._fetch_one(
            """
            SELECT MAX(date_id) AS date_id
            FROM (
                SELECT date_id FROM ads_kpi_daily
                UNION SELECT date_id FROM ads_sales_trend_daily
                UNION SELECT date_id FROM ads_product_rank_daily
                UNION SELECT date_id FROM ads_category_share_daily
                UNION SELECT date_id FROM ads_user_profile_daily
                UNION SELECT date_id FROM ads_funnel_daily
            ) dates
            """
        )
        return row["date_id"] if row and row.get("date_id") else None

    def get_kpi(self, date_id: str) -> dict[str, Any] | None:
        return self._fetch_one(
            """
            SELECT date_id, total_sales_amount, total_order_count, paid_user_count,
                   avg_order_amount, payment_conversion_rate
            FROM ads_kpi_daily
            WHERE date_id = %s
            """,
            (date_id,),
        )

    def get_trend(self, date_id: str) -> list[dict[str, Any]]:
        return self._fetch_all(
            """
            SELECT date_id, sales_amount, order_count, paid_user_count
            FROM ads_sales_trend_daily
            WHERE date_id = %s
            ORDER BY date_id
            """,
            (date_id,),
        )

    def get_product_rank(self, date_id: str) -> list[dict[str, Any]]:
        return self._fetch_all(
            """
            SELECT date_id, rank_no, product_id, product_name, category, sales_quantity, sales_amount
            FROM ads_product_rank_daily
            WHERE date_id = %s
            ORDER BY rank_no
            """,
            (date_id,),
        )

    def get_category_share(self, date_id: str) -> list[dict[str, Any]]:
        return self._fetch_all(
            """
            SELECT date_id, category, sales_amount, sales_quantity, sales_share
            FROM ads_category_share_daily
            WHERE date_id = %s
            ORDER BY sales_share DESC, sales_amount DESC, category
            """,
            (date_id,),
        )

    def get_user_profile(self, date_id: str) -> list[dict[str, Any]]:
        return self._fetch_all(
            """
            SELECT date_id, dimension_type, dimension_value, user_count, buyer_count, sales_amount
            FROM ads_user_profile_daily
            WHERE date_id = %s
            ORDER BY dimension_type, user_count DESC, dimension_value
            """,
            (date_id,),
        )

    def get_funnel(self, date_id: str) -> list[dict[str, Any]]:
        return self._fetch_all(
            """
            SELECT date_id, stage_name, stage_order, stage_count, conversion_rate
            FROM ads_funnel_daily
            WHERE date_id = %s
            ORDER BY stage_order
            """,
            (date_id,),
        )
```

- [ ] **Step 4: Run tests to verify they pass**

Run:

```powershell
python -m pytest backend/tests/test_ads_repository.py -q
```

Expected: PASS.

- [ ] **Step 5: Commit**

```powershell
git add backend/app/ads/repository.py backend/tests/test_ads_repository.py
git commit -m "feat: add ads repository"
```

## Task 3: ADS Service

**Files:**
- Create: `backend/app/ads/service.py`
- Test: `backend/tests/test_ads_service.py`

- [ ] **Step 1: Write failing service tests**

Create `backend/tests/test_ads_service.py`:

```python
from decimal import Decimal

import pytest

from backend.app.ads.errors import AdsDataNotFound
from backend.app.ads.service import AdsService


class FakeRepository:
    def __init__(self):
        self.latest_date = "2026-07-02"
        self.calls = []
        self.kpi = {
            "date_id": "2026-07-02",
            "total_sales_amount": Decimal("100.00"),
            "total_order_count": 2,
            "paid_user_count": 1,
            "avg_order_amount": Decimal("50.00"),
            "payment_conversion_rate": Decimal("0.5000"),
        }
        self.trend = [{"date_id": "2026-07-02", "sales_amount": Decimal("100.00"), "order_count": 2, "paid_user_count": 1}]
        self.product_rank = [{"date_id": "2026-07-02", "rank_no": 1, "product_id": 1, "product_name": "Keyboard", "category": "electronics", "sales_quantity": 3, "sales_amount": Decimal("99.00")}]
        self.category_share = [{"date_id": "2026-07-02", "category": "electronics", "sales_amount": Decimal("99.00"), "sales_quantity": 3, "sales_share": Decimal("1.0000")}]
        self.user_profile = [{"date_id": "2026-07-02", "dimension_type": "gender", "dimension_value": "unknown", "user_count": 1, "buyer_count": 1, "sales_amount": Decimal("99.00")}]
        self.funnel = [{"date_id": "2026-07-02", "stage_name": "payment", "stage_order": 3, "stage_count": 1, "conversion_rate": Decimal("1.0000")}]

    def get_latest_date(self):
        return self.latest_date

    def get_kpi(self, date_id):
        self.calls.append(("kpi", date_id))
        return self.kpi

    def get_trend(self, date_id):
        self.calls.append(("trend", date_id))
        return self.trend

    def get_product_rank(self, date_id):
        self.calls.append(("product_rank", date_id))
        return self.product_rank

    def get_category_share(self, date_id):
        self.calls.append(("category_share", date_id))
        return self.category_share

    def get_user_profile(self, date_id):
        self.calls.append(("user_profile", date_id))
        return self.user_profile

    def get_funnel(self, date_id):
        self.calls.append(("funnel", date_id))
        return self.funnel


def test_service_uses_explicit_date_for_kpi():
    repo = FakeRepository()
    service = AdsService(repo)

    result = service.get_kpi("2026-07-01")

    assert result.date_id == "2026-07-02"
    assert repo.calls == [("kpi", "2026-07-01")]


def test_service_uses_latest_date_when_date_omitted():
    repo = FakeRepository()
    service = AdsService(repo)

    service.get_funnel(None)

    assert repo.calls == [("funnel", "2026-07-02")]


def test_service_raises_not_found_when_latest_date_missing():
    repo = FakeRepository()
    repo.latest_date = None
    service = AdsService(repo)

    with pytest.raises(AdsDataNotFound, match="No ADS data is available"):
        service.get_kpi(None)


def test_service_raises_not_found_when_section_empty():
    repo = FakeRepository()
    repo.trend = []
    service = AdsService(repo)

    with pytest.raises(AdsDataNotFound, match="No ADS trend data"):
        service.get_trend("2026-07-02")


def test_overview_composes_all_sections():
    repo = FakeRepository()
    service = AdsService(repo)

    overview = service.get_overview(None)

    assert overview.date_id == "2026-07-02"
    assert overview.kpi.total_order_count == 2
    assert len(overview.trend) == 1
    assert len(overview.product_rank) == 1
    assert len(overview.category_share) == 1
    assert len(overview.user_profile) == 1
    assert len(overview.funnel) == 1
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```powershell
python -m pytest backend/tests/test_ads_service.py -q
```

Expected: FAIL because `backend.app.ads.service` does not exist.

- [ ] **Step 3: Implement service**

Create `backend/app/ads/service.py`:

```python
from backend.app.ads.errors import AdsDataNotFound
from backend.app.ads.repository import AdsRepository
from backend.app.ads.schemas import (
    CategoryShareItem,
    FunnelItem,
    KpiResponse,
    OverviewResponse,
    ProductRankItem,
    SalesTrendItem,
    UserProfileItem,
)


class AdsService:
    def __init__(self, repository: AdsRepository):
        self.repository = repository

    def _resolve_date(self, date_id: str | None) -> str:
        if date_id:
            return date_id
        latest = self.repository.get_latest_date()
        if not latest:
            raise AdsDataNotFound("No ADS data is available")
        return latest

    def get_kpi(self, date_id: str | None) -> KpiResponse:
        resolved = self._resolve_date(date_id)
        row = self.repository.get_kpi(resolved)
        if not row:
            raise AdsDataNotFound(f"No ADS KPI data found for date {resolved}")
        return KpiResponse(**row)

    def get_trend(self, date_id: str | None) -> tuple[str, list[SalesTrendItem]]:
        resolved = self._resolve_date(date_id)
        rows = self.repository.get_trend(resolved)
        if not rows:
            raise AdsDataNotFound(f"No ADS trend data found for date {resolved}")
        return resolved, [SalesTrendItem(**row) for row in rows]

    def get_product_rank(self, date_id: str | None) -> tuple[str, list[ProductRankItem]]:
        resolved = self._resolve_date(date_id)
        rows = self.repository.get_product_rank(resolved)
        if not rows:
            raise AdsDataNotFound(f"No ADS product rank data found for date {resolved}")
        return resolved, [ProductRankItem(**row) for row in rows]

    def get_category_share(self, date_id: str | None) -> tuple[str, list[CategoryShareItem]]:
        resolved = self._resolve_date(date_id)
        rows = self.repository.get_category_share(resolved)
        if not rows:
            raise AdsDataNotFound(f"No ADS category share data found for date {resolved}")
        return resolved, [CategoryShareItem(**row) for row in rows]

    def get_user_profile(self, date_id: str | None) -> tuple[str, list[UserProfileItem]]:
        resolved = self._resolve_date(date_id)
        rows = self.repository.get_user_profile(resolved)
        if not rows:
            raise AdsDataNotFound(f"No ADS user profile data found for date {resolved}")
        return resolved, [UserProfileItem(**row) for row in rows]

    def get_funnel(self, date_id: str | None) -> tuple[str, list[FunnelItem]]:
        resolved = self._resolve_date(date_id)
        rows = self.repository.get_funnel(resolved)
        if not rows:
            raise AdsDataNotFound(f"No ADS funnel data found for date {resolved}")
        return resolved, [FunnelItem(**row) for row in rows]

    def get_overview(self, date_id: str | None) -> OverviewResponse:
        resolved = self._resolve_date(date_id)
        kpi = self.get_kpi(resolved)
        _, trend = self.get_trend(resolved)
        _, product_rank = self.get_product_rank(resolved)
        _, category_share = self.get_category_share(resolved)
        _, user_profile = self.get_user_profile(resolved)
        _, funnel = self.get_funnel(resolved)
        return OverviewResponse(
            date_id=resolved,
            kpi=kpi,
            trend=trend,
            product_rank=product_rank,
            category_share=category_share,
            user_profile=user_profile,
            funnel=funnel,
        )
```

- [ ] **Step 4: Run tests to verify they pass**

Run:

```powershell
python -m pytest backend/tests/test_ads_service.py -q
```

Expected: PASS.

- [ ] **Step 5: Commit**

```powershell
git add backend/app/ads/service.py backend/tests/test_ads_service.py
git commit -m "feat: add ads service layer"
```

## Task 4: ADS Router and App Wiring

**Files:**
- Create: `backend/app/ads/router.py`
- Modify: `backend/app/main.py`
- Test: `backend/tests/test_ads_api.py`

- [ ] **Step 1: Write failing API tests**

Create `backend/tests/test_ads_api.py`:

```python
from decimal import Decimal

from fastapi.testclient import TestClient

from backend.app.ads.errors import AdsDataNotFound, AdsDatabaseUnavailable
from backend.app.ads.router import get_ads_service
from backend.app.ads.schemas import KpiResponse, OverviewResponse
from backend.app.main import app


class FakeAdsService:
    def get_kpi(self, date_id):
        return KpiResponse(
            date_id=date_id or "2026-07-02",
            total_sales_amount=Decimal("100.00"),
            total_order_count=2,
            paid_user_count=1,
            avg_order_amount=Decimal("50.00"),
            payment_conversion_rate=Decimal("0.5000"),
        )

    def get_trend(self, date_id):
        return date_id or "2026-07-02", [{"sales_amount": Decimal("100.00"), "order_count": 2, "paid_user_count": 1}]

    def get_product_rank(self, date_id):
        return date_id or "2026-07-02", [{"rank_no": 1, "product_id": 1, "product_name": "Keyboard", "category": "electronics", "sales_quantity": 3, "sales_amount": Decimal("99.00")}]

    def get_category_share(self, date_id):
        return date_id or "2026-07-02", [{"category": "electronics", "sales_amount": Decimal("99.00"), "sales_quantity": 3, "sales_share": Decimal("1.0000")}]

    def get_user_profile(self, date_id):
        return date_id or "2026-07-02", [{"dimension_type": "gender", "dimension_value": "unknown", "user_count": 1, "buyer_count": 1, "sales_amount": Decimal("99.00")}]

    def get_funnel(self, date_id):
        return date_id or "2026-07-02", [{"stage_name": "payment", "stage_order": 3, "stage_count": 1, "conversion_rate": Decimal("1.0000")}]

    def get_overview(self, date_id):
        kpi = self.get_kpi(date_id)
        return OverviewResponse(
            date_id=kpi.date_id,
            kpi=kpi,
            trend=[],
            product_rank=[],
            category_share=[],
            user_profile=[],
            funnel=[],
        )


def test_kpi_endpoint_returns_explicit_date():
    app.dependency_overrides[get_ads_service] = lambda: FakeAdsService()
    client = TestClient(app)

    response = client.get("/api/ads/kpi?date=2026-07-01")

    app.dependency_overrides.clear()
    assert response.status_code == 200
    assert response.json()["date_id"] == "2026-07-01"
    assert response.json()["total_sales_amount"] == 100.0


def test_kpi_endpoint_accepts_omitted_date():
    app.dependency_overrides[get_ads_service] = lambda: FakeAdsService()
    client = TestClient(app)

    response = client.get("/api/ads/kpi")

    app.dependency_overrides.clear()
    assert response.status_code == 200
    assert response.json()["date_id"] == "2026-07-02"


def test_trend_endpoint_returns_items_wrapper():
    app.dependency_overrides[get_ads_service] = lambda: FakeAdsService()
    client = TestClient(app)

    response = client.get("/api/ads/trend?date=2026-07-01")

    app.dependency_overrides.clear()
    assert response.status_code == 200
    assert response.json() == {
        "date_id": "2026-07-01",
        "items": [{"sales_amount": 100.0, "order_count": 2, "paid_user_count": 1}],
    }


def test_invalid_date_returns_422():
    app.dependency_overrides[get_ads_service] = lambda: FakeAdsService()
    client = TestClient(app)

    response = client.get("/api/ads/kpi?date=2026-7-1")

    app.dependency_overrides.clear()
    assert response.status_code == 422


def test_ads_not_found_maps_to_404():
    class MissingService(FakeAdsService):
        def get_kpi(self, date_id):
            raise AdsDataNotFound("No ADS KPI data found")

    app.dependency_overrides[get_ads_service] = lambda: MissingService()
    client = TestClient(app)

    response = client.get("/api/ads/kpi")

    app.dependency_overrides.clear()
    assert response.status_code == 404
    assert response.json() == {"detail": "No ADS KPI data found"}


def test_database_failure_maps_to_503():
    class BrokenService(FakeAdsService):
        def get_kpi(self, date_id):
            raise AdsDatabaseUnavailable("ADS database query failed")

    app.dependency_overrides[get_ads_service] = lambda: BrokenService()
    client = TestClient(app)

    response = client.get("/api/ads/kpi")

    app.dependency_overrides.clear()
    assert response.status_code == 503
    assert response.json() == {"detail": "ADS database query failed"}
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```powershell
python -m pytest backend/tests/test_ads_api.py -q
```

Expected: FAIL because `backend.app.ads.router` does not exist and `main.py` has not included the router.

- [ ] **Step 3: Implement router and app wiring**

Create `backend/app/ads/router.py`:

```python
import re
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query

from backend.app.ads.errors import AdsDatabaseUnavailable, AdsDataNotFound
from backend.app.ads.repository import AdsRepository
from backend.app.ads.schemas import (
    KpiResponse,
    ListResponse,
    OverviewResponse,
)
from backend.app.ads.service import AdsService
from backend.app.database import connect_mysql


router = APIRouter(prefix="/api/ads", tags=["ads"])
DateQuery = Annotated[str | None, Query(pattern=r"^\d{4}-\d{2}-\d{2}$")]


def get_ads_service() -> AdsService:
    return AdsService(AdsRepository(connect_mysql()))


def _handle_ads_error(exc: Exception) -> None:
    if isinstance(exc, AdsDataNotFound):
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    if isinstance(exc, AdsDatabaseUnavailable):
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    raise exc


@router.get("/kpi", response_model=KpiResponse)
def get_kpi(date: DateQuery = None, service: AdsService = Depends(get_ads_service)) -> KpiResponse:
    try:
        return service.get_kpi(date)
    except Exception as exc:
        _handle_ads_error(exc)


@router.get("/trend", response_model=ListResponse)
def get_trend(date: DateQuery = None, service: AdsService = Depends(get_ads_service)) -> ListResponse:
    try:
        date_id, items = service.get_trend(date)
        return ListResponse(date_id=date_id, items=[item.model_dump() for item in items])
    except Exception as exc:
        _handle_ads_error(exc)


@router.get("/products/rank", response_model=ListResponse)
def get_product_rank(date: DateQuery = None, service: AdsService = Depends(get_ads_service)) -> ListResponse:
    try:
        date_id, items = service.get_product_rank(date)
        return ListResponse(date_id=date_id, items=[item.model_dump() for item in items])
    except Exception as exc:
        _handle_ads_error(exc)


@router.get("/categories/share", response_model=ListResponse)
def get_category_share(date: DateQuery = None, service: AdsService = Depends(get_ads_service)) -> ListResponse:
    try:
        date_id, items = service.get_category_share(date)
        return ListResponse(date_id=date_id, items=[item.model_dump() for item in items])
    except Exception as exc:
        _handle_ads_error(exc)


@router.get("/users/profile", response_model=ListResponse)
def get_user_profile(date: DateQuery = None, service: AdsService = Depends(get_ads_service)) -> ListResponse:
    try:
        date_id, items = service.get_user_profile(date)
        return ListResponse(date_id=date_id, items=[item.model_dump() for item in items])
    except Exception as exc:
        _handle_ads_error(exc)


@router.get("/funnel", response_model=ListResponse)
def get_funnel(date: DateQuery = None, service: AdsService = Depends(get_ads_service)) -> ListResponse:
    try:
        date_id, items = service.get_funnel(date)
        return ListResponse(date_id=date_id, items=[item.model_dump() for item in items])
    except Exception as exc:
        _handle_ads_error(exc)


@router.get("/overview", response_model=OverviewResponse)
def get_overview(date: DateQuery = None, service: AdsService = Depends(get_ads_service)) -> OverviewResponse:
    try:
        return service.get_overview(date)
    except Exception as exc:
        _handle_ads_error(exc)
```

Remove the unused `import re` if the implementation does not use it after editing.

Modify `backend/app/main.py`:

```python
from fastapi import FastAPI

from backend.app.ads.router import router as ads_router


app = FastAPI(title="Ecommerce Spark Warehouse API")
app.include_router(ads_router)


@app.get("/api/health")
def health() -> dict[str, str]:
    return {
        "status": "ok",
        "service": "ecommerce-spark-warehouse-api"
    }
```

- [ ] **Step 4: Run API and health tests**

Run:

```powershell
python -m pytest backend/tests/test_ads_api.py backend/tests/test_health.py -q
```

Expected: PASS.

- [ ] **Step 5: Commit**

```powershell
git add backend/app/ads/router.py backend/app/main.py backend/tests/test_ads_api.py
git commit -m "feat: add ads api routes"
```

## Task 5: Dependencies, Documentation, and Foundation Check

**Files:**
- Modify: `backend/requirements.txt`
- Create: `backend/README.md`
- Modify: `README.md`
- Modify: `deploy/scripts/check.ps1`
- Test: `backend/tests/test_ads_assets.py`

- [ ] **Step 1: Write failing asset/documentation tests**

Create `backend/tests/test_ads_assets.py`:

```python
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_backend_requirements_include_mysql_connector():
    requirements = read("backend/requirements.txt")

    assert "mysql-connector-python" in requirements


def test_backend_readme_documents_ads_api():
    readme = read("backend/README.md").lower()

    assert "fastapi ads api" in readme
    assert "ads_mysql_host" in readme
    assert "/api/ads/overview" in readme
    assert "/api/ads/products/rank" in readme
    assert "warehouse/scripts/export_ads_mysql.ps1" in readme


def test_foundation_check_includes_ads_api_files():
    script = read("deploy/scripts/check.ps1")

    for path in (
        "backend/app/ads/router.py",
        "backend/app/ads/service.py",
        "backend/app/ads/repository.py",
        "backend/app/ads/schemas.py",
        "backend/app/config.py",
        "backend/app/database.py",
        "backend/README.md",
    ):
        assert path in script
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```powershell
python -m pytest backend/tests/test_ads_assets.py -q
```

Expected: FAIL because docs/check updates are missing.

- [ ] **Step 3: Update dependencies and docs**

Append to `backend/requirements.txt`:

```text
mysql-connector-python==9.1.0
```

Create `backend/README.md`:

```markdown
# FastAPI ADS API

The backend exposes read-only ADS data APIs for the ecommerce dashboard. It reads MySQL tables loaded by the warehouse exporter.

## Start

```powershell
python -m pip install -r backend/requirements.txt
python -m uvicorn backend.app.main:app --reload
```

## MySQL Environment

- `ADS_MYSQL_HOST`, default `localhost`
- `ADS_MYSQL_PORT`, default `3306`
- `ADS_MYSQL_DATABASE`, default `ecommerce_ads`
- `ADS_MYSQL_USER`, default `ecommerce`
- `ADS_MYSQL_PASSWORD`, default `ecommerce_password`

Before calling ADS APIs, run:

```powershell
powershell -ExecutionPolicy Bypass -File warehouse/scripts/export_ads_mysql.ps1 -BatchDate 2026-07-01
```

## Endpoints

- `GET /api/health`
- `GET /api/ads/overview`
- `GET /api/ads/kpi`
- `GET /api/ads/trend`
- `GET /api/ads/products/rank`
- `GET /api/ads/categories/share`
- `GET /api/ads/users/profile`
- `GET /api/ads/funnel`

Each ADS endpoint accepts optional `?date=YYYY-MM-DD`. If omitted, the API reads the latest available ADS date.
```

Update root `README.md` tech stack line from planned API to active API:

```markdown
- API: FastAPI ADS data service
```

Update `deploy/scripts/check.ps1` by adding these required paths:

```powershell
"backend/README.md",
"backend/app/config.py",
"backend/app/database.py",
"backend/app/ads/router.py",
"backend/app/ads/service.py",
"backend/app/ads/repository.py",
"backend/app/ads/schemas.py",
"backend/app/ads/errors.py",
```

- [ ] **Step 4: Run asset and foundation checks**

Run:

```powershell
python -m pytest backend/tests/test_ads_assets.py -q
powershell -ExecutionPolicy Bypass -File deploy/scripts/check.ps1
```

Expected: PASS.

- [ ] **Step 5: Commit**

```powershell
git add backend/requirements.txt backend/README.md README.md deploy/scripts/check.ps1 backend/tests/test_ads_assets.py
git commit -m "docs: document ads api backend"
```

## Task 6: Final Verification, Review, Push, and PR

**Files:**
- No new implementation files unless final review finds a blocker.

- [ ] **Step 1: Run backend tests**

Run:

```powershell
python -m pytest backend/tests -q
```

Expected: all backend tests pass.

- [ ] **Step 2: Run shared foundation check**

Run:

```powershell
powershell -ExecutionPolicy Bypass -File deploy/scripts/check.ps1
```

Expected: `Project foundation check passed.`

- [ ] **Step 3: Run final status checks**

Run:

```powershell
git status --short --branch
git log --oneline --decorate -8
```

Expected:

- Current branch is `codex/phase6-fastapi-ads-api`.
- Only unrelated untracked `architecture-options.html` may remain.
- Phase 6 commits are present after `main`.

- [ ] **Step 4: Request code review**

Use `superpowers:requesting-code-review` with:

- Base: `main`
- Head: `HEAD`
- Description: FastAPI ADS API backend reading MySQL ADS tables.
- Requirements: `docs/superpowers/specs/2026-07-04-fastapi-ads-api-design.md`

Fix Critical and Important findings before pushing.

- [ ] **Step 5: Push and create PR**

Push with the local proxy if direct GitHub access is unstable:

```powershell
git -c http.proxy=http://127.0.0.1:7897 -c https.proxy=http://127.0.0.1:7897 push -u origin codex/phase6-fastapi-ads-api
```

Create a ready PR against `main` with:

```markdown
## Summary
- add FastAPI ADS data service endpoints
- add MySQL-backed ADS repository and service layer
- document backend startup and ADS API usage

## Tests
- `python -m pytest backend/tests -q`
- `powershell -ExecutionPolicy Bypass -File deploy/scripts/check.ps1`
```

- [ ] **Step 6: Report completion**

Report:

- PR URL
- Verification commands and pass counts
- Any remaining untracked files
- Suggested next phase: Vue/ECharts dashboard consuming `/api/ads/*`

## Plan Self-Review

- Spec coverage: endpoints, optional date behavior, MySQL config, layered architecture, error handling, testing, and docs are covered by Tasks 1-6.
- Completeness scan: no unresolved marker language remains.
- Type consistency: `date_id` is used internally and in responses; query parameter remains `date`; repository methods match service calls; service outputs match router response models.
