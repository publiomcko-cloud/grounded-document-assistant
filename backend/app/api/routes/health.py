import time
from datetime import datetime, timezone

from fastapi import APIRouter, status
from fastapi.responses import JSONResponse
from redis import Redis
from sqlalchemy import text

from app.core.config import get_settings
from app.db.session import engine

router = APIRouter()
settings = get_settings()


@router.get("/health")
def health() -> JSONResponse:
    database_check = _check_database()
    redis_check = _check_redis()
    overall_status = (
        "ok"
        if database_check["status"] == "ok" and redis_check["status"] == "ok"
        else "degraded"
    )
    response_status = (
        status.HTTP_200_OK
        if overall_status == "ok"
        else status.HTTP_503_SERVICE_UNAVAILABLE
    )
    return JSONResponse(
        status_code=response_status,
        content={
            "status": overall_status,
            "environment": settings.app_env,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "checks": {
                "database": database_check,
                "redis": redis_check,
            },
        },
    )


def _check_database() -> dict[str, object]:
    started = time.perf_counter()
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        latency_ms = round((time.perf_counter() - started) * 1000, 2)
        return {"status": "ok", "latency_ms": latency_ms}
    except Exception as exc:
        latency_ms = round((time.perf_counter() - started) * 1000, 2)
        return {
            "status": "error",
            "latency_ms": latency_ms,
            "detail": str(exc),
        }


def _check_redis() -> dict[str, object]:
    started = time.perf_counter()
    redis_client = Redis.from_url(settings.redis_connection_url)
    try:
        redis_client.ping()
        latency_ms = round((time.perf_counter() - started) * 1000, 2)
        return {"status": "ok", "latency_ms": latency_ms}
    except Exception as exc:
        latency_ms = round((time.perf_counter() - started) * 1000, 2)
        return {
            "status": "error",
            "latency_ms": latency_ms,
            "detail": str(exc),
        }
    finally:
        redis_client.close()
