from collections.abc import Callable, Iterator
from contextlib import suppress
from typing import Annotated, TypeVar

from fastapi import APIRouter, Depends, HTTPException, Query

from backend.app.ads.errors import AdsDataNotFound, AdsDatabaseUnavailable
from backend.app.ads.repository import AdsRepository
from backend.app.ads.schemas import AdsBaseModel, KpiResponse, ListResponse, OverviewResponse
from backend.app.ads.service import AdsService
from backend.app.database import connect_mysql

router = APIRouter(prefix="/api/ads", tags=["ads"])

DateQuery = Annotated[
    str | None,
    Query(alias="date", pattern=r"^\d{4}-\d{2}-\d{2}$"),
]
ResponseT = TypeVar("ResponseT")


def get_ads_service() -> Iterator[AdsService]:
    try:
        connection = connect_mysql()
    except Exception as exc:
        raise HTTPException(status_code=503, detail="ADS database query failed") from exc

    try:
        yield AdsService(AdsRepository(connection))
    finally:
        with suppress(Exception):
            connection.close()


AdsServiceDependency = Annotated[AdsService, Depends(get_ads_service)]


def _handle_ads_errors(fetch: Callable[[], ResponseT]) -> ResponseT:
    try:
        return fetch()
    except AdsDataNotFound as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except AdsDatabaseUnavailable as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


def _list_response(items_result: tuple[str, list[AdsBaseModel]]) -> ListResponse:
    date_id, items = items_result
    return ListResponse(
        date_id=date_id,
        items=[item.model_dump(mode="json") for item in items],
    )


@router.get("/overview", response_model=OverviewResponse)
def read_overview(
    service: AdsServiceDependency,
    date_id: DateQuery = None,
) -> OverviewResponse:
    return _handle_ads_errors(lambda: service.get_overview(date_id))


@router.get("/kpi", response_model=KpiResponse)
def read_kpi(
    service: AdsServiceDependency,
    date_id: DateQuery = None,
) -> KpiResponse:
    return _handle_ads_errors(lambda: service.get_kpi(date_id))


@router.get("/trend", response_model=ListResponse)
def read_trend(
    service: AdsServiceDependency,
    date_id: DateQuery = None,
) -> ListResponse:
    return _handle_ads_errors(lambda: _list_response(service.get_trend(date_id)))


@router.get("/products/rank", response_model=ListResponse)
def read_product_rank(
    service: AdsServiceDependency,
    date_id: DateQuery = None,
) -> ListResponse:
    return _handle_ads_errors(lambda: _list_response(service.get_product_rank(date_id)))


@router.get("/categories/share", response_model=ListResponse)
def read_category_share(
    service: AdsServiceDependency,
    date_id: DateQuery = None,
) -> ListResponse:
    return _handle_ads_errors(lambda: _list_response(service.get_category_share(date_id)))


@router.get("/users/profile", response_model=ListResponse)
def read_user_profile(
    service: AdsServiceDependency,
    date_id: DateQuery = None,
) -> ListResponse:
    return _handle_ads_errors(lambda: _list_response(service.get_user_profile(date_id)))


@router.get("/funnel", response_model=ListResponse)
def read_funnel(
    service: AdsServiceDependency,
    date_id: DateQuery = None,
) -> ListResponse:
    return _handle_ads_errors(lambda: _list_response(service.get_funnel(date_id)))
