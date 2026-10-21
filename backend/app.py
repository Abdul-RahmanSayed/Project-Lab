"""One local app, with checked startup and a small FDA router."""

from contextlib import asynccontextmanager
import json
import logging
import time
import uuid

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException

from .config import Settings
from .errors import ApiError, ClientDisconnected, unavailable
from .fda.router import router
from .fda.service import Service
from .jobs import Jobs


log = logging.getLogger("project_lab")


def error_response(error, request_id):
    headers = {"Cache-Control": "no-store", "X-Request-ID": request_id, "X-API-Contract": "fda-v1"}
    if error.code == "SERVICE_BUSY":
        headers["Retry-After"] = "2"
    return JSONResponse({"error": {"code": error.code, "message": error.message,
                                   "details": [], "retryable": error.retryable}, "requestId": request_id},
                        status_code=error.status, headers=headers)


class Boundary:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)
        state = scope.setdefault("state", {})
        state.update(started=time.monotonic(), request_id=str(uuid.uuid4()))
        sent = False
        status = None
        outcome = "complete"

        async def response_send(message):
            nonlocal sent, status
            if message["type"] == "http.response.start":
                sent, status = True, message["status"]
                headers = message.setdefault("headers", [])
                for key, value in ((b"x-request-id", state["request_id"].encode()), (b"x-api-contract", b"fda-v1")):
                    headers[:] = [(k, v) for k, v in headers if k.lower() != key]
                    headers.append((key, value))
                fda = scope["app"].state.fda
                if fda is not None:
                    headers.append((b"x-fda-release-id", fda.release_id.encode()))
            await send(message)

        try:
            if len(scope.get("raw_path", b"")) + len(scope["query_string"]) + bool(scope["query_string"]) > 8192:
                error = ApiError(414, "REQUEST_TARGET_TOO_LONG", "The request URL is too long.")
                return await error_response(error, state["request_id"])(scope, receive, response_send)
            await self.app(scope, receive, response_send)
        except ClientDisconnected:
            outcome = "disconnected"
        except Exception as exc:
            log.error("request_failure type=%s request_id=%s", type(exc).__name__, state["request_id"])
            if not sent:
                error = ApiError(500, "INTERNAL_ERROR", "An unexpected error occurred.")
                await error_response(error, state["request_id"])(scope, receive, response_send)
        finally:
            route = scope.get("route")
            log.info(json.dumps({"route": getattr(route, "path", "unmatched"), "requestId": state["request_id"],
                                 "status": status, "releaseId": getattr(scope["app"].state.fda, "release_id", None),
                                 "outcome": outcome,
                                 "totalMs": round((time.monotonic() - state["started"]) * 1000, 3)}))


def create_app(settings: Settings | None = None):
    settings = settings or Settings.from_environment()

    @asynccontextmanager
    async def lifespan(app):
        app.state.jobs = Jobs(settings.sql_jobs, settings.request_seconds)
        try:
            app.state.fda = Service(settings)
        except Exception as exc:
            app.state.fda = None
            log.error("release_unavailable type=%s", type(exc).__name__)
        try:
            yield
        finally:
            await app.state.jobs.close()

    app = FastAPI(title="Project Lab FDA Explorer", version="1.0.0", lifespan=lifespan, debug=False)
    app.state.fda = None
    app.add_middleware(Boundary)
    if settings.allowed_origins:
        app.add_middleware(CORSMiddleware, allow_origins=list(settings.allowed_origins), allow_methods=["GET"],
                           allow_credentials=False, allow_headers=["If-None-Match"],
                           expose_headers=["ETag", "X-Request-ID", "X-FDA-Release-ID", "X-API-Contract", "Retry-After"])

    @app.exception_handler(ApiError)
    async def expected(request: Request, error: ApiError):
        return error_response(error, request.state.request_id)

    @app.exception_handler(HTTPException)
    async def http_error(request: Request, error: HTTPException):
        code = "NOT_FOUND" if error.status_code == 404 else "METHOD_NOT_ALLOWED"
        response = error_response(ApiError(error.status_code, code, "The route or method is not supported."), request.state.request_id)
        if error.headers and "Allow" in error.headers:
            response.headers["Allow"] = error.headers["Allow"]
        return response

    @app.exception_handler(RequestValidationError)
    async def validation_error(request: Request, error: RequestValidationError):
        return error_response(ApiError(422, "INVALID_PARAMETER", "The request is invalid."), request.state.request_id)

    @app.get("/healthz")
    async def health():
        return JSONResponse({"status": "ok"}, headers={"Cache-Control": "no-store"})

    @app.get("/readyz")
    async def ready():
        fda = app.state.fda
        if fda is None or not fda.ready:
            raise unavailable()
        return JSONResponse({"status": "ready", "releaseId": fda.release_id}, headers={"Cache-Control": "no-store"})

    @app.get("/api/v1/projects")
    async def projects():
        fda = app.state.fda
        return JSONResponse({"projects": [{"id": "fda", "title": "FDA Explorer", "metadataUrl": "/api/v1/fda/metadata",
            "capabilities": ["overview", "reports", "reportDetail"], "ready": fda is not None and fda.ready,
            "activeReleaseId": fda.release_id if fda is not None and fda.ready else None}]}, headers={"Cache-Control": "no-store"})

    app.include_router(router)
    return app
