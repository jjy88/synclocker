import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.openapi.utils import get_openapi
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

from app.api import auth, holds, reservations, sessions
from app.db import pool
from app.errors import DomainError

logger = logging.getLogger("synclocker")


@asynccontextmanager
async def lifespan(app: FastAPI):
    pool.open()
    pool.wait()
    yield
    pool.close()


app = FastAPI(title="SyncLocker API", version="0.1.0", lifespan=lifespan)

app.include_router(auth.router)
app.include_router(sessions.router)
app.include_router(holds.router)
app.include_router(reservations.router)
app.mount("/ui", StaticFiles(directory=Path(__file__).parent / "static", html=True), name="ui")


@app.get("/", include_in_schema=False)
def root():
    return RedirectResponse("/ui/")


def _error(status: int, code: str, message: str) -> JSONResponse:
    return JSONResponse(status_code=status, content={"error": {"code": code, "message": message}})


@app.exception_handler(DomainError)
async def domain_error_handler(request: Request, exc: DomainError):
    return _error(exc.status_code, exc.code, exc.message)


@app.exception_handler(RequestValidationError)
async def validation_error_handler(request: Request, exc: RequestValidationError):
    # Invalid input is 400 in our contract. Only field names are returned, never internals.
    fields = sorted({".".join(str(p) for p in e["loc"][1:]) or str(e["loc"][0]) for e in exc.errors()})
    return _error(400, "INVALID_INPUT", "Invalid input: " + ", ".join(fields))


@app.exception_handler(Exception)
async def unexpected_error_handler(request: Request, exc: Exception):
    # The stack trace goes to the server log only, never to the caller.
    logger.exception("Unhandled error on %s %s", request.method, request.url.path)
    return _error(500, "INTERNAL_ERROR", "Internal server error")


def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    schema = get_openapi(title=app.title, version=app.version, routes=app.routes)
    # FastAPI documents invalid input as 422, but our handler returns 400 (every route already
    # lists 400 in its responses). Remove the 422 entries so the contract matches the behaviour.
    for path_item in schema["paths"].values():
        for operation in path_item.values():
            operation.get("responses", {}).pop("422", None)
    for unused in ("HTTPValidationError", "ValidationError"):
        schema.get("components", {}).get("schemas", {}).pop(unused, None)
    app.openapi_schema = schema
    return schema


app.openapi = custom_openapi
