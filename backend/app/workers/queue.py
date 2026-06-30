import uuid

from redis import Redis
from rq import Queue

from app.core.config import get_settings
from app.models.enums import LogStatus
from app.services.ingestion import create_ingestion_log, process_document_version

settings = get_settings()


def get_redis_connection() -> Redis:
    return Redis.from_url(settings.redis_connection_url)


def get_ingestion_queue() -> Queue:
    return Queue(
        settings.ingestion_queue_name,
        connection=get_redis_connection(),
        default_timeout=settings.ingestion_job_timeout_seconds,
    )


def enqueue_document_ingestion(
    db,
    *,
    document_version_id: uuid.UUID,
    trigger: str,
) -> str | None:
    if settings.ingestion_queue_eager:
        create_ingestion_log(
            db,
            document_version_id=document_version_id,
            step="queue",
            status=LogStatus.SUCCESS,
            message=f"Ingestion ran inline for {trigger}.",
            details={"mode": "eager", "trigger": trigger},
        )
        db.commit()
        process_document_version(document_version_id)
        return None

    try:
        job = get_ingestion_queue().enqueue(
            "app.workers.tasks.run_document_ingestion",
            str(document_version_id),
        )
    except Exception as exc:
        create_ingestion_log(
            db,
            document_version_id=document_version_id,
            step="queue",
            status=LogStatus.FAILED,
            message="Failed to enqueue ingestion job.",
            details={"trigger": trigger, "error": str(exc)},
        )
        db.commit()
        raise

    create_ingestion_log(
        db,
        document_version_id=document_version_id,
        step="queue",
        status=LogStatus.SUCCESS,
        message="Document was queued for ingestion.",
        details={
            "trigger": trigger,
            "job_id": job.id,
            "queue": settings.ingestion_queue_name,
        },
    )
    db.commit()
    return job.id
