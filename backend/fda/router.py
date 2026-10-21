"""HTTP glue; data policy and calculation stay out of routes."""

from functools import partial
from typing import Annotated

from fastapi import APIRouter, Query, Request, Response

from backend.errors import unavailable
from .models import (DetailQuery, DetailResponse, ErrorResponse, ExploreResponse, MetadataQuery,
                     MetadataResponse, ReportsQuery, ReportsResponse, SelectionQuery)
from .parameters import checked_release, filters, identifier, page_limit, parameters, read_cursor


router = APIRouter(prefix="/api/v1/fda", tags=["FDA"], responses={
    status: {"model": ErrorResponse} for status in (400, 404, 409, 414, 422, 500, 503)})
SELECTION = {"startYear", "endYear", "productFilter", "releaseId"}


def service(request):
    value = request.app.state.fda
    if value is None or not value.ready:
        raise unavailable()
    return value


def data_response(payload, **headers):
    return Response(payload, media_type="application/json", headers={"Cache-Control": "no-store", **headers})


@router.get("/metadata", response_model=MetadataResponse)
async def metadata(request: Request, declared: Annotated[MetadataQuery, Query()]):
    params = parameters(request, {"releaseId"})
    current = service(request)
    checked_release(params, current.release_id)
    return data_response(current.metadata_payload)


@router.get("/explore", response_model=ExploreResponse)
async def overview(request: Request, declared: Annotated[SelectionQuery, Query()]):
    params = parameters(request, SELECTION)
    current = service(request)
    checked_release(params, current.release_id)
    selection = filters(params, current.default_filters)
    if selection == current.default_filters:
        headers = {"Cache-Control": "public, max-age=0, must-revalidate", "ETag": current.default_etag}
        match = request.headers.get("if-none-match", "")
        if any(value.strip() in ("*", current.default_etag, "W/" + current.default_etag) for value in match.split(",")):
            return Response(status_code=304, headers=headers)
        return Response(current.default_payload, media_type="application/json", headers=headers)
    payload = await request.app.state.jobs.run(request, partial(current.execute, "overview", selection))
    return data_response(payload)


@router.get("/reports", response_model=ReportsResponse)
async def reports(request: Request, declared: Annotated[ReportsQuery, Query()]):
    params = parameters(request, SELECTION | {"limit", "cursor", "sort"})
    current = service(request)
    checked_release(params, current.release_id)
    selection = filters(params, current.default_filters)
    limit = page_limit(params)
    after = read_cursor(params.get("cursor"), current.release_id, selection, limit)
    payload = await request.app.state.jobs.run(request, partial(current.execute, "page", selection, limit=limit, after=after))
    return data_response(payload)


@router.get("/reports/detail", response_model=DetailResponse)
async def report(request: Request, declared: Annotated[DetailQuery, Query()]):
    params = parameters(request, SELECTION | {"reportId"})
    current = service(request)
    checked_release(params, current.release_id)
    selection = filters(params, current.default_filters)
    report_id = identifier(params.get("reportId"))
    payload = await request.app.state.jobs.run(request, partial(current.execute, "detail", selection, report_id=report_id))
    return data_response(payload)
