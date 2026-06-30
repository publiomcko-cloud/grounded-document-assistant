import logging
import time
import uuid

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.requests import Request

from app.api.router import api_router
from app.core.config import get_settings

settings = get_settings()
logger = logging.getLogger("grounded_document_assistant.api")

if not logging.getLogger().handlers:
    logging.basicConfig(level=logging.INFO, format="%(message)s")

app = FastAPI(
    title="Grounded Document Assistant API",
    description=("Backend control plane for the Grounded Document Assistant MVP."),
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def add_request_observability(request: Request, call_next):
    request_id = request.headers.get("X-Request-Id", str(uuid.uuid4()))
    workspace_id = request.headers.get("X-Workspace-Id", "-")
    started = time.perf_counter()
    request.state.request_id = request_id

    try:
        response = await call_next(request)
    except Exception:
        duration_ms = round((time.perf_counter() - started) * 1000, 2)
        logger.exception(
            (
                "request_failed request_id=%s method=%s path=%s "
                "workspace_id=%s duration_ms=%s"
            ),
            request_id,
            request.method,
            request.url.path,
            workspace_id,
            duration_ms,
        )
        raise

    duration_ms = round((time.perf_counter() - started) * 1000, 2)
    response.headers["X-Request-Id"] = request_id
    logger.info(
        (
            "request_complete request_id=%s method=%s path=%s status_code=%s "
            "workspace_id=%s duration_ms=%s"
        ),
        request_id,
        request.method,
        request.url.path,
        response.status_code,
        workspace_id,
        duration_ms,
    )
    return response


app.include_router(api_router)
